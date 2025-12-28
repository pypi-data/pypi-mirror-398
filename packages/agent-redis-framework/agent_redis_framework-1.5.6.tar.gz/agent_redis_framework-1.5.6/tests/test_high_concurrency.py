#!/usr/bin/env python3
"""
高并发性能测试 - TPS=500 目标
测试覆盖：Stream、ZSet、Hash 场景
"""

import asyncio
import time
import threading
import statistics
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Callable, Optional
import uuid
import random
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from agent_redis_framework.helper import (
    get_streams_client, get_sorted_set_queue, get_hash_client, get_redis_util
)
from agent_redis_framework.redis_client import (
    get_pool_stats, log_pool_stats
)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    operation_type: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    total_duration: float
    tps: float
    avg_latency: float
    min_latency: float
    max_latency: float
    p95_latency: float
    p99_latency: float
    error_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.operation_times: List[float] = []
        self.errors: List[Exception] = []
        self.start_time: float = 0
        self.end_time: float = 0
        self.lock = threading.Lock()
    
    def start(self):
        """开始监控"""
        self.start_time = time.time()
        self.operation_times.clear()
        self.errors.clear()
    
    def record_operation(self, duration: float, error: Optional[Exception] = None):
        """记录单次操作"""
        with self.lock:
            if error:
                self.errors.append(error)
            else:
                self.operation_times.append(duration)
    
    def stop(self) -> PerformanceMetrics:
        """停止监控并生成指标"""
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        successful_ops = len(self.operation_times)
        failed_ops = len(self.errors)
        total_ops = successful_ops + failed_ops
        
        if successful_ops > 0:
            avg_latency = statistics.mean(self.operation_times)
            min_latency = min(self.operation_times)
            max_latency = max(self.operation_times)
            
            # 计算百分位数
            sorted_times = sorted(self.operation_times)
            p95_idx = int(0.95 * len(sorted_times))
            p99_idx = int(0.99 * len(sorted_times))
            p95_latency = sorted_times[p95_idx] if p95_idx < len(sorted_times) else max_latency
            p99_latency = sorted_times[p99_idx] if p99_idx < len(sorted_times) else max_latency
        else:
            avg_latency = min_latency = max_latency = p95_latency = p99_latency = 0
        
        tps = total_ops / total_duration if total_duration > 0 else 0
        error_rate = failed_ops / total_ops if total_ops > 0 else 0
        
        return PerformanceMetrics(
            operation_type="",
            total_operations=total_ops,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            total_duration=total_duration,
            tps=tps,
            avg_latency=avg_latency * 1000,  # 转换为毫秒
            min_latency=min_latency * 1000,
            max_latency=max_latency * 1000,
            p95_latency=p95_latency * 1000,
            p99_latency=p99_latency * 1000,
            error_rate=error_rate * 100  # 转换为百分比
        )


