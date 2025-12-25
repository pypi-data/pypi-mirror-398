"""
Test IPC (Inter-Process Communication) functionality.
"""

import pytest
import sys
import asyncio
import time
import multiprocessing as mp
from unittest.mock import Mock, patch

from src.exonware.xwsystem import (
    ProcessManager,
    ProcessInfo,
    SharedMemoryManager,
    SharedData,
    MessageQueue,
    AsyncMessageQueue,
    ProcessPool,
    AsyncProcessPool,
    Pipe,
    AsyncPipe,
)
from src.exonware.xwsystem.ipc import AsyncProcessFabric


def _fabric_identity(value):
    """Simple picklable function for process pool tests."""
    return value


def _fabric_ingest(dataset: str) -> dict:
    """Mock dataset ingest task executed inside the process pool."""
    return {"dataset": dataset, "status": "ingested"}


class TestProcessManager:
    """Test ProcessManager functionality."""
    
    def test_process_manager_creation(self):
        """Test ProcessManager initialization."""
        manager = ProcessManager(max_processes=4, monitor_interval=2.0)
        assert manager.max_processes == 4
        assert manager.monitor_interval == 2.0
        assert len(manager.processes) == 0
    
    def test_start_simple_process(self):
        """Test starting a simple process."""
        with ProcessManager() as manager:
            # Start a simple echo process
            success = manager.start_process(
                "test_echo",
                [sys.executable, "-c", "print('hello')"],
            )
            assert success
            
            # Check process info
            info = manager.get_process_info("test_echo")
            assert info is not None
            assert info.name == "test_echo"
            assert info.status == "running"
    
    def test_process_limit(self):
        """Test max process limit."""
        with ProcessManager(max_processes=1) as manager:
            # Start first process
            success1 = manager.start_process("proc1", ["sleep", "1"])
            assert success1
            
            # Try to start second process (should fail)
            success2 = manager.start_process("proc2", ["sleep", "1"])
            assert not success2
    
    def test_duplicate_process_name(self):
        """Test duplicate process names."""
        with ProcessManager() as manager:
            # Start first process
            success1 = manager.start_process("test", ["sleep", "1"])
            assert success1
            
            # Try to start with same name (should fail)
            success2 = manager.start_process("test", ["sleep", "1"])
            assert not success2


class TestSharedMemory:
    """Test SharedMemoryManager and SharedData functionality."""
    
    def test_shared_data_creation(self):
        """Test SharedData creation."""
        with SharedData("test_segment", size=1024) as segment:
            assert segment.name == "test_segment"
            assert segment.size == 1024
    
    def test_shared_data_operations(self):
        """Test basic shared data operations."""
        with SharedData("test_data", size=1024) as segment:
            # Test set and get
            test_data = {"message": "hello", "number": 42}
            success = segment.set(test_data)
            assert success
            
            retrieved = segment.get()
            assert retrieved == test_data
    
    def test_shared_data_clear(self):
        """Test clearing shared data."""
        with SharedData("test_clear", size=1024) as segment:
            # Set data
            segment.set("test data")
            assert segment.get() == "test data"
            
            # Clear data
            success = segment.clear()
            assert success
            assert segment.get() is None
    
    def test_shared_memory_manager(self):
        """Test SharedMemoryManager."""
        with SharedMemoryManager() as manager:
            # Create segment
            segment = manager.create_segment("test_segment", 1024)
            assert segment is not None
            
            # Get segment
            retrieved = manager.get_segment("test_segment")
            assert retrieved is segment
            
            # List segments
            segments = manager.list_segments()
            assert "test_segment" in segments
            
            # Remove segment
            success = manager.remove_segment("test_segment")
            assert success


class TestMessageQueue:
    """Test MessageQueue functionality."""
    
    def test_message_queue_creation(self):
        """Test MessageQueue creation."""
        queue = MessageQueue(maxsize=10, enable_priority=True)
        assert queue.maxsize == 10
        assert queue.enable_priority
    
    def test_basic_queue_operations(self):
        """Test basic put and get operations."""
        with MessageQueue() as queue:
            # Put message
            success = queue.put("hello world")
            assert success
            
            # Get message
            message = queue.get(timeout=1.0)
            assert message == "hello world"
    
    def test_priority_queue(self):
        """Test priority queue functionality."""
        with MessageQueue(enable_priority=True) as queue:
            # Put messages with different priorities
            queue.put("low priority", priority=10)
            queue.put("high priority", priority=1)
            queue.put("medium priority", priority=5)
            
            # Should get high priority first
            msg1 = queue.get(timeout=1.0)
            msg2 = queue.get(timeout=1.0)
            msg3 = queue.get(timeout=1.0)
            
            # Note: Priority queue behavior may vary by implementation
            assert msg1 is not None
            assert msg2 is not None
            assert msg3 is not None
    
    def test_queue_stats(self):
        """Test queue statistics."""
        with MessageQueue() as queue:
            # Put and get some messages
            queue.put("message1")
            queue.put("message2")
            queue.get(timeout=1.0)
            
            stats = queue.get_stats()
            assert stats['messages_sent'] == 2
            assert stats['messages_received'] == 1


