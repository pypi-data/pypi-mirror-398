import uuid
import pytest
from unittest.mock import Mock, patch

from agent_redis_framework.helper import (
    get_redis_util,
    get_sorted_set_queue,
    get_hash_client,
)
from agent_redis_framework.utils import RedisUtil
from agent_redis_framework import get_redis_client

# UV_INDEX_URL=https://pypi.org/simple/ uv sync --extra dev
# UV_INDEX_URL=https://pypi.org/simple/ uv run pytest -q -rs tests/test_helper.py

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
    """生成测试用的唯一键名"""
    return f"test:helper:{uuid.uuid4().hex}{'.' + suffix if suffix else ''}"


@pytest.fixture()
def redis_util(redis_available):
    """创建 RedisUtil 实例用于测试"""
    return RedisUtil()


class TestHelperFunctions:
    """测试 helper 模块中的各种辅助函数"""
    
    def test_get_sorted_set_queue(self, redis_available):
        """测试获取有序集合队列"""
        queue = get_sorted_set_queue("test_key")
        assert queue is not None
        assert hasattr(queue, 'push')  # SortedSetQueue 使用 push 方法
        assert hasattr(queue, 'size')  # SortedSetQueue 使用 size 方法
    
    def test_get_hash_client(self, redis_available):
        """测试获取哈希客户端"""
        client = get_hash_client("test_key")
        assert client is not None
        assert hasattr(client, 'set')  # HashClient 使用 set 方法
        assert hasattr(client, 'get')  # HashClient 使用 get 方法
    
    def test_get_redis_util(self, redis_available):
        """测试获取 Redis 工具类"""
        util = get_redis_util()
        assert util is not None
        assert hasattr(util, 'set')
        assert hasattr(util, 'redis')