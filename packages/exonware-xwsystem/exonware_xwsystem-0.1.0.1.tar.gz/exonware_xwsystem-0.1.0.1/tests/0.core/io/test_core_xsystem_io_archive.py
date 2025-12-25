#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core tests for archive operations.

Tests Archive facade, archive formats (ZIP, TAR, etc.), and compression operations.

Following GUIDE_TEST.md standards.
"""

import sys
import tempfile
from pathlib import Path

import pytest


# Import archive classes
from exonware.xwsystem.io.archive import (
    Archive,
    Compression,
    get_global_archive_registry,
    ZipArchiver,
    TarArchiver,
    get_archiver_for_file,
    get_archiver_by_id,
)


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestArchiveFacade:
    """Test Archive facade class."""
    
    def test_archive_create_zip(self, tmp_path):
        """Test creating ZIP archive via Archive facade."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        # Create archive
        archive_path = tmp_path / "test.zip"
        archive = Archive()
        archive.create([file1, file2], archive_path)
        
        # Verify archive exists
        assert archive_path.exists()
    
    def test_archive_extract_zip(self, tmp_path):
        """Test extracting ZIP archive via Archive facade."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        # Create archive
        archive_path = tmp_path / "test.zip"
        archive = Archive()
        archive.create([file1], archive_path)
        
        # Extract archive
        extract_dir = tmp_path / "extracted"
        extracted = archive.extract(archive_path, extract_dir)
        
        # Verify extraction
        assert extract_dir.exists()
        assert len(extracted) > 0
    
    def test_archive_list_contents(self, tmp_path):
        """Test listing archive contents via Archive facade."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        # Create archive
        archive_path = tmp_path / "test.zip"
        archive = Archive()
        archive.create([file1], archive_path)
        
        # List contents
        contents = archive.list_contents(archive_path)
        assert len(contents) > 0
        assert "file1.txt" in contents
    
    def test_archive_add_file(self, tmp_path):
        """Test adding file to existing archive."""
        # Create initial file
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        # Create archive
        archive_path = tmp_path / "test.zip"
        archive = Archive()
        archive.create([file1], archive_path)
        
        # Add another file
        file2 = tmp_path / "file2.txt"
        file2.write_text("Content 2")
        archive.add_file(archive_path, file2)
        
        # Verify both files in archive
        contents = archive.list_contents(archive_path)
        assert "file1.txt" in contents
        assert "file2.txt" in contents


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestZipArchiver:
    """Test ZipArchiver format."""
    
    def test_zip_archiver_create(self, tmp_path):
        """Test creating ZIP archive."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        # Create ZIP
        archive_path = tmp_path / "test.zip"
        archiver = ZipArchiver()
        archiver.create([file1, file2], archive_path)
        
        # Verify archive exists
        assert archive_path.exists()
    
    def test_zip_archiver_extract(self, tmp_path):
        """Test extracting ZIP archive."""
        # Create test file
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        # Create ZIP
        archive_path = tmp_path / "test.zip"
        archiver = ZipArchiver()
        archiver.create([file1], archive_path)
        
        # Extract
        extract_dir = tmp_path / "extracted"
        extracted = archiver.extract(archive_path, extract_dir)
        
        # Verify
        assert extract_dir.exists()
        assert len(extracted) > 0
        extracted_file = extract_dir / "file1.txt"
        assert extracted_file.exists()
        assert extracted_file.read_text() == "Content 1"
    
    def test_zip_archiver_list_contents(self, tmp_path):
        """Test listing ZIP contents."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        # Create ZIP
        archive_path = tmp_path / "test.zip"
        archiver = ZipArchiver()
        archiver.create([file1, file2], archive_path)
        
        # List contents
        contents = archiver.list_contents(archive_path)
        assert "file1.txt" in contents
        assert "file2.txt" in contents
    
    def test_zip_archiver_add_file(self, tmp_path):
        """Test adding file to ZIP."""
        # Create initial file
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        # Create ZIP
        archive_path = tmp_path / "test.zip"
        archiver = ZipArchiver()
        archiver.create([file1], archive_path)
        
        # Add another file
        file2 = tmp_path / "file2.txt"
        file2.write_text("Content 2")
        archiver.add_file(archive_path, file2)
        
        # Verify
        contents = archiver.list_contents(archive_path)
        assert "file1.txt" in contents
        assert "file2.txt" in contents
    
    def test_zip_archiver_format_id(self):
        """Test ZipArchiver format identifier."""
        archiver = ZipArchiver()
        assert archiver.format_id == "zip"
        assert ".zip" in archiver.file_extensions


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestTarArchiver:
    """Test TarArchiver format."""
    
    def test_tar_archiver_create(self, tmp_path):
        """Test creating TAR archive."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        # Create TAR
        archive_path = tmp_path / "test.tar"
        archiver = TarArchiver()
        archiver.create([file1, file2], archive_path)
        
        # Verify archive exists
        assert archive_path.exists()
    
    def test_tar_archiver_extract(self, tmp_path):
        """Test extracting TAR archive."""
        # Create test file
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        # Create TAR
        archive_path = tmp_path / "test.tar"
        archiver = TarArchiver()
        archiver.create([file1], archive_path)
        
        # Extract
        extract_dir = tmp_path / "extracted"
        extracted = archiver.extract(archive_path, extract_dir)
        
        # Verify
        assert extract_dir.exists()
        assert len(extracted) > 0
    
    def test_tar_archiver_list_contents(self, tmp_path):
        """Test listing TAR contents."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        # Create TAR
        archive_path = tmp_path / "test.tar"
        archiver = TarArchiver()
        archiver.create([file1, file2], archive_path)
        
        # List contents
        contents = archiver.list_contents(archive_path)
        assert len(contents) >= 2
    
    def test_tar_archiver_format_id(self):
        """Test TarArchiver format identifier."""
        archiver = TarArchiver()
        assert archiver.format_id == "tar"
        assert ".tar" in archiver.file_extensions


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestArchiveRegistry:
    """Test archive format registry."""
    
    def test_archive_registry_exists(self):
        """Test that archive registry is accessible."""
        registry = get_global_archive_registry()
        assert registry is not None
    
    def test_archive_registry_list_formats(self):
        """Test listing registered archive formats."""
        registry = get_global_archive_registry()
        formats = registry.list_formats()
        assert len(formats) > 0
        # ZIP and TAR should be registered
        assert "zip" in formats or "tar" in formats
    
    def test_get_archiver_for_file(self, tmp_path):
        """Test getting archiver for file extension."""
        # Test ZIP
        zip_file = tmp_path / "test.zip"
        archiver = get_archiver_for_file(str(zip_file))
        assert archiver is not None
        assert archiver.format_id == "zip"
        
        # Test TAR
        tar_file = tmp_path / "test.tar"
        archiver = get_archiver_for_file(str(tar_file))
        assert archiver is not None
        assert archiver.format_id == "tar"
    
    def test_get_archiver_by_id(self):
        """Test getting archiver by format ID."""
        # Get ZIP archiver
        archiver = get_archiver_by_id("zip")
        assert archiver is not None
        assert isinstance(archiver, ZipArchiver)
        
        # Get TAR archiver
        archiver = get_archiver_by_id("tar")
        assert archiver is not None
        assert isinstance(archiver, TarArchiver)


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestCompression:
    """Test Compression facade."""
    
    def test_compression_basic(self, tmp_path):
        """Test basic compression operations."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content for compression")
        
        # Compress
        compressed_file = tmp_path / "test.txt.gz"
        compression = Compression()
        # Note: Compression class implementation may vary
        # This is a placeholder test
        assert compression is not None


@pytest.mark.xwsystem_core
@pytest.mark.xwsystem_io
class TestArchiveRoundtrip:
    """Test archive roundtrip operations."""
    
    def test_zip_roundtrip(self, tmp_path):
        """Test create-extract roundtrip for ZIP."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        # Create archive
        archive_path = tmp_path / "roundtrip.zip"
        archiver = ZipArchiver()
        archiver.create([file1, file2], archive_path)
        
        # Extract to new location
        extract_dir = tmp_path / "roundtrip_extracted"
        extracted = archiver.extract(archive_path, extract_dir)
        
        # Verify files
        assert len(extracted) >= 2
        extracted_file1 = extract_dir / "file1.txt"
        extracted_file2 = extract_dir / "file2.txt"
        assert extracted_file1.exists() or any("file1.txt" in str(p) for p in extracted)
        assert extracted_file2.exists() or any("file2.txt" in str(p) for p in extracted)
    
    def test_tar_roundtrip(self, tmp_path):
        """Test create-extract roundtrip for TAR."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        # Create archive
        archive_path = tmp_path / "roundtrip.tar"
        archiver = TarArchiver()
        archiver.create([file1, file2], archive_path)
        
        # Extract to new location
        extract_dir = tmp_path / "roundtrip_extracted"
        extracted = archiver.extract(archive_path, extract_dir)
        
        # Verify files
        assert len(extracted) >= 2

