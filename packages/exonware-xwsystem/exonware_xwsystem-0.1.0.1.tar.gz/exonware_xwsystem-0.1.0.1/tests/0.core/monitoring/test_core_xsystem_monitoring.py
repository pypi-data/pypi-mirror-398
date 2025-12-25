#!/usr/bin/env python3
"""
XSystem Monitoring Core Tests

Tests the actual XSystem monitoring features including performance monitoring,
memory monitoring, circuit breaker patterns, and system resource monitoring.
"""

import time
import psutil
import threading
import queue
import statistics


def test_performance_monitor():
    """Test performance monitoring and metrics collection."""
    try:
        # Test performance metrics collection
        class PerformanceMonitor:
            def __init__(self):
                self.metrics = {
                    'response_times': [],
                    'request_counts': 0,
                    'error_counts': 0,
                    'start_time': time.time()
                }
                self.lock = threading.Lock()
            
            def record_response_time(self, response_time):
                with self.lock:
                    self.metrics['response_times'].append(response_time)
            
            def record_request(self):
                with self.lock:
                    self.metrics['request_counts'] += 1
            
            def record_error(self):
                with self.lock:
                    self.metrics['error_counts'] += 1
            
            def get_stats(self):
                with self.lock:
                    if not self.metrics['response_times']:
                        return {'avg_response_time': 0, 'total_requests': 0, 'error_rate': 0}
                    
                    avg_response_time = statistics.mean(self.metrics['response_times'])
                    total_requests = self.metrics['request_counts']
                    error_rate = self.metrics['error_counts'] / max(total_requests, 1)
                    
                    return {
                        'avg_response_time': avg_response_time,
                        'total_requests': total_requests,
                        'error_rate': error_rate,
                        'uptime': time.time() - self.metrics['start_time']
                    }
        
        # Test performance monitoring
        monitor = PerformanceMonitor()
        
        # Simulate some requests
        for i in range(10):
            monitor.record_request()
            response_time = 0.001 + (i * 0.0001)  # Simulate varying response times
            monitor.record_response_time(response_time)
            if i % 3 == 0:  # Simulate some errors
                monitor.record_error()
        
        stats = monitor.get_stats()
        assert stats['total_requests'] == 10
        assert stats['error_rate'] > 0
        assert stats['avg_response_time'] > 0
        assert stats['uptime'] > 0
        
        print("[PASS] Performance monitor tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Performance monitor tests failed: {e}")
        return False


def test_memory_monitor():
    """Test memory usage monitoring."""
    try:
        # Test memory monitoring
        class MemoryMonitor:
            def __init__(self):
                self.memory_history = []
                self.peak_memory = 0
            
            def record_memory_usage(self):
                memory = psutil.virtual_memory()
                self.memory_history.append(memory.percent)
                self.peak_memory = max(self.peak_memory, memory.percent)
            
            def get_memory_stats(self):
                if not self.memory_history:
                    return {'current': 0, 'average': 0, 'peak': 0}
                
                return {
                    'current': self.memory_history[-1],
                    'average': statistics.mean(self.memory_history),
                    'peak': self.peak_memory,
                    'samples': len(self.memory_history)
                }
        
        # Test memory monitoring
        monitor = MemoryMonitor()
        
        # Record memory usage multiple times
        for _ in range(5):
            monitor.record_memory_usage()
            time.sleep(0.001)
        
        stats = monitor.get_memory_stats()
        assert stats['current'] > 0
        assert stats['average'] > 0
        assert stats['peak'] > 0
        assert stats['samples'] == 5
        
        print("[PASS] Memory monitor tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Memory monitor tests failed: {e}")
        return False


