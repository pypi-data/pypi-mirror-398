#!/usr/bin/env python3
"""
xSystem Performance Benchmark Suite
===================================

Comprehensive benchmarks for all xSystem components to ensure production-grade performance.

Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Company: eXonware.com
Generated: 2025-01-27
"""

import asyncio
import time
import statistics
import multiprocessing as mp
from typing import Any, Callable
from dataclasses import dataclass
import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from exonware.xwsystem import (
    # Async I/O
    async_safe_write_text, async_safe_read_text,
    # Caching
    LRUCache, AsyncLRUCache, LFUCache, TTLCache,
    # HTTP
    AdvancedHttpClient, MockTransport,
    # Validation
    xModel, Field,
    # IPC
    MessageQueue, AsyncMessageQueue, ProcessPool, SharedData,
    # Serialization
    JsonSerializer, YamlSerializer, MsgPackSerializer,
    # Security
    AES_GCM, secure_hash,
    # System Monitoring
    get_cpu_usage, get_memory_usage
)


@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""
    name: str
    operations: int
    total_time: float
    ops_per_second: float
    avg_time_per_op: float
    min_time: float
    max_time: float
    memory_usage_mb: float
    cpu_usage_percent: float


class PerformanceBenchmark:
    """
    Comprehensive performance benchmark suite for xSystem.
    
    Features:
    - Multi-threaded and async benchmarks
    - Memory usage monitoring
    - CPU usage tracking
    - Statistical analysis
    - Comparative reporting
    """
    
    def __init__(self, iterations: int = 1000, warmup_iterations: int = 100):
        """
        Initialize benchmark suite.
        
        Args:
            iterations: Number of iterations for each benchmark
            warmup_iterations: Number of warmup iterations
        """
        self.iterations = iterations
        self.warmup_iterations = warmup_iterations
        self.results: list[BenchmarkResult] = []
    
    def run_benchmark(self, name: str, func: Callable, *args, **kwargs) -> BenchmarkResult:
        """
        Run a single benchmark test.
        
        Args:
            name: Benchmark name
            func: Function to benchmark
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            BenchmarkResult
        """
        print(f"🔄 Running benchmark: {name}")
        
        # Warmup
        for _ in range(self.warmup_iterations):
            try:
                func(*args, **kwargs)
            except Exception:
                pass
        
        # Measure baseline memory and CPU
        initial_memory = self._get_memory_usage()
        initial_cpu = get_cpu_usage(interval=0.1) if 'get_cpu_usage' in globals() else 0.0
        
        # Run actual benchmark
        times = []
        start_time = time.perf_counter()
        
        for _ in range(self.iterations):
            op_start = time.perf_counter()
            try:
                func(*args, **kwargs)
                op_end = time.perf_counter()
                times.append(op_end - op_start)
            except Exception as e:
                print(f"  ⚠️  Error in benchmark {name}: {e}")
                times.append(0.0)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Measure final memory and CPU
        final_memory = self._get_memory_usage()
        final_cpu = get_cpu_usage(interval=0.1) if 'get_cpu_usage' in globals() else 0.0
        
        # Calculate statistics
        ops_per_second = self.iterations / total_time if total_time > 0 else 0
        avg_time = statistics.mean(times) if times else 0
        min_time = min(times) if times else 0
        max_time = max(times) if times else 0
        memory_delta = final_memory - initial_memory
        cpu_delta = final_cpu - initial_cpu
        
        result = BenchmarkResult(
            name=name,
            operations=self.iterations,
            total_time=total_time,
            ops_per_second=ops_per_second,
            avg_time_per_op=avg_time,
            min_time=min_time,
            max_time=max_time,
            memory_usage_mb=memory_delta,
            cpu_usage_percent=cpu_delta
        )
        
        self.results.append(result)
        
        print(f"  ✅ {ops_per_second:,.0f} ops/sec ({avg_time*1000:.3f}ms avg)")
        return result
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    async def run_async_benchmark(self, name: str, func: Callable, *args, **kwargs) -> BenchmarkResult:
        """
        Run an async benchmark test.
        
        Args:
            name: Benchmark name
            func: Async function to benchmark
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            BenchmarkResult
        """
        print(f"🔄 Running async benchmark: {name}")
        
        # Warmup
        for _ in range(self.warmup_iterations):
            try:
                await func(*args, **kwargs)
            except Exception:
                pass
        
        # Measure baseline
        initial_memory = self._get_memory_usage()
        
        # Run benchmark
        times = []
        start_time = time.perf_counter()
        
        for _ in range(self.iterations):
            op_start = time.perf_counter()
            try:
                await func(*args, **kwargs)
                op_end = time.perf_counter()
                times.append(op_end - op_start)
            except Exception as e:
                print(f"  ⚠️  Error in async benchmark {name}: {e}")
                times.append(0.0)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        final_memory = self._get_memory_usage()
        
        # Calculate statistics
        ops_per_second = self.iterations / total_time if total_time > 0 else 0
        avg_time = statistics.mean(times) if times else 0
        min_time = min(times) if times else 0
        max_time = max(times) if times else 0
        memory_delta = final_memory - initial_memory
        
        result = BenchmarkResult(
            name=name,
            operations=self.iterations,
            total_time=total_time,
            ops_per_second=ops_per_second,
            avg_time_per_op=avg_time,
            min_time=min_time,
            max_time=max_time,
            memory_usage_mb=memory_delta,
            cpu_usage_percent=0.0
        )
        
        self.results.append(result)
        print(f"  ✅ {ops_per_second:,.0f} ops/sec ({avg_time*1000:.3f}ms avg)")
        return result


