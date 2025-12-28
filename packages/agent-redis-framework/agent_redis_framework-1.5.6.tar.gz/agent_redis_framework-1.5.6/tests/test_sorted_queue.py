import time
import uuid
import json
import pytest

from agent_redis_framework import SortedSetQueue, SortedTask, get_redis_client

# UV_INDEX_URL=https://pypi.org/simple/ uv sync --extra dev
# UV_INDEX_URL=https://pypi.org/simple/ uv run pytest -q -rs tests/test_sorted_queue.py

@pytest.fixture(scope="module")
def redis_available():
    """检查 Redis 是否可用，不可用则跳过整个模块测试。"""
    client = get_redis_client()
    try:
        if not client.ping():
            pytest.skip("Redis server not responding to PING")
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
    return client


def _k(suffix: str = "") -> str:
    return f"test:sorted_queue:{uuid.uuid4().hex}{":" + suffix if suffix else ''}"


@pytest.fixture()
def sorted_queue(redis_available):
    # 为每个测试创建一个唯一的队列键
    test_key = _k("queue")
    return SortedSetQueue(test_key)


def print_method_call(method_name: str, args: tuple = (), kwargs: dict | None = None, result=None):
    """打印方法调用的入参和出参"""
    kwargs = kwargs or {}
    args_str = ", ".join([repr(arg) for arg in args])
    kwargs_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
    params = ", ".join(filter(None, [args_str, kwargs_str]))
    
    print(f"\n[METHOD CALL] {method_name}({params})")
    print(f"[RESULT] -> {repr(result)}")


def test_sorted_task_serialization():
    """测试 SortedTask 的序列化和反序列化"""
    print("\n=== 测试 SortedTask 序列化 ===")
    
    # 创建任务
    task = SortedTask(
        payload='{"type": "email", "recipient": "test@example.com"}',
        meta={"priority": "high", "retry_count": 0}
    )
    print_method_call("SortedTask.__init__", 
                     args=(task.payload,), 
                     kwargs={"meta": task.meta}, 
                     result=task)
    
    # 序列化
    json_str = task.to_json()
    print_method_call("SortedTask.to_json", result=json_str)
    
    # 反序列化
    restored_task = SortedTask.from_json(json_str)
    print_method_call("SortedTask.from_json", args=(json_str,), result=restored_task)
    
    assert restored_task.payload == task.payload
    assert restored_task.meta == task.meta


def test_push_and_size(sorted_queue: SortedSetQueue):
    """测试推送任务和获取队列大小"""
    print("\n=== 测试推送任务和队列大小 ===")
    
    # 初始大小应为0
    initial_size = sorted_queue.size()
    print_method_call("SortedSetQueue.size", result=initial_size)
    assert initial_size == 0
    
    # 创建测试任务
    task1 = SortedTask(payload="task1", meta={"type": "test"})
    task2 = SortedTask(payload="task2", meta={"type": "test"})
    
    # 推送任务（使用默认分数）
    sorted_queue.push(task1)
    print_method_call("SortedSetQueue.push", args=(task1,))
    
    # 推送任务（指定分数）
    sorted_queue.push(task2, score=1.0)
    print_method_call("SortedSetQueue.push", args=(task2,), kwargs={"score": 1.0})
    
    # 检查队列大小
    final_size = sorted_queue.size()
    print_method_call("SortedSetQueue.size", result=final_size)
    assert final_size == 2
    
    # 清理
    sorted_queue.clear()
    print_method_call("SortedSetQueue.clear")


def test_pop_and_handle_edge_cases(sorted_queue: SortedSetQueue):
    """测试pop_and_handle的边界情况"""
    print("\n=== 测试pop_and_handle边界情况 ===")
    
    # 测试空队列
    def empty_handler(score: float, task: SortedTask) -> bool:
        return True
    
    empty_count = sorted_queue.pop_and_handle(callback=empty_handler, count=5)
    print_method_call("SortedSetQueue.pop_and_handle", 
                     kwargs={"callback": "empty_handler", "count": 5},
                     result=empty_count)
    assert empty_count == 0
    
    # 添加3个任务
    tasks = [
        (SortedTask(payload="task1"), 1.0),
        (SortedTask(payload="task2"), 2.0),
        (SortedTask(payload="task3"), 3.0),
    ]
    
    for task, score in tasks:
        sorted_queue.push(task, score)
        print_method_call("SortedSetQueue.push", args=(task,), kwargs={"score": score})
    
    processed_tasks = []
    
    def counting_handler(score: float, task: SortedTask) -> bool:
        processed_tasks.append((score, task))
        return True
    
    # 测试count=0（应该至少处理1个）
    zero_count = sorted_queue.pop_and_handle(callback=counting_handler, count=0)
    print_method_call("SortedSetQueue.pop_and_handle", 
                     kwargs={"callback": "counting_handler", "count": 0},
                     result=zero_count)
    assert zero_count == 1
    assert len(processed_tasks) == 1
    
    # 测试count大于队列大小
    processed_tasks.clear()
    large_count = sorted_queue.pop_and_handle(callback=counting_handler, count=10)
    print_method_call("SortedSetQueue.pop_and_handle", 
                     kwargs={"callback": "counting_handler", "count": 10},
                     result=large_count)
    assert large_count == 2  # 只剩2个任务
    assert len(processed_tasks) == 2
    
    # 验证队列为空
    final_size = sorted_queue.size()
    print_method_call("SortedSetQueue.size", result=final_size)
    assert final_size == 0
    
    # 清理
    sorted_queue.clear()
    print_method_call("SortedSetQueue.clear")