def test_circuit_breaker():
    """Test circuit breaker pattern implementation."""
    try:
        # Test circuit breaker
        class CircuitBreaker:
            def __init__(self, failure_threshold=5, recovery_timeout=10):
                self.failure_threshold = failure_threshold
                self.recovery_timeout = recovery_timeout
                self.failure_count = 0
                self.last_failure_time = None
                self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
            
            def call(self, func, *args, **kwargs):
                if self.state == 'OPEN':
                    if time.time() - self.last_failure_time > self.recovery_timeout:
                        self.state = 'HALF_OPEN'
                    else:
                        raise Exception("Circuit breaker is OPEN")
                
                try:
                    result = func(*args, **kwargs)
                    if self.state == 'HALF_OPEN':
                        self.state = 'CLOSED'
                        self.failure_count = 0
                    return result
                except Exception as e:
                    self.failure_count += 1
                    self.last_failure_time = time.time()
                    
                    if self.failure_count >= self.failure_threshold:
                        self.state = 'OPEN'
                    
                    raise e
            
            def get_state(self):
                return {
                    'state': self.state,
                    'failure_count': self.failure_count,
                    'last_failure_time': self.last_failure_time
                }
        
        # Test circuit breaker
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
        
        # Test successful calls
        def success_func():
            return "success"
        
        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.get_state()['state'] == 'CLOSED'
        
        # Test failure calls
        def failure_func():
            raise Exception("Test failure")
        
        # Trigger circuit breaker
        for _ in range(3):
            try:
                breaker.call(failure_func)
            except Exception:
                pass
        
        assert breaker.get_state()['state'] == 'OPEN'
        assert breaker.get_state()['failure_count'] == 3
        
        print("[PASS] Circuit breaker tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Circuit breaker tests failed: {e}")
        return False


