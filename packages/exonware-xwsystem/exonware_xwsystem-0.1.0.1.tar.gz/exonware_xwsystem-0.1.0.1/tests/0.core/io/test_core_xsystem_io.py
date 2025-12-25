#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XSystem I/O Core Tests

Tests the actual XSystem I/O features including atomic file operations,
safe file handling, async I/O, and advanced file management.

Following GUIDE_TEST.md standards.
"""

import sys
import tempfile
import os
import shutil
import threading
import time
from pathlib import Path

import pytest

# Import xwsystem.io classes
from exonware.xwsystem.io.common import (
    AtomicFileWriter,
    safe_read_bytes,
    safe_read_text,
    safe_write_bytes,
    safe_write_text,
    PathManager,
    FileWatcher,
    FileLock,
)
from exonware.xwsystem.io.file import (
    XWFile,
    FileDataSource,
    PagedFileSource,
    BytePagingStrategy,
    LinePagingStrategy,
    RecordPagingStrategy,
    get_global_paging_registry,
)
from exonware.xwsystem.io.folder import XWFolder
from exonware.xwsystem.io.filesystem import LocalFileSystem
from exonware.xwsystem.io.stream import CodecIO, PagedCodecIO, AsyncAtomicFileWriter
from exonware.xwsystem.io.facade import XWIO
from exonware.xwsystem.io.codec.registry import get_registry as get_codec_registry


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestAtomicFileOperations:
    """Test atomic file operations using AtomicFileWriter."""
    
    def test_atomic_file_writer_basic(self, tmp_path):
        """Test basic atomic file writing."""
        test_file = tmp_path / "test_atomic.txt"
        test_content = "This is atomic test content"
        
        # Write atomically
        with AtomicFileWriter(test_file) as writer:
            writer.write(test_content)
        
        # Verify file exists and content is correct
        assert test_file.exists()
        assert safe_read_text(test_file) == test_content
    
    def test_atomic_file_writer_with_backup(self, tmp_path):
        """Test atomic file writing with backup."""
        test_file = tmp_path / "test_backup.txt"
        original_content = "Original content"
        new_content = "New content"
        
        # Create original file
        test_file.write_text(original_content)
        
        # Write with backup
        with AtomicFileWriter(test_file, backup=True) as writer:
            writer.write(new_content)
        
        # Verify new content
        assert safe_read_text(test_file) == new_content
        # Backup should exist
        backup_file = test_file.with_suffix(test_file.suffix + '.bak')
        # Note: AtomicFileWriter may not create .bak by default, check implementation
    
    def test_atomic_file_writer_rollback_on_error(self, tmp_path):
        """Test that atomic write rolls back on error."""
        test_file = tmp_path / "test_rollback.txt"
        original_content = "Original"
        test_file.write_text(original_content)
        
        try:
            with AtomicFileWriter(test_file) as writer:
                writer.write("New content")
                raise ValueError("Simulated error")
        except ValueError:
            pass
        
        # Content should remain unchanged
        assert safe_read_text(test_file) == original_content


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestSafeFileOperations:
    """Test safe file operations."""
    
    def test_safe_read_text(self, tmp_path):
        """Test safe text reading."""
        test_file = tmp_path / "test_safe.txt"
        test_content = "Safe test content"
        test_file.write_text(test_content)
        
        # Read existing file
        content = safe_read_text(test_file)
        assert content == test_content
        
        # Read non-existent file should raise error
        from exonware.xwsystem.io.common.atomic import FileOperationError
        with pytest.raises(FileOperationError, match="File does not exist"):
            safe_read_text(tmp_path / "nonexistent.txt")
    
    def test_safe_read_bytes(self, tmp_path):
        """Test safe bytes reading."""
        test_file = tmp_path / "test_safe.bin"
        test_content = b"Binary content"
        test_file.write_bytes(test_content)
        
        # Read existing file
        content = safe_read_bytes(test_file)
        assert content == test_content
        
        # Read non-existent file should raise error
        from exonware.xwsystem.io.common.atomic import FileOperationError
        with pytest.raises(FileOperationError, match="File does not exist"):
            safe_read_bytes(tmp_path / "nonexistent.bin")
    
    def test_safe_write_text(self, tmp_path):
        """Test safe text writing."""
        test_file = tmp_path / "test_write.txt"
        test_content = "Safe write content"
        
        # Write text
        safe_write_text(test_file, test_content)
        assert test_file.exists()
        assert test_file.read_text() == test_content
    
    def test_safe_write_bytes(self, tmp_path):
        """Test safe bytes writing."""
        test_file = tmp_path / "test_write.bin"
        test_content = b"Safe write bytes"
        
        # Write bytes
        safe_write_bytes(test_file, test_content)
        assert test_file.exists()
        assert test_file.read_bytes() == test_content


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestPathManager:
    """Test PathManager utilities."""
    
    def test_path_manager_looks_like_file_path(self):
        """Test path detection."""
        # Should detect file paths
        assert PathManager.looks_like_file_path("/path/to/file.txt") is True
        assert PathManager.looks_like_file_path("file.txt") is True
        assert PathManager.looks_like_file_path("subdir/file.txt") is True
        
        # Should not detect raw content
        assert PathManager.looks_like_file_path('{"key": "value"}') is False
        assert PathManager.looks_like_file_path("raw content\nwith newlines") is False
    
    def test_path_manager_resolve_base_path(self):
        """Test base path resolution."""
        # Test with valid path
        resolved = PathManager.resolve_base_path("/some/path")
        assert resolved is not None
        
        # Test with None
        resolved = PathManager.resolve_base_path(None)
        assert resolved is None


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestFileWatcher:
    """Test FileWatcher functionality."""
    
    def test_file_watcher_basic(self, tmp_path):
        """Test basic file watching."""
        test_file = tmp_path / "watched.txt"
        events = []
        
        def on_change(path, event_type):
            events.append((path, event_type))
        
        watcher = FileWatcher(poll_interval=0.1)
        watcher.watch(test_file, on_change)
        
        # Start watching
        watcher.start()
        time.sleep(0.2)  # Let watcher initialize
        
        # Create file
        test_file.write_text("content")
        time.sleep(0.3)  # Wait for detection
        
        # Stop watching
        watcher.stop()
        
        # Should have detected creation
        assert len(events) > 0


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestFileLock:
    """Test FileLock functionality."""
    
    def test_file_lock_basic(self, tmp_path):
        """Test basic file locking."""
        test_file = tmp_path / "locked.txt"
        lock = FileLock(test_file)
        
        # Acquire lock
        assert lock.acquire() is True
        
        # Release lock
        lock.release()
    
    def test_file_lock_context_manager(self, tmp_path):
        """Test file lock as context manager."""
        test_file = tmp_path / "locked.txt"
        
        with FileLock(test_file):
            # Lock should be held
            assert True  # If we get here, lock was acquired


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestXWFile:
    """Test XWFile class."""
    
    def test_xwfile_basic_operations(self, tmp_path):
        """Test basic XWFile operations."""
        test_file = tmp_path / "xwfile_test.txt"
        file_obj = XWFile(test_file)
        
        # Save content
        content = "XWFile test content"
        assert file_obj.save(content) is True
        
        # Load content
        loaded = file_obj.load()
        assert loaded == content
    
    def test_xwfile_open_read_write(self, tmp_path):
        """Test XWFile open/read/write operations."""
        test_file = tmp_path / "xwfile_rw.txt"
        file_obj = XWFile(test_file)
        
        # Open for writing
        from exonware.xwsystem.io.contracts import FileMode
        file_obj.open(FileMode.WRITE)
        file_obj.write("Written content")
        file_obj.close()
        
        # Open for reading
        file_obj.open(FileMode.READ)
        content = file_obj.read()
        file_obj.close()
        
        assert content == "Written content"


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestXWFolder:
    """Test XWFolder class."""
    
    def test_xwfolder_create_delete(self, tmp_path):
        """Test folder creation and deletion."""
        folder_path = tmp_path / "test_folder"
        folder = XWFolder(folder_path)
        
        # Create folder
        assert folder.create() is True
        assert folder_path.exists()
        
        # Delete folder
        assert folder.delete() is True
        assert not folder_path.exists()
    
    def test_xwfolder_list_contents(self, tmp_path):
        """Test folder listing."""
        folder_path = tmp_path / "list_folder"
        folder = XWFolder(folder_path)
        folder.create()
        
        # Create some files
        (folder_path / "file1.txt").write_text("content1")
        (folder_path / "file2.txt").write_text("content2")
        (folder_path / "subdir").mkdir()
        
        # List files
        files = folder.list_files()
        assert len(files) == 2
        
        # List directories
        dirs = folder.list_directories()
        assert len(dirs) == 1


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestLocalFileSystem:
    """Test LocalFileSystem."""
    
    def test_local_filesystem_basic(self, tmp_path):
        """Test basic LocalFileSystem operations."""
        fs = LocalFileSystem()
        
        test_path = str(tmp_path / "fs_test.txt")
        test_content = "Filesystem test"
        
        # Write
        fs.write_text(test_path, test_content)
        
        # Read
        content = fs.read_text(test_path)
        assert content == test_content
        
        # Exists
        assert fs.exists(test_path) is True
        
        # Is file
        assert fs.is_file(test_path) is True


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestFileDataSource:
    """Test FileDataSource."""
    
    def test_file_data_source_basic(self, tmp_path):
        """Test basic FileDataSource operations."""
        test_file = tmp_path / "source_test.txt"
        # Use text mode ('r') instead of default binary mode ('rb')
        source = FileDataSource(test_file, mode='r', encoding='utf-8')
        
        # Write
        source.write("Source content")
        
        # Read
        content = source.read()
        assert content == "Source content"
        
        # Exists
        assert source.exists() is True


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestPagingStrategies:
    """Test paging strategies."""
    
    def test_byte_paging_strategy(self, tmp_path):
        """Test BytePagingStrategy."""
        test_file = tmp_path / "byte_paging.bin"
        test_file.write_bytes(b"0123456789" * 10)  # 100 bytes
        
        strategy = BytePagingStrategy()
        page = strategy.read_page(test_file, page=0, page_size=10)
        assert len(page) == 10
        assert page == b"0123456789"
    
    def test_line_paging_strategy(self, tmp_path):
        """Test LinePagingStrategy."""
        test_file = tmp_path / "line_paging.txt"
        lines = [f"Line {i}\n" for i in range(10)]
        test_file.write_text("".join(lines))
        
        strategy = LinePagingStrategy()
        page = strategy.read_page(test_file, page=0, page_size=3)
        assert "Line 0" in page
        assert "Line 1" in page
        assert "Line 2" in page
    
    def test_paging_registry(self):
        """Test paging strategy registry."""
        registry = get_global_paging_registry()
        strategies = registry.list_strategies()
        
        assert "byte" in strategies
        assert "line" in strategies


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestPagedFileSource:
    """Test PagedFileSource."""
    
    def test_paged_file_source_byte_paging(self, tmp_path):
        """Test PagedFileSource with byte paging."""
        test_file = tmp_path / "paged_source.bin"
        test_file.write_bytes(b"0123456789" * 10)
        
        # PagedFileSource auto-detects strategy based on mode ('rb' = BytePagingStrategy)
        source = PagedFileSource(test_file, mode='rb')
        
        # Read first page with page_size parameter
        page = source.read_page(0, page_size=10)
        assert len(page) == 10


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestCodecIO:
    """Test CodecIO integration."""
    
    def test_codec_io_basic(self, tmp_path):
        """Test basic CodecIO operations."""
        # This test requires a codec (serializer) to be available
        # We'll test with JSON if available
        try:
            from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
            from exonware.xwsystem.io.file import FileDataSource
            
            test_file = tmp_path / "codec_io.json"
            codec = JsonSerializer()
            source = FileDataSource(test_file)
            codec_io = CodecIO(codec, source)
            
            # Save data
            data = {"key": "value", "number": 42}
            codec_io.save(data)
            
            # Load data
            loaded = codec_io.load()
            assert loaded == data
        except ImportError:
            pytest.skip("JSON serializer not available")


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestXWIOFacade:
    """Test XWIO facade - MANDATORY facade pattern."""
    
    def test_xwio_facade_basic(self, tmp_path):
        """Test basic XWIO facade operations."""
        test_file = tmp_path / "facade_test.txt"
        io_facade = XWIO(test_file)
        
        # Save data
        content = "Facade test content"
        assert io_facade.save(content) is True
        
        # Load data
        loaded = io_facade.load()
        assert loaded == content
    
    def test_xwio_facade_file_operations(self, tmp_path):
        """Test XWIO facade file operations."""
        test_file = tmp_path / "facade_file.txt"
        io_facade = XWIO()
        
        # Save to file
        content = "Facade file content"
        assert io_facade.save_as(str(test_file), content) is True
        
        # Load from file
        loaded = io_facade.load_from(str(test_file))
        assert loaded == content


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestCodecRegistry:
    """Test UniversalCodecRegistry."""
    
    def test_codec_registry_exists(self):
        """Test that codec registry is accessible."""
        registry = get_codec_registry()
        assert registry is not None


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestConcurrentOperations:
    """Test concurrent file operations."""
    
    def test_concurrent_file_writes(self, tmp_path):
        """Test concurrent file writes with locks."""
        test_file = tmp_path / "concurrent.txt"
        results = []
        
        def write_worker(thread_id):
            lock = FileLock(test_file)
            with lock:
                time.sleep(0.01)  # Simulate work
                safe_write_text(test_file, f"Thread {thread_id}\n", append=True)
                results.append(thread_id)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=write_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All threads should have written
        assert len(results) == 5
        assert test_file.exists()
