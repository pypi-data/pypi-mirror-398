#!/usr/bin/env python3
"""Integration tests for archive format conversion workflows."""

import pytest

from exonware.xwsystem.io.file import XWFile, FormatConverter
from exonware.xwsystem.io.codec.base import get_global_registry
from exonware.xwsystem.io.defs import CodecCategory
from exonware.xwsystem.io.archive.archivers import ZipArchiver


def test_archiver_registration_in_registry():
    """Ensure archive formats are registered with the global codec registry."""
    registry = get_global_registry()

    zip_codec = registry.get_by_id("zip")
    tar_codec = registry.get_by_id("tar")

    assert zip_codec is not None
    assert tar_codec is not None

    if hasattr(zip_codec, "category"):
        assert zip_codec.category == CodecCategory.ARCHIVE
    if hasattr(tar_codec, "category"):
        assert tar_codec.category == CodecCategory.ARCHIVE


def test_validate_archive_compatibility():
    """Validate archive-to-archive compatibility via FormatConverter."""
    registry = get_global_registry()
    zip_codec = registry.get_by_id("zip")
    tar_codec = registry.get_by_id("tar")
    converter = FormatConverter()

    assert zip_codec is not None and tar_codec is not None
    converter.validate_compatibility(zip_codec, tar_codec)


def test_zip_to_tar_conversion(tmp_path):
    """Convert a zip archive to tar using both static and instance APIs."""
    test_file = tmp_path / "payload.txt"
    test_file.write_text("Test content for compression")

    zip_archiver = ZipArchiver()
    zip_data = zip_archiver.compress({"payload.txt": test_file.read_bytes()})
    zip_path = tmp_path / "payload.zip"
    zip_path.write_bytes(zip_data)

    tar_path = tmp_path / "payload.tar"
    XWFile.convert(zip_path, tar_path, source_format="zip", target_format="tar")
    assert tar_path.exists()
    assert tar_path.stat().st_size > 0

    tar_path_2 = tmp_path / "payload_copy.tar"
    XWFile(zip_path).save_as(tar_path_2, target_format="tar")
    assert tar_path_2.exists()
    assert tar_path_2.stat().st_size > 0