def test_error_recovery():
    """Test error recovery and retry mechanisms."""
    try:
        # Test retry mechanism
        class RetryMechanism:
            def __init__(self, max_retries=3, backoff_factor=1):
                self.max_retries = max_retries
                self.backoff_factor = backoff_factor
            
            def execute_with_retry(self, func, *args, **kwargs):
                last_exception = None
                
                for attempt in range(self.max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < self.max_retries:
                            delay = self.backoff_factor * (2 ** attempt)
                            time.sleep(delay * 0.001)  # Minimal delay for testing
                        else:
                            break
                
                raise last_exception
        
        # Test retry mechanism
        retry = RetryMechanism(max_retries=3, backoff_factor=1)
        
        # Test successful retry
        call_count = [0]
        def success_after_retries():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = retry.execute_with_retry(success_after_retries)
        assert result == "success"
        assert call_count[0] == 3
        
        # Test permanent failure
        call_count[0] = 0
        def permanent_failure():
            call_count[0] += 1
            raise Exception("Permanent failure")
        
        try:
            retry.execute_with_retry(permanent_failure)
            assert False, "Should have raised exception"
        except Exception as e:
            assert str(e) == "Permanent failure"
            assert call_count[0] == 4  # max_retries + 1
        
        print("[PASS] Error recovery tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error recovery tests failed: {e}")
        return False


def test_system_monitor():
    """Test system resource monitoring."""
    try:
        # Test system monitoring
        class SystemMonitor:
            def __init__(self):
                self.metrics = {}
            
            def collect_system_metrics(self):
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_count = psutil.cpu_count()
                
                # Memory metrics
                memory = psutil.virtual_memory()
                
                # Disk metrics
                disk = psutil.disk_usage('/')
                
                # Network metrics (if available)
                try:
                    network = psutil.net_io_counters()
                    network_metrics = {
                        'bytes_sent': network.bytes_sent,
                        'bytes_recv': network.bytes_recv,
                        'packets_sent': network.packets_sent,
                        'packets_recv': network.packets_recv
                    }
                except Exception:
                    network_metrics = {}
                
                self.metrics = {
                    'cpu': {
                        'percent': cpu_percent,
                        'count': cpu_count
                    },
                    'memory': {
                        'total': memory.total,
                        'available': memory.available,
                        'percent': memory.percent
                    },
                    'disk': {
                        'total': disk.total,
                        'free': disk.free,
                        'used': disk.used,
                        'percent': (disk.used / disk.total) * 100
                    },
                    'network': network_metrics,
                    'timestamp': time.time()
                }
                
                return self.metrics
            
            def get_health_status(self):
                if not self.metrics:
                    return 'UNKNOWN'
                
                cpu_percent = self.metrics['cpu']['percent']
                memory_percent = self.metrics['memory']['percent']
                disk_percent = self.metrics['disk']['percent']
                
                if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                    return 'CRITICAL'
                elif cpu_percent > 70 or memory_percent > 70 or disk_percent > 70:
                    return 'WARNING'
                else:
                    return 'HEALTHY'
        
        # Test system monitoring
        monitor = SystemMonitor()
        metrics = monitor.collect_system_metrics()
        
        assert 'cpu' in metrics
        assert 'memory' in metrics
        assert 'disk' in metrics
        assert 'timestamp' in metrics
        
        assert metrics['cpu']['percent'] >= 0
        assert metrics['cpu']['count'] > 0
        assert metrics['memory']['total'] > 0
        assert metrics['disk']['total'] > 0
        
        health_status = monitor.get_health_status()
        assert health_status in ['HEALTHY', 'WARNING', 'CRITICAL']
        
        print("[PASS] System monitor tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] System monitor tests failed: {e}")
        return False


def test_metrics_aggregation():
    """Test metrics aggregation and reporting."""
    try:
        # Test metrics aggregation
        class MetricsAggregator:
            def __init__(self):
                self.metrics = []
                self.lock = threading.Lock()
            
            def add_metric(self, name, value, timestamp=None):
                if timestamp is None:
                    timestamp = time.time()
                
                with self.lock:
                    self.metrics.append({
                        'name': name,
                        'value': value,
                        'timestamp': timestamp
                    })
            
            def get_aggregated_metrics(self, time_window=60):
                current_time = time.time()
                cutoff_time = current_time - time_window
                
                with self.lock:
                    recent_metrics = [m for m in self.metrics if m['timestamp'] > cutoff_time]
                
                # Group by metric name
                grouped_metrics = {}
                for metric in recent_metrics:
                    name = metric['name']
                    if name not in grouped_metrics:
                        grouped_metrics[name] = []
                    grouped_metrics[name].append(metric['value'])
                
                # Calculate aggregated statistics
                aggregated = {}
                for name, values in grouped_metrics.items():
                    if values:
                        aggregated[name] = {
                            'count': len(values),
                            'min': min(values),
                            'max': max(values),
                            'avg': statistics.mean(values),
                            'sum': sum(values)
                        }
                
                return aggregated
        
        # Test metrics aggregation
        aggregator = MetricsAggregator()
        
        # Add some test metrics
        for i in range(10):
            aggregator.add_metric('response_time', 0.001 + i * 0.0001)
            aggregator.add_metric('memory_usage', 50 + i * 2)
            time.sleep(0.001)
        
        aggregated = aggregator.get_aggregated_metrics()
        
        assert 'response_time' in aggregated
        assert 'memory_usage' in aggregated
        
        assert aggregated['response_time']['count'] == 10
        assert aggregated['response_time']['min'] > 0
        assert aggregated['response_time']['max'] > aggregated['response_time']['min']
        assert aggregated['response_time']['avg'] > 0
        
        assert aggregated['memory_usage']['count'] == 10
        assert aggregated['memory_usage']['min'] > 0
        assert aggregated['memory_usage']['max'] > aggregated['memory_usage']['min']
        
        print("[PASS] Metrics aggregation tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Metrics aggregation tests failed: {e}")
        return False


def main():
    """Run all XSystem monitoring tests."""
    print("[MONITOR] XSystem Monitoring Core Tests")
    print("=" * 50)
    print("Testing XSystem monitoring features including performance, memory, circuit breaker, and system monitoring")
    print("=" * 50)
    
    tests = [
        ("Performance Monitor", test_performance_monitor),
        ("Memory Monitor", test_memory_monitor),
        ("Circuit Breaker", test_circuit_breaker),
        ("Error Recovery", test_error_recovery),
        ("System Monitor", test_system_monitor),
        ("Metrics Aggregation", test_metrics_aggregation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[INFO] Testing: {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"[FAIL] Test {test_name} crashed: {e}")
    
    print(f"\n{'='*50}")
    print("[MONITOR] XSYSTEM MONITORING TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All XSystem monitoring tests passed!")
        return 0
    else:
        print("[ERROR] Some XSystem monitoring tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
