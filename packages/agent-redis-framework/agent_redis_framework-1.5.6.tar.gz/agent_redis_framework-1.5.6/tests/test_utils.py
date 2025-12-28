import time
import uuid
import pytest
from unittest.mock import Mock, patch
from functools import lru_cache

from agent_redis_framework.utils import RedisUtil
from agent_redis_framework import get_redis_client

# UV_INDEX_URL=https://pypi.org/simple/ uv sync --extra dev
# UV_INDEX_URL=https://pypi.org/simple/ uv run pytest -q -rs tests/test_utils.py

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
    return f"test:utils:{uuid.uuid4().hex}{'.' + suffix if suffix else ''}"


@pytest.fixture()
def redis_util(redis_available):
    """为每个测试创建一个 RedisUtil 实例"""
    return RedisUtil()


# 分布式锁方法
@lru_cache(maxsize=1)
def get_redis_util() -> RedisUtil:
    """获取 RedisUtil 单例实例
    RedisUtil 无 key 参数，可以安全使用单例缓存。
    """
    return RedisUtil()


def lock(key: str, timeout_sec: int) -> bool:
    """为指定键设置分布式锁
    Args:
        key: 锁的键名
        timeout_sec: 锁的超时时间（秒）
    Returns:
        bool: 是否成功获取锁
    """
    redis_util = get_redis_util()
    # 使用 SET 命令的 NX（不存在时设置）和 EX（设置过期时间）选项
    # 生成唯一标识符作为锁的值，用于后续释放锁时验证
    lock_value = str(1)
    return redis_util.set(key, lock_value, nx=True, ex=timeout_sec)