def test_pop_and_handle_descending_order(sorted_queue: SortedSetQueue):
    """测试降序弹出任务"""
    print("\n=== 测试降序弹出任务 ===")
    
    # 添加任务
    tasks = [
        (SortedTask(payload="low_score", meta={"score": 1}), 1.0),
        (SortedTask(payload="high_score", meta={"score": 10}), 10.0),
        (SortedTask(payload="mid_score", meta={"score": 5}), 5.0),
    ]
    
    for task, score in tasks:
        sorted_queue.push(task, score)
        print_method_call("SortedSetQueue.push", args=(task,), kwargs={"score": score})
    
    processed_tasks = []
    
    def desc_handler(score: float, task: SortedTask) -> bool:
        processed_tasks.append((score, task))
        print(f"  [HANDLER] 降序处理任务: score={score}, payload={task.payload}")
        return True
    
    # 降序弹出2个任务
    desc_count = sorted_queue.pop_and_handle(
        callback=desc_handler, 
        ascending=False, 
        count=2
    )
    print_method_call("SortedSetQueue.pop_and_handle", 
                     kwargs={
                         "callback": "desc_handler", 
                         "ascending": False, 
                         "count": 2
                     },
                     result=desc_count)
    
    # 验证返回计数
    assert desc_count == 2
    
    # 验证降序处理（应该先处理分数最高的）
    assert len(processed_tasks) == 2
    assert processed_tasks[0][0] == 10.0  # high_score
    assert processed_tasks[1][0] == 5.0   # mid_score
    
    # 验证剩余任务
    remaining_size = sorted_queue.size()
    print_method_call("SortedSetQueue.size", result=remaining_size)
    assert remaining_size == 1
    
    # 清理
    sorted_queue.clear()
    print_method_call("SortedSetQueue.clear")


def test_pop_and_handle_mixed_success_failure(sorted_queue: SortedSetQueue):
    """测试混合成功和失败的处理情况"""
    print("\n=== 测试混合成功和失败处理 ===")
    
    # 添加任务
    tasks = [
        (SortedTask(payload="success_task", meta={"should_fail": False}), 1.0),
        (SortedTask(payload="failure_task", meta={"should_fail": True}), 2.0),
        (SortedTask(payload="success_task2", meta={"should_fail": False}), 3.0),
    ]
    
    for task, score in tasks:
        sorted_queue.push(task, score)
        print_method_call("SortedSetQueue.push", args=(task,), kwargs={"score": score})
    
    failed_tasks = []
    
    def mixed_handler(score: float, task: SortedTask) -> bool:
        should_fail = task.meta.get("should_fail", False)
        print(f"  [HANDLER] 处理任务: score={score}, payload={task.payload}, will_fail={should_fail}")
        return not should_fail
    
    def mixed_failure_handler(score: float, task: SortedTask) -> None:
        failed_tasks.append((score, task))
        print(f"  [FAILURE] 任务失败: score={score}, payload={task.payload}")
    
    # 处理所有任务
    mixed_count = sorted_queue.pop_and_handle(
        callback=mixed_handler,
        on_failure=mixed_failure_handler,
        count=3
    )
    print_method_call("SortedSetQueue.pop_and_handle", 
                     kwargs={
                         "callback": "mixed_handler",
                         "on_failure": "mixed_failure_handler",
                         "count": 3
                     },
                     result=mixed_count)
    
    # 验证处理计数（所有任务都被处理了，不管成功还是失败）
    assert mixed_count == 3
    
    # 验证失败处理
    assert len(failed_tasks) == 1
    assert failed_tasks[0][1].payload == "failure_task"
    
    # 验证队列为空
    final_size = sorted_queue.size()
    print_method_call("SortedSetQueue.size", result=final_size)
    assert final_size == 0
    
    # 清理
    sorted_queue.clear()
    print_method_call("SortedSetQueue.clear")


