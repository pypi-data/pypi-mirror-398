from __future__ import annotations

import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable

import redis  # type: ignore[reportMissingImports]
from ..env import env_int
from ..redis_client import get_redis_client

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class StreamMsg:
    """Redis流消息数据类    
    Attributes:
        payload: 消息的字段数据，可以是JSON字符串或原生字符串
        meta: 消息的元数据，类型为 dict[str, bytes | str | int | float]
    """
    payload: str
    meta: dict[str, bytes | str | int | float] = field(default_factory=dict)


class StreamClient:
    """Redis流的高级客户端, 支持消费者组功能
    这是一个基于Redis流的高级封装客户端, 提供了完整的流处理功能。
    """

    def __init__(self, stream: str) -> None:
        """初始化Redis流客户端
        
        Args:
            stream: 流名称
        """
        self.stream: str = stream
        self.redis: redis.Redis = get_redis_client()
        self._stop_event = threading.Event()
        self._reader_thread: threading.Thread | None = None
        self._worker_pool_size = env_int("STREAM_WORKER_POOL_SIZE", 4)
        self._executor = ThreadPoolExecutor(max_workers=self._worker_pool_size)


    def ensure_group(self, group: str) -> None:
        """确保消费者组存在, 如果不存在则创建
        Args:
            group: 消费者组名称
        Note:
            如果消费者组已存在, 会忽略BUSYGROUP错误；
            如果流不存在, 会自动创建流。
        """
        try:
            self.redis.xgroup_create(name=self.stream, groupname=group, id="$", mkstream=True)
        except Exception as e:
            # 消费者组可能已经存在
            msg = str(e)
            if "BUSYGROUP" in msg:
                return
            raise
        
    def push(self, msg: StreamMsg, maxlen: int | None = None) -> str:
        """将消息推送到 Redis Stream。
        存储时将按扁平化字段写入，键前缀为 '__m_'.
        """
        fields: dict[str, Any] = {"payload": msg.payload}
        # 校验并扁平化 meta
        if msg.meta:
            for k, v in msg.meta.items():
                fields[f"__m_{k}"] = v
        # 推送
        if maxlen is not None:
            msg_key = self.redis.xadd(self.stream, fields, maxlen=maxlen, approximate=True)  # type: ignore
        else:
            msg_key = self.redis.xadd(self.stream, fields)  # type: ignore
        # 确保返回字符串类型
        if isinstance(msg_key, bytes):
            return msg_key.decode('utf-8')
        return str(msg_key)

    def _read_messages(self, group: str, consumer: str, count: int, block_ms: int, callback: Callable[[str, StreamMsg], bool]) -> None:
        """独立线程中运行的消息读取和处理逻辑
        Args:
            group: 消费者组名称
            consumer: 消费者名称
            count: 每次读取的消息数量
            block_ms: 阻塞等待时间（毫秒）
            callback: 消息处理回调函数
        """
        self.ensure_group(group)
        
        while not self._stop_event.is_set():
            try:
                entries = self.redis.xreadgroup(
                    groupname=group,
                    consumername=consumer,
                    streams={self.stream: ">"},
                    count=count,
                    block=block_ms,
                )
            except Exception:
                time.sleep(0.5)
                continue

            if not entries:
                continue

            for _, messages in entries:  # type: ignore
                for msg_key, fields in messages:
                    if self._stop_event.is_set():
                        return
                    
                    # 解码字段
                    decoded_fields = {
                        k.decode('utf-8') if isinstance(k, bytes) else k:
                        v.decode('utf-8') if isinstance(v, bytes) else v
                        for k, v in fields.items()
                    }
                    
                    # 提取 payload 和 meta
                    payload = decoded_fields.pop("payload", "")
                    meta = {k[4:]: v for k, v in decoded_fields.items() if k.startswith("__m_")}
                    
                    # 创建消息对象
                    msg_id = msg_key.decode('utf-8') if isinstance(msg_key, bytes) else msg_key
                    msg = StreamMsg(payload=payload, meta=meta)
                    
                    # 直接提交给线程池处理
                    self._executor.submit(self._process_message, msg_id, msg, msg_key, group, callback)
                        

    def _process_message(self, msg_id: str, msg: StreamMsg, msg_key: Any, group: str, callback: Callable[[str, StreamMsg], bool]) -> None:
        """处理单个消息
        Args:
            msg_id: 消息ID
            msg: 消息对象
            msg_key: Redis消息键
            group: 消费者组名称
            callback: 消息处理回调函数
        """
        try:
            if callback(msg_id, msg):
                self.redis.xack(self.stream, group, msg_key)
        except Exception as e:
            print(f"Error processing message {msg_id}: {e}")

    def consume(
        self,
        group: str,
        consumer: str,
        callback: Callable[[str, StreamMsg], bool],
        *,
        count: int = 10,
        block_ms: int = 5000,
    ) -> None:
        """消费流消息（多线程版本）
        
        使用独立的读取线程从Redis流中读取消息，并使用线程池处理消息。
        这种架构提供了更好的并发性能和资源利用率。
        
        Args:
            group: 消费者组名称
            consumer: 消费者名称
            callback: 消息处理函数，返回 True 确认消息，False 不确认
            count: 每次读取的消息数量
            block_ms: 阻塞等待时间（毫秒）
        """
        # 重置停止事件
        self._stop_event.clear()
        
        # 启动消息读取线程
        self._reader_thread = threading.Thread(
            target=self._read_messages,
            args=(group, consumer, count, block_ms, callback),
            daemon=True
        )
        self._reader_thread.start()
        
        try:
            # 主循环：等待读取线程完成
            while not self._stop_event.is_set() and self._reader_thread.is_alive():
                time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\nReceived interrupt signal, shutting down...")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """停止消费者
        
        优雅地关闭读取线程和线程池，等待正在处理的消息完成。
        """
        print("Stopping stream consumer...")
        
        # 设置停止事件
        self._stop_event.set()
        
        # 等待读取线程结束
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=5.0)
        
        # 关闭线程池
        if self._executor:
            self._executor.shutdown(wait=True)
            
        print("Stream consumer stopped.")