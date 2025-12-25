#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Shelve serializer.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_serialization
class TestShelveSerializer:
    """Test Shelve serializer."""
    
    def test_shelve_serializer_roundtrip(self, tmp_path):
        """Test Shelve serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.database.shelve import ShelveSerializer
            
            serializer = ShelveSerializer()
            test_file = tmp_path / "test.shelf"
            test_data = {"key": "value", "number": 42}
            
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            
            assert loaded == test_data
        except ImportError:
            pytest.skip("Shelve serializer not available")