def test_pop_and_handle(sorted_queue: SortedSetQueue):
    """测试弹出和处理任务"""
    print("\n=== 测试弹出和处理任务 ===")
    
    # 推送多个任务，分数不同
    tasks = [
        (SortedTask(payload="high_priority", meta={"priority": "high"}), 1.0),
        (SortedTask(payload="medium_priority", meta={"priority": "medium"}), 5.0),
        (SortedTask(payload="low_priority", meta={"priority": "low"}), 10.0),
    ]
    
    for task, score in tasks:
        sorted_queue.push(task, score)
        print_method_call("SortedSetQueue.push", args=(task,), kwargs={"score": score})
    
    processed_tasks = []
    
    def task_handler(score: float, task: SortedTask) -> bool:
        processed_tasks.append((score, task))
        print(f"  [HANDLER] 处理任务: score={score}, payload={task.payload}")
        return True
    
    def failure_handler(score: float, task: SortedTask) -> None:
        print(f"  [FAILURE] 任务处理失败: score={score}, payload={task.payload}")
    
    # 弹出并处理任务（升序，应该先处理分数最低的）
    processed_count = sorted_queue.pop_and_handle(
        callback=task_handler,
        on_failure=failure_handler,
        ascending=True,
        count=2
    )
    print_method_call("SortedSetQueue.pop_and_handle", 
                     kwargs={
                         "callback": "task_handler",
                         "on_failure": "failure_handler", 
                         "ascending": True,
                         "count": 2
                     },
                     result=processed_count)
    
    # 验证返回的处理计数
    assert processed_count == 2
    
    # 验证处理顺序（应该按分数升序）
    assert len(processed_tasks) == 2
    assert processed_tasks[0][0] == 1.0  # high_priority
    assert processed_tasks[1][0] == 5.0  # medium_priority
    
    # 检查剩余任务数量
    remaining_size = sorted_queue.size()
    print_method_call("SortedSetQueue.size", result=remaining_size)
    assert remaining_size == 1
    
    # 清理
    sorted_queue.clear()
    print_method_call("SortedSetQueue.clear")


def test_pop_and_handle_failure(sorted_queue: SortedSetQueue):
    """测试任务处理失败的情况"""
    print("\n=== 测试任务处理失败 ===")
    
    task = SortedTask(payload="failing_task", meta={"will_fail": True})
    sorted_queue.push(task, score=1.0)
    print_method_call("SortedSetQueue.push", args=(task,), kwargs={"score": 1.0})
    
    failed_tasks = []
    
    def failing_handler(score: float, task: SortedTask) -> bool:
        print(f"  [HANDLER] 尝试处理任务: score={score}, payload={task.payload}")
        return False  # 模拟处理失败
    
    def failure_handler(score: float, task: SortedTask) -> None:
        failed_tasks.append((score, task))
        print(f"  [FAILURE] 任务处理失败: score={score}, payload={task.payload}")
    
    processed_count = sorted_queue.pop_and_handle(
        callback=failing_handler,
        on_failure=failure_handler,
        count=1
    )
    print_method_call("SortedSetQueue.pop_and_handle",
                     kwargs={
                         "callback": "failing_handler",
                         "on_failure": "failure_handler",
                         "count": 1
                     },
                     result=processed_count)
    
    # 验证返回的处理计数（即使失败也算处理了）
    assert processed_count == 1
    
    # 验证失败处理
    assert len(failed_tasks) == 1
    assert failed_tasks[0][1].payload == "failing_task"
    
    # 清理
    sorted_queue.clear()
    print_method_call("SortedSetQueue.clear")


def test_get_min_max_score(sorted_queue: SortedSetQueue):
    """测试获取最小和最大分数"""
    print("\n=== 测试获取最小和最大分数 ===")
    
    # 空队列时的返回值
    min_score = sorted_queue.get_min_score()
    max_score = sorted_queue.get_max_score()
    print_method_call("SortedSetQueue.get_min_score", result=min_score)
    print_method_call("SortedSetQueue.get_max_score", result=max_score)
    assert min_score == -1.0  # 空队列时返回 -1.0
    assert max_score == 0.0   # 空队列时返回 0.0
    
    # 添加任务
    tasks_scores = [
        (SortedTask(payload="task1"), 3.0),
        (SortedTask(payload="task2"), 1.0),
        (SortedTask(payload="task3"), 5.0),
    ]
    
    for task, score in tasks_scores:
        sorted_queue.push(task, score)
        print_method_call("SortedSetQueue.push", args=(task,), kwargs={"score": score})
    
    # 获取最小和最大分数
    min_score = sorted_queue.get_min_score()
    max_score = sorted_queue.get_max_score()
    print_method_call("SortedSetQueue.get_min_score", result=min_score)
    print_method_call("SortedSetQueue.get_max_score", result=max_score)
    
    assert min_score == 1.0
    assert max_score == 5.0
    
    # 清理
    sorted_queue.clear()
    print_method_call("SortedSetQueue.clear")


