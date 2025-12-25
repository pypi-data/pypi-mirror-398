#!/usr/bin/env python3
"""
Core I/O Test Runner

Tests atomic file operations, async operations, and file management.
Focuses on the main I/O functionality and real-world file operations.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: January 02, 2025
"""

import sys
import tempfile
import asyncio
from pathlib import Path
from typing import Any


class IoCoreTester:
    """Core tester for I/O functionality."""
    
    def __init__(self):
        self.test_data_dir = Path(__file__).parent / "data"
        self.test_data_dir.mkdir(exist_ok=True)
        self.results: dict[str, bool] = {}
        
    def test_atomic_file_writer(self) -> bool:
        """Test atomic file writer functionality."""
        try:
            from exonware.xwsystem.io.atomic_file import AtomicFileWriter
            
            # Test text file writing
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                temp_file = Path(f.name)
            
            try:
                test_content = "This is test content for atomic file writing.\nLine 2\nLine 3"
                
                with AtomicFileWriter(temp_file) as writer:
                    writer.write(test_content)
                
                # Verify file was written correctly
                assert temp_file.exists()
                with open(temp_file, 'r') as f:
                    content = f.read()
                    assert content == test_content
                
                print("[PASS] Atomic file writer tests passed")
                return True
                
            finally:
                temp_file.unlink(missing_ok=True)
            
        except Exception as e:
            print(f"[FAIL] Atomic file writer tests failed: {e}")
            return False
    
    def test_safe_file_operations(self) -> bool:
        """Test safe file operations."""
        try:
            from exonware.xwsystem.io.atomic_file import (
                safe_write_text, safe_read_text, 
                safe_write_bytes, safe_read_bytes
            )
            
            # Test text operations
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                temp_file = Path(f.name)
            
            try:
                test_text = "This is test text content for safe operations."
                
                # Test safe write text
                safe_write_text(temp_file, test_text)
                assert temp_file.exists()
                
                # Test safe read text
                read_text = safe_read_text(temp_file)
                assert read_text == test_text
                
                # Test bytes operations
                test_bytes = b"This is test binary content for safe operations."
                
                # Test safe write bytes
                safe_write_bytes(temp_file, test_bytes)
                
                # Test safe read bytes
                read_bytes = safe_read_bytes(temp_file)
                assert read_bytes == test_bytes
                
                print("[PASS] Safe file operations tests passed")
                return True
                
            finally:
                temp_file.unlink(missing_ok=True)
            
        except Exception as e:
            print(f"[FAIL] Safe file operations tests failed: {e}")
            return False
    
    def test_async_file_operations(self) -> bool:
        """Test async file operations."""
        try:
            from exonware.xwsystem.io.async_operations import (
                async_safe_write_text, async_safe_read_text,
                async_safe_write_bytes, async_safe_read_bytes
            )
            
            async def test_async_operations():
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                    temp_file = Path(f.name)
                
                try:
                    test_text = "This is test text content for async operations."
                    test_bytes = b"This is test binary content for async operations."
                    
                    # Test async write text
                    await async_safe_write_text(temp_file, test_text)
                    assert temp_file.exists()
                    
                    # Test async read text
                    read_text = await async_safe_read_text(temp_file)
                    assert read_text == test_text
                    
                    # Test async write bytes
                    await async_safe_write_bytes(temp_file, test_bytes)
                    
                    # Test async read bytes
                    read_bytes = await async_safe_read_bytes(temp_file)
                    assert read_bytes == test_bytes
                    
                    return True
                    
                finally:
                    temp_file.unlink(missing_ok=True)
            
            # Run async test
            result = asyncio.run(test_async_operations())
            if result:
                print("[PASS] Async file operations tests passed")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"[FAIL] Async file operations tests failed: {e}")
            return False
    
    def test_file_operation_errors(self) -> bool:
        """Test file operation error handling."""
        try:
            from exonware.xwsystem.io.atomic_file import (
                safe_write_text, safe_read_text, FileOperationError
            )
            
            # Test writing to invalid path
            invalid_path = Path("/invalid/path/that/does/not/exist/file.txt")
            
            try:
                safe_write_text(invalid_path, "test content")
                print("[WARNING]  Expected error for invalid path")
                return False
            except (FileOperationError, OSError, PermissionError):
                pass  # Expected behavior
            
            # Test reading from non-existent file
            non_existent_file = Path("/tmp/non_existent_file.txt")
            
            try:
                content = safe_read_text(non_existent_file)
                print("[WARNING]  Expected error for non-existent file")
                return False
            except (FileOperationError, FileNotFoundError):
                pass  # Expected behavior
            
            print("[PASS] File operation error handling tests passed")
            return True
            
        except Exception as e:
            print(f"[FAIL] File operation error handling tests failed: {e}")
            return False
    
    def test_path_manager(self) -> bool:
        """Test path manager functionality."""
        try:
            from exonware.xwsystem.io.path_manager import PathManager
            
            path_manager = PathManager()
            
            # Test path normalization
            test_paths = [
                "/tmp/test.txt",
                "C:\\Users\\test\\file.txt",
                "./relative/path.txt",
                "../parent/file.txt"
            ]
            
            for path in test_paths:
                normalized = path_manager.normalize_path(path)
                assert isinstance(normalized, Path)
            
            # Test path validation
            valid_paths = [
                "/tmp/test.txt",
                "./relative/path.txt"
            ]
            
            for path in valid_paths:
                is_valid = path_manager.validate_path(path)
                assert isinstance(is_valid, bool)
            
            print("[PASS] Path manager tests passed")
            return True
            
        except Exception as e:
            print(f"[FAIL] Path manager tests failed: {e}")
            return False
    
    def test_concurrent_file_operations(self) -> bool:
        """Test concurrent file operations."""
        try:
            import threading
            from exonware.xwsystem.io.atomic_file import safe_write_text, safe_read_text
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                temp_file = Path(f.name)
            
            try:
                results = []
                errors = []
                
                def write_operation(thread_id):
                    try:
                        content = f"Thread {thread_id} content"
                        safe_write_text(temp_file, content)
                        results.append(f"Thread {thread_id} wrote successfully")
                    except Exception as e:
                        errors.append(f"Thread {thread_id} error: {e}")
                
                # Create multiple threads
                threads = []
                for i in range(5):
                    thread = threading.Thread(target=write_operation, args=(i,))
                    threads.append(thread)
                    thread.start()
                
                # Wait for all threads to complete
                for thread in threads:
                    thread.join()
                
                # Verify file exists and has content
                assert temp_file.exists()
                content = safe_read_text(temp_file)
                assert len(content) > 0
                
                print("[PASS] Concurrent file operations tests passed")
                return True
                
            finally:
                temp_file.unlink(missing_ok=True)
            
        except Exception as e:
            print(f"[FAIL] Concurrent file operations tests failed: {e}")
            return False
    
    def test_all_serialization_tests(self) -> int:
        """Run all serialization core tests."""
        print("[SERIALIZATION] XSystem Core Serialization Tests")
        print("=" * 50)
        print("Testing all main serialization features with comprehensive roundtrip testing")
        print("=" * 50)
        
        # Run the actual XSystem serialization tests
        try:
            import sys
            from pathlib import Path
            test_xwsystem_path = Path(__file__).parent / "test_core_xwsystem_serialization.py"
            sys.path.insert(0, str(test_xwsystem_path.parent))
            
            import test_core_xwsystem_serialization
            return test_core_xwsystem_serialization.main()
        except Exception as e:
            print(f"[FAIL] Failed to run XSystem serialization tests: {e}")
            return 1
    
    def test_all_io_tests(self) -> int:
        """Run all I/O core tests."""
        print("[IO] XSystem Core I/O Tests")
        print("=" * 50)
        print("Testing all main I/O features with comprehensive validation")
        print("=" * 50)
        
        # Run I/O tests
        io_result = 0
        try:
            import sys
            from pathlib import Path
            test_basic_path = Path(__file__).parent / "test_core_xwsystem_io.py"
            sys.path.insert(0, str(test_basic_path.parent))
            
            import test_core_xwsystem_io
            io_result = test_core_xwsystem_io.main()
        except Exception as e:
            print(f"[FAIL] Failed to run basic I/O tests: {e}")
            io_result = 1
        
        # Run serialization tests
        serialization_result = self.test_all_serialization_tests()
        
        # Return failure if either failed
        return 0 if (io_result == 0 and serialization_result == 0) else 1


def run_all_io_tests() -> int:
    """Main entry point for I/O core tests using pytest."""
    import pytest
    from pathlib import Path
    
    # Get test directory
    test_dir = Path(__file__).parent
    
    # Run all core IO tests using pytest
    exit_code = pytest.main([
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
        str(test_dir),
        "-m", "xwsystem_core or xwsystem_io or xwsystem_serialization",
    ])
    
    return exit_code


def run_all_serialization_tests() -> int:
    """Run serialization core tests."""
    import pytest
    from pathlib import Path
    
    test_dir = Path(__file__).parent
    
    exit_code = pytest.main([
        "-v",
        "--tb=short",
        str(test_dir),
        "-m", "xwsystem_serialization",
        "-k", "serialization",
    ])
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_all_io_tests())
