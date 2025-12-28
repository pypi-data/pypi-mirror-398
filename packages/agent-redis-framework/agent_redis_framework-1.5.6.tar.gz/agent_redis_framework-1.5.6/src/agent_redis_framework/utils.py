# Redis 通用操作
from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Dict, List, Optional

import redis
from .redis_client import get_redis_client

class RedisUtil:

    def __init__(self) -> None:
        self.redis: redis.Redis = get_redis_client()

    # 键操作
    def get(self, key: str) -> Optional[str]:
        return self.redis.get(key)  # type: ignore

    def expire(self, key: str, seconds: int) -> bool:
        """为键设置过期时间（秒），返回是否设置成功。"""
        return bool(self.redis.expire(key, seconds))

    def delete(self, key: str) -> bool:
        """删除单个键，返回是否删除成功。"""
        return bool(self.redis.delete(key))
        
    def delete_many(self, keys: Iterable[str]) -> bool:
        """删除多个键，返回是否删除成功。"""
        return bool(self.redis.delete(*keys))

    def exists(self, key: str) -> bool:
        """检查键是否存在。"""
        return bool(self.redis.exists(key))

    def set(self, key: str, value: Any, ex: Optional[int] = None, px: Optional[int] = None, 
            nx: bool = False, xx: bool = False) -> bool:
        """设置键值对
        
        Args:
            key: 键名
            value: 值
            ex: 过期时间（秒），与 px 互斥
            px: 过期时间（毫秒），与 ex 互斥
            nx: 仅在键不存在时设置，与 xx 互斥
            xx: 仅在键存在时设置，与 nx 互斥
            
        Returns:
            bool: 是否设置成功
        """
        result = self.redis.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        return bool(result)

    def set_nx(self, key: str, value: Any) -> bool:
        """仅在键不存在时设置键值对（SET IF NOT EXISTS）
        Args:
            key: 键名
            value: 值
        Returns:
            bool: 是否设置成功（True表示键不存在且设置成功，False表示键已存在）
        """
        return bool(self.redis.setnx(key, value))

    def ttl(self, key: str) -> int:
        """获取键的剩余生存时间（秒），-1表示永不过期，-2表示键不存在。"""
        result = self.redis.ttl(key)
        return result  # type: ignore

    def type(self, key: str) -> str:
        """获取键的数据类型。"""
        result = self.redis.type(key)
        return result.decode('utf-8') if isinstance(result, bytes) else str(result)

    def keys(self, pattern: str = "*") -> List[str]:
        """根据模式匹配获取键列表。注意：在生产环境中慎用，建议使用 scan。"""
        result = self.redis.keys(pattern)
        return [key.decode('utf-8') if isinstance(key, bytes) else str(key) for key in result]  # type: ignore

    def rename(self, old_key: str, new_key: str) -> bool:
        """重命名键，返回是否成功。"""
        try:
            self.redis.rename(old_key, new_key)
            return True
        except redis.ResponseError:
            return False

    def persist(self, key: str) -> bool:
        """移除键的过期时间，使其永不过期。"""
        return bool(self.redis.persist(key))

    def info(self, section: Optional[str] = None) -> Dict[str, Any]:
        """获取 Redis 服务器信息。"""
        return self.redis.info(section)  # type: ignore

    def dbsize(self) -> int:
        """获取当前数据库中键的数量。"""
        return self.redis.dbsize()  # type: ignore

    def flushdb(self, asynchronous: bool = False) -> bool:
        """清空当前数据库。"""
        try:
            self.redis.flushdb(asynchronous=asynchronous)
            return True
        except Exception:
            return False

    def flushall(self, asynchronous: bool = False) -> bool:
        """清空所有数据库。"""
        try:
            self.redis.flushall(asynchronous=asynchronous)
            return True
        except Exception:
            return False

    def select(self, db: int) -> bool:
        """选择数据库。"""
        try:
            self.redis.select(db)
            return True
        except Exception:
            return False

    def memory_usage(self, key: str) -> Optional[int]:
        """获取键占用的内存字节数。"""
        try:
            return self.redis.memory_usage(key)  # type: ignore
        except Exception:
            return None

    # 事务操作
    def multi_exec(self, commands: List[tuple]) -> List[Any]:
        """执行事务操作，commands 为 (方法名, 参数) 的列表。"""
        pipe = self.redis.pipeline()
        try:
            for cmd, args in commands:
                getattr(pipe, cmd)(*args)
            return pipe.execute()
        except Exception as e:
            pipe.reset()
            raise e
    
    # 全局操作
    def ping(self) -> bool:
        """测试 Redis 连接是否正常。"""
        try:
            return self.redis.ping()  # type: ignore
        except Exception:
            return False


# 为了让 mypy/pyright 等类型检查器更友好地识别导出项
__all__ = ["RedisUtil"]