def benchmark_caching():
    """Benchmark caching performance."""
    benchmark = PerformanceBenchmark(iterations=10000)
    
    print("\n🚀 CACHING BENCHMARKS")
    print("=" * 40)
    
    # LRU Cache
    lru = LRUCache(capacity=1000)
    benchmark.run_benchmark("LRU Cache Put", lru.put, "key", "value")
    benchmark.run_benchmark("LRU Cache Get", lru.get, "key")
    
    # LFU Cache
    lfu = LFUCache(capacity=1000)
    benchmark.run_benchmark("LFU Cache Put", lfu.put, "key", "value")
    benchmark.run_benchmark("LFU Cache Get", lfu.get, "key")
    
    # TTL Cache
    ttl = TTLCache(capacity=1000, ttl=60)
    benchmark.run_benchmark("TTL Cache Put", ttl.put, "key", "value")
    benchmark.run_benchmark("TTL Cache Get", ttl.get, "key")
    
    return benchmark.results


async def benchmark_async_caching():
    """Benchmark async caching performance."""
    benchmark = PerformanceBenchmark(iterations=5000)
    
    print("\n🚀 ASYNC CACHING BENCHMARKS")
    print("=" * 40)
    
    # Async LRU Cache
    async_lru = AsyncLRUCache(capacity=1000)
    await benchmark.run_async_benchmark("Async LRU Put", async_lru.put, "key", "value")
    await benchmark.run_async_benchmark("Async LRU Get", async_lru.get, "key")
    
    return benchmark.results


def benchmark_serialization():
    """Benchmark serialization performance."""
    benchmark = PerformanceBenchmark(iterations=1000)
    
    print("\n🚀 SERIALIZATION BENCHMARKS")
    print("=" * 40)
    
    # Test data
    test_data = {
        "users": [
            {"id": i, "name": f"User{i}", "active": i % 2 == 0, "score": i * 1.5}
            for i in range(100)
        ],
        "metadata": {
            "version": "1.0",
            "timestamp": time.time(),
            "config": {"debug": False, "max_items": 1000}
        }
    }
    
    # JSON Serialization
    json_serializer = JsonSerializer()
    benchmark.run_benchmark("JSON Serialize", json_serializer.serialize, test_data)
    
    serialized = json_serializer.serialize(test_data)
    benchmark.run_benchmark("JSON Deserialize", json_serializer.deserialize, serialized)
    
    # YAML Serialization (if available)
    try:
        yaml_serializer = YamlSerializer()
        benchmark.run_benchmark("YAML Serialize", yaml_serializer.serialize, test_data)
        yaml_serialized = yaml_serializer.serialize(test_data)
        benchmark.run_benchmark("YAML Deserialize", yaml_serializer.deserialize, yaml_serialized)
    except Exception:
        print("  ⚠️  YAML serializer not available")
    
    # MessagePack Serialization (if available)
    try:
        msgpack_serializer = MsgPackSerializer()
        benchmark.run_benchmark("MsgPack Serialize", msgpack_serializer.serialize, test_data)
        msgpack_serialized = msgpack_serializer.serialize(test_data)
        benchmark.run_benchmark("MsgPack Deserialize", msgpack_serializer.deserialize, msgpack_serialized)
    except Exception:
        print("  ⚠️  MsgPack serializer not available")
    
    return benchmark.results


