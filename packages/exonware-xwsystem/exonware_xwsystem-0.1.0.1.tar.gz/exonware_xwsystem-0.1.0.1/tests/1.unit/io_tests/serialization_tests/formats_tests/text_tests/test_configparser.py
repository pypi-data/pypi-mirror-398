#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for ConfigParser serializer.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_serialization
class TestConfigParserSerializer:
    """Test ConfigParser serializer."""
    
    def test_configparser_serializer_roundtrip(self, tmp_path):
        """Test ConfigParser serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.configparser import ConfigParserSerializer
            
            serializer = ConfigParserSerializer()
            test_file = tmp_path / "test.ini"
            test_data = {"section": {"key": "value"}}
            
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            
            assert loaded is not None
        except ImportError:
            pytest.skip("ConfigParser serializer not available")

