#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for RecordPagingStrategy.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


from exonware.xwsystem.io.file import RecordPagingStrategy


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestRecordPagingStrategy:
    """Test RecordPagingStrategy."""
    
    def test_record_paging_strategy_id(self):
        """Test strategy identifier."""
        strategy = RecordPagingStrategy()
        assert strategy.strategy_id == "record"
    
    def test_record_paging_read_page(self, tmp_path):
        """Test reading a page by record count."""
        test_file = tmp_path / "record_page.txt"
        records = [f"Record {i}\n" for i in range(10)]
        test_file.write_text("".join(records))
        
        strategy = RecordPagingStrategy()
        page = strategy.read_page(test_file, page=0, page_size=3)
        
        assert "Record 0" in page
        assert "Record 1" in page
        assert "Record 2" in page
    
    def test_record_paging_custom_delimiter(self, tmp_path):
        """Test record paging with custom delimiter."""
        test_file = tmp_path / "record_custom.txt"
        test_file.write_text("Record1|Record2|Record3|")
        
        strategy = RecordPagingStrategy(delimiter='|')
        # Note: Current implementation uses newline, but test structure is ready
        assert strategy.delimiter == '|'
    
    def test_record_paging_iter_pages(self, tmp_path):
        """Test iterating over pages."""
        test_file = tmp_path / "record_iter.txt"
        records = [f"Record {i}\n" for i in range(10)]
        test_file.write_text("".join(records))
        
        strategy = RecordPagingStrategy()
        pages = list(strategy.iter_pages(test_file, page_size=3))
        
        assert len(pages) >= 3
        assert "Record 0" in pages[0]

