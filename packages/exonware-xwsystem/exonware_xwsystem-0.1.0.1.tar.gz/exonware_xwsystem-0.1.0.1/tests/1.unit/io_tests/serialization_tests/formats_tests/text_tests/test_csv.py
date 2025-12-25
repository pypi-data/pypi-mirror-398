#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for CSV serializer.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_serialization
class TestCsvSerializer:
    """Test CSV serializer."""
    
    def test_csv_serializer_roundtrip(self, tmp_path):
        """Test CSV serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.csv import CsvSerializer
            
            serializer = CsvSerializer()
            test_file = tmp_path / "test.csv"
            # CSV works with list of dicts
            test_data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
            
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            
            assert loaded is not None
        except ImportError:
            pytest.skip("CSV serializer not available")

