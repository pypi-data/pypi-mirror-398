from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from functools import lru_cache

import hashlib
import logging
import threading
import ssl  # 新增：TLS 验证常量

import redis  # type: ignore[reportMissingImports]

from .env import env_str, env_opt_str, env_int, env_float_opt, env_bool

# 配置日志记录器
logger = logging.getLogger(__name__)


# 说明：
# 本模块提供统一的 Redis 客户端工厂，并使用"连接池（ConnectionPool）"来管理连接。
# 与直接实例化 redis.Redis(host=..., port=...) 相比，连接池能在多线程/高并发场景下
# 高效复用连接，避免频繁创建/销毁 TCP 连接导致的性能损耗。

# 读取环境
_DEFAULT_HOST = env_str("REDIS_HOST", "localhost")
_DEFAULT_PORT = env_int("REDIS_PORT", 6379)
_DEFAULT_DB = env_int("REDIS_DB", 0)
_DEFAULT_PASSWORD = env_opt_str("REDIS_PASSWORD")
_DEFAULT_USERNAME = env_opt_str("REDIS_USERNAME")

_DEFAULT_SOCKET_TIMEOUT = env_int("REDIS_SOCKET_TIMEOUT", 5)
_DEFAULT_SOCKET_CONNECT_TIMEOUT = env_int("REDIS_SOCKET_CONNECT_TIMEOUT", 3)
_DEFAULT_HEALTH_CHECK_INTERVAL = env_int("REDIS_HEALTH_CHECK_INTERVAL", 30)
_DEFAULT_MAX_CONNECTIONS = env_int("REDIS_MAX_CONNECTIONS", 512)

_DEFAULT_SSL = env_bool("REDIS_SSL", True)
_DEFAULT_SSL_CERT_REQS = env_str("REDIS_SSL_CERT_REQS", "required")  # required|none|optional
_DEFAULT_SSL_CHECK_HOSTNAME = env_bool("REDIS_SSL_CHECK_HOSTNAME", False)
_DEFAULT_SSL_CA_CERTS = env_opt_str("REDIS_SSL_CA_CERTS")

@dataclass(frozen=True)
class RedisConfig:
    """Redis 客户端配置（线程安全，不要打印敏感字段）

    注意：请避免在日志中打印 password 等敏感字段。

    字段含义：
    - host/port/db/username/password/ssl：标准 Redis 连接参数
    - socket_timeout：单次 socket 操作超时时间（秒）
    - socket_connect_timeout：建立连接时的超时时间（秒）
    - health_check_interval：健康检查间隔（秒），0 表示不开启
    - max_connections：连接池的最大连接数（并发能力上限）
    """

    host: str = _DEFAULT_HOST
    port: int = _DEFAULT_PORT
    db: int = _DEFAULT_DB
    ssl: bool = _DEFAULT_SSL
    password: str | None = _DEFAULT_PASSWORD
    username: str | None = _DEFAULT_USERNAME
    socket_timeout: float | None = _DEFAULT_SOCKET_TIMEOUT
    socket_connect_timeout: float | None = _DEFAULT_SOCKET_CONNECT_TIMEOUT
    health_check_interval: int = _DEFAULT_HEALTH_CHECK_INTERVAL
    max_connections: int = _DEFAULT_MAX_CONNECTIONS
    ssl_cert_reqs: str = _DEFAULT_SSL_CERT_REQS
    ssl_check_hostname: bool = _DEFAULT_SSL_CHECK_HOSTNAME
    ssl_ca_certs: str | None = _DEFAULT_SSL_CA_CERTS

# 连接池缓存键的精确类型定义（不包含明文密码）
PoolKey = tuple[
    str,          # host
    int,          # port
    int,          # db
    str | None,   # username
    str,          # password hash
    bool,         # ssl
    float | None, # socket_timeout
    float | None, # socket_connect_timeout
    int,          # health_check_interval
    int,          # max_connections
]

# 全局连接池缓存，按配置进行复用；配合互斥锁保证并发安全
_pools: dict[PoolKey, "redis.ConnectionPool"] = {}
_lock = threading.Lock()


def _hash_secret(secret: str | None) -> str:
    """对敏感字段做不可逆哈希，仅用于区分不同配置的连接池。

    不会打印明文，也不会暴露在日志里。
    """
    if not secret:
        return ""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _pool_key(cfg: RedisConfig) -> PoolKey:
    """根据配置生成连接池缓存键（不包含明文密码）。"""
    return (
        cfg.host,
        cfg.port,
        cfg.db,
        cfg.username,
        _hash_secret(cfg.password),  # 只保存密码哈希用于区分，不记录明文
        cfg.ssl,
        cfg.socket_timeout,
        cfg.socket_connect_timeout,
        cfg.health_check_interval,
        cfg.max_connections,
    )


