#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for DBM serializer.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_serialization
class TestDbmSerializer:
    """Test DBM serializer."""
    
    def test_dbm_serializer_roundtrip(self, tmp_path):
        """Test DBM serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.database.dbm import DbmSerializer
            
            serializer = DbmSerializer()
            test_file = tmp_path / "test.dbm"
            test_data = {"key": "value", "number": 42}
            
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            
            assert loaded == test_data
        except ImportError:
            pytest.skip("DBM serializer not available")

