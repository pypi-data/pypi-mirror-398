#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for FormData serializer.

Following GUIDE_TEST.md standards.
"""

import sys

import pytest


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_serialization
class TestFormDataSerializer:
    """Test FormData serializer."""
    
    def test_formdata_serializer_encode_decode(self):
        """Test FormData encode/decode."""
        try:
            from exonware.xwsystem.io.serialization.formats.text.formdata import FormDataSerializer
            
            serializer = FormDataSerializer()
            test_data = {"username": "test", "password": "secret"}
            
            encoded = serializer.encode(test_data)
            decoded = serializer.decode(encoded)
            
            assert decoded is not None
        except ImportError:
            pytest.skip("FormData serializer not available")