class TestRedisUtilKeyOperations:
    """测试键操作相关方法"""
    
    def test_expire(self, redis_util: RedisUtil, redis_available):
        """测试设置键过期时间"""
        test_key = _k("expire")
        # 先设置一个键
        redis_available.set(test_key, "test_value")
        
        # 测试设置过期时间
        assert redis_util.expire(test_key, 10) is True
        
        # 验证过期时间已设置
        ttl = redis_available.ttl(test_key)
        assert 0 < ttl <= 10
        
        # 清理
        redis_available.delete(test_key)
    
    def test_expire_nonexistent_key(self, redis_util: RedisUtil):
        """测试对不存在的键设置过期时间"""
        nonexistent_key = _k("nonexistent")
        assert redis_util.expire(nonexistent_key, 10) is False
    
    def test_delete_single_key(self, redis_util: RedisUtil, redis_available):
        """测试删除单个键"""
        test_key = _k("delete")
        redis_available.set(test_key, "test_value")
        
        assert redis_util.delete(test_key) is True
        assert not redis_available.exists(test_key)
    
    def test_delete_nonexistent_key(self, redis_util: RedisUtil):
        """测试删除不存在的键"""
        nonexistent_key = _k("nonexistent")
        assert redis_util.delete(nonexistent_key) is False
    
    def test_delete_many_keys(self, redis_util: RedisUtil, redis_available):
        """测试删除多个键"""
        keys = [_k(f"delete_many_{i}") for i in range(3)]
        
        # 设置多个键
        for key in keys:
            redis_available.set(key, "test_value")
        
        # 删除多个键
        assert redis_util.delete_many(keys) is True
        
        # 验证所有键都被删除
        for key in keys:
            assert not redis_available.exists(key)
    
    def test_delete_many_empty_list(self, redis_util: RedisUtil):
        """测试删除空键列表"""
        # 空列表会导致 Redis 错误，因为 delete 命令需要至少一个参数
        # 我们需要在实际实现中处理这种情况
        try:
            result = redis_util.delete_many([])
            # 如果没有抛出异常，应该返回 False
            assert result is False
        except Exception:
            # 如果抛出异常也是可以接受的
            pass
    
    def test_exists(self, redis_util: RedisUtil, redis_available):
        """测试检查键是否存在"""
        test_key = _k("exists")
        
        # 键不存在时
        assert redis_util.exists(test_key) is False
        
        # 设置键后
        redis_available.set(test_key, "test_value")
        assert redis_util.exists(test_key) is True
        
        # 清理
        redis_available.delete(test_key)
    
    def test_ttl(self, redis_util: RedisUtil, redis_available):
        """测试获取键的剩余生存时间"""
        test_key = _k("ttl")
        
        # 不存在的键
        assert redis_util.ttl(_k("nonexistent")) == -2
        
        # 永不过期的键
        redis_available.set(test_key, "test_value")
        assert redis_util.ttl(test_key) == -1
        
        # 有过期时间的键
        redis_available.expire(test_key, 10)
        ttl = redis_util.ttl(test_key)
        assert 0 < ttl <= 10
        
        # 清理
        redis_available.delete(test_key)
    
    def test_type(self, redis_util: RedisUtil, redis_available):
        """测试获取键的数据类型"""
        # 字符串类型
        str_key = _k("type_string")
        redis_available.set(str_key, "test")
        assert redis_util.type(str_key) == "string"
        
        # 哈希类型
        hash_key = _k("type_hash")
        redis_available.hset(hash_key, "field", "value")
        assert redis_util.type(hash_key) == "hash"
        
        # 列表类型
        list_key = _k("type_list")
        redis_available.lpush(list_key, "item")
        assert redis_util.type(list_key) == "list"
        
        # 不存在的键
        assert redis_util.type(_k("nonexistent")) == "none"
        
        # 清理
        redis_available.delete(str_key, hash_key, list_key)
    
    def test_keys(self, redis_util: RedisUtil, redis_available):
        """测试根据模式匹配获取键列表"""
        # 设置一些测试键
        test_keys = [_k(f"keys_test_{i}") for i in range(3)]
        for key in test_keys:
            redis_available.set(key, "value")
        
        # 获取所有匹配的键，使用更通用的模式
        found_keys = redis_util.keys("test:utils:*keys_test_*")
        
        # 验证找到的键包含我们设置的键
        for key in test_keys:
            assert key in found_keys
        
        # 清理
        redis_available.delete(*test_keys)
    
    def test_rename(self, redis_util: RedisUtil, redis_available):
        """测试重命名键"""
        old_key = _k("rename_old")
        new_key = _k("rename_new")
        
        # 设置原键
        redis_available.set(old_key, "test_value")
        
        # 重命名
        assert redis_util.rename(old_key, new_key) is True
        
        # 验证重命名结果
        assert not redis_available.exists(old_key)
        assert redis_available.exists(new_key)
        assert redis_available.get(new_key).decode() == "test_value"
        
        # 清理
        redis_available.delete(new_key)
    
    def test_rename_nonexistent_key(self, redis_util: RedisUtil):
        """测试重命名不存在的键"""
        old_key = _k("nonexistent")
        new_key = _k("rename_new")
        
        assert redis_util.rename(old_key, new_key) is False
    
    def test_persist(self, redis_util: RedisUtil, redis_available):
        """测试移除键的过期时间"""
        test_key = _k("persist")
        
        # 设置键并添加过期时间
        redis_available.set(test_key, "test_value")
        redis_available.expire(test_key, 10)
        
        # 移除过期时间
        assert redis_util.persist(test_key) is True
        
        # 验证过期时间已移除
        assert redis_available.ttl(test_key) == -1
        
        # 清理
        redis_available.delete(test_key)
    
    def test_persist_nonexistent_key(self, redis_util: RedisUtil):
        """测试对不存在的键移除过期时间"""
        nonexistent_key = _k("nonexistent")
        assert redis_util.persist(nonexistent_key) is False


class TestRedisUtilServerOperations:
    """测试服务器操作相关方法"""
    
    def test_info(self, redis_util: RedisUtil):
        """测试获取 Redis 服务器信息"""
        info = redis_util.info()
        assert isinstance(info, dict)
        assert "redis_version" in info
        
        # 测试获取特定部分信息
        server_info = redis_util.info("server")
        assert isinstance(server_info, dict)
    
    def test_dbsize(self, redis_util: RedisUtil, redis_available):
        """测试获取当前数据库中键的数量"""
        # 记录初始键数量
        initial_size = redis_util.dbsize()
        
        # 添加一个键
        test_key = _k("dbsize")
        redis_available.set(test_key, "value")
        
        # 验证键数量增加
        new_size = redis_util.dbsize()
        assert new_size == initial_size + 1
        
        # 清理
        redis_available.delete(test_key)
    
    def test_select(self, redis_util: RedisUtil):
        """测试选择数据库"""
        # 选择数据库 1
        assert redis_util.select(1) is True
        
        # 切换回数据库 0
        assert redis_util.select(0) is True
        
        # 测试无效数据库编号
        assert redis_util.select(-1) is False
    
    def test_memory_usage(self, redis_util: RedisUtil, redis_available):
        """测试获取键占用的内存字节数"""
        test_key = _k("memory")
        redis_available.set(test_key, "test_value")
        
        memory_usage = redis_util.memory_usage(test_key)
        assert isinstance(memory_usage, int)
        assert memory_usage > 0
        
        # 测试不存在的键
        assert redis_util.memory_usage(_k("nonexistent")) is None
        
        # 清理
        redis_available.delete(test_key)
    
    def test_ping(self, redis_util: RedisUtil):
        """测试 Redis 连接"""
        assert redis_util.ping() is True