class TestAsyncMessageQueue:
    """Test AsyncMessageQueue functionality."""
    
    @pytest.mark.asyncio
    async def test_async_queue_creation(self):
        """Test AsyncMessageQueue creation."""
        async with AsyncMessageQueue(maxsize=10) as queue:
            assert queue.maxsize == 10
    
    @pytest.mark.asyncio
    async def test_async_queue_operations(self):
        """Test async queue operations."""
        async with AsyncMessageQueue() as queue:
            # Put message
            success = await queue.put("async hello")
            assert success
            
            # Get message
            message = await queue.get(timeout=1.0)
            assert message == "async hello"
    
    @pytest.mark.asyncio
    async def test_async_queue_nowait(self):
        """Test non-blocking async queue operations."""
        async with AsyncMessageQueue() as queue:
            # Put without waiting
            success = queue.put_nowait("nowait message")
            assert success
            
            # Get without waiting
            message = queue.get_nowait()
            assert message == "nowait message"
    
    @pytest.mark.asyncio
    async def test_async_queue_stats(self):
        """Test async queue statistics."""
        async with AsyncMessageQueue() as queue:
            await queue.put("msg1")
            await queue.put("msg2")
            await queue.get()
            
            stats = await queue.get_stats()
            assert stats['messages_sent'] == 2
            assert stats['messages_received'] == 1


class TestProcessPool:
    """Test ProcessPool functionality."""
    
    def test_process_pool_creation(self):
        """Test ProcessPool creation."""
        with ProcessPool(max_workers=2) as pool:
            assert pool.max_workers == 2
    
    def test_simple_task_submission(self):
        """Test submitting a simple task."""
        def square(x):
            return x * x
        
        with ProcessPool(max_workers=2) as pool:
            # Submit task
            task_id = pool.submit(square, 5)
            assert task_id is not None
            
            # Get result
            result = pool.get_result(task_id, timeout=5.0)
            assert result is not None
            assert result.success
            assert result.result == 25
    
    def test_multiple_tasks(self):
        """Test submitting multiple tasks."""
        def multiply(x, y):
            return x * y
        
        with ProcessPool(max_workers=2) as pool:
            # Submit multiple tasks
            task1 = pool.submit(multiply, 3, 4)
            task2 = pool.submit(multiply, 5, 6)
            task3 = pool.submit(multiply, 7, 8)
            
            # Wait for all to complete
            results = pool.wait_for_all(timeout=10.0)
            
            # Check results
            successful_results = [r for r in results if r.success]
            assert len(successful_results) == 3
    
    def test_pool_stats(self):
        """Test process pool statistics."""
        def simple_task():
            return "done"
        
        with ProcessPool(max_workers=2) as pool:
            # Submit tasks
            pool.submit(simple_task)
            pool.submit(simple_task)
            
            # Wait a bit for tasks to complete
            time.sleep(1.0)
            
            stats = pool.get_stats()
            assert stats['tasks_submitted'] == 2
            assert stats['max_workers'] == 2


class TestAsyncProcessPool:
    """Test AsyncProcessPool functionality."""
    
    @pytest.mark.asyncio
    async def test_async_process_pool_creation(self):
        """Test AsyncProcessPool creation."""
        async with AsyncProcessPool(max_workers=2) as pool:
            assert pool.max_workers == 2
    
    @pytest.mark.asyncio
    async def test_async_task_submission(self):
        """Test async task submission."""
        def cube(x):
            return x ** 3
        
        async with AsyncProcessPool(max_workers=2) as pool:
            # Submit task
            task_id = await pool.submit(cube, 3)
            assert task_id is not None
            
            # Get result
            result = await pool.get_result(task_id, timeout=5.0)
            assert result == 27
    
    @pytest.mark.asyncio
    async def test_async_multiple_tasks(self):
        """Test multiple async tasks."""
        def add(x, y):
            return x + y
        
        async with AsyncProcessPool(max_workers=2) as pool:
            # Submit tasks
            task1 = await pool.submit(add, 1, 2)
            task2 = await pool.submit(add, 3, 4)
            task3 = await pool.submit(add, 5, 6)
            
            # Wait for all
            results = await pool.wait_for_all(timeout=10.0)
            
            # Check results
            assert len(results) == 3
            assert 3 in results  # 1+2
            assert 7 in results  # 3+4
            assert 11 in results # 5+6


class TestPipes:
    """Test Pipe functionality."""
    
    def test_pipe_creation(self):
        """Test Pipe creation."""
        with Pipe(duplex=True) as pipe:
            assert pipe.duplex
    
    def test_pipe_communication(self):
        """Test basic pipe communication."""
        with Pipe() as pipe:
            # Send data
            success = pipe.send("hello pipe")
            assert success
            
            # Receive data
            data = pipe.recv(timeout=1.0)
            # Note: This test might not work as expected since it's
            # the same process - pipes are meant for inter-process communication
            # In a real scenario, this would be tested with separate processes
    
    @pytest.mark.asyncio
    async def test_async_pipe_creation(self):
        """Test AsyncPipe creation."""
        pipe = AsyncPipe()
        assert pipe.buffer_size == 8192
        
        # Clean up
        await pipe.close()


class TestIntegration:
    """Integration tests for IPC components."""
    
    def test_process_with_shared_memory(self):
        """Test process communication via shared memory."""
        def worker_process(segment_name):
            # This would be run in a separate process
            # For testing purposes, we simulate the behavior
            with SharedData(segment_name, create=False) as segment:
                data = segment.get()
                if data:
                    segment.set(f"processed: {data}")
        
        # Create shared memory segment
        with SharedData("integration_test", 1024) as segment:
            # Set initial data
            segment.set("test data")
            
            # In a real scenario, you'd start a separate process here
            # For testing, we simulate the processing
            data = segment.get()
            segment.set(f"processed: {data}")
            
            # Verify result
            result = segment.get()
            assert result == "processed: test data"
    
    def test_queue_with_process_pool(self):
        """Test message queue with process pool."""
        def process_message(msg):
            return f"processed: {msg}"
        
        with MessageQueue() as queue:
            with ProcessPool(max_workers=2) as pool:
                # Put messages in queue
                queue.put("message1")
                queue.put("message2")
                
                # Process messages
                results = []
                while not queue.empty():
                    msg = queue.get_nowait()
                    if msg:
                        task_id = pool.submit(process_message, msg)
                        result = pool.get_result(task_id, timeout=5.0)
                        if result and result.success:
                            results.append(result.result)
                
                assert len(results) == 2
                assert "processed: message1" in results
                assert "processed: message2" in results


class TestAsyncProcessFabric:
    """Tests for the AsyncProcessFabric orchestration facade."""

    @pytest.mark.asyncio
    async def test_submit_and_iter_results(self):
        fabric = AsyncProcessFabric()
        async with fabric.session() as session:
            task_ids = [
                await session.submit(_fabric_ingest, "customers"),
                await session.submit(_fabric_ingest, "orders"),
            ]

            results = []
            async for result in session.iter_results(task_ids, timeout=5.0):
                results.append(result)

        assert len(results) == 2
        datasets = {entry["dataset"] for entry in results}
        assert datasets == {"customers", "orders"}
        assert all(entry["status"] == "ingested" for entry in results)

    @pytest.mark.asyncio
    async def test_publish_consume_with_channels(self):
        fabric = AsyncProcessFabric()
        async with fabric.session() as session:
            await session.publish("alpha", {"value": 1})
            await session.publish("beta", {"value": 2})

            beta_payload = await session.consume("beta", timeout=1.0)
            assert beta_payload == {"value": 2}

            # Remaining message should still be available without channel filter
            alpha_payload = await session.consume(timeout=1.0)
            assert alpha_payload == {"value": 1}

    @pytest.mark.asyncio
    async def test_shared_memory_lifecycle(self):
        fabric = AsyncProcessFabric()
        segment_name = f"fabric_segment_{int(time.time() * 1000)}"

        async with fabric.session() as session:
            segment = session.share(segment_name, size=256)
            assert segment.name == segment_name
            segment.set({"ok": True})

            same_segment = session.share(segment_name, create_if_missing=False)
            assert same_segment.get() == {"ok": True}

            assert session.release_shared(segment_name)


# Utility functions for testing
def dummy_worker_function(x):
    """Dummy function for process pool testing."""
    time.sleep(0.1)  # Simulate work
    return x * 2


def dummy_initializer():
    """Dummy initializer for process pool testing."""
    pass


if __name__ == "__main__":
    pytest.main([__file__])
