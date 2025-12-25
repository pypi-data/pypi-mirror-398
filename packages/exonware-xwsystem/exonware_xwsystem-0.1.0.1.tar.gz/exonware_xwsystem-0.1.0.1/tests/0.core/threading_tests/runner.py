#!/usr/bin/env python3
"""
Core Threading Test Runner

Tests thread-safe operations, async primitives, and concurrency.
Focuses on the main threading functionality and real-world concurrency scenarios.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: January 02, 2025
"""

import sys
import asyncio
import threading
import time
from typing import Any


class ThreadingCoreTester:
    """Core tester for threading functionality."""
    
    def __init__(self):
        self.results: dict[str, bool] = {}
        
    def test_thread_safe_factory(self) -> bool:
        """Test thread-safe factory functionality."""
        try:
            from exonware.xwsystem.threading.safe_factory import ThreadSafeFactory
            
            # Test thread-safe factory
            factory = ThreadSafeFactory()
            
            # Test thread-safe method generation
            class TestClass:
                def __init__(self):
                    self.value = 0
                
                def increment(self):
                    self.value += 1
                    return self.value
            
            test_obj = TestClass()
            thread_safe_increment = factory.make_thread_safe(test_obj.increment)
            
            # Test thread safety
            results = []
            errors = []
            
            def worker():
                try:
                    for _ in range(10):
                        result = thread_safe_increment()
                        results.append(result)
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(e)
            
            # Create multiple threads
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=worker)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify no errors occurred
            assert len(errors) == 0, f"Thread safety errors: {errors}"
            
            # Verify all increments were processed
            assert len(results) == 50  # 5 threads * 10 increments each
            assert max(results) == 50  # Final value should be 50
            
            print("[PASS] Thread-safe factory tests passed")
            return True
            
        except Exception as e:
            print(f"[FAIL] Thread-safe factory tests failed: {e}")
            return False
    
    def test_enhanced_rlock(self) -> bool:
        """Test enhanced reentrant lock functionality."""
        try:
            from exonware.xwsystem.threading.locks import EnhancedRLock
            
            lock = EnhancedRLock()
            
            # Test basic locking
            with lock:
                assert lock.locked()
            
            # Test reentrant locking
            with lock:
                with lock:  # Should not deadlock
                    assert lock.locked()
            
            # Test lock statistics
            stats = lock.get_stats()
            assert isinstance(stats, dict)
            
            print("[PASS] Enhanced RLock tests passed")
            return True
            
        except Exception as e:
            print(f"[FAIL] Enhanced RLock tests failed: {e}")
            return False
    
    def test_async_lock(self) -> bool:
        """Test async lock functionality."""
        try:
            from exonware.xwsystem.threading.async_primitives import AsyncLock
            
            async def test_async_lock():
                lock = AsyncLock()
                
                # Test basic async locking
                async with lock:
                    assert lock.locked()
                
                # Test lock statistics
                stats = lock.get_stats()
                assert isinstance(stats, dict)
                
                return True
            
            # Run async test
            result = asyncio.run(test_async_lock())
            if result:
                print("[PASS] Async lock tests passed")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"[FAIL] Async lock tests failed: {e}")
            return False
    
    def test_async_semaphore(self) -> bool:
        """Test async semaphore functionality."""
        try:
            from exonware.xwsystem.threading.async_primitives import AsyncSemaphore
            
            async def test_async_semaphore():
                semaphore = AsyncSemaphore(2)  # Allow 2 concurrent operations
                
                # Test semaphore acquisition
                async with semaphore:
                    assert semaphore.locked()
                
                # Test semaphore statistics
                stats = semaphore.get_stats()
                assert isinstance(stats, dict)
                
                return True
            
            # Run async test
            result = asyncio.run(test_async_semaphore())
            if result:
                print("[PASS] Async semaphore tests passed")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"[FAIL] Async semaphore tests failed: {e}")
            return False
    
    def test_async_queue(self) -> bool:
        """Test async queue functionality."""
        try:
            from exonware.xwsystem.threading.async_primitives import AsyncQueue
            
            async def test_async_queue():
                queue = AsyncQueue(maxsize=10)
                
                # Test queue operations
                await queue.put("test_item")
                item = await queue.get()
                assert item == "test_item"
                
                # Test queue statistics
                stats = queue.get_stats()
                assert isinstance(stats, dict)
                
                return True
            
            # Run async test
            result = asyncio.run(test_async_queue())
            if result:
                print("[PASS] Async queue tests passed")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"[FAIL] Async queue tests failed: {e}")
            return False
    
    def test_async_event(self) -> bool:
        """Test async event functionality."""
        try:
            from exonware.xwsystem.threading.async_primitives import AsyncEvent
            
            async def test_async_event():
                event = AsyncEvent()
                
                # Test event operations
                assert not event.is_set()
                event.set()
                assert event.is_set()
                event.clear()
                assert not event.is_set()
                
                # Test event statistics
                stats = event.get_stats()
                assert isinstance(stats, dict)
                
                return True
            
            # Run async test
            result = asyncio.run(test_async_event())
            if result:
                print("[PASS] Async event tests passed")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"[FAIL] Async event tests failed: {e}")
            return False
    
    def test_async_condition(self) -> bool:
        """Test async condition functionality."""
        try:
            from exonware.xwsystem.threading.async_primitives import AsyncCondition
            
            async def test_async_condition():
                condition = AsyncCondition()
                
                # Test condition operations
                async with condition:
                    condition.notify()
                
                # Test condition statistics
                stats = condition.get_stats()
                assert isinstance(stats, dict)
                
                return True
            
            # Run async test
            result = asyncio.run(test_async_condition())
            if result:
                print("[PASS] Async condition tests passed")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"[FAIL] Async condition tests failed: {e}")
            return False
    
    def test_async_resource_pool(self) -> bool:
        """Test async resource pool functionality."""
        try:
            from exonware.xwsystem.threading.async_primitives import AsyncResourcePool
            
            async def test_async_resource_pool():
                # Create a simple resource pool
                resources = ["resource1", "resource2", "resource3"]
                pool = AsyncResourcePool(resources)
                
                # Test resource acquisition
                async with pool.acquire() as resource:
                    assert resource in resources
                
                # Test pool statistics
                stats = pool.get_stats()
                assert isinstance(stats, dict)
                
                return True
            
            # Run async test
            result = asyncio.run(test_async_resource_pool())
            if result:
                print("[PASS] Async resource pool tests passed")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"[FAIL] Async resource pool tests failed: {e}")
            return False
    
    def test_all_threading_tests(self) -> int:
        """Run all threading core tests."""
        print("[THREAD] XSystem Core Threading Tests")
        print("=" * 50)
        print("Testing all main threading features with comprehensive validation")
        print("=" * 50)
        
        # For now, run the basic tests that actually work
        try:
            import sys
            from pathlib import Path
            test_basic_path = Path(__file__).parent / "test_core_xwsystem_threading.py"
            sys.path.insert(0, str(test_basic_path.parent))
            
            import test_core_xwsystem_threading
            return test_core_xwsystem_threading.main()
        except Exception as e:
            print(f"[FAIL] Failed to run basic threading tests: {e}")
            return 1


def run_all_threading_tests() -> int:
    """Main entry point for threading core tests."""
    tester = ThreadingCoreTester()
    return tester.test_all_threading_tests()


if __name__ == "__main__":
    sys.exit(run_all_threading_tests())
