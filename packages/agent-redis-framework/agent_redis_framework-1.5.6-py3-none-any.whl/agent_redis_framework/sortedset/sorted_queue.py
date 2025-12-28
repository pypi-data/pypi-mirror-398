from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from typing import Callable, cast

import redis
from ..redis_client import get_redis_client


@dataclass(frozen=True)
class SortedTask:
    """任务数据类
    
    Attributes:
        payload: 任务的负载数据
        meta: 任务的元数据
    """
    payload: str
    meta: dict[str, bytes | str | int | float] = field(default_factory=dict)

    def to_json(self) -> str:
        """将任务对象序列化为JSON字符串
        
        Returns:
            str: 紧凑格式的JSON字符串，用于存储到Redis中
        """
        return json.dumps(asdict(self), separators=(",", ":"))

    @staticmethod
    def from_json(data: str) -> "SortedTask":
        """从JSON字符串反序列化为任务对象
        
        Args:
            data: JSON格式的任务数据字符串
            
        Returns:
            SortedTask: 反序列化后的任务对象
        """
        obj = json.loads(data)
        return SortedTask(payload=obj.get("payload", ""), meta=obj.get("meta", {}))


class SortedSetQueue:
    """基于Redis有序集合的任务调度队列
    
    这是一个轻量级的Redis有序集合封装，用于任务调度和优先级队列。
    
    主要功能：
    - zadd: 推送带有分数的任务（如优先级或时间戳）
    - zrange: 按分数顺序读取任务
    - zrem: 处理后移除任务
    
    在多消费者场景中，使用ZPOPMIN进行原子性任务声明，
    它会原子性地弹出分数最低的成员。
    
    适用场景：
    - 优先级任务队列
    - 延时任务调度
    - 多消费者任务分发
    
    重构说明：
    - key参数已从构造函数移到各个方法中
    - 一个SortedSetQueue实例可以操作多个不同的sortedset
    - 避免了为每个sortedset创建单独实例的开销
    """

    def __init__(self, key: str) -> None:
        """初始化有序集合队列
        
        Args:            
            key: Redis中有序集合的键名
            redis_client: Redis客户端实例，如果未提供则使用默认客户端
        """
        self.key = key
        self.redis: redis.Redis = get_redis_client()

    def push(self, task: SortedTask, score: float | None = None):
        """将任务推送到队列中
        
        Args:
            task: 要推送的任务对象
            score: 任务的分数（用于排序，分数越低优先级越高）。
                  如果不提供，则使用当前时间戳作为分数
        """
        if score is None:
            score = time.time()
        self.redis.zadd(self.key, {task.to_json(): score})

    def pop_and_handle(
        self,
        callback: Callable[[float, SortedTask], bool],
        *,
        on_failure: Callable[[float, SortedTask], None] | None = None,
        ascending: bool = True,
        count: int = 1,
    ) -> int:
        """原子性地弹出并处理任务
        Args:
            callback: 任务处理函数，返回True表示成功
            on_failure: 失败处理回调函数
            ascending: True表示从低分数开始弹出
            count: 弹出任务数量
        Returns:
            int: 实际处理的任务数量
        """
        result = cast(list[tuple[bytes, float]],
                     self.redis.zpopmin(self.key, max(1, count)) if ascending else self.redis.zpopmax(self.key, max(1, count)))
        
        if not result:
            return 0

        # 遍历处理所有弹出的任务
        processed_count = 0
        for member, score in result:
            task = SortedTask.from_json(member.decode() if isinstance(member, bytes) else member)
            success = callback(float(score), task)
            if not success and on_failure:
                on_failure(float(score), task)
            processed_count += 1
            
        return processed_count

    def get_max_score(self) -> float:
        """获取队列中任务的最大分数
        Returns:
            float | None: 队列中任务的最大分数，如果队列为空则返回None
        """
        # 使用ZRANGE获取分数最高的一个成员（倒序，从-1到-1）
        result = cast(list[tuple[bytes, float]], 
                     self.redis.zrange(self.key, -1, -1, withscores=True))
        
        if not result:
            return 0.0
        
        _, score = result[0]
        return float(score)

    def get_min_score(self) -> float | None:
        """获取队列中任务的最小分数
        Returns:
            float | None: 队列中任务的最小分数，如果队列为空则返回None
        """
        # 使用ZRANGE获取分数最低的一个成员（正序，从0到0）
        result = cast(list[tuple[bytes, float]], 
                     self.redis.zrange(self.key, 0, 0, withscores=True))
        
        if not result:
            return -1.0
        
        _, score = result[0]
        return float(score)

    def remove(self, task: SortedTask) -> bool:
        """从队列中移除指定的任务
        Args:
            task: 要移除的任务对象
        Returns:
            bool: True表示成功移除，False表示任务不存在
        """
        removed_count = int(cast(int, self.redis.zrem(self.key, task.to_json())))
        return removed_count > 0

    def size(self) -> int:
        """获取队列中任务的数量
        Returns:
            int: 队列中任务的总数
        """
        return int(cast(int, self.redis.zcard(self.key)))

    def clear(self) -> None:
        """清空队列中的所有任务
        注意：此操作会删除整个Redis键，不可恢复
        """
        self.redis.delete(self.key)

    def scan_and_handle(
        self,
        callback: Callable[[float, SortedTask], None],
        *,
        count: int | None = None,
        limit: int | None = None,
    ) -> int:
        """使用ZSCAN游标遍历，并将每个成员的 (score, task) 交由回调处理

        Args:
            callback: 回调函数，入参为 (score, task)；遍历期间如需删除/修改，请在回调内部自行调用
                      相关 Redis 操作（例如通过 `get_redis_client()` 或外部持有的客户端执行 `zrem/zadd`）。
            count: 传递给 ZSCAN 的每批数量提示（非严格限制）
            limit: 最大处理条数；为 None 时不限制

        Returns:
            int: 实际处理的成员数量（即回调被调用的次数）

        注意:
            - ZSCAN 为弱一致遍历，遍历期间进行删除/更新可能导致跳过或重复项，这是 Redis 的预期行为。
        """
        processed = 0
        cursor = 0
        while True:
            cursor_items = cast(tuple[int, list[tuple[str | bytes, float]]], self.redis.zscan(self.key, cursor=cursor, count=count))
            cursor, items = cursor_items
            if not items:
                if cursor == 0:
                    break
            for member, score in items:
                member_str = member.decode() if isinstance(member, bytes) else member
                task = SortedTask.from_json(member_str)
                callback(float(score), task)
                processed += 1
                if limit is not None and processed >= limit:
                    return processed
            if cursor == 0:
                break
        return processed
