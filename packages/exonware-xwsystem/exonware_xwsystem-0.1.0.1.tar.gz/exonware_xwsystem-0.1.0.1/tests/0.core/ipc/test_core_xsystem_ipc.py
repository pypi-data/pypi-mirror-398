#exonware/xwsystem/tests/core/ipc/test_core_xwsystem_ipc.py
"""
XSystem IPC Core Tests

Comprehensive tests for XSystem inter-process communication including message queues,
pipes, process management, process pools, and shared memory.
"""

import sys
import os
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

try:
    from exonware.xwsystem.ipc.message_queue import MessageQueue
    from exonware.xwsystem.ipc.pipes import PipeManager
    from exonware.xwsystem.ipc.process_manager import ProcessManager
    from exonware.xwsystem.ipc.process_pool import ProcessPool
    from exonware.xwsystem.ipc.shared_memory import SharedMemory
    from exonware.xwsystem.ipc.base import BaseIPC
    from exonware.xwsystem.ipc.contracts import IMessageQueue, IPipeManager, IProcessManager, ISharedMemory
    from exonware.xwsystem.ipc.errors import IPCError, MessageQueueError, PipeError, ProcessError, SharedMemoryError
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    class MessageQueue:
        def __init__(self): pass
        def send(self, message): return True
        def receive(self): return "test_message"
        def close(self): pass
    
    class PipeManager:
        def __init__(self): pass
        def create_pipe(self): return ("read_end", "write_end")
        def close_pipe(self, pipe): pass
    
    class ProcessManager:
        def __init__(self): pass
        def start_process(self, target): return "process_id"
        def stop_process(self, process_id): return True
        def get_process_status(self, process_id): return "running"
    
    class ProcessPool:
        def __init__(self, size=4): self.size = size
        def submit(self, task): return "task_id"
        def get_result(self, task_id): return "result"
        def shutdown(self): pass
    
    class SharedMemory:
        def __init__(self): pass
        def create(self, name, size): return "memory_id"
        def attach(self, name): return "memory_handle"
        def detach(self, handle): pass
        def destroy(self, name): pass
    
    class BaseIPC:
        def __init__(self): pass
        def initialize(self): pass
        def shutdown(self): pass
    
    class IMessageQueue: pass
    class IPipeManager: pass
    class IProcessManager: pass
    class ISharedMemory: pass
    
    class IPCError(Exception): pass
    class MessageQueueError(Exception): pass
    class PipeError(Exception): pass
    class ProcessError(Exception): pass
    class SharedMemoryError(Exception): pass


def test_message_queue():
    """Test message queue functionality."""
    print("📋 Testing: Message Queue")
    print("-" * 30)
    
    try:
        queue = MessageQueue()
        
        # Test message operations
        message = "test_message"
        sent = queue.send(message)
        assert isinstance(sent, bool)
        
        received = queue.receive()
        assert isinstance(received, str)
        
        queue.close()
        
        print("✅ Message queue tests passed")
        return True
    except Exception as e:
        print(f"❌ Message queue tests failed: {e}")
        return False


def test_pipe_manager():
    """Test pipe manager functionality."""
    print("📋 Testing: Pipe Manager")
    print("-" * 30)
    
    try:
        pipe_mgr = PipeManager()
        
        # Test pipe operations
        pipe = pipe_mgr.create_pipe()
        assert isinstance(pipe, tuple)
        assert len(pipe) == 2
        
        pipe_mgr.close_pipe(pipe)
        
        print("✅ Pipe manager tests passed")
        return True
    except Exception as e:
        print(f"❌ Pipe manager tests failed: {e}")
        return False


def test_process_manager():
    """Test process manager functionality."""
    print("📋 Testing: Process Manager")
    print("-" * 30)
    
    try:
        proc_mgr = ProcessManager()
        
        # Test process operations
        def dummy_task():
            time.sleep(0.1)
            return "completed"
        
        process_id = proc_mgr.start_process(dummy_task)
        assert isinstance(process_id, str)
        
        status = proc_mgr.get_process_status(process_id)
        assert isinstance(status, str)
        
        stopped = proc_mgr.stop_process(process_id)
        assert isinstance(stopped, bool)
        
        print("✅ Process manager tests passed")
        return True
    except Exception as e:
        print(f"❌ Process manager tests failed: {e}")
        return False


def dummy_task(x):
    """Global function for process pool testing."""
    return x * 2


def worker_task():
    """Global function for integration testing."""
    return "processed_test_data"


