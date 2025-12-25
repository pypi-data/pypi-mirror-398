#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for PagedFileSource.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


from exonware.xwsystem.io.file import PagedFileSource, BytePagingStrategy, LinePagingStrategy


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestPagedFileSource:
    """Test PagedFileSource class."""
    
    def test_paged_file_source_initialization(self, tmp_path):
        """Test PagedFileSource initialization."""
        test_file = tmp_path / "paged_test.bin"
        source = PagedFileSource(test_file)
        
        assert source._path == test_file
        assert source._paging_strategy is not None
    
    def test_paged_file_source_byte_paging(self, tmp_path):
        """Test PagedFileSource with byte paging."""
        test_file = tmp_path / "byte_paged.bin"
        test_file.write_bytes(b"0123456789" * 10)  # 100 bytes
        
        source = PagedFileSource(test_file, mode='rb')
        
        # Read first page
        page = source.read_page(0, page_size=10)
        assert len(page) == 10
        assert page == b"0123456789"
    
    def test_paged_file_source_line_paging(self, tmp_path):
        """Test PagedFileSource with line paging."""
        test_file = tmp_path / "line_paged.txt"
        lines = [f"Line {i}\n" for i in range(10)]
        test_file.write_text("".join(lines))
        
        source = PagedFileSource(test_file, mode='r')
        
        # Read first page (3 lines)
        page = source.read_page(0, page_size=3)
        assert "Line 0" in page
        assert "Line 1" in page
        assert "Line 2" in page
    
    def test_paged_file_source_custom_strategy(self, tmp_path):
        """Test PagedFileSource with custom strategy."""
        test_file = tmp_path / "custom_paged.txt"
        test_file.write_text("Content")
        
        strategy = BytePagingStrategy()
        source = PagedFileSource(test_file, paging_strategy=strategy)
        
        assert source._paging_strategy is strategy
    
    def test_paged_file_source_total_size(self, tmp_path):
        """Test getting total size."""
        test_file = tmp_path / "size_test.bin"
        test_file.write_bytes(b"Content")
        
        source = PagedFileSource(test_file)
        size = source.total_size
        assert size == len(b"Content")
    
    def test_paged_file_source_iter_pages(self, tmp_path):
        """Test iterating over pages."""
        test_file = tmp_path / "iter_test.bin"
        test_file.write_bytes(b"0123456789" * 5)  # 50 bytes
        
        source = PagedFileSource(test_file, mode='rb')
        
        pages = list(source.iter_pages(page_size=10))
        assert len(pages) == 5
        assert pages[0] == b"0123456789"

