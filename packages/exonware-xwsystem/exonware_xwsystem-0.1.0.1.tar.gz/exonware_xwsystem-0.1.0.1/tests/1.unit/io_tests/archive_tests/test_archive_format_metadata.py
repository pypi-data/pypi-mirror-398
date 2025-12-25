#!/usr/bin/env python3
"""
Unit tests for archive format metadata and discovery.
"""

import pytest

from exonware.xwsystem.io.archive.formats import (
    ZipArchiver,
    TarArchiver,
    SevenZipArchiver,
    ZstandardArchiver,
    RarArchiver,
    BrotliArchiver,
    Lz4Archiver,
    ZpaqArchiver,
    WimArchiver,
    SquashfsArchiver,
    get_archiver_for_file,
    get_archiver_by_id,
)

ARCHIVER_MODULE_PATHS = [
    "exonware.xwsystem.io.archive.formats.zip",
    "exonware.xwsystem.io.archive.formats.tar",
    "exonware.xwsystem.io.archive.formats.sevenzip",
    "exonware.xwsystem.io.archive.formats.zstandard",
    "exonware.xwsystem.io.archive.formats.rar",
    "exonware.xwsystem.io.archive.formats.brotli_format",
    "exonware.xwsystem.io.archive.formats.lz4_format",
    "exonware.xwsystem.io.archive.formats.zpaq_format",
    "exonware.xwsystem.io.archive.formats.wim_format",
    "exonware.xwsystem.io.archive.formats.squashfs_format",
]


ARCHIVER_CASES = [
    (ZipArchiver, "zip", [".zip"]),
    (TarArchiver, "tar", [".tar"]),
    (SevenZipArchiver, "7z", [".7z"]),
    (ZstandardArchiver, "zst", [".zst", ".tar.zst"]),
    (RarArchiver, "rar", [".rar"]),
    (BrotliArchiver, "br", [".br", ".tar.br"]),
    (Lz4Archiver, "lz4", [".lz4", ".tar.lz4"]),
    (ZpaqArchiver, "zpaq", [".zpaq"]),
    (WimArchiver, "wim", [".wim"]),
    (SquashfsArchiver, "squashfs", [".squashfs"]),
]


@pytest.mark.parametrize("module_path", ARCHIVER_MODULE_PATHS)
def test_archiver_modules_importable(module_path):
    """Ensure each archive format module is importable directly."""
    __import__(module_path)


@pytest.mark.parametrize("archiver_cls, expected_id, _", ARCHIVER_CASES)
def test_archiver_classes_importable(archiver_cls, expected_id, _):
    """Verify each archiver class is importable and exposes expected id."""
    archiver = archiver_cls()
    assert archiver.format_id == expected_id


@pytest.mark.parametrize(
    "filename, expected_cls",
    [
        ("backup.7z", SevenZipArchiver),
        ("data.tar.zst", ZstandardArchiver),
        ("archive.rar", RarArchiver),
        ("files.zip", ZipArchiver),
        ("backup.tar.xz", TarArchiver),
        ("web.tar.br", BrotliArchiver),
        ("logs.tar.lz4", Lz4Archiver),
        ("extreme.zpaq", ZpaqArchiver),
        ("system.wim", WimArchiver),
        ("rootfs.squashfs", SquashfsArchiver),
    ],
)
def test_get_archiver_for_file(filename, expected_cls):
    """Ensure get_archiver_for_file resolves the correct archiver class."""
    archiver = get_archiver_for_file(filename)
    assert isinstance(archiver, expected_cls)


@pytest.mark.parametrize(
    "format_id, expected_cls",
    [
        ("7z", SevenZipArchiver),
        ("zst", ZstandardArchiver),
        ("rar", RarArchiver),
        ("zip", ZipArchiver),
        ("tar", TarArchiver),
        ("br", BrotliArchiver),
        ("lz4", Lz4Archiver),
        ("zpaq", ZpaqArchiver),
        ("wim", WimArchiver),
        ("squashfs", SquashfsArchiver),
    ],
)
def test_get_archiver_by_id(format_id, expected_cls):
    """Ensure get_archiver_by_id returns the correct archiver instance."""
    archiver = get_archiver_by_id(format_id)
    assert isinstance(archiver, expected_cls)


@pytest.mark.parametrize("archiver_cls, expected_id, expected_exts", ARCHIVER_CASES)
def test_archiver_metadata(archiver_cls, expected_id, expected_exts):
    """Validate format metadata for each archiver."""
    archiver = archiver_cls()
    assert archiver.format_id == expected_id
    for ext in expected_exts:
        assert ext in archiver.file_extensions

