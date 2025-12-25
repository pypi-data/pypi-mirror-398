#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for BSON serializer.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_serialization
class TestBsonSerializer:
    """Test BSON serializer."""
    
    def test_bson_serializer_roundtrip(self, tmp_path):
        """Test BSON serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.binary.bson import BsonSerializer
            
            serializer = BsonSerializer()
            test_file = tmp_path / "test.bson"
            test_data = {"key": "value", "number": 42}
            
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            
            assert loaded == test_data
        except ImportError:
            pytest.skip("BSON serializer not available")

