# Agent Redis Framework

一个优雅、高效的 Python Redis 框架，专为多任务调度与消息流处理而设计。提供基于 Redis Sorted Sets 的轻量任务队列和基于 Redis Streams 的消费组封装，适合构建可扩展的分布式任务系统。

## ✨ 核心特性

### SortedSetQueue - 智能任务队列
- **优先级调度**: 基于 Redis Sorted Set 实现的轻量任务队列
- **原子操作**: 使用 `ZPOPMIN`/`ZPOPMAX` 确保多消费者场景下的任务安全分发
- **灵活排序**: 支持按分数升序/降序弹出任务
- **失败处理**: 内置任务处理失败的回调机制
- **批量处理**: 支持一次性弹出并处理多个任务

### 📡 StreamClient - 流式消息处理
- **消费组管理**: 完整的 Redis Streams 消费组封装
- **自动 ACK**: 消息处理成功后自动确认
- **流量控制**: 支持流长度限制和自动修剪
- **阻塞消费**: 可配置的阻塞时间和批量消费
- **错误恢复**: 处理待确认消息和消费者故障恢复
- **内置线程池**: 自动管理读取线程和消息处理线程池，提供高并发性能

### 🔧 HashClient - 高效Hash操作
- **类型统一**: 写入时将 bytes/int/float 转为字符串；读取时返回 str（不存在返回 None）
- **批量操作**: 支持批量设置和获取多个字段
- **数值操作**: 内置整数和浮点数自增功能
- **字段管理**: 完整的字段存在性检查、删除和清空功能
- **过期控制**: 支持为整个Hash设置过期时间

### 🔧 企业级特性
- **连接池管理**: 自动连接池复用，优化高并发性能
- **环境配置**: 灵活的 `.env` 文件和环境变量支持
- **类型安全**: 完整的 Python 类型注解
- **线程安全**: 所有核心组件支持多线程并发
- **轻量依赖**: 仅依赖 `redis` 和 `typing-extensions`

## 🚀 快速开始

### Redis 连接配置

#### 环境变量配置

创建 `.env` 文件：
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password
REDIS_MAX_CONNECTIONS=20
```

```python
from agent_redis_framework import get_redis

# 自动从环境变量加载配置
redis_client = get_redis()
print(redis_client.ping())  # True
```

### SortedSetQueue - 任务队列示例

```python
from agent_redis_framework import SortedSetQueue, SortedTask
import time

queue = SortedSetQueue()
queue_key = "my_task_queue"

# 清空队列（可选）
queue.clear(queue_key)

# 推送任务（分数越小优先级越高）
import json
queue.push(queue_key, SortedTask(payload=json.dumps({"priority": "high"})), score=1)
queue.push(queue_key, SortedTask(payload=json.dumps({"priority": "normal"})), score=5)
queue.push(queue_key, SortedTask(payload=json.dumps({"priority": "low"})), score=10)

# 定义任务处理函数
def process_task(score: float, task: SortedTask) -> bool:
    print(f"Processing task at score {score}: {task.payload}")
    # 模拟任务处理
    time.sleep(0.1)
    return True  # 返回 True 表示处理成功

# 定义失败处理函数
def handle_failure(score: float, task: SortedTask) -> None:
    print(f"Task failed at score {score}, logging for retry...")

# 原子弹出并处理任务
processed = queue.pop_and_handle(
    queue_key,
    callback=process_task,
    on_failure=handle_failure,
    count=2  # 一次处理 2 个任务
)

print(f"Processed {len(processed)} tasks")
print(f"Remaining tasks: {queue.size(queue_key)}")
```

### StreamClient - 流式消息示例

- StreamMsg.meta 的类型已收紧为：`dict[str, bytes | str | int | float]`
- push() 会将 meta 扁平化写入 Redis，字段名前缀为 `__m_`（例如：`__m_trace_id`）
- consume() 的回调签名已更新为：`callback(msg_key: str, msg: StreamMsg) -> bool`

```python
from agent_redis_framework import StreamClient, StreamMsg
import time
import json

# 初始化 - 传入流名称
stream_client = StreamClient("user_events")

group_name = "analytics_group"
consumer_name = "consumer_1"

# 创建消费组（幂等操作）
stream_client.ensure_group(group_name)

# 推送消息（payload 建议为 JSON 字符串；meta 仅允许标量值）
msg = StreamMsg(
    payload=json.dumps({
        "event_type": "user_login",
        "user_id": "12345",
        "timestamp": time.time(),
        "ip_address": "192.168.1.100"
    }),
    meta={"source": "readme", "request_id": "req-1", "retry": 0}
)
msg_key = stream_client.push(msg)
print(f"Message pushed with ID: {msg_key}")

# 定义消息处理函数（新版签名）
def handle_message(msg_key: str, msg: StreamMsg) -> bool:
    print(f"Processing message {msg_key}")
    print(f"Payload: {msg.payload}")  # 若为 JSON 字符串，可自行 json.loads
    print(f"Meta: {msg.meta}")       # 来自 __m_ 前缀字段
    time.sleep(0.1)
    return True

# 启动消费者 - StreamClient内部自动管理线程池
stream_client.consume(
    group=group_name,
    consumer=consumer_name,
    callback=handle_message,   # 注意：签名为 (msg_key, msg)
    block_ms=5000,             # 5秒阻塞超时
    count=10                   # 每次最多读取10条消息
)

# 在另一个进程或线程中推送更多消息
for i in range(3):
    msg = StreamMsg(
        payload=json.dumps({
            "event_type": "page_view",
            "user_id": f"user_{i}",
            "page": f"/page/{i}",
            "timestamp": time.time()
        }),
        meta={"source": "readme", "seq": i}
    )
    stream_client.push(msg)
    time.sleep(1)

# 优雅停止消费者
stream_client.stop()
```

### HashClient - Hash 操作示例

- 统一类型：写入时将 bytes/int/float 转为字符串；读取时返回 str（不存在返回 None）。
- 支持的标量类型：bytes | str | int | float（复杂结构请先序列化为字符串）。

```python
from agent_redis_framework import HashClient

# 创建HashClient实例，绑定到特定的key
h = HashClient("user:1")

# 基础写入/读取
h.set("name", "Alice")                # -> 1 表示新字段，0 表示覆盖
print(h.get("name"))                     # -> "Alice" 或 None

# 批量写/读
h.set_many({"age": 18, "score": 99.5})
print(h.get_many(["name", "age", "score", "missing"]))  # -> {'name': 'Alice', 'age': '18', 'score': '99.5', 'missing': None}
print(h.get_all())                          # -> {'name': 'Alice', 'age': '18', 'score': '99.5'}

# 查询/统计
print(h.keys())     # -> ["name", "age", "score"]
print(h.values())   # -> ["Alice", "18", "99.5"]
print(h.len())      # -> 字段数量

# 数值自增
print(h.incr("visits", 1))       # -> 最新整数值
print(h.incr_float("ratio", 0.1)) # -> 最新浮点值

# 存在/删除/过期
print(h.exists("name"))    # -> True/False
print(h.delete("age", "score"))  # -> 实际删除的字段数量
print(h.expire(60))         # -> 是否设置成功
# 清理
h.clear()              # 删除整个 Hash 键

## 🏗️ 高级用法

### 流消息批量处理

```python
from agent_redis_framework import StreamClient, StreamMsg
import json

stream_client = StreamClient("order_stream")

# 批量推送消息
messages = [
    {"order_id": f"order_{i}", "amount": i * 100, "status": "pending"}
    for i in range(100)
]

for msg in messages:
    stream_msg = StreamMsg(payload=json.dumps(msg), meta={"batch": 1})
    stream_client.push(stream_msg, maxlen=1000)  # 限制流长度

# 批量消费处理 - 内置线程池自动处理并发
def batch_process_orders(msg_key: str, msg: StreamMsg) -> bool:
    order_data = json.loads(msg.payload) if msg.payload else {}
    print(f"Processing order: {order_data.get('order_id', 'unknown')} with key {msg_key}")
    return True

stream_client.consume(
    group="order_processors",
    consumer="processor_1",
    callback=batch_process_orders,
    count=50,  # 每次批量处理50条消息
    block_ms=1000
)

# 停止消费者
stream_client.stop()
```

## 📚 API 参考（关键变更）

### HashClient
- `__init__(key: str, redis_client=None)` - 创建HashClient实例，绑定到指定的Redis Hash键
- `set(field, value: bytes | str | int | float) -> int` - 设置单个字段；1 表示新字段，0 表示覆盖
- `setnx(field, value) -> bool` - 仅当字段不存在时设置
- `set_many(mapping: dict[str, bytes | str | int | float]) -> None` - 批量设置多个字段
- `get(field) -> str | None` - 获取单个字段；不存在返回 None
- `get_many(fields: Iterable[str]) -> dict[str, str | None]` - 批量获取多个字段
- `get_all() -> dict[str, str]` - 获取整个 Hash，字段和值均为 str
- `len() -> int` - 返回字段数量
- `keys() -> list[str]` - 返回所有字段名（str）
- `values() -> list[str]` - 返回所有字段值（str）
- `incr(field, amount: int = 1) -> int` - 整数自增并返回最新值
- `incr_float(field, amount: float = 1.0) -> float` - 浮点自增并返回最新值
- `exists(field) -> bool` - 字段是否存在
- `delete(*fields) -> int` - 删除一个或多个字段，返回删除数量
- `clear() -> None` - 删除整个 Hash 键
- `expire(seconds: int) -> bool` - 设置过期时间（秒）

备注：写入的标量值都会转换为字符串存储；读取统一返回 str（或 None）。

### StreamClient
- `__init__(stream: str)` - 初始化流客户端，传入流名称
- `push(msg, maxlen=None)` - 将 StreamMsg 推送到流中；meta 会以 `__m_` 前缀扁平化写入
- `consume(group, consumer, callback, block_ms=5000, count=1)` - 消费消息；`callback` 签名为 `(msg_key: str, msg: StreamMsg) -> bool`；内置线程池自动处理并发
- `ensure_group(group)` - 确保消费者组存在，如不存在则创建
- `stop()` - 优雅停止消费者，关闭读取线程和线程池

### 数据类
- `StreamMsg(payload, meta={})` - 流消息数据类，payload 为字符串格式；meta 类型为 `dict[str, bytes | str | int | float]`
- `SortedTask(payload, meta={})` - 队列任务数据类，payload 为字符串格式；meta 为字典类型

注意：复杂结构（如列表/字典）请先 JSON 序列化后放入 payload；meta 仅接受标量类型。如果一定要在 meta 保留复杂结构，请先自行序列化为字符串。