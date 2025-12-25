#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for BytePagingStrategy.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


from exonware.xwsystem.io.file import BytePagingStrategy


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestBytePagingStrategy:
    """Test BytePagingStrategy."""
    
    def test_byte_paging_strategy_id(self):
        """Test strategy identifier."""
        strategy = BytePagingStrategy()
        assert strategy.strategy_id == "byte"
    
    def test_byte_paging_read_page(self, tmp_path):
        """Test reading a page by byte offset."""
        test_file = tmp_path / "byte_page.bin"
        test_file.write_bytes(b"0123456789" * 10)  # 100 bytes
        
        strategy = BytePagingStrategy()
        page = strategy.read_page(test_file, page=0, page_size=10)
        
        assert len(page) == 10
        assert page == b"0123456789"
    
    def test_byte_paging_read_multiple_pages(self, tmp_path):
        """Test reading multiple pages."""
        test_file = tmp_path / "byte_pages.bin"
        test_file.write_bytes(b"0123456789" * 10)
        
        strategy = BytePagingStrategy()
        
        # Read first page
        page0 = strategy.read_page(test_file, page=0, page_size=10)
        assert page0 == b"0123456789"
        
        # Read second page
        page1 = strategy.read_page(test_file, page=1, page_size=10)
        assert page1 == b"0123456789"
    
    def test_byte_paging_iter_pages(self, tmp_path):
        """Test iterating over pages."""
        test_file = tmp_path / "byte_iter.bin"
        test_file.write_bytes(b"0123456789" * 5)  # 50 bytes
        
        strategy = BytePagingStrategy()
        pages = list(strategy.iter_pages(test_file, page_size=10))
        
        assert len(pages) == 5
        assert all(len(page) == 10 for page in pages)