def test_remove_task(sorted_queue: SortedSetQueue):
    """测试移除指定任务"""
    print("\n=== 测试移除指定任务 ===")
    
    task1 = SortedTask(payload="task_to_remove", meta={"id": 1})
    task2 = SortedTask(payload="task_to_keep", meta={"id": 2})
    
    # 添加任务
    sorted_queue.push(task1, score=1.0)
    sorted_queue.push(task2, score=2.0)
    print_method_call("SortedSetQueue.push", args=(task1,), kwargs={"score": 1.0})
    print_method_call("SortedSetQueue.push", args=(task2,), kwargs={"score": 2.0})
    
    initial_size = sorted_queue.size()
    print_method_call("SortedSetQueue.size", result=initial_size)
    assert initial_size == 2
    
    # 移除存在的任务
    removed = sorted_queue.remove(task1)
    print_method_call("SortedSetQueue.remove", args=(task1,), result=removed)
    assert removed is True
    
    # 尝试移除不存在的任务
    removed_again = sorted_queue.remove(task1)
    print_method_call("SortedSetQueue.remove", args=(task1,), result=removed_again)
    assert removed_again is False
    
    # 检查最终大小
    final_size = sorted_queue.size()
    print_method_call("SortedSetQueue.size", result=final_size)
    assert final_size == 1
    
    # 清理
    sorted_queue.clear()
    print_method_call("SortedSetQueue.clear")


def test_clear_queue(sorted_queue: SortedSetQueue):
    """测试清空队列"""
    print("\n=== 测试清空队列 ===")
    
    # 添加多个任务
    for i in range(5):
        task = SortedTask(payload=f"task_{i}", meta={"index": i})
        sorted_queue.push(task, score=float(i))
        print_method_call("SortedSetQueue.push", args=(task,), kwargs={"score": float(i)})
    
    # 验证队列不为空
    size_before = sorted_queue.size()
    print_method_call("SortedSetQueue.size", result=size_before)
    assert size_before == 5
    
    # 清空队列
    sorted_queue.clear()
    print_method_call("SortedSetQueue.clear")
    
    # 验证队列为空
    size_after = sorted_queue.size()
    print_method_call("SortedSetQueue.size", result=size_after)
    assert size_after == 0


def test_complex_workflow(sorted_queue: SortedSetQueue):
    """测试复杂的工作流程"""
    print("\n=== 测试复杂工作流程 ===")
    
    # 模拟任务调度场景
    tasks = [
        (SortedTask(payload='{"type": "email", "to": "user1@example.com"}', 
                   meta={"priority": "high", "created_at": time.time()}), 1.0),
        (SortedTask(payload='{"type": "sms", "to": "+1234567890"}', 
                   meta={"priority": "medium", "created_at": time.time()}), 5.0),
        (SortedTask(payload='{"type": "push", "device_id": "device123"}', 
                   meta={"priority": "low", "created_at": time.time()}), 10.0),
    ]
    
    # 批量推送任务
    for task, score in tasks:
        sorted_queue.push(task, score)
        print_method_call("SortedSetQueue.push", args=(task,), kwargs={"score": score})
    
    # 获取队列状态
    size = sorted_queue.size()
    min_score = sorted_queue.get_min_score()
    max_score = sorted_queue.get_max_score()
    print_method_call("SortedSetQueue.size", result=size)
    print_method_call("SortedSetQueue.get_min_score", result=min_score)
    print_method_call("SortedSetQueue.get_max_score", result=max_score)
    
    assert size == 3
    assert min_score == 1.0
    assert max_score == 10.0
    
    # 处理高优先级任务
    processed_count = 0
    
    def priority_handler(score: float, task: SortedTask) -> bool:
        nonlocal processed_count
        payload_data = json.loads(task.payload)
        print(f"  [HANDLER] 处理 {payload_data['type']} 任务: {payload_data}")
        processed_count += 1
        return True
    
    # 只处理一个任务（最高优先级）
    actual_processed = sorted_queue.pop_and_handle(callback=priority_handler, count=1)
    print_method_call("SortedSetQueue.pop_and_handle", 
                     kwargs={"callback": "priority_handler", "count": 1},
                     result=actual_processed)
    
    # 验证返回的处理计数与实际处理计数一致
    assert actual_processed == 1
    assert processed_count == 1
    
    # 检查剩余任务
    remaining_size = sorted_queue.size()
    print_method_call("SortedSetQueue.size", result=remaining_size)
    assert remaining_size == 2
    
    # 清理
    sorted_queue.clear()
    print_method_call("SortedSetQueue.clear")