class HighConcurrencyTester:
    """高并发测试器"""
    
    def __init__(self, target_tps: int = 500, test_duration: int = 30):
        self.target_tps = target_tps
        self.test_duration = test_duration
        self.max_workers = min(100, target_tps // 2)  # 限制最大线程数
        
        # 设置高并发环境变量
        os.environ.update({
            'REDIS_MAX_CONNECTIONS': '1024',
            'REDIS_SOCKET_TIMEOUT': '5',
            'REDIS_SOCKET_CONNECT_TIMEOUT': '3',
            'REDIS_HEALTH_CHECK_INTERVAL': '30'
        })
        
        print(f"🚀 高并发测试配置:")
        print(f"   目标 TPS: {self.target_tps}")
        print(f"   测试时长: {self.test_duration}秒")
        print(f"   最大工作线程: {self.max_workers}")
        print(f"   连接池配置: max_connections={os.getenv('REDIS_MAX_CONNECTIONS')}")
    
    def _execute_with_rate_limit(self, operation_func: Callable, monitor: PerformanceMonitor):
        """以指定速率执行操作"""
        interval = 1.0 / self.target_tps  # 每次操作的间隔时间
        
        def worker():
            while time.time() - monitor.start_time < self.test_duration:
                start_time = time.time()
                error = None
                
                try:
                    operation_func()
                except Exception as e:
                    error = e
                
                end_time = time.time()
                duration = end_time - start_time
                monitor.record_operation(duration, error)
                
                # 控制速率
                elapsed = end_time - start_time
                if elapsed < interval:
                    time.sleep(interval - elapsed)
        
        # 启动多个工作线程
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(worker) for _ in range(self.max_workers)]
            
            # 等待所有任务完成或超时
            for future in as_completed(futures, timeout=self.test_duration + 5):
                try:
                    future.result()
                except Exception as e:
                    print(f"Worker 线程异常: {e}")
    
    def test_stream_operations(self) -> PerformanceMetrics:
        """测试 Stream 操作性能"""
        print("\n📡 开始 Stream 高并发测试...")
        
        stream_name = f"test_stream_{uuid.uuid4().hex[:8]}"
        consumer_group = "test_group"
        
        # 初始化 Stream 客户端
        stream_client = get_streams_client(stream_name)
        
        # 创建消费者组
        try:
            stream_client.ensure_group(consumer_group)
        except Exception:
            pass  # 组可能已存在
        
        monitor = PerformanceMonitor()
        
        def stream_operation():
            """Stream 操作：发送消息"""
            from agent_redis_framework.streams import StreamMsg
            message_data = StreamMsg(
                payload=json.dumps({
                    'id': str(uuid.uuid4()),
                    'timestamp': str(int(time.time() * 1000)),
                    'data': f"test_message_{random.randint(1000, 9999)}",
                    'payload': 'x' * random.randint(100, 500)  # 随机大小的负载
                }),
                meta={'test': 'high_concurrency', 'seq': random.randint(1, 1000)}
            )
            stream_client.push(message_data)
        
        monitor.start()
        self._execute_with_rate_limit(stream_operation, monitor)
        metrics = monitor.stop()
        metrics.operation_type = "Stream Operations"
        
        # 清理
        try:
            redis_util = get_redis_util()
            redis_util.redis.delete(stream_name)
        except Exception:
            pass
        
        return metrics
    
    def test_zset_operations(self) -> PerformanceMetrics:
        """测试 ZSet (SortedSet) 操作性能"""
        print("\n🏆 开始 ZSet 高并发测试...")
        
        queue_name = f"test_zset_{uuid.uuid4().hex[:8]}"
        sorted_queue = get_sorted_set_queue(queue_name)
        
        monitor = PerformanceMonitor()
        
        def zset_operation():
            """ZSet 操作：添加、查询、排名"""
            from agent_redis_framework.sortedset import SortedTask
            operation_type = random.choice(['push', 'size'])
            
            if operation_type == 'push':
                # 添加元素
                score = random.uniform(0, 1000)
                task = SortedTask(
                    payload=json.dumps({'task_id': str(uuid.uuid4())}),
                    meta={'priority': score}
                )
                sorted_queue.push(task, score)
            
            elif operation_type == 'size':
                # 获取队列大小
                sorted_queue.size()

        monitor.start()
        self._execute_with_rate_limit(zset_operation, monitor)
        metrics = monitor.stop()
        metrics.operation_type = "ZSet Operations"
        
        # 清理
        try:
            redis_util = get_redis_util()
            redis_util.redis.delete(queue_name)
        except Exception:
            pass
        
        return metrics
    
    def test_hash_operations(self) -> PerformanceMetrics:
        """测试 Hash 操作性能"""
        print("\n🗂️ 开始 Hash 高并发测试...")
        
        hash_name = f"test_hash_{uuid.uuid4().hex[:8]}"
        hash_client = get_hash_client(hash_name)
        
        monitor = PerformanceMonitor()
        
        def hash_operation():
            """Hash 操作：设置、获取、批量操作"""
            operation_type = random.choice(['set', 'get', 'set_many', 'get_many'])
            
            if operation_type == 'set':
                # 设置单个字段
                field = f"field_{random.randint(1, 1000)}"
                value = f"value_{uuid.uuid4().hex}"
                hash_client.set(field, value)
            
            elif operation_type == 'get':
                # 获取单个字段
                field = f"field_{random.randint(1, 1000)}"
                try:
                    hash_client.get(field)
                except Exception:
                    pass  # 字段可能不存在
            
            elif operation_type == 'set_many':
                # 批量设置 - 确保类型兼容
                from typing import cast
                from agent_redis_framework.hashes.hash_client import SupportedScalar
                fields = cast(dict[str, SupportedScalar], {
                    f"batch_field_{i}": f"batch_value_{uuid.uuid4().hex[:8]}"
                    for i in range(5)
                })
                hash_client.set_many(fields)
            
            elif operation_type == 'get_many':
                # 批量获取
                fields = [f"field_{i}" for i in range(1, 11)]
                try:
                    hash_client.get_many(fields)
                except Exception:
                    pass
        
        monitor.start()
        self._execute_with_rate_limit(hash_operation, monitor)
        metrics = monitor.stop()
        metrics.operation_type = "Hash Operations"
        
        # 清理
        try:
            redis_util = get_redis_util()
            redis_util.redis.delete(hash_name)
        except Exception:
            pass
        
        return metrics
    
    def run_comprehensive_test(self) -> Dict[str, PerformanceMetrics]:
        """运行综合性能测试"""
        print("🎯 开始高并发综合性能测试")
        print("=" * 60)
        
        # 记录初始连接池状态
        print("\n📊 测试前连接池状态:")
        log_pool_stats()
        
        results = {}
        
        # 依次测试各个场景
        test_scenarios = [
            ("stream", self.test_stream_operations),
            ("zset", self.test_zset_operations),
            ("hash", self.test_hash_operations)
        ]
        
        for scenario_name, test_func in test_scenarios:
            print(f"\n🔄 等待 3 秒后开始 {scenario_name.upper()} 测试...")
            time.sleep(3)  # 给连接池一些恢复时间
            
            try:
                metrics = test_func()
                results[scenario_name] = metrics
                
                # 输出即时结果
                print(f"✅ {metrics.operation_type} 测试完成:")
                print(f"   TPS: {metrics.tps:.2f}")
                print(f"   成功率: {100 - metrics.error_rate:.2f}%")
                print(f"   平均延迟: {metrics.avg_latency:.2f}ms")
                
            except Exception as e:
                print(f"❌ {scenario_name.upper()} 测试失败: {e}")
                results[scenario_name] = None
        
        # 记录测试后连接池状态
        print("\n📊 测试后连接池状态:")
        log_pool_stats()
        
        return results
    
    def generate_report(self, results: Dict[str, PerformanceMetrics]) -> str:
        """生成测试报告"""
        report_lines = [
            "🎯 高并发性能测试报告",
            "=" * 60,
            f"测试配置: 目标 TPS={self.target_tps}, 测试时长={self.test_duration}秒",
            f"连接池配置: max_connections={os.getenv('REDIS_MAX_CONNECTIONS')}",
            ""
        ]
        
        # 汇总统计
        total_tps = 0
        total_operations = 0
        successful_scenarios = 0
        
        for scenario_name, metrics in results.items():
            if metrics:
                total_tps += metrics.tps
                total_operations += metrics.total_operations
                successful_scenarios += 1
        
        report_lines.extend([
            "📈 汇总统计:",
            f"   总 TPS: {total_tps:.2f}",
            f"   总操作数: {total_operations}",
            f"   成功场景: {successful_scenarios}/{len(results)}",
            ""
        ])
        
        # 详细结果
        for scenario_name, metrics in results.items():
            if metrics:
                report_lines.extend([
                    f"🔍 {metrics.operation_type} 详细结果:",
                    f"   TPS: {metrics.tps:.2f} (目标: {self.target_tps})",
                    f"   总操作数: {metrics.total_operations}",
                    f"   成功操作: {metrics.successful_operations}",
                    f"   失败操作: {metrics.failed_operations}",
                    f"   成功率: {100 - metrics.error_rate:.2f}%",
                    f"   平均延迟: {metrics.avg_latency:.2f}ms",
                    f"   P95 延迟: {metrics.p95_latency:.2f}ms",
                    f"   P99 延迟: {metrics.p99_latency:.2f}ms",
                    f"   最小延迟: {metrics.min_latency:.2f}ms",
                    f"   最大延迟: {metrics.max_latency:.2f}ms",
                    ""
                ])
            else:
                report_lines.extend([
                    f"❌ {scenario_name.upper()} 测试失败",
                    ""
                ])
        
        # 性能评估
        report_lines.extend([
            "🎯 性能评估:",
        ])
        
        if total_tps >= self.target_tps * 0.9:
            report_lines.append("   ✅ 优秀: 达到目标 TPS 的 90% 以上")
        elif total_tps >= self.target_tps * 0.7:
            report_lines.append("   ⚠️ 良好: 达到目标 TPS 的 70-90%")
        else:
            report_lines.append("   ❌ 需要优化: 未达到目标 TPS 的 70%")
        
        # 优化建议
        report_lines.extend([
            "",
            "💡 优化建议:",
        ])
        
        if total_tps < self.target_tps * 0.8:
            report_lines.extend([
                "   - 考虑增加 REDIS_MAX_CONNECTIONS",
                "   - 检查网络延迟和 Redis 服务器性能",
                "   - 优化业务逻辑减少单次操作复杂度"
            ])
        
        avg_error_rate = sum(m.error_rate for m in results.values() if m) / successful_scenarios if successful_scenarios > 0 else 0
        if avg_error_rate > 1:
            report_lines.extend([
                "   - 错误率较高，检查 Redis 连接稳定性",
                "   - 考虑增加重试机制和错误处理"
            ])
        
        return "\n".join(report_lines)


def main():
    """主函数"""
    # 创建测试器
    tester = HighConcurrencyTester(target_tps=500, test_duration=30)
    
    try:
        # 运行测试
        results = tester.run_comprehensive_test()
        
        # 生成并输出报告
        report = tester.generate_report(results)
        print("\n" + report)
        
        # 保存报告到文件
        report_file = f"performance_test_report_{int(time.time())}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 保存 JSON 格式的详细数据
        json_data = {
            'test_config': {
                'target_tps': tester.target_tps,
                'test_duration': tester.test_duration,
                'max_workers': tester.max_workers
            },
            'results': {k: v.to_dict() if v else None for k, v in results.items()},
            'timestamp': int(time.time())
        }
        
        json_file = f"performance_test_data_{int(time.time())}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 报告已保存:")
        print(f"   文本报告: {report_file}")
        print(f"   JSON 数据: {json_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()