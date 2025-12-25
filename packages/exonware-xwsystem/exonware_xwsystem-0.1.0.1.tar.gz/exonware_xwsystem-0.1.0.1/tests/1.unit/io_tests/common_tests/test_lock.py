#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for FileLock.

Following GUIDE_TEST.md standards.
"""

import sys
import time
from pathlib import Path

import pytest

from exonware.xwsystem.io.common import FileLock


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestFileLock:
    """Test FileLock class."""
    
    def test_file_lock_initialization(self, tmp_path):
        """Test FileLock initialization."""
        test_file = tmp_path / "lock_test.txt"
        lock = FileLock(test_file)
        
        assert lock._path == test_file
        assert lock._lock_path == test_file.with_suffix(test_file.suffix + '.lock')
    
    def test_file_lock_acquire(self, tmp_path):
        """Test acquiring a lock."""
        test_file = tmp_path / "acquire_test.txt"
        lock = FileLock(test_file)
        
        assert lock.acquire() is True
        assert lock._locked is True
        lock.release()
    
    def test_file_lock_release(self, tmp_path):
        """Test releasing a lock."""
        test_file = tmp_path / "release_test.txt"
        lock = FileLock(test_file)
        
        lock.acquire()
        lock.release()
        assert lock._locked is False
    
    def test_file_lock_context_manager(self, tmp_path):
        """Test FileLock as context manager."""
        test_file = tmp_path / "context_test.txt"
        
        with FileLock(test_file) as lock:
            assert lock._locked is True
        
        assert lock._locked is False
    
    def test_file_lock_timeout(self, tmp_path):
        """Test lock timeout."""
        test_file = tmp_path / "timeout_test.txt"
        lock1 = FileLock(test_file, timeout=0.1)
        lock2 = FileLock(test_file, timeout=0.1)
        
        # Acquire first lock
        assert lock1.acquire() is True
        
        # Try to acquire second lock (should timeout)
        assert lock2.acquire() is False
        
        lock1.release()