async def benchmark_async_io():
    """Benchmark async I/O performance."""
    benchmark = PerformanceBenchmark(iterations=100)
    
    print("\n🚀 ASYNC I/O BENCHMARKS")
    print("=" * 40)
    
    # Test data
    test_content = "x" * 1024  # 1KB of data
    test_file = "benchmark_test.txt"
    
    # Async file operations
    await benchmark.run_async_benchmark("Async Write", async_safe_write_text, test_file, test_content)
    await benchmark.run_async_benchmark("Async Read", async_safe_read_text, test_file)
    
    # Cleanup
    try:
        os.remove(test_file)
    except:
        pass
    
    return benchmark.results


def benchmark_validation():
    """Benchmark validation performance."""
    benchmark = PerformanceBenchmark(iterations=1000)
    
    print("\n🚀 VALIDATION BENCHMARKS")
    print("=" * 40)
    
    # Define model
    class TestUser(xModel):
        name: str
        age: int = Field(ge=0, le=150)
        email: str = Field(pattern=r'^[^@]+@[^@]+\.[^@]+$')
        score: float = Field(ge=0.0, le=100.0)
    
    # Test data
    valid_data = {
        "name": "John Doe",
        "age": "30",  # String that should be coerced to int
        "email": "john@example.com",
        "score": 85.5
    }
    
    # Validation benchmark
    benchmark.run_benchmark("Model Validation", TestUser.model_validate, valid_data)
    
    # Schema generation benchmark
    benchmark.run_benchmark("Schema Generation", TestUser.model_json_schema)
    
    return benchmark.results


def benchmark_security():
    """Benchmark security operations."""
    benchmark = PerformanceBenchmark(iterations=100)
    
    print("\n🚀 SECURITY BENCHMARKS")
    print("=" * 40)
    
    # AES-GCM encryption
    key = AES_GCM.generate_key(256)
    cipher = AES_GCM(key)
    nonce = AES_GCM.generate_nonce()
    test_data = b"x" * 1024  # 1KB of data
    
    benchmark.run_benchmark("AES-GCM Encrypt", cipher.encrypt, nonce, test_data, b"auth")
    
    encrypted = cipher.encrypt(nonce, test_data, b"auth")
    benchmark.run_benchmark("AES-GCM Decrypt", cipher.decrypt, nonce, encrypted, b"auth")
    
    # Secure hashing
    benchmark.run_benchmark("SHA256 Hash", secure_hash, test_data, "SHA256")
    benchmark.run_benchmark("SHA512 Hash", secure_hash, test_data, "SHA512")
    
    return benchmark.results


async def benchmark_http():
    """Benchmark HTTP client performance."""
    benchmark = PerformanceBenchmark(iterations=100)
    
    print("\n🚀 HTTP CLIENT BENCHMARKS")
    print("=" * 40)
    
    # Mock responses for testing
    mock_responses = {
        "https://api.test.com/data": {
            "status_code": 200,
            "content": b'{"success": true, "data": "test"}',
            "headers": {"Content-Type": "application/json"}
        }
    }
    
    # HTTP client with mock transport
    transport = MockTransport(mock_responses)
    client = AdvancedHttpClient(transport=transport)
    
    # HTTP GET benchmark
    await benchmark.run_async_benchmark("HTTP GET", client.get, "https://api.test.com/data")
    
    await client.close()
    return benchmark.results


def benchmark_ipc():
    """Benchmark IPC performance."""
    benchmark = PerformanceBenchmark(iterations=100)
    
    print("\n🚀 IPC BENCHMARKS")
    print("=" * 40)
    
    # Message Queue
    with MessageQueue(maxsize=1000) as queue:
        benchmark.run_benchmark("Queue Put", queue.put, "test message")
        benchmark.run_benchmark("Queue Get", queue.get_nowait)
    
    # Shared Memory
    with SharedData("benchmark_segment", 1024) as segment:
        test_data = {"benchmark": True, "data": list(range(50))}
        benchmark.run_benchmark("Shared Memory Set", segment.set, test_data)
        benchmark.run_benchmark("Shared Memory Get", segment.get)
    
    return benchmark.results


def benchmark_process_pool():
    """Benchmark process pool performance."""
    benchmark = PerformanceBenchmark(iterations=20)
    
    print("\n🚀 PROCESS POOL BENCHMARKS")
    print("=" * 40)
    
    def cpu_task(n):
        """Simple CPU-intensive task."""
        return sum(i * i for i in range(n))
    
    with ProcessPool(max_workers=mp.cpu_count()) as pool:
        # Submit task benchmark
        benchmark.run_benchmark("Process Pool Submit", pool.submit, cpu_task, 1000)
        
        # Wait for results (submit multiple tasks)
        task_ids = []
        for _ in range(10):
            task_id = pool.submit(cpu_task, 1000)
            task_ids.append(task_id)
        
        # Wait for completion
        start_time = time.perf_counter()
        results = pool.wait_for_all(timeout=30.0)
        end_time = time.perf_counter()
        
        successful = len([r for r in results if r.success])
        total_time = end_time - start_time
        throughput = successful / total_time if total_time > 0 else 0
        
        print(f"  ✅ Process Pool Throughput: {throughput:.1f} tasks/sec ({successful}/{len(results)} successful)")
    
    return benchmark.results


