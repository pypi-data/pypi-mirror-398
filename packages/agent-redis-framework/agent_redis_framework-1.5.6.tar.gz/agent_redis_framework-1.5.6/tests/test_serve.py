from fastapi import FastAPI, HTTPException
import threading
from contextlib import asynccontextmanager

from agent_redis_framework.streams.stream_client import StreamClient, StreamMsg


# Global instances
# Stream consumer configuration
STREAM_NAME = "test-stream"
stream_client = StreamClient(STREAM_NAME)  # 需要传入流名称


GROUP_NAME = "test-group"
CONSUMER_NAME = "test-consumer"
consumer_thread = None


def stream_message_handler(msg_key: str, msg: StreamMsg) -> bool:
    """处理流消息的回调函数"""
    print(f"收到流消息: {msg_key} @{STREAM_NAME} -> {msg.payload} -> {msg.meta}")
    return True


def start_stream_consumer():
    """启动流消费者"""
    try:
        # 确保消费者组存在
        stream_client.ensure_group(GROUP_NAME)
        
        # 开始消费 - StreamClient内部已实现线程池处理
        stream_client.consume(
            group=GROUP_NAME,
            consumer=CONSUMER_NAME,
            callback=stream_message_handler,
            count=10,
            block_ms=1000
        )
    except Exception as e:
        print(f"流消费者错误: {e}")


def stop_stream_consumer():
    """停止流消费者"""
    stream_client.stop()
    print("流消费者已停止")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_thread
    # Startup
    print("Starting FastAPI test server for agent-redis-framework")
    consumer_thread = threading.Thread(target=start_stream_consumer, daemon=True)
    consumer_thread.start()
    yield
    # Shutdown
    print("Shutting down FastAPI test server")
    stop_stream_consumer()


app = FastAPI(
    title="Agent Redis Framework Test API",
    description="简化的API用于测试StreamClient",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/stream/push")
async def stream_push(message_request: StreamMsg, maxlen: int | None = None):
    try:
        # StreamMsg 不再包含 stream 字段，直接使用传入的消息
        msg_key = stream_client.push(message_request, maxlen=maxlen)
        return {
            "stream": STREAM_NAME,
            "msg_key": msg_key,
            "payload": message_request.payload,
            "meta": message_request.meta,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Optionally run the app for manual testing
    try:
        uvicorn = __import__('uvicorn')
        uvicorn.run(app, host="0.0.0.0", port=8081)
    except ImportError:
        print("uvicorn not installed. Install it with: pip install uvicorn")
        print("Or run the server using: uvicorn test_serve:app --host 0.0.0.0 --port 8081")