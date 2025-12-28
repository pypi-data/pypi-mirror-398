from __future__ import annotations

from collections.abc import Iterable

import redis
from ..redis_client import get_redis_client

# 支持的标量类型：与项目中 meta/payload 的风格保持一致（标量优先，复杂结构请先序列化为字符串）
SupportedScalar = bytes | str | int | float


def _to_str(v: SupportedScalar) -> str:
    """将值转换为字符串以便写入 Redis。

    - bytes -> utf-8 解码
    - str   -> 原样返回
    - int/float -> 使用 str() 转换
    """
    if isinstance(v, bytes):
        return v.decode("utf-8")
    if isinstance(v, (int, float)):
        return str(v)
    return v


def _from_bytes(v: bytes | str | None) -> str | None:
    """将从 Redis 读取到的值转换为 str（如果是 bytes 则解码）。"""
    if v is None:
        return None
    if isinstance(v, bytes):
        return v.decode("utf-8")
    return v


class HashClient:
    """Redis Hash 数据结构的便捷封装

    提供对常见 Hash 操作的高层封装，统一处理 bytes/str 的转换，确保类型友好：
    - set/get：单字段写入与读取
    - set_many/get_many：多字段批量操作
    - get_all/keys/values/len：便捷查询
    - incr/incr_float：数值自增
    - exists/delete/clear：字段与键的删除

    使用方式：
        >>> h = HashClient("user:1")
        >>> h.set("name", "Alice")
        >>> h.get("name")
        'Alice'
    """

    def __init__(self, key: str) -> None:
        self.key: str = key
        self.redis: redis.Redis = get_redis_client()

    # 基础写入
    def set(self, field: str, value: SupportedScalar) -> int:
        """设置单个字段。
        返回：1 表示新字段，0 表示覆盖。
        """
        return int(self.redis.hset(self.key, field, _to_str(value)))  # type: ignore

    def setnx(self, field: str, value: SupportedScalar) -> bool:
        """仅当字段不存在时设置，返回 True 表示设置成功。"""
        return bool(self.redis.hsetnx(self.key, field, _to_str(value)))

    def set_many(self, mapping: dict[str, SupportedScalar]) -> None:
        """批量设置多个字段。"""
        if not mapping:
            return
        data = {k: _to_str(v) for k, v in mapping.items()}
        # redis-py: hset(name, mapping={...})
        self.redis.hset(self.key, mapping=data)

    # 基础读取
    def get(self, field: str) -> str | None:
        """获取单个字段的值；不存在则返回 None。"""
        return _from_bytes(self.redis.hget(self.key, field))  # type: ignore

    def get_many(self, fields: Iterable[str]) -> dict[str, str | None]:
        """批量获取多个字段，返回字典（保持字段对应的顺序不做强保证）。"""
        fs = list(fields)
        if not fs:
            return {}
        values = self.redis.hmget(self.key, fs)
        # values: list[bytes|str|None]
        return {f: _from_bytes(v) for f, v in zip(fs, values)}  # type: ignore

    def get_all(self) -> dict[str, str]:
        """获取整个 Hash（字段和值均以 str 返回）。"""
        raw = self.redis.hgetall(self.key)  # type: ignore
        out: dict[str, str] = {}
        for k, v in raw.items():  # type: ignore
            kk = k.decode("utf-8") if isinstance(k, bytes) else k
            vv = v.decode("utf-8") if isinstance(v, bytes) else v
            out[kk] = vv
        return out

    # 统计与键空间
    def len(self) -> int:
        """返回字段数量。"""
        return int(self.redis.hlen(self.key))  # type: ignore

    def keys(self) -> list[str]:
        """返回所有字段名（str）。"""
        raw = self.redis.hkeys(self.key)  # type: ignore
        return [k.decode("utf-8") if isinstance(k, bytes) else k for k in raw]  # type: ignore

    def values(self) -> list[str]:
        """返回所有字段值（str）。"""
        raw = self.redis.hvals(self.key)  # type: ignore
        return [v.decode("utf-8") if isinstance(v, bytes) else v for v in raw]  # type: ignore

    # 数值操作
    def incr(self, field: str, amount: int = 1) -> int:
        """将字段的整数值增加 amount，返回最新值。"""
        return int(self.redis.hincrby(self.key, field, amount))  # type: ignore

    def incr_float(self, field: str, amount: float = 1.0) -> float:
        """将字段的浮点数值增加 amount，返回最新值。"""
        return float(self.redis.hincrbyfloat(self.key, field, amount))  # type: ignore

    # 字段存在与删除
    def exists(self, field: str) -> bool:
        """字段是否存在。"""
        return bool(self.redis.hexists(self.key, field))

    def delete(self, *fields: str) -> int:
        """删除一个或多个字段，返回删除的字段数量。"""
        if not fields:
            return 0
        return int(self.redis.hdel(self.key, *fields))  # type: ignore

    def clear(self) -> None:
        """删除整个 Hash 键。"""
        self.redis.delete(self.key)