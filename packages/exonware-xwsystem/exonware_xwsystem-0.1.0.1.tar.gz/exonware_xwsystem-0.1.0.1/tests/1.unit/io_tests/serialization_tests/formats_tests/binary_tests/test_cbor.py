#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for CBOR serializer.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_serialization
class TestCborSerializer:
    """Test CBOR serializer."""
    
    def test_cbor_serializer_roundtrip(self, tmp_path):
        """Test CBOR serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.binary.cbor import CborSerializer
            
            serializer = CborSerializer()
            test_file = tmp_path / "test.cbor"
            test_data = {"key": "value", "number": 42}
            
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            
            assert loaded == test_data
        except ImportError:
            pytest.skip("CBOR serializer not available")

