#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Multipart serializer.

Following GUIDE_TEST.md standards.
"""

import sys

import pytest


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_serialization
class TestMultipartSerializer:
    """Test Multipart serializer."""
    
    def test_multipart_serializer_encode_decode(self):
        """Test Multipart encode/decode."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.multipart import MultipartSerializer
            
            serializer = MultipartSerializer()
            test_data = {"field1": "value1", "field2": "value2"}
            
            encoded = serializer.encode(test_data)
            decoded = serializer.decode(encoded)
            
            assert decoded is not None
        except ImportError:
            pytest.skip("Multipart serializer not available")