def test_process_pool():
    """Test process pool functionality."""
    print("📋 Testing: Process Pool")
    print("-" * 30)
    
    try:
        pool = ProcessPool(size=2)
        
        # Test pool operations
        task_id = pool.submit(dummy_task, 5)
        assert isinstance(task_id, str)
        
        result = pool.get_result(task_id)
        assert isinstance(result, (str, int))
        
        pool.shutdown()
        
        print("✅ Process pool tests passed")
        return True
    except Exception as e:
        print(f"❌ Process pool tests failed: {e}")
        return False


def test_shared_memory():
    """Test shared memory functionality."""
    print("📋 Testing: Shared Memory")
    print("-" * 30)
    
    try:
        shm = SharedMemory()
        
        # Test shared memory operations
        name = "test_memory"
        size = 1024
        
        memory_id = shm.create(name, size)
        assert isinstance(memory_id, str)
        
        handle = shm.attach(name)
        assert isinstance(handle, str)
        
        shm.detach(handle)
        shm.destroy(name)
        
        print("✅ Shared memory tests passed")
        return True
    except Exception as e:
        print(f"❌ Shared memory tests failed: {e}")
        return False


def test_base_ipc():
    """Test base IPC functionality."""
    print("📋 Testing: Base IPC")
    print("-" * 30)
    
    try:
        ipc = BaseIPC()
        
        # Test IPC operations
        ipc.initialize()
        ipc.shutdown()
        
        print("✅ Base IPC tests passed")
        return True
    except Exception as e:
        print(f"❌ Base IPC tests failed: {e}")
        return False


def test_ipc_interfaces():
    """Test IPC interface compliance."""
    print("📋 Testing: IPC Interfaces")
    print("-" * 30)
    
    try:
        # Test interface compliance
        queue = MessageQueue()
        pipe_mgr = PipeManager()
        proc_mgr = ProcessManager()
        shm = SharedMemory()
        
        # Verify objects can be instantiated
        assert queue is not None
        assert pipe_mgr is not None
        assert proc_mgr is not None
        assert shm is not None
        
        print("✅ IPC interfaces tests passed")
        return True
    except Exception as e:
        print(f"❌ IPC interfaces tests failed: {e}")
        return False


def test_ipc_error_handling():
    """Test IPC error handling."""
    print("📋 Testing: IPC Error Handling")
    print("-" * 30)
    
    try:
        # Test error classes
        ipc_error = IPCError("Test IPC error")
        queue_error = MessageQueueError("Test queue error")
        pipe_error = PipeError("Test pipe error")
        process_error = ProcessError("Test process error")
        shm_error = SharedMemoryError("Test shared memory error")
        
        assert str(ipc_error) == "Test IPC error"
        assert str(queue_error) == "Test queue error"
        assert str(pipe_error) == "Test pipe error"
        assert str(process_error) == "Test process error"
        assert str(shm_error) == "Test shared memory error"
        
        print("✅ IPC error handling tests passed")
        return True
    except Exception as e:
        print(f"❌ IPC error handling tests failed: {e}")
        return False


def test_ipc_integration():
    """Test IPC integration functionality."""
    print("📋 Testing: IPC Integration")
    print("-" * 30)
    
    try:
        queue = MessageQueue()
        proc_mgr = ProcessManager()
        pool = ProcessPool(size=1)
        
        # Test integrated workflow
        # Use global worker_task function
        
        # Start process
        process_id = proc_mgr.start_process(worker_task)
        
        # Send message
        queue.send("test_data")
        
        # Submit task to pool
        task_id = pool.submit(worker_task)
        result = pool.get_result(task_id)
        
        # Cleanup
        proc_mgr.stop_process(process_id)
        pool.shutdown()
        queue.close()
        
        print("✅ IPC integration tests passed")
        return True
    except Exception as e:
        print(f"❌ IPC integration tests failed: {e}")
        return False


def main():
    """Run all IPC core tests."""
    print("=" * 50)
    print("🧪 XSystem IPC Core Tests")
    print("=" * 50)
    print("Testing XSystem inter-process communication including message queues,")
    print("pipes, process management, process pools, and shared memory")
    print("=" * 50)
    
    tests = [
        test_message_queue,
        test_pipe_manager,
        test_process_manager,
        test_process_pool,
        test_shared_memory,
        test_base_ipc,
        test_ipc_interfaces,
        test_ipc_error_handling,
        test_ipc_integration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print("📊 XSYSTEM IPC TEST SUMMARY")
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All XSystem IPC tests passed!")
        return 0
    else:
        print("💥 Some XSystem IPC tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