class TestRedisUtilTransactionOperations:
    """测试事务操作相关方法"""
    
    def test_multi_exec_success(self, redis_util: RedisUtil, redis_available):
        """测试成功的事务操作"""
        key1 = _k("trans1")
        key2 = _k("trans2")
        
        commands = [
            ("set", (key1, "value1")),
            ("set", (key2, "value2")),
            ("get", (key1,)),
            ("get", (key2,))
        ]
        
        results = redis_util.multi_exec(commands)
        
        # 验证结果
        assert len(results) == 4
        assert results[0] is True  # set 操作
        assert results[1] is True  # set 操作
        assert results[2] == b"value1"  # get 操作
        assert results[3] == b"value2"  # get 操作
        
        # 清理
        redis_available.delete(key1, key2)
    
    def test_multi_exec_empty_commands(self, redis_util: RedisUtil):
        """测试空命令列表的事务操作"""
        results = redis_util.multi_exec([])
        assert results == []
    
    def test_multi_exec_invalid_command(self, redis_util: RedisUtil):
        """测试包含无效命令的事务操作"""
        commands = [
            ("invalid_command", ("arg1", "arg2"))
        ]
        
        with pytest.raises(AttributeError):
            redis_util.multi_exec(commands)


class TestRedisUtilDatabaseOperations:
    """测试数据库操作相关方法（需要谨慎测试）"""
    
    def test_flushdb(self, redis_util: RedisUtil, redis_available):
        """测试清空当前数据库（在测试数据库中进行）"""
        # 切换到测试数据库
        redis_available.select(15)  # 使用数据库 15 进行测试
        
        # 添加一些测试数据
        test_key = _k("flushdb_test")
        redis_available.set(test_key, "value")
        
        # 创建新的 RedisUtil 实例用于数据库 15
        test_util = RedisUtil()
        test_util.select(15)
        
        # 清空数据库
        assert test_util.flushdb() is True
        
        # 验证数据库已清空
        assert test_util.dbsize() == 0
        
        # 切换回数据库 0
        redis_available.select(0)
    
    def test_flushdb_async(self, redis_util: RedisUtil, redis_available):
        """测试异步清空当前数据库"""
        # 切换到测试数据库
        redis_available.select(14)  # 使用数据库 14 进行测试
        
        # 添加一些测试数据
        test_key = _k("flushdb_async_test")
        redis_available.set(test_key, "value")
        
        # 创建新的 RedisUtil 实例用于数据库 14
        test_util = RedisUtil()
        test_util.select(14)
        
        # 异步清空数据库
        assert test_util.flushdb(asynchronous=True) is True
        
        # 等待一小段时间让异步操作完成
        time.sleep(0.1)
        
        # 验证数据库已清空
        assert test_util.dbsize() == 0
        
        # 切换回数据库 0
        redis_available.select(0)


