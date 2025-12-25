#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for FileWatcher.

Following GUIDE_TEST.md standards.
"""

import sys
import time
from pathlib import Path

import pytest


from exonware.xwsystem.io.common import FileWatcher


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestFileWatcher:
    """Test FileWatcher class."""
    
    def test_file_watcher_initialization(self):
        """Test FileWatcher initialization."""
        watcher = FileWatcher(poll_interval=0.1)
        assert watcher._poll_interval == 0.1
        assert watcher._running is False
    
    def test_file_watcher_watch(self, tmp_path):
        """Test watching a file."""
        test_file = tmp_path / "watched.txt"
        events = []
        
        def on_change(path, event_type):
            events.append((path, event_type))
        
        watcher = FileWatcher(poll_interval=0.1)
        watcher.watch(test_file, on_change)
        
        assert test_file in watcher._watched
    
    def test_file_watcher_unwatch(self, tmp_path):
        """Test unwatching a file."""
        test_file = tmp_path / "unwatched.txt"
        
        watcher = FileWatcher()
        watcher.watch(test_file, lambda p, e: None)
        watcher.unwatch(test_file)
        
        assert test_file not in watcher._watched
    
    def test_file_watcher_start_stop(self, tmp_path):
        """Test starting and stopping watcher."""
        test_file = tmp_path / "start_stop.txt"
        
        watcher = FileWatcher(poll_interval=0.1)
        watcher.watch(test_file, lambda p, e: None)
        
        watcher.start()
        assert watcher._running is True
        
        time.sleep(0.2)  # Let it run briefly
        
        watcher.stop()
        assert watcher._running is False
    
    def test_file_watcher_detect_changes(self, tmp_path):
        """Test detecting file changes."""
        test_file = tmp_path / "change_test.txt"
        events = []
        
        def on_change(path, event_type):
            events.append((path, event_type))
        
        watcher = FileWatcher(poll_interval=0.1)
        watcher.watch(test_file, on_change)
        watcher.start()
        
        time.sleep(0.2)  # Let watcher initialize
        
        # Create file
        test_file.write_text("content")
        time.sleep(0.3)  # Wait for detection
        
        watcher.stop()
        
        # Should have detected creation
        assert len(events) > 0