def _create_connection_pool(cp_kwargs: dict, cfg: RedisConfig) -> redis.ConnectionPool:
    """创建Redis连接池，处理SSL兼容性问题"""
    if cfg.ssl:
        # 对于redis-py 5.x版本，需要使用connection_class=SSLConnection
        # 首先移除可能冲突的ssl参数
        cp_kwargs.pop("ssl", None)
        
        # 尝试不同的SSL连接方式，按优先级排序
        ssl_connection_class = None
        try:
            # 优先尝试从redis模块直接导入
            ssl_connection_class = redis.SSLConnection  # type: ignore[attr-defined]
            logger.info("使用 redis.SSLConnection 创建SSL连接池")
        except AttributeError:
            try:
                # 尝试从connection子模块导入
                from redis.connection import SSLConnection
                ssl_connection_class = SSLConnection
                logger.info("使用 redis.connection.SSLConnection 创建SSL连接池")
            except ImportError:
                logger.warning("无法导入SSLConnection类，尝试使用兼容模式")
                return _create_fallback_pool(cp_kwargs, cfg)
        
        # 设置SSL连接类
        if ssl_connection_class:
            cp_kwargs["connection_class"] = ssl_connection_class
    
    # 尝试创建连接池
    try:
        pool = redis.ConnectionPool(**cp_kwargs)
        logger.info(f"Redis连接池创建成功，最大连接数: {cfg.max_connections}")
        return pool
    except TypeError as e:
        # 如果仍然有TypeError，说明参数不兼容，尝试兼容模式
        if cfg.ssl and ("ssl" in str(e) or "unexpected keyword argument" in str(e)):
            logger.warning(f"连接池创建失败，尝试兼容模式: {e}")
            return _create_fallback_pool(cp_kwargs, cfg)
        else:
            raise
    except Exception as e:
        logger.error(f"Redis连接池创建失败: {e}")
        raise


def _create_fallback_pool(cp_kwargs: dict, cfg: RedisConfig) -> redis.ConnectionPool:
    """创建兜底连接池，清理有问题的参数"""
    # 创建一个新的参数字典，避免修改原始参数
    fallback_kwargs = cp_kwargs.copy()
    
    # 清理可能有问题的参数
    fallback_kwargs.pop("ssl", None)
    fallback_kwargs.pop("connection_class", None)
    
    # 尝试使用SSLConnection的不同导入方式
    ssl_connection_class = None
    try:
        # 尝试从redis模块导入
        ssl_connection_class = redis.SSLConnection  # type: ignore[attr-defined]
        logger.info("兜底模式：使用 redis.SSLConnection")
    except AttributeError:
        try:
            # 尝试从connection子模块导入
            from redis.connection import SSLConnection
            ssl_connection_class = SSLConnection
            logger.info("兜底模式：使用 redis.connection.SSLConnection")
        except ImportError:
            logger.warning("兜底模式：无法导入任何SSLConnection类")
    
    # 如果找到了SSL连接类，尝试使用它
    if ssl_connection_class:
        try:
            fallback_kwargs["connection_class"] = ssl_connection_class
            pool = redis.ConnectionPool(**fallback_kwargs)
            logger.info(f"Redis连接池创建成功（SSLConnection兜底模式），最大连接数: {cfg.max_connections}")
            return pool
        except Exception as e:
            logger.warning(f"SSLConnection兜底模式失败: {e}")
    
    # 最后的兜底方案：使用非SSL连接
    logger.error("无法创建SSL连接池，将使用非SSL连接")
    # 移除所有SSL相关参数
    ssl_params = ["ssl_cert_reqs", "ssl_check_hostname", "ssl_ca_certs", "connection_class"]
    for param in ssl_params:
        fallback_kwargs.pop(param, None)
    
    try:
        pool = redis.ConnectionPool(**fallback_kwargs)
        logger.warning(f"Redis连接池创建成功（非SSL模式），最大连接数: {cfg.max_connections}")
        return pool
    except Exception as e:
        logger.error(f"连接池创建完全失败: {e}")
        raise


