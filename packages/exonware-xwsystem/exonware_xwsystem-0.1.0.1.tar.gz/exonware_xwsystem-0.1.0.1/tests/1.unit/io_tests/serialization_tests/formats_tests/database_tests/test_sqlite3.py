#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for SQLite3 serializer.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_serialization
class TestSqlite3Serializer:
    """Test SQLite3 serializer."""
    
    def test_sqlite3_serializer_roundtrip(self, tmp_path):
        """Test SQLite3 serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.database.sqlite3 import Sqlite3Serializer
            
            serializer = Sqlite3Serializer()
            test_file = tmp_path / "test.db"
            test_data = {"key": "value", "number": 42}
            
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            
            assert loaded == test_data
        except ImportError:
            pytest.skip("SQLite3 serializer not available")