def generate_report(all_results: list[BenchmarkResult]) -> str:
    """Generate comprehensive benchmark report."""
    report = []
    report.append("=" * 80)
    report.append("🚀 xSystem Performance Benchmark Report")
    report.append("=" * 80)
    report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"System: {sys.platform} | Python: {sys.version.split()[0]}")
    report.append("")
    
    # Group results by category
    categories = {}
    for result in all_results:
        category = result.name.split()[0]
        if category not in categories:
            categories[category] = []
        categories[category].append(result)
    
    # Generate category reports
    for category, results in categories.items():
        report.append(f"📊 {category.upper()} PERFORMANCE")
        report.append("-" * 40)
        
        for result in results:
            report.append(f"  {result.name}:")
            report.append(f"    Operations/sec: {result.ops_per_second:,.0f}")
            report.append(f"    Avg time/op:    {result.avg_time_per_op*1000:.3f}ms")
            report.append(f"    Min/Max time:   {result.min_time*1000:.3f}ms / {result.max_time*1000:.3f}ms")
            if result.memory_usage_mb > 0:
                report.append(f"    Memory usage:   {result.memory_usage_mb:.2f}MB")
            report.append("")
        
        # Category summary
        avg_ops = statistics.mean([r.ops_per_second for r in results])
        report.append(f"  📈 {category} Average: {avg_ops:,.0f} ops/sec")
        report.append("")
    
    # Overall summary
    total_ops = sum(r.ops_per_second for r in all_results)
    avg_ops = total_ops / len(all_results) if all_results else 0
    
    report.append("🎯 OVERALL PERFORMANCE SUMMARY")
    report.append("-" * 40)
    report.append(f"Total benchmarks:     {len(all_results)}")
    report.append(f"Average performance:  {avg_ops:,.0f} ops/sec")
    report.append(f"Best performance:     {max(r.ops_per_second for r in all_results):,.0f} ops/sec")
    report.append(f"Total operations:     {sum(r.operations for r in all_results):,}")
    report.append("")
    
    # Performance grades
    report.append("🏆 PERFORMANCE GRADES")
    report.append("-" * 40)
    
    for result in sorted(all_results, key=lambda x: x.ops_per_second, reverse=True)[:10]:
        if result.ops_per_second >= 100000:
            grade = "🥇 EXCELLENT"
        elif result.ops_per_second >= 50000:
            grade = "🥈 VERY GOOD"
        elif result.ops_per_second >= 10000:
            grade = "🥉 GOOD"
        else:
            grade = "📊 ACCEPTABLE"
        
        report.append(f"  {grade}: {result.name} ({result.ops_per_second:,.0f} ops/sec)")
    
    report.append("")
    report.append("=" * 80)
    
    return "\n".join(report)


async def main():
    """Run comprehensive benchmark suite."""
    print("🚀 Starting xSystem Performance Benchmark Suite")
    print("=" * 60)
    
    all_results = []
    
    try:
        # Run all benchmarks
        all_results.extend(benchmark_caching())
        all_results.extend(await benchmark_async_caching())
        all_results.extend(benchmark_serialization())
        all_results.extend(await benchmark_async_io())
        all_results.extend(benchmark_validation())
        all_results.extend(benchmark_security())
        all_results.extend(await benchmark_http())
        all_results.extend(benchmark_ipc())
        all_results.extend(benchmark_process_pool())
        
        # Generate and display report
        report = generate_report(all_results)
        print("\n" + report)
        
        # Save report to file
        with open("benchmark_report.txt", "w") as f:
            f.write(report)
        
        print("\n📁 Report saved to: benchmark_report.txt")
        
        # Save detailed results as JSON
        results_data = [
            {
                "name": r.name,
                "operations": r.operations,
                "ops_per_second": r.ops_per_second,
                "avg_time_ms": r.avg_time_per_op * 1000,
                "memory_usage_mb": r.memory_usage_mb
            }
            for r in all_results
        ]
        
        with open("benchmark_results.json", "w") as f:
            json.dump(results_data, f, indent=2)
        
        print("📁 Detailed results saved to: benchmark_results.json")
        
    except Exception as e:
        print(f"❌ Benchmark suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
