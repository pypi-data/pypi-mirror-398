import time
import json

from agent_redis_framework.sortedset.sorted_queue import SortedSetQueue, SortedTask
from agent_redis_framework.redis_client import get_redis_client


def make_tasks(n):
    tasks = []
    for i in range(n):
        tasks.append(SortedTask(payload=f"p{i}", meta={"i": i}))
    return tasks


def setup_queue(key: str):
    q = SortedSetQueue(key)
    q.clear()
    return q


def test_scan_keep():
    key = "arw:test:zscan:keep"
    q = setup_queue(key)
    for t in make_tasks(5):
        q.push(t)
    processed = q.scan_and_handle(lambda s, t: None)
    assert processed == q.size()


def test_scan_delete():
    key = "arw:test:zscan:delete"
    q = setup_queue(key)
    for t in make_tasks(5):
        q.push(t)
    rc = get_redis_client()
    processed = q.scan_and_handle(
        lambda s, t: rc.zrem(key, t.to_json()) if t.payload == "p2" else None
    )
    assert processed == 5
    assert q.size() == 4


def test_scan_update_score():
    key = "arw:test:zscan:update_score"
    q = setup_queue(key)
    base = time.time()
    for i, t in enumerate(make_tasks(3)):
        q.push(t, score=base + i)
    rc = get_redis_client()
    processed = q.scan_and_handle(
        lambda s, t: rc.zadd(key, {t.to_json(): base + 100}) if t.payload == "p0" else None
    )
    assert processed == 3
    assert q.get_max_score() >= base + 100


def test_scan_update_member():
    key = "arw:test:zscan:update_member"
    q = setup_queue(key)
    for t in make_tasks(3):
        q.push(t)
    new_task = SortedTask(payload="p0-new", meta={"x": 1})
    rc = get_redis_client()
    def cb(s, t):
        if t.payload == "p0":
            rc.zrem(key, t.to_json())
            rc.zadd(key, {new_task.to_json(): s})
            return None
    processed = q.scan_and_handle(cb)
    assert processed == 3
    rc = get_redis_client()
    members = rc.zrange(key, 0, -1)
    assert any(json.loads(m)["payload"] == "p0-new" for m in members)
    assert not any(json.loads(m)["payload"] == "p0" for m in members)
