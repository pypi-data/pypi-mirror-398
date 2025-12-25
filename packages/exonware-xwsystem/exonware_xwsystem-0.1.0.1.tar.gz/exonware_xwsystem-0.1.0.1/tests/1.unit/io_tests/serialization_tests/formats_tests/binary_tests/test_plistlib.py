#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for PlistLib serializer.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_serialization
class TestPlistSerializer:
    """Test PlistLib serializer."""
    
    def test_plist_serializer_roundtrip(self, tmp_path):
        """Test PlistLib serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.binary.plistlib import PlistSerializer
            
            serializer = PlistSerializer()
            test_file = tmp_path / "test.plist"
            test_data = {"key": "value", "number": 42}
            
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            
            assert loaded == test_data
        except ImportError:
            pytest.skip("PlistLib serializer not available")

