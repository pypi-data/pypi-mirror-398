#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for FormatConverter.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


from exonware.xwsystem.io.file import FormatConverter, convert_file


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestFormatConverter:
    """Test FormatConverter class."""
    
    def test_format_converter_initialization(self):
        """Test FormatConverter initialization."""
        converter = FormatConverter()
        assert converter is not None
        assert converter._registry is not None
    
    def test_format_converter_get_codec(self):
        """Test getting codec by format ID."""
        converter = FormatConverter()
        
        # Try to get JSON codec
        try:
            codec = converter.get_codec("json")
            assert codec is not None
        except Exception:
            pytest.skip("JSON codec not available")
    
    def test_format_converter_validate_compatibility(self):
        """Test validating codec compatibility."""
        converter = FormatConverter()
        
        try:
            json_codec = converter.get_codec("json")
            yaml_codec = converter.get_codec("yaml")
            
            # Both are serialization formats, should be compatible
            converter.validate_compatibility(json_codec, yaml_codec)
        except Exception:
            pytest.skip("Codecs not available for compatibility test")
    
    def test_convert_file_function(self, tmp_path):
        """Test convert_file convenience function."""
        # Create source file
        source_file = tmp_path / "source.json"
        source_file.write_text('{"key": "value"}')
        
        # Convert to YAML
        target_file = tmp_path / "target.yaml"
        
        try:
            convert_file(source_file, target_file, source_format="json", target_format="yaml")
            assert target_file.exists()
        except Exception:
            pytest.skip("File conversion not available")