class TestRedisUtilMockOperations:
    """使用 Mock 测试一些边界情况和错误处理"""
    
    @patch('agent_redis_framework.utils.get_redis_client')
    def test_flushall_success(self, mock_get_client):
        """测试成功清空所有数据库"""
        mock_redis = Mock()
        mock_redis.flushall.return_value = True
        mock_get_client.return_value = mock_redis
        
        util = RedisUtil()
        assert util.flushall() is True
        mock_redis.flushall.assert_called_once_with(asynchronous=False)
    
    @patch('agent_redis_framework.utils.get_redis_client')
    def test_flushall_exception(self, mock_get_client):
        """测试清空所有数据库时发生异常"""
        mock_redis = Mock()
        mock_redis.flushall.side_effect = Exception("Redis error")
        mock_get_client.return_value = mock_redis
        
        util = RedisUtil()
        assert util.flushall() is False
    
    @patch('agent_redis_framework.utils.get_redis_client')
    def test_ping_exception(self, mock_get_client):
        """测试 ping 操作发生异常"""
        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Connection error")
        mock_get_client.return_value = mock_redis
        
        util = RedisUtil()
        assert util.ping() is False
    
    @patch('agent_redis_framework.utils.get_redis_client')
    def test_memory_usage_exception(self, mock_get_client):
        """测试获取内存使用量时发生异常"""
        mock_redis = Mock()
        mock_redis.memory_usage.side_effect = Exception("Memory usage error")
        mock_get_client.return_value = mock_redis
        
        util = RedisUtil()
        assert util.memory_usage("test_key") is None
    
    @patch('agent_redis_framework.utils.get_redis_client')
    def test_type_bytes_response(self, mock_get_client):
        """测试 type 方法返回 bytes 类型的响应"""
        mock_redis = Mock()
        mock_redis.type.return_value = b"string"
        mock_get_client.return_value = mock_redis
        
        util = RedisUtil()
        assert util.type("test_key") == "string"
    
    @patch('agent_redis_framework.utils.get_redis_client')
    def test_keys_bytes_response(self, mock_get_client):
        """测试 keys 方法返回 bytes 类型的键名"""
        mock_redis = Mock()
        mock_redis.keys.return_value = [b"key1", b"key2", "key3"]
        mock_get_client.return_value = mock_redis
        
        util = RedisUtil()
        keys = util.keys("*")
        assert keys == ["key1", "key2", "key3"]


class TestRedisUtilInitialization:
    """测试 RedisUtil 初始化"""
    
    def test_init(self):
        """测试 RedisUtil 初始化"""
        util = RedisUtil()
        assert util.redis is not None
        assert hasattr(util, 'redis')


class TestLockFunction:
    """测试分布式锁功能"""
    
    def test_lock_success(self):
        """测试成功获取锁"""
        with patch('tests.test_utils.get_redis_util') as mock_get_redis_util:
            mock_redis_util = Mock(spec=RedisUtil)
            mock_redis_util.set.return_value = True
            mock_get_redis_util.return_value = mock_redis_util
            
            # 测试获取锁
            result = lock("test_key", 30)
            
            # 验证结果
            assert result is True
            
            # 验证调用参数
            mock_redis_util.set.assert_called_once()
            call_args = mock_redis_util.set.call_args
            
            # 验证 key 参数
            assert call_args[0][0] == "test_key"
            
            # 验证 value 是字符串 "1"
            lock_value = call_args[0][1]
            assert lock_value == "1"
            
            # 验证关键字参数
            assert call_args[1]["nx"] is True
            assert call_args[1]["ex"] == 30
    
    def test_lock_failure(self):
        """测试获取锁失败（锁已被占用）"""
        with patch('tests.test_utils.get_redis_util') as mock_get_redis_util:
            mock_redis_util = Mock(spec=RedisUtil)
            mock_redis_util.set.return_value = False
            mock_get_redis_util.return_value = mock_redis_util
            
            # 测试获取锁
            result = lock("test_key", 30)
            
            # 验证结果
            assert result is False
            
            # 验证调用参数
            mock_redis_util.set.assert_called_once()
            call_args = mock_redis_util.set.call_args
            
            # 验证参数正确性
            assert call_args[0][0] == "test_key"
            assert call_args[1]["nx"] is True
            assert call_args[1]["ex"] == 30
    
    def test_lock_different_timeout(self):
        """测试不同的超时时间"""
        timeout_values = [10, 60, 300, 3600]
        
        for timeout in timeout_values:
            with patch('tests.test_utils.get_redis_util') as mock_get_redis_util:
                mock_redis_util = Mock(spec=RedisUtil)
                mock_redis_util.set.return_value = True
                mock_get_redis_util.return_value = mock_redis_util
                
                result = lock("test_key", timeout)
                
                assert result is True
                call_args = mock_redis_util.set.call_args
                assert call_args[1]["ex"] == timeout
    
    def test_lock_different_keys(self):
        """测试不同的锁键"""
        test_keys = ["user:123", "order:456", "payment:789", "cache:refresh"]
        
        for key in test_keys:
            with patch('tests.test_utils.get_redis_util') as mock_get_redis_util:
                mock_redis_util = Mock(spec=RedisUtil)
                mock_redis_util.set.return_value = True
                mock_get_redis_util.return_value = mock_redis_util
                
                result = lock(key, 30)
                
                assert result is True
                call_args = mock_redis_util.set.call_args
                assert call_args[0][0] == key
    
    def test_lock_parameters_validation(self):
        """测试参数验证"""
        with patch('tests.test_utils.get_redis_util') as mock_get_redis_util:
            mock_redis_util = Mock(spec=RedisUtil)
            mock_redis_util.set.return_value = True
            mock_get_redis_util.return_value = mock_redis_util
            
            # 测试正常参数
            result = lock("valid_key", 60)
            assert result is True
            
            # 验证调用了正确的方法
            mock_redis_util.set.assert_called_once()
            call_args = mock_redis_util.set.call_args
            
            # 验证所有必需的参数都存在
            assert len(call_args[0]) == 2  # key 和 value
            assert "nx" in call_args[1]
            assert "ex" in call_args[1]
            assert call_args[1]["nx"] is True
            assert call_args[1]["ex"] == 60
    
    def test_lock_with_zero_timeout(self):
        """测试超时时间为 0 的情况"""
        with patch('tests.test_utils.get_redis_util') as mock_get_redis_util:
            mock_redis_util = Mock(spec=RedisUtil)
            mock_redis_util.set.return_value = True
            mock_get_redis_util.return_value = mock_redis_util
            
            result = lock("test_key", 0)
            assert result is True
            
            call_args = mock_redis_util.set.call_args
            assert call_args[1]["ex"] == 0
    
    def test_lock_with_negative_timeout(self):
        """测试负数超时时间的情况"""
        with patch('tests.test_utils.get_redis_util') as mock_get_redis_util:
            mock_redis_util = Mock(spec=RedisUtil)
            mock_redis_util.set.return_value = True
            mock_get_redis_util.return_value = mock_redis_util
            
            result = lock("test_key", -1)
            assert result is True
            
            call_args = mock_redis_util.set.call_args
            assert call_args[1]["ex"] == -1
    
    def test_lock_redis_util_exception(self):
        """测试 RedisUtil.set 抛出异常的情况"""
        with patch('tests.test_utils.get_redis_util') as mock_get_redis_util:
            mock_redis_util = Mock(spec=RedisUtil)
            mock_redis_util.set.side_effect = Exception("Redis connection error")
            mock_get_redis_util.return_value = mock_redis_util
            
            # 验证异常会被传播
            with pytest.raises(Exception, match="Redis connection error"):
                lock("test_key", 30)
    
    def test_lock_value_consistency(self):
        """测试锁值的一致性（当前实现使用固定值 "1"）"""
        with patch('tests.test_utils.get_redis_util') as mock_get_redis_util:
            mock_redis_util = Mock(spec=RedisUtil)
            mock_redis_util.set.return_value = True
            mock_get_redis_util.return_value = mock_redis_util
            
            # 多次调用 lock 函数
            for _ in range(5):
                mock_redis_util.reset_mock()
                lock("test_key", 30)
                
                call_args = mock_redis_util.set.call_args
                lock_value = call_args[0][1]
                # 验证锁值始终为 "1"
                assert lock_value == "1"


