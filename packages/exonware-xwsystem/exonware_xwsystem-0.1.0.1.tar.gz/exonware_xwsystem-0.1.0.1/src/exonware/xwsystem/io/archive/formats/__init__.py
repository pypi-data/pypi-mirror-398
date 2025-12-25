#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/formats/__init__.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 1, 2025

Archive format implementations - COMPREHENSIVE 2025 SUPPORT.

Pluggable archive formats registered with ArchiveFormatRegistry.

SUPPORTED FORMATS (Ranked by compression quality):

| Rank | Format         | Type       | Compression       | Use Case                        |
|------|----------------|------------|-------------------|---------------------------------|
| 1    | 7z             | Container  | LZMA2             | Best ratio + AES-256            |
| 2    | Zstandard      | Stream     | Zstd              | Fast modern (backups/DBs)       |
| 3    | RAR5           | Container  | Proprietary       | Strong + recovery               |
| 4    | ZIP/ZIPX       | Container  | Deflate/LZMA      | Widely supported                |
| 5    | tar.zst/tar.xz | Container  | Zstd/LZMA2        | Linux backups                   |
| 6    | Brotli         | Stream     | Brotli            | Web & text assets               |
| 7    | LZ4            | Stream     | LZ4               | Ultra fast real-time            |
| 8    | ZPAQ           | Journaled  | PAQ               | Extreme compression (archival)  |
| 9    | WIM            | Container  | LZX               | Windows system images           |
| 10   | SquashFS       | Filesystem | LZMA/LZ4          | Embedded systems                |

Priority 1 (Security): Safe format operations
Priority 2 (Usability): Auto-registration + lazy install
Priority 3 (Maintainability): Modular formats
Priority 4 (Performance): Efficient format handling
Priority 5 (Extensibility): Easy to add more formats
"""

# Standard formats (always available)
from .zip import ZipArchiver
from .tar import TarArchiver

# Advanced formats (lazy loaded - will be imported on first access)
# This allows lazy mode to install missing dependencies (like wimlib) before import
_advanced_formats = {
    'SevenZipArchiver': ('.sevenzip', 'SevenZipArchiver'),  # RANK #1
    'ZstandardArchiver': ('.zstandard', 'ZstandardArchiver'),  # RANK #2
    'RarArchiver': ('.rar', 'RarArchiver'),  # RANK #3
    'BrotliArchiver': ('.brotli_format', 'BrotliArchiver'),  # RANK #6
    'Lz4Archiver': ('.lz4_format', 'Lz4Archiver'),  # RANK #7
    'ZpaqArchiver': ('.zpaq_format', 'ZpaqArchiver'),  # RANK #8
    'WimArchiver': ('.wim_format', 'WimArchiver'),  # RANK #9
    'SquashfsArchiver': ('.squashfs_format', 'SquashfsArchiver'),  # RANK #10
}

# Auto-register built-in formats
from ..base import get_global_archive_registry

_registry = get_global_archive_registry()

# Register standard formats immediately
_registry.register(ZipArchiver)  # ZIP/ZIPX
_registry.register(TarArchiver)  # TAR variants

# Advanced formats will be registered lazily via __getattr__


# Convenience functions (like codec!)
def get_archiver_for_file(path: str):
    """
    Get archiver by file extension (auto-detection!).
    
    Examples:
        >>> get_archiver_for_file("backup.7z")  # Returns SevenZipArchiver
        >>> get_archiver_for_file("data.tar.zst")  # Returns ZstandardArchiver
    """
    return get_global_archive_registry().get_by_extension(path)


def get_archiver_by_id(format_id: str):
    """
    Get archiver by format ID.
    
    Examples:
        >>> get_archiver_by_id("7z")  # Returns SevenZipArchiver
        >>> get_archiver_by_id("zst")  # Returns ZstandardArchiver
    """
    return get_global_archive_registry().get_by_id(format_id)


def register_archive_format(format_class):
    """Decorator to register custom archive format."""
    get_global_archive_registry().register(format_class)
    return format_class


def __getattr__(name: str):
    """
    Lazy load advanced archive formats on first access.
    
    This allows lazy mode to install missing dependencies (like wimlib, py7zr)
    before the format module is imported.
    """
    if name in _advanced_formats:
        module_path, class_name = _advanced_formats[name]
        # Import module lazily - lazy hook will catch missing dependencies
        module = __import__(f'{__name__}{module_path}', fromlist=[class_name])
        format_class = getattr(module, class_name)
        # Register format on first access
        _registry.register(format_class)
        # Cache for future access
        globals()[name] = format_class
        return format_class
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Standard formats
    "ZipArchiver",
    "TarArchiver",
    
    # Advanced formats (lazy install)
    "SevenZipArchiver",  # RANK #1
    "ZstandardArchiver",  # RANK #2
    "RarArchiver",  # RANK #3
    "BrotliArchiver",  # RANK #6
    "Lz4Archiver",  # RANK #7
    "ZpaqArchiver",  # RANK #8
    "WimArchiver",  # RANK #9
    "SquashfsArchiver",  # RANK #10
    
    # Registry functions
    "get_archiver_for_file",
    "get_archiver_by_id",
    "register_archive_format",
]

