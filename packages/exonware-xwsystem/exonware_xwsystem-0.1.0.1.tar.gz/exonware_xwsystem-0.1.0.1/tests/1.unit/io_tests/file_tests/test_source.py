#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for FileDataSource.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


from exonware.xwsystem.io.file import FileDataSource


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestFileDataSource:
    """Test FileDataSource class."""
    
    def test_file_data_source_initialization(self, tmp_path):
        """Test FileDataSource initialization."""
        test_file = tmp_path / "source_test.txt"
        source = FileDataSource(test_file)
        
        assert source._path == test_file
    
    def test_file_data_source_read_text(self, tmp_path):
        """Test reading text from FileDataSource."""
        test_file = tmp_path / "read_text.txt"
        test_file.write_text("Text content")
        
        source = FileDataSource(test_file, mode='r', encoding='utf-8')
        content = source.read()
        assert content == "Text content"
    
    def test_file_data_source_read_bytes(self, tmp_path):
        """Test reading bytes from FileDataSource."""
        test_file = tmp_path / "read_bytes.bin"
        test_file.write_bytes(b"Binary content")
        
        source = FileDataSource(test_file, mode='rb')
        content = source.read()
        assert content == b"Binary content"
    
    def test_file_data_source_write_text(self, tmp_path):
        """Test writing text to FileDataSource."""
        test_file = tmp_path / "write_text.txt"
        source = FileDataSource(test_file, mode='w', encoding='utf-8')
        
        source.write("Written text")
        assert test_file.exists()
        assert test_file.read_text() == "Written text"
    
    def test_file_data_source_write_bytes(self, tmp_path):
        """Test writing bytes to FileDataSource."""
        test_file = tmp_path / "write_bytes.bin"
        source = FileDataSource(test_file, mode='wb')
        
        source.write(b"Written bytes")
        assert test_file.exists()
        assert test_file.read_bytes() == b"Written bytes"
    
    def test_file_data_source_exists(self, tmp_path):
        """Test checking existence."""
        test_file = tmp_path / "exists.txt"
        source = FileDataSource(test_file)
        
        assert source.exists() is False
        
        test_file.write_text("content")
        assert source.exists() is True
    
    def test_file_data_source_delete(self, tmp_path):
        """Test deleting file."""
        test_file = tmp_path / "delete.txt"
        test_file.write_text("content")
        
        source = FileDataSource(test_file)
        source.delete()
        assert not test_file.exists()
    
    def test_file_data_source_uri(self, tmp_path):
        """Test URI property."""
        test_file = tmp_path / "uri_test.txt"
        source = FileDataSource(test_file)
        
        uri = source.uri
        assert uri.startswith("file://")
        assert "uri_test.txt" in uri
    
    def test_file_data_source_scheme(self, tmp_path):
        """Test scheme property."""
        test_file = tmp_path / "scheme_test.txt"
        source = FileDataSource(test_file)
        
        assert source.scheme == "file"

