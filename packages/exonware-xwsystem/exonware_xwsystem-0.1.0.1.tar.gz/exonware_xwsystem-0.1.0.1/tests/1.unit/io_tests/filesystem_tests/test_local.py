#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for LocalFileSystem.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest

from exonware.xwsystem.io.filesystem import LocalFileSystem


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestLocalFileSystem:
    """Test LocalFileSystem class."""
    
    def test_local_filesystem_initialization(self):
        """Test LocalFileSystem initialization."""
        fs = LocalFileSystem()
        assert fs is not None
        assert fs.scheme == "file"
    
    def test_local_filesystem_write_read_text(self, tmp_path):
        """Test writing and reading text."""
        fs = LocalFileSystem()
        test_path = str(tmp_path / "fs_text.txt")
        test_content = "Filesystem text"
        
        fs.write_text(test_path, test_content)
        content = fs.read_text(test_path)
        
        assert content == test_content
    
    def test_local_filesystem_write_read_bytes(self, tmp_path):
        """Test writing and reading bytes."""
        fs = LocalFileSystem()
        test_path = str(tmp_path / "fs_bytes.bin")
        test_content = b"Filesystem bytes"
        
        fs.write_bytes(test_path, test_content)
        content = fs.read_bytes(test_path)
        
        assert content == test_content
    
    def test_local_filesystem_exists(self, tmp_path):
        """Test checking existence."""
        fs = LocalFileSystem()
        test_path = str(tmp_path / "fs_exists.txt")
        
        assert fs.exists(test_path) is False
        
        fs.write_text(test_path, "content")
        assert fs.exists(test_path) is True
    
    def test_local_filesystem_is_file(self, tmp_path):
        """Test checking if path is file."""
        fs = LocalFileSystem()
        test_path = str(tmp_path / "fs_file.txt")
        fs.write_text(test_path, "content")
        
        assert fs.is_file(test_path) is True
        assert fs.is_file(str(tmp_path)) is False
    
    def test_local_filesystem_is_dir(self, tmp_path):
        """Test checking if path is directory."""
        fs = LocalFileSystem()
        test_dir = tmp_path / "fs_dir"
        test_dir.mkdir()
        
        assert fs.is_dir(str(test_dir)) is True
        assert fs.is_dir(str(tmp_path / "nonexistent")) is False
    
    def test_local_filesystem_listdir(self, tmp_path):
        """Test listing directory."""
        fs = LocalFileSystem()
        test_dir = tmp_path / "list_dir"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")
        
        items = fs.listdir(str(test_dir))
        assert len(items) == 2
        assert "file1.txt" in items
        assert "file2.txt" in items
    
    def test_local_filesystem_mkdir(self, tmp_path):
        """Test creating directory."""
        fs = LocalFileSystem()
        test_dir = str(tmp_path / "mkdir_test")
        
        fs.mkdir(test_dir)
        assert Path(test_dir).exists()
        assert Path(test_dir).is_dir()
    
    def test_local_filesystem_remove(self, tmp_path):
        """Test removing file."""
        fs = LocalFileSystem()
        test_file = tmp_path / "remove_test.txt"
        test_file.write_text("content")
        
        fs.remove(str(test_file))
        assert not test_file.exists()
    
    def test_local_filesystem_copy(self, tmp_path):
        """Test copying file."""
        fs = LocalFileSystem()
        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("content")
        
        fs.copy(str(source), str(dest))
        assert dest.exists()
        assert dest.read_text() == "content"
    
    def test_local_filesystem_move(self, tmp_path):
        """Test moving file."""
        fs = LocalFileSystem()
        source = tmp_path / "move_source.txt"
        dest = tmp_path / "move_dest.txt"
        source.write_text("content")
        
        fs.move(str(source), str(dest))
        assert not source.exists()
        assert dest.exists()
        assert dest.read_text() == "content"

