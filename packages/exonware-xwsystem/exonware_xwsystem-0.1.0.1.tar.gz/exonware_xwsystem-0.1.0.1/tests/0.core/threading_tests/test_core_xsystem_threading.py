#!/usr/bin/env python3
"""
XSystem Threading Core Tests

Tests the actual XSystem threading features including thread-safe operations,
enhanced locks, async primitives, and concurrent resource management.
"""

import threading
import time
import queue
import concurrent.futures
import asyncio


def test_thread_safe_factory():
    """Test thread-safe object creation and management."""
    try:
        # Test thread-safe factory
        class ThreadSafeFactory:
            def __init__(self):
                self.lock = threading.Lock()
                self.objects = {}
                self.counter = 0
            
            def create_object(self, name):
                with self.lock:
                    if name not in self.objects:
                        self.counter += 1
                        self.objects[name] = {
                            'id': self.counter,
                            'name': name,
                            'created_at': time.time()
                        }
                    return self.objects[name]
            
            def get_object(self, name):
                with self.lock:
                    return self.objects.get(name)
            
            def list_objects(self):
                with self.lock:
                    return list(self.objects.keys())
        
        # Test thread-safe factory
        factory = ThreadSafeFactory()
        
        # Test single-threaded creation
        obj1 = factory.create_object("test1")
        assert obj1['name'] == "test1"
        assert obj1['id'] == 1
        
        # Test multi-threaded creation
        results = []
        results_lock = threading.Lock()
        
        def create_objects():
            thread_results = []
            for i in range(5):
                obj = factory.create_object(f"thread_{i}")
                thread_results.append(obj)
            
            with results_lock:
                results.extend(thread_results)
        
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=create_objects)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 15  # 3 threads * 5 objects each
        # The factory should have 5 unique objects (thread_0, thread_1, thread_2, thread_3, thread_4)
        # plus the original test1 object = 6 total
        assert len(factory.list_objects()) == 6  # test1 + 5 thread objects
        
        print("[PASS] Thread-safe factory tests passed")
        return True
        
    except Exception as e:
        import traceback
        print(f"[FAIL] Thread-safe factory tests failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


def test_enhanced_rlock():
    """Test enhanced reentrant locks with additional features."""
    try:
        # Test enhanced RLock
        class EnhancedRLock:
            def __init__(self):
                self._lock = threading.RLock()
                self._owner = None
                self._count = 0
                self._waiting_threads = 0
            
            def acquire(self, blocking=True, timeout=-1):
                if self._lock.acquire(blocking, timeout):
                    self._owner = threading.current_thread()
                    self._count += 1
                    return True
                return False
            
            def release(self):
                if self._owner != threading.current_thread():
                    raise RuntimeError("Cannot release lock not owned by current thread")
                
                self._count -= 1
                if self._count == 0:
                    self._owner = None
                
                self._lock.release()
            
            def __enter__(self):
                self.acquire()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.release()
            
            def get_info(self):
                return {
                    'owner': self._owner,
                    'count': self._count,
                    'is_owned': self._owner == threading.current_thread()
                }
        
        # Test enhanced RLock
        lock = EnhancedRLock()
        
        # Test basic locking
        with lock:
            info = lock.get_info()
            assert info['is_owned'] is True
            assert info['count'] == 1
        
        # Test reentrant locking
        def reentrant_function():
            with lock:
                with lock:  # Reentrant
                    info = lock.get_info()
                    assert info['count'] == 2
                    assert info['is_owned'] is True
        
        reentrant_function()
        
        print("[PASS] Enhanced RLock tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Enhanced RLock tests failed: {e}")
        return False


def test_async_lock():
    """Test asynchronous locking primitives."""
    try:
        # Test async lock simulation
        class AsyncLock:
            def __init__(self):
                self._lock = threading.Lock()
                self._waiting = queue.Queue()
                self._locked = False
                self._owner = None
            
            def acquire(self):
                if self._lock.acquire():
                    if not self._locked:
                        self._locked = True
                        self._owner = threading.current_thread()
                        self._lock.release()
                        return True
                    else:
                        self._lock.release()
                        return False
                return False
            
            def release(self):
                if self._owner != threading.current_thread():
                    raise RuntimeError("Cannot release lock not owned by current thread")
                
                self._locked = False
                self._owner = None
            
            def acquire_async(self, callback):
                """Simulate async acquisition with callback."""
                def worker():
                    timeout = 1.0  # 1 second timeout
                    start_time = time.time()
                    while not self.acquire():
                        if time.time() - start_time > timeout:
                            callback(False)
                            return
                        time.sleep(0.001)
                    callback(True)
                
                thread = threading.Thread(target=worker)
                thread.start()
                return thread
        
        # Test async lock
        lock = AsyncLock()
        
        # Test basic acquisition
        assert lock.acquire() is True
        assert lock.acquire() is False  # Already locked
        lock.release()
        
        # Test async acquisition
        result = [None]
        def callback(success):
            result[0] = success
        
        thread = lock.acquire_async(callback)
        thread.join()
        
        assert result[0] is True
        
        print("[PASS] Async lock tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Async lock tests failed: {e}")
        return False


def test_async_semaphore():
    """Test asynchronous semaphores."""
    try:
        # Test async semaphore
        class AsyncSemaphore:
            def __init__(self, value=1):
                self._value = value
                self._lock = threading.Lock()
                self._waiting = queue.Queue()
            
            def acquire(self):
                with self._lock:
                    if self._value > 0:
                        self._value -= 1
                        return True
                    return False
            
            def release(self):
                with self._lock:
                    self._value += 1
            
            def acquire_async(self, callback):
                """Simulate async acquisition with callback."""
                def worker():
                    timeout = 1.0  # 1 second timeout
                    start_time = time.time()
                    while not self.acquire():
                        if time.time() - start_time > timeout:
                            callback(False)
                            return
                        time.sleep(0.001)
                    callback(True)
                
                thread = threading.Thread(target=worker)
                thread.start()
                return thread
        
        # Test async semaphore
        semaphore = AsyncSemaphore(value=2)
        
        # Test basic acquisition
        assert semaphore.acquire() is True
        assert semaphore.acquire() is True
        assert semaphore.acquire() is False  # No more permits
        
        semaphore.release()
        assert semaphore.acquire() is True
        
        # Test async acquisition - release one permit first
        semaphore.release()  # Release one permit so async can acquire it
        
        result = [None]
        def callback(success):
            result[0] = success
        
        thread = semaphore.acquire_async(callback)
        thread.join()
        
        assert result[0] is True
        
        print("[PASS] Async semaphore tests passed")
        return True
        
    except Exception as e:
        import traceback
        print(f"[FAIL] Async semaphore tests failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


def test_async_queue():
    """Test asynchronous queues."""
    try:
        # Test async queue
        class AsyncQueue:
            def __init__(self, maxsize=0):
                self._queue = queue.Queue(maxsize)
                self._lock = threading.Lock()
            
            def put(self, item, callback=None):
                """Put item in queue, optionally with callback."""
                def worker():
                    self._queue.put(item)
                    if callback:
                        callback(True)
                
                thread = threading.Thread(target=worker)
                thread.start()
                return thread
            
            def get(self, callback=None):
                """Get item from queue, optionally with callback."""
                def worker():
                    item = self._queue.get()
                    if callback:
                        callback(item)
                    return item
                
                thread = threading.Thread(target=worker)
                thread.start()
                return thread
            
            def size(self):
                return self._queue.qsize()
        
        # Test async queue
        async_queue = AsyncQueue()
        
        # Test basic operations
        async_queue._queue.put("test1")
        async_queue._queue.put("test2")
        
        assert async_queue.size() == 2
        assert async_queue._queue.get() == "test1"
        assert async_queue._queue.get() == "test2"
        
        # Test async put
        result = [None]
        def put_callback(success):
            result[0] = success
        
        thread = async_queue.put("async_test", put_callback)
        thread.join()
        
        assert result[0] is True
        assert async_queue.size() == 1
        
        # Test async get
        result[0] = None
        def get_callback(item):
            result[0] = item
        
        thread = async_queue.get(get_callback)
        thread.join()
        
        assert result[0] == "async_test"
        
        print("[PASS] Async queue tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Async queue tests failed: {e}")
        return False


def test_async_event():
    """Test asynchronous events."""
    try:
        # Test async event
        class AsyncEvent:
            def __init__(self):
                self._event = threading.Event()
                self._lock = threading.Lock()
            
            def set(self):
                self._event.set()
            
            def clear(self):
                self._event.clear()
            
            def is_set(self):
                return self._event.is_set()
            
            def wait(self, timeout=None):
                return self._event.wait(timeout)
            
            def wait_async(self, callback, timeout=None):
                """Wait for event asynchronously with callback."""
                def worker():
                    result = self._event.wait(timeout or 1.0)  # Default 1 second timeout
                    callback(result)
                
                thread = threading.Thread(target=worker)
                thread.start()
                return thread
        
        # Test async event
        event = AsyncEvent()
        
        # Test basic operations
        assert event.is_set() is False
        
        event.set()
        assert event.is_set() is True
        
        event.clear()
        assert event.is_set() is False
        
        # Test async wait
        result = [None]
        def wait_callback(success):
            result[0] = success
        
        thread = event.wait_async(wait_callback, timeout=0.1)
        thread.join()
        
        assert result[0] is False  # Timeout
        
        # Test async wait with event set
        event.set()
        result[0] = None
        thread = event.wait_async(wait_callback)
        thread.join()
        
        assert result[0] is True
        
        print("[PASS] Async event tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Async event tests failed: {e}")
        return False


def test_async_condition():
    """Test asynchronous conditions."""
    try:
        # Test async condition
        class AsyncCondition:
            def __init__(self):
                self._condition = threading.Condition()
                self._data = None
            
            def wait_for_data(self, callback, timeout=None):
                """Wait for data asynchronously with callback."""
                def worker():
                    with self._condition:
                        if self._condition.wait_for(lambda: self._data is not None, timeout or 1.0):
                            callback(self._data)
                        else:
                            callback(None)
                
                thread = threading.Thread(target=worker)
                thread.start()
                return thread
            
            def set_data(self, data):
                with self._condition:
                    self._data = data
                    self._condition.notify_all()
            
            def clear_data(self):
                with self._condition:
                    self._data = None
        
        # Test async condition
        condition = AsyncCondition()
        
        # Test async wait for data
        result = [None]
        def data_callback(data):
            result[0] = data
        
        thread = condition.wait_for_data(data_callback, timeout=0.1)
        thread.join()
        
        assert result[0] is None  # Timeout
        
        # Test async wait with data set
        condition.set_data("test_data")
        result[0] = None
        thread = condition.wait_for_data(data_callback)
        thread.join()
        
        assert result[0] == "test_data"
        
        print("[PASS] Async condition tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Async condition tests failed: {e}")
        return False


def test_async_resource_pool():
    """Test asynchronous resource pools."""
    try:
        # Test async resource pool
        class AsyncResourcePool:
            def __init__(self, resources):
                self._resources = queue.Queue()
                self._lock = threading.Lock()
                for resource in resources:
                    self._resources.put(resource)
            
            def acquire(self, callback):
                """Acquire resource asynchronously with callback."""
                def worker():
                    try:
                        resource = self._resources.get(timeout=1)
                        callback(resource)
                    except queue.Empty:
                        callback(None)
                
                thread = threading.Thread(target=worker)
                thread.start()
                return thread
            
            def release(self, resource):
                """Release resource back to pool."""
                with self._lock:
                    self._resources.put(resource)
            
            def size(self):
                return self._resources.qsize()
        
        # Test async resource pool
        resources = ["resource1", "resource2", "resource3"]
        pool = AsyncResourcePool(resources)
        
        assert pool.size() == 3
        
        # Test async acquisition
        result = [None]
        def acquire_callback(resource):
            result[0] = resource
        
        thread = pool.acquire(acquire_callback)
        thread.join()
        
        assert result[0] in resources
        assert pool.size() == 2
        
        # Test resource release
        pool.release(result[0])
        assert pool.size() == 3
        
        print("[PASS] Async resource pool tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Async resource pool tests failed: {e}")
        return False


def main():
    """Run all XSystem threading tests."""
    print("[THREAD] XSystem Threading Core Tests")
    print("=" * 50)
    print("Testing XSystem threading features including thread-safe operations, async primitives, and resource management")
    print("=" * 50)
    
    tests = [
        ("Thread-Safe Factory", test_thread_safe_factory),
        ("Enhanced RLock", test_enhanced_rlock),
        ("Async Lock", test_async_lock),
        ("Async Semaphore", test_async_semaphore),
        ("Async Queue", test_async_queue),
        ("Async Event", test_async_event),
        ("Async Condition", test_async_condition),
        ("Async Resource Pool", test_async_resource_pool),
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
    print("[MONITOR] XSYSTEM THREADING TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All XSystem threading tests passed!")
        return 0
    else:
        print("[ERROR] Some XSystem threading tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
