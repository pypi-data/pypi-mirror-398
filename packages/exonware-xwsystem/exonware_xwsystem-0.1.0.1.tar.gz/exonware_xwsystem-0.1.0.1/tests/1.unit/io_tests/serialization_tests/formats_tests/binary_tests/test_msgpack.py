#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for MessagePack serializer.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_serialization
class TestMsgPackSerializer:
    """Test MessagePack serializer."""
    
    def test_msgpack_serializer_roundtrip(self, tmp_path):
        """Test MessagePack serializer roundtrip."""
        try:
            from exonware.xwsystem.io.serialization.formats.binary.msgpack import MsgPackSerializer
            
            serializer = MsgPackSerializer()
            test_file = tmp_path / "test.msgpack"
            test_data = {"key": "value", "number": 42}
            
            serializer.save_file(test_data, test_file)
            loaded = serializer.load_file(test_file)
            
            assert loaded == test_data
        except ImportError:
            pytest.skip("MessagePack serializer not available")

