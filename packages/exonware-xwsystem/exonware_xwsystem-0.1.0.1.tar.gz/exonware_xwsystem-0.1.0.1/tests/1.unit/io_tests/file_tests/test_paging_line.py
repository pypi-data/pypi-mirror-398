#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for LinePagingStrategy.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


from exonware.xwsystem.io.file import LinePagingStrategy


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestLinePagingStrategy:
    """Test LinePagingStrategy."""
    
    def test_line_paging_strategy_id(self):
        """Test strategy identifier."""
        strategy = LinePagingStrategy()
        assert strategy.strategy_id == "line"
    
    def test_line_paging_read_page(self, tmp_path):
        """Test reading a page by line count."""
        test_file = tmp_path / "line_page.txt"
        lines = [f"Line {i}\n" for i in range(10)]
        test_file.write_text("".join(lines))
        
        strategy = LinePagingStrategy()
        page = strategy.read_page(test_file, page=0, page_size=3)
        
        assert "Line 0" in page
        assert "Line 1" in page
        assert "Line 2" in page
    
    def test_line_paging_read_multiple_pages(self, tmp_path):
        """Test reading multiple pages."""
        test_file = tmp_path / "line_pages.txt"
        lines = [f"Line {i}\n" for i in range(10)]
        test_file.write_text("".join(lines))
        
        strategy = LinePagingStrategy()
        
        # Read first page
        page0 = strategy.read_page(test_file, page=0, page_size=3)
        assert "Line 0" in page0
        
        # Read second page
        page1 = strategy.read_page(test_file, page=1, page_size=3)
        assert "Line 3" in page1
    
    def test_line_paging_iter_pages(self, tmp_path):
        """Test iterating over pages."""
        test_file = tmp_path / "line_iter.txt"
        lines = [f"Line {i}\n" for i in range(10)]
        test_file.write_text("".join(lines))
        
        strategy = LinePagingStrategy()
        pages = list(strategy.iter_pages(test_file, page_size=3))
        
        assert len(pages) >= 3
        assert "Line 0" in pages[0]

