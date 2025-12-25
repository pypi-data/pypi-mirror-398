#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for folder base classes.

Following GUIDE_TEST.md standards.
"""

import sys

import pytest

from exonware.xwsystem.io.folder.base import AFolderSource


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestAFolderSource:
    """Test AFolderSource base class."""
    
    def test_afolder_source_initialization(self, tmp_path):
        """Test base class initialization."""
        folder_path = tmp_path / "base_folder"
        # Note: AFolderSource is abstract, so we test through XWFolder
        from exonware.xwsystem.io.folder import XWFolder
        
        folder = XWFolder(folder_path)
        assert folder.dir_path == folder_path

