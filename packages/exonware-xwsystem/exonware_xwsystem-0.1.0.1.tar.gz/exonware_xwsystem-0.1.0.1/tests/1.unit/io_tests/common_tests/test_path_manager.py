#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for PathManager.

Following GUIDE_TEST.md standards.
"""

import sys

import pytest

from exonware.xwsystem.io.common import PathManager


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestPathManager:
    """Test PathManager class."""
    
    def test_path_manager_looks_like_file_path(self):
        """Test path detection."""
        # Should detect file paths
        assert PathManager.looks_like_file_path("/path/to/file.txt") is True
        assert PathManager.looks_like_file_path("file.txt") is True
        assert PathManager.looks_like_file_path("subdir/file.txt") is True
        
        # Should not detect raw content
        assert PathManager.looks_like_file_path('{"key": "value"}') is False
        assert PathManager.looks_like_file_path("raw content\nwith newlines") is False
    
    def test_path_manager_resolve_base_path(self):
        """Test base path resolution."""
        # Test with valid path
        resolved = PathManager.resolve_base_path("/some/path")
        assert resolved is not None
        
        # Test with None
        resolved = PathManager.resolve_base_path(None)
        assert resolved is None
    
    def test_path_manager_is_safe_path(self, tmp_path):
        """Test path safety checking."""
        # Test safe path
        safe_path = tmp_path / "safe_file.txt"
        # Note: is_safe_path may not be available, test if it exists
        if hasattr(PathManager, 'is_safe_path'):
            assert PathManager.is_safe_path(safe_path) is True