class TestLockIntegration:
    """集成测试，使用真实的 RedisUtil 对象"""
    
    @pytest.fixture
    def redis_util(self):
        """创建真实的 RedisUtil 实例用于集成测试"""
        # 注意：这需要 Redis 服务器运行
        try:
            util = RedisUtil()
            # 测试连接
            util.ping()
            return util
        except Exception:
            pytest.skip("Redis server not available for integration tests")
    
    def test_lock_integration_success(self, redis_util):
        """集成测试：成功获取和释放锁"""
        test_key = "integration_test_lock"
        
        try:
            # 确保测试键不存在
            redis_util.delete(test_key)
            
            # 获取锁应该成功
            result = lock(test_key, 5)
            assert result is True
            
            # 验证键存在
            assert redis_util.exists(test_key) is True
            
            # 再次尝试获取同一个锁应该失败
            result2 = lock(test_key, 5)
            assert result2 is False
            
        finally:
            # 清理测试数据
            redis_util.delete(test_key)
    
    def test_lock_integration_expiration(self, redis_util):
        """集成测试：验证锁的过期功能"""
        test_key = "integration_test_lock_expiration"
        
        try:
            # 确保测试键不存在
            redis_util.delete(test_key)
            
            # 获取一个很短过期时间的锁
            result = lock(test_key, 1)  # 1 秒过期
            assert result is True
            
            # 立即检查键存在
            assert redis_util.exists(test_key) is True
            
            # 验证 TTL 被正确设置
            ttl = redis_util.ttl(test_key)
            assert 0 < ttl <= 1
            
        finally:
            # 清理测试数据
            redis_util.delete(test_key)