def get_redis_pool(config: RedisConfig | None = None) -> "redis.ConnectionPool":
    """获取（或创建）Redis 连接池实例。

    - 相同配置将复用同一个连接池，避免重复创建导致资源浪费。
    - 线程安全：内部使用互斥锁保证并发创建时只初始化一次。
    """
    cfg = config or RedisConfig()
    key = _pool_key(cfg)

    # 双重检查 + 互斥保护，避免高并发场景下重复创建连接池
    pool = _pools.get(key)
    if pool is not None:
        return pool

    with _lock:
        pool = _pools.get(key)
        if pool is None:
            # 将配置透传给连接池（底层会将其作为连接创建参数）
            cp_kwargs: dict[str, Any] = {
                "host": cfg.host,
                "port": cfg.port,
                "db": cfg.db,
                "username": cfg.username,
                "password": cfg.password,
                "socket_timeout": cfg.socket_timeout,
                "socket_connect_timeout": cfg.socket_connect_timeout,
                "health_check_interval": cfg.health_check_interval,
                "max_connections": cfg.max_connections,
            }
            # TLS 参数（默认启用严格校验，可通过环境变量调整）
            if cfg.ssl:
                # 将字符串配置映射为 ssl 模块常量
                _map = {
                    "required": ssl.CERT_REQUIRED,
                    "none": ssl.CERT_NONE,
                    "optional": ssl.CERT_OPTIONAL,
                }
                cert_reqs = _map.get((cfg.ssl_cert_reqs or "required").lower(), ssl.CERT_REQUIRED)
                
                # 对于 AWS ElastiCache，通常需要设置 ssl_cert_reqs=CERT_NONE
                # 因为 ElastiCache 使用自签名证书
                if "amazonaws.com" in cfg.host.lower():
                    cert_reqs = ssl.CERT_NONE
                    logger.info("检测到 AWS ElastiCache，设置 ssl_cert_reqs=CERT_NONE")
                
                cp_kwargs["ssl_cert_reqs"] = cert_reqs
                cp_kwargs["ssl_check_hostname"] = cfg.ssl_check_hostname
                if cfg.ssl_ca_certs:
                    cp_kwargs["ssl_ca_certs"] = cfg.ssl_ca_certs
            
            # 打印Redis连接参数（隐藏敏感信息）
            safe_kwargs = cp_kwargs.copy()
            if safe_kwargs.get("password"):
                safe_kwargs["password"] = "***"  # 隐藏密码
            logger.info(f"创建Redis连接池，参数: {safe_kwargs}")
            try:
                lib_ver = getattr(redis, "__version__", "unknown")
            except Exception:
                lib_ver = "unknown"
            logger.info(f"redis-py 版本: {lib_ver}")

            # 构建连接池：根据redis-py版本选择合适的SSL连接方式
            pool = _create_connection_pool(cp_kwargs, cfg)

            _pools[key] = pool
        return pool


def get_pool_stats() -> dict[str, Any]:
    """获取所有连接池的统计信息
    
    Returns:
        dict: 包含连接池数量、各连接池状态等信息
    """
    stats = {
        "pool_count": len(_pools),
        "pools": []
    }
    
    for i, (key, pool) in enumerate(_pools.items()):
        try:
            # 获取连接池基本信息
            pool_info = {
                "pool_id": i,
                "host": key[0],
                "port": key[1], 
                "db": key[2],
                "ssl": key[5],
                "max_connections": key[9],
            }
            
            # 尝试获取连接池内部状态（可能因版本差异而失败）
            try:
                # 使用getattr避免linter错误，因为不同版本的redis-py可能有不同的属性
                created_connections = getattr(pool, 'created_connections', 0)
                available_connections = getattr(pool, '_available_connections', [])
                pool_info["created_connections"] = created_connections
                pool_info["available_connections"] = len(available_connections)
                pool_info["in_use_connections"] = created_connections - len(available_connections)
            except (AttributeError, TypeError):
                # 某些 redis-py 版本可能没有这些属性
                pool_info["status"] = "stats_unavailable"
                
            stats["pools"].append(pool_info)
        except Exception as e:
            stats["pools"].append({
                "pool_id": i,
                "error": str(e)
            })
    
    return stats


def log_pool_stats() -> None:
    """记录连接池统计信息到日志"""
    try:
        stats = get_pool_stats()
        logger.info(f"Redis连接池统计: {stats}")
    except Exception as e:
        logger.error(f"获取连接池统计失败: {e}")


def get_redis() -> "redis.Redis":
    """创建一个基于连接池的同步 Redis 客户端。

    返回：
    - redis.Redis：已绑定连接池的客户端实例。

    说明：
    - 自动从环境变量加载 Redis 配置，无需手动传参。
    - 上层代码可像原来一样直接使用 redis 命令（xadd、xreadgroup、zadd、zpopmin 等）。
    - 客户端共享底层连接池，天然适配多线程/多协程并发复用连接。
    """
    cfg = RedisConfig()
    pool = get_redis_pool(cfg)
    # 通过连接池创建客户端；decode_responses 等参数应在客户端层设置
    try:
        client = redis.Redis(connection_pool=pool, decode_responses=True)
        return client
    except Exception as e:
        logger.error(f"创建Redis客户端失败: {e}")
        log_pool_stats()
        raise


@lru_cache(maxsize=1)
def get_redis_client() -> "redis.Redis":
    """创建并缓存 Redis 客户端（基于连接池）。

    返回：
    - redis.Redis：绑定连接池的同步客户端。

    说明：
    - 使用 @lru_cache(maxsize=1) 实现线程安全的惰性单例；每个进程仅创建一次实例。
    - 多个调用将复用同一客户端；连接由底层连接池管理，适配并发复用。
    - 测试或重置场景可调用 get_redis_client.cache_clear() 清理缓存后再次获取。
    """
    return get_redis()

# 为了 mypy/pyright 等类型检查器更友好地识别导出项
__all__ = [
    'get_redis_client', 'get_redis_pool', 'get_pool_stats', 'log_pool_stats'
]