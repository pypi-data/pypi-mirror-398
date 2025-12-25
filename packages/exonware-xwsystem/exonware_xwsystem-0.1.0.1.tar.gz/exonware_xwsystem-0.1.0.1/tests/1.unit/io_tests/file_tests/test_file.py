#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for XWFile class.

Following GUIDE_TEST.md standards.
"""

import sys
import tempfile
from pathlib import Path

import pytest

from exonware.xwsystem.io.file import XWFile
from exonware.xwsystem.io.contracts import FileMode


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestXWFile:
    """Test XWFile class."""
    
    def test_xwfile_initialization(self, tmp_path):
        """Test XWFile initialization."""
        test_file = tmp_path / "test.txt"
        file_obj = XWFile(test_file)
        
        assert file_obj.file_path == test_file
        assert file_obj.validate_paths is True
    
    def test_xwfile_save_text(self, tmp_path):
        """Test saving text content."""
        test_file = tmp_path / "save_test.txt"
        file_obj = XWFile(test_file)
        
        content = "Test content"
        assert file_obj.save(content) is True
        assert test_file.exists()
        assert test_file.read_text() == content
    
    def test_xwfile_load_text(self, tmp_path):
        """Test loading text content."""
        test_file = tmp_path / "load_test.txt"
        test_file.write_text("Loaded content")
        
        file_obj = XWFile(test_file)
        loaded = file_obj.load()
        assert loaded == "Loaded content"
    
    def test_xwfile_open_read_write(self, tmp_path):
        """Test open/read/write operations."""
        test_file = tmp_path / "rw_test.txt"
        file_obj = XWFile(test_file)
        
        # Open for writing
        file_obj.open(FileMode.WRITE)
        file_obj.write("Written")
        file_obj.close()
        
        # Open for reading
        file_obj.open(FileMode.READ)
        content = file_obj.read()
        file_obj.close()
        
        assert content == "Written"
    
    def test_xwfile_get_size(self, tmp_path):
        """Test getting file size."""
        test_file = tmp_path / "size_test.txt"
        test_file.write_text("Content")
        
        file_obj = XWFile(test_file)
        size = file_obj.get_size()
        assert size > 0
    
    def test_xwfile_exists(self, tmp_path):
        """Test checking file existence."""
        test_file = tmp_path / "exists_test.txt"
        file_obj = XWFile(test_file)
        
        assert file_obj.exists() is False
        
        test_file.write_text("content")
        assert file_obj.exists() is True

