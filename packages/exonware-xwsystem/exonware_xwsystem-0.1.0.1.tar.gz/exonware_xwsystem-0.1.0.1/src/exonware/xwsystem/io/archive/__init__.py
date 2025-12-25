#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/__init__.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Archive and compression with REGISTRY PATTERN!

Like codec system - auto-detection and extensibility!

Priority 1 (Security): Safe archive operations
Priority 2 (Usability): Auto-detect format from extension
Priority 3 (Maintainability): Clean registry pattern
Priority 4 (Performance): Efficient compression
Priority 5 (Extensibility): Easy to add 7z, RAR, zstd, etc.
"""

# Contracts
from ..contracts import (
    IArchiveFormat,
    ICompressor,
    IArchiveMetadata,
)

# Definitions
from ..defs import (
    ArchiveFormat,
    CompressionAlgorithm,
    CompressionLevel,
)

# Base classes + registries
from .base import (
    AArchiveFormat,
    ACompressor,
    ArchiveFormatRegistry,
    CompressionRegistry,
    get_global_archive_registry,
    get_global_compression_registry,
)

# Errors
from ..errors import (
    ArchiveError,
    ArchiveFormatError,
    ArchiveNotFoundError,
    ExtractionError,
    CompressionError,
    DecompressionError,
)

# Format implementations + registry functions
from .formats import (
    get_archiver_for_file,
    get_archiver_by_id,
    register_archive_format,
)

# NEW: Archivers (Codecs - In-memory) - I→A→XW pattern
from .archivers import ZipArchiver, TarArchiver

# NEW: Archive Files (File persistence) - I→A→XW pattern
from .archive_files import ZipFile, TarFile

# Facades
from .archive import Archive
from .compression import Compression

# IMPORTANT: Register archivers with CodecRegistry for conversion support
from . import codec_integration  # Registers all archivers as codecs


__all__ = [
    # Contracts
    "IArchiveFormat",
    "ICompressor",
    "IArchiveMetadata",
    
    # Definitions
    "ArchiveFormat",
    "CompressionAlgorithm",
    "CompressionLevel",
    
    # Base classes
    "AArchiveFormat",
    "ACompressor",
    
    # Registries
    "ArchiveFormatRegistry",
    "CompressionRegistry",
    "get_global_archive_registry",
    "get_global_compression_registry",
    
    # Errors
    "ArchiveError",
    "ArchiveFormatError",
    "ArchiveNotFoundError",
    "ExtractionError",
    "CompressionError",
    "DecompressionError",
    
    # Archivers (Codecs - In-memory) - I→A→XW pattern
    "ZipArchiver",
    "TarArchiver",
    
    # Archive Files (File persistence)
    "ZipFile",
    "TarFile",
    
    # Registry functions
    "get_archiver_for_file",
    "get_archiver_by_id",
    "register_archive_format",
    
    # Facades
    "Archive",
    "Compression",
]