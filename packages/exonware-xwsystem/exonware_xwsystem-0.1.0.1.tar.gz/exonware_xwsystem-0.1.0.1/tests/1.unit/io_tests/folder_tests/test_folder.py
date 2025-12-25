#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for XWFolder class.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest

from exonware.xwsystem.io.folder import XWFolder


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestXWFolder:
    """Test XWFolder class."""
    
    def test_xwfolder_initialization(self, tmp_path):
        """Test XWFolder initialization."""
        folder_path = tmp_path / "test_folder"
        folder = XWFolder(folder_path)
        
        assert folder.dir_path == folder_path
    
    def test_xwfolder_create(self, tmp_path):
        """Test creating a folder."""
        folder_path = tmp_path / "create_folder"
        folder = XWFolder(folder_path)
        
        assert folder.create() is True
        assert folder_path.exists()
        assert folder_path.is_dir()
    
    def test_xwfolder_delete(self, tmp_path):
        """Test deleting a folder."""
        folder_path = tmp_path / "delete_folder"
        folder = XWFolder(folder_path)
        folder.create()
        
        assert folder.delete() is True
        assert not folder_path.exists()
    
    def test_xwfolder_delete_recursive(self, tmp_path):
        """Test deleting a folder recursively."""
        folder_path = tmp_path / "recursive_folder"
        folder = XWFolder(folder_path)
        folder.create()
        
        # Create subdirectory and file
        (folder_path / "subdir").mkdir()
        (folder_path / "file.txt").write_text("content")
        
        assert folder.delete(recursive=True) is True
        assert not folder_path.exists()
    
    def test_xwfolder_list_files(self, tmp_path):
        """Test listing files in folder."""
        folder_path = tmp_path / "list_folder"
        folder = XWFolder(folder_path)
        folder.create()
        
        # Create files
        (folder_path / "file1.txt").write_text("content1")
        (folder_path / "file2.txt").write_text("content2")
        
        files = folder.list_files()
        assert len(files) == 2
        assert any("file1.txt" in str(f) for f in files)
        assert any("file2.txt" in str(f) for f in files)
    
    def test_xwfolder_list_directories(self, tmp_path):
        """Test listing directories in folder."""
        folder_path = tmp_path / "list_dirs"
        folder = XWFolder(folder_path)
        folder.create()
        
        # Create subdirectories
        (folder_path / "subdir1").mkdir()
        (folder_path / "subdir2").mkdir()
        
        dirs = folder.list_directories()
        assert len(dirs) == 2
    
    def test_xwfolder_copy_to(self, tmp_path):
        """Test copying folder."""
        source_path = tmp_path / "source_folder"
        dest_path = tmp_path / "dest_folder"
        
        folder = XWFolder(source_path)
        folder.create()
        (source_path / "file.txt").write_text("content")
        
        assert folder.copy_to(dest_path) is True
        assert dest_path.exists()
        assert (dest_path / "file.txt").exists()
    
    def test_xwfolder_move_to(self, tmp_path):
        """Test moving folder."""
        source_path = tmp_path / "source_move"
        dest_path = tmp_path / "dest_move"
        
        folder = XWFolder(source_path)
        folder.create()
        (source_path / "file.txt").write_text("content")
        
        assert folder.move_to(dest_path) is True
        assert not source_path.exists()
        assert dest_path.exists()
    
    def test_xwfolder_get_size(self, tmp_path):
        """Test getting folder size."""
        folder_path = tmp_path / "size_folder"
        folder = XWFolder(folder_path)
        folder.create()
        
        (folder_path / "file.txt").write_text("content")
        size = folder.get_size()
        assert size > 0
    
    def test_xwfolder_is_empty(self, tmp_path):
        """Test checking if folder is empty."""
        folder_path = tmp_path / "empty_folder"
        folder = XWFolder(folder_path)
        folder.create()
        
        assert folder.is_empty() is True
        
        (folder_path / "file.txt").write_text("content")
        assert folder.is_empty() is False

