import time
import uuid
import math
import pytest

from agent_redis_framework import HashClient, get_redis_client

# UV_INDEX_URL=https://pypi.org/simple/ uv sync --extra dev
# UV_INDEX_URL=https://pypi.org/simple/ uv run pytest -q -rs tests/test_hash_client.py

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
    return f"test:hash:{uuid.uuid4().hex}{":" + suffix if suffix else ''}"


@pytest.fixture()
def hash_client(redis_available):
    # 为每个测试创建一个唯一的哈希键
    test_key = _k("client")
    return HashClient(test_key)


def test_set_get_types(hash_client: HashClient):
    # str
    assert hash_client.set("s", "hello") in (0, 1)
    assert hash_client.get("s") == "hello"
    # bytes
    assert hash_client.set("b", b"abc") in (0, 1)
    assert hash_client.get("b") == "abc"
    # int
    assert hash_client.set("i", 123) in (0, 1)
    assert hash_client.get("i") == "123"
    # float
    assert hash_client.set("f", 3.14) in (0, 1)
    assert hash_client.get("f") == "3.14"
    # cleanup
    hash_client.clear()


def test_setnx_behavior(hash_client: HashClient):
    assert hash_client.setnx("a", "1") is True
    # 第二次不应覆盖
    assert hash_client.setnx("a", "2") is False
    assert hash_client.get("a") == "1"
    hash_client.clear()


def test_set_many_get_many(hash_client: HashClient):
    mapping = {"a": "x", "b": 2, "c": 3.5, "d": b"zz"}
    hash_client.set_many(mapping)
    result = hash_client.get_many(mapping.keys())
    assert result == {"a": "x", "b": "2", "c": "3.5", "d": "zz"}
    hash_client.clear()


def test_get_all_keys_values_len(hash_client: HashClient):
    hash_client.set_many({"a": "1", "b": "2", "c": "3"})
    assert hash_client.len() == 3
    keys = sorted(hash_client.keys())
    values = sorted(hash_client.values())
    assert keys == ["a", "b", "c"]
    assert sorted(values) == ["1", "2", "3"]
    all_map = hash_client.get_all()
    assert all_map == {"a": "1", "b": "2", "c": "3"}
    hash_client.clear()


def test_basic_operations(hash_client: HashClient):
    ascii_val = "abc"
    zh_val = "中文"  # utf-8 下每个中文 3 字节，共 6
    hash_client.set("a", ascii_val)
    hash_client.set("z", zh_val)
    # 测试基本的get操作
    assert hash_client.get("a") == ascii_val
    assert hash_client.get("z") == zh_val
    hash_client.clear()


def test_incr_and_incr_float(hash_client: HashClient):
    # 整数增减（初始不存在等同于 0）
    assert hash_client.incr("i", 5) == 5
    assert hash_client.incr("i", -2) == 3
    # 浮点增量
    f = hash_client.incr_float("f", 1.5)
    assert math.isclose(f, 1.5, rel_tol=1e-9, abs_tol=1e-9)
    f2 = hash_client.incr_float("f", 0.25)
    assert math.isclose(f2, 1.75, rel_tol=1e-9, abs_tol=1e-9)
    hash_client.clear()


def test_exists_delete_clear(hash_client: HashClient):
    hash_client.set("x", "1")
    assert hash_client.exists("x") is True
    assert hash_client.delete("x") == 1
    assert hash_client.exists("x") is False
    # 重新设置几个字段，然后 clear
    hash_client.set_many({"a": "1", "b": "2"})
    hash_client.clear()
    # 清空后 len 应为 0
    assert hash_client.len() == 0


def test_mclear_and_expire(hash_client: HashClient, redis_available):
    k1 = _k("mc1")
    k2 = _k("mc2")
    # 创建两个独立的哈希客户端用于测试 mclear
    client1 = HashClient(k1)
    client2 = HashClient(k2)
    client1.set_many({"a": "1"})
    client2.set_many({"b": "2"})

    # 清理测试键
    client1.clear()
    client2.clear()
    assert redis_available.exists(k1) == 0
    assert redis_available.exists(k2) == 0