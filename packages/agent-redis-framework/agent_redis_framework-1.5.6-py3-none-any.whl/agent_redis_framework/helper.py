from agent_redis_framework import SortedSetQueue, StreamClient, HashClient, RedisUtil


# 按键返回 SortedSetQueue 实例（移除缓存，避免连接池碎片化）
def get_sorted_set_queue(key: str) -> SortedSetQueue:
    """获取指定 key 的 SortedSetQueue 实例    
    底层连接池会自动复用连接，无需在此层缓存实例。
    """
    return SortedSetQueue(key)


# 按键返回 HashClient 实例
def get_hash_client(key: str) -> HashClient:
    """获取 Redis HashClient 实例
    """
    return HashClient(key)


# 按流名回 StreamClient 实例
def get_streams_client(stream: str) -> StreamClient:
    """获取 Redis Stream 客户端（按流名）
    """
    return StreamClient(stream)

# RedisUtil 保持单例缓存（因为无 key 参数，不会碎片化）
from functools import lru_cache

@lru_cache(maxsize=1)
def get_redis_util() -> RedisUtil:
    """获取 RedisUtil 单例实例
    RedisUtil 无 key 参数，可以安全使用单例缓存。
    """
    return RedisUtil()

__all__ = [
    "get_sorted_set_queue",
    "get_streams_client", 
    "get_hash_client",
    "get_redis_util",
]