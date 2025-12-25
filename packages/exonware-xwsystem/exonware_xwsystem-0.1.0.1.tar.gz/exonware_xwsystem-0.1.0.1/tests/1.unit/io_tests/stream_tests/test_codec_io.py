#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for CodecIO.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest

from exonware.xwsystem.io.stream import CodecIO
from exonware.xwsystem.io.file import FileDataSource


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestCodecIO:
    """Test CodecIO class."""
    
    def test_codec_io_initialization(self, tmp_path):
        """Test CodecIO initialization."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
            
            test_file = tmp_path / "codec_io.json"
            codec = JsonSerializer()
            source = FileDataSource(test_file)
            codec_io = CodecIO(codec, source)
            
            assert codec_io.codec is codec
            assert codec_io.source is source
        except ImportError:
            pytest.skip("JSON serializer not available")
    
    def test_codec_io_save(self, tmp_path):
        """Test saving via CodecIO."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
            
            test_file = tmp_path / "codec_save.json"
            codec = JsonSerializer()
            source = FileDataSource(test_file)
            codec_io = CodecIO(codec, source)
            
            data = {"key": "value"}
            codec_io.save(data)
            
            assert test_file.exists()
        except ImportError:
            pytest.skip("JSON serializer not available")
    
    def test_codec_io_load(self, tmp_path):
        """Test loading via CodecIO."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
            
            test_file = tmp_path / "codec_load.json"
            test_file.write_text('{"key": "value"}')
            
            codec = JsonSerializer()
            source = FileDataSource(test_file)
            codec_io = CodecIO(codec, source)
            
            data = codec_io.load()
            assert data == {"key": "value"}
        except ImportError:
            pytest.skip("JSON serializer not available")
    
    def test_codec_io_exists(self, tmp_path):
        """Test checking existence via CodecIO."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.json import JsonSerializer
            
            test_file = tmp_path / "codec_exists.json"
            codec = JsonSerializer()
            source = FileDataSource(test_file)
            codec_io = CodecIO(codec, source)
            
            assert codec_io.exists() is False
            
            test_file.write_text("{}")
            assert codec_io.exists() is True
        except ImportError:
            pytest.skip("JSON serializer not available")

