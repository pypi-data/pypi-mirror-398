#!/usr/bin/env python3
"""
Core-level sanity checks for IO package reorganisation.
"""

import pytest


@pytest.mark.xwsystem_core
def test_io_module_imports():
    """Ensure top-level IO module and key submodules import cleanly."""
    import exonware.xwsystem.io as io_module  # noqa: F401

    from exonware.xwsystem.io.file import FileDataSource, PagedFileSource, XWFile  # noqa: F401
    from exonware.xwsystem.io.folder import XWFolder  # noqa: F401
    from exonware.xwsystem.io.stream import CodecIO, PagedCodecIO  # noqa: F401
    from exonware.xwsystem.io.archive import Archive, Compression  # noqa: F401
    from exonware.xwsystem.io.filesystem import LocalFileSystem  # noqa: F401
    from exonware.xwsystem.io.common import AtomicFileWriter, FileLock, FileWatcher  # noqa: F401


@pytest.mark.xwsystem_core
def test_io_registries_expose_entries():
    """Verify registry utilities expose non-empty listings."""
    from exonware.xwsystem.io.file import get_global_paging_registry
    from exonware.xwsystem.io.archive import get_global_archive_registry

    paging_reg = get_global_paging_registry()
    archive_reg = get_global_archive_registry()

    assert paging_reg.list_strategies(), "Expected paging strategies to be registered"
    assert archive_reg.list_formats(), "Expected archive formats to be registered"

