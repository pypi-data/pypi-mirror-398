"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

I/O utilities for safe file operations, path management, and codec integration.

FINAL CLEAN STRUCTURE:
├── contracts.py     - ALL interfaces in ONE file
├── defs.py          - ALL enums in ONE file
├── errors.py        - ALL exceptions in ONE file
├── base.py          - Root base classes
├── codec/           - Codec abstractions
├── common/          - Shared utilities (atomic, path, watcher, lock)
├── file/            - File-specific implementations + modular paging
├── folder/          - Folder-specific implementations
├── stream/          - Stream operations + codec integration
├── filesystem/      - Virtual filesystem abstractions
├── archive/         - Archive + compression (registry-based)
└── manager/         - High-level managers

Priority 1 (Security): Safe operations, validation, atomic writes
Priority 2 (Usability): Clean organization, easy imports
Priority 3 (Maintainability): No duplication, single source of truth
Priority 4 (Performance): Efficient imports, registry patterns
Priority 5 (Extensibility): Modular design, easy to extend
"""

# ═══════════════════════════════════════════════════════════════════════
# ROOT LEVEL - Core Definitions (1 defs, 1 errors, 1 contracts)
# ═══════════════════════════════════════════════════════════════════════

from .defs import (
    FileMode, FileType, PathType, OperationResult, LockType,
    AtomicMode, WatcherEvent, LockMode, PathSecurityLevel,
    PagingMode, FileEncoding, TraversalMode, StreamMode,
    CodecIOMode, FSScheme, ArchiveFormat, CompressionAlgorithm,
    CompressionLevel, ManagerMode,
)

from .errors import (
    FileNotFoundError as XWFileNotFoundError,
    FilePermissionError as XWPermissionError,
    FileLockError, FileReadError, FileWriteError,
)

from .contracts import (
    # Original interfaces
    IFile, IFolder, IPath, IStream, IAsyncIO,
    IAtomicOperations, IBackupOperations, ITemporaryOperations,
    IUnifiedIO, IFileManager,
    # New interfaces
    IDataSource, IPagedDataSource,
    ICodecIO, IPagedCodecIO,
    IFileWatcher, IFileLock, IFileSystem,
    IArchiver, IArchiveFile, ICompression,
)

from .base import (
    AFile, AFolder, APath, AStream, AAsyncIO,
    AAtomicOperations, ABackupOperations, ATemporaryOperations,
    AUnifiedIO, AFileManager,
)

# ═══════════════════════════════════════════════════════════════════════
# COMMON - Shared Utilities
# ═══════════════════════════════════════════════════════════════════════

from .common import (
    AtomicFileWriter, FileOperationError,
    safe_read_bytes, safe_read_text, safe_read_with_fallback,
    safe_write_bytes, safe_write_text,
    PathManager, FileWatcher, FileLock,
)

# ═══════════════════════════════════════════════════════════════════════
# FILE - File Operations + Modular Paging
# ═══════════════════════════════════════════════════════════════════════

from .file import (
    FileDataSource, PagedFileSource, XWFile,
    # Paging strategies
    BytePagingStrategy, LinePagingStrategy, RecordPagingStrategy,
    # Paging registry
    PagingStrategyRegistry, get_global_paging_registry,
    register_paging_strategy, get_paging_strategy, auto_detect_paging_strategy,
)

# ═══════════════════════════════════════════════════════════════════════
# FOLDER - Folder Operations
# ═══════════════════════════════════════════════════════════════════════

from .folder import XWFolder

# ═══════════════════════════════════════════════════════════════════════
# STREAM - Stream + Codec Integration
# ═══════════════════════════════════════════════════════════════════════

from .stream import (
    CodecIO, PagedCodecIO, AsyncAtomicFileWriter,
)

# ═══════════════════════════════════════════════════════════════════════
# FILESYSTEM - Virtual Filesystem
# ═══════════════════════════════════════════════════════════════════════

from .filesystem import LocalFileSystem

# ═══════════════════════════════════════════════════════════════════════
# ARCHIVE - Archive + Compression (Registry-based)
# ═══════════════════════════════════════════════════════════════════════

from .archive import (
    # Legacy Archive
    Archive, Compression,
    # Archivers (Codecs - In-memory)
    ZipArchiver, TarArchiver,
    # Archive Files (File persistence)
    ZipFile, TarFile,
    # Registry
    ArchiveFormatRegistry, get_global_archive_registry,
    register_archive_format, get_archiver_for_file,
)

# ═══════════════════════════════════════════════════════════════════════
# FACADE - Main Facade (MANDATORY Pattern)
# ═══════════════════════════════════════════════════════════════════════

from .facade import XWIO

# ═══════════════════════════════════════════════════════════════════════
# CODEC - Codec System Integration
# ═══════════════════════════════════════════════════════════════════════

from .codec.contracts import ICodec, ICodecMetadata
from .codec.base import ACodec
from .codec.registry import UniversalCodecRegistry, get_registry

# Type aliases for backward compatibility
from .contracts import EncodeOptions, DecodeOptions, Serializer, Formatter

# ═══════════════════════════════════════════════════════════════════════
# SERIALIZATION - All Serialization Formats (29+ formats)
# ═══════════════════════════════════════════════════════════════════════

from . import serialization
from .serialization import (
    ISerialization, ASerialization,
    SerializationRegistry, get_serialization_registry,
)

__all__ = [
    # Enums/Types
    "FileMode", "FileType", "PathType", "OperationResult", "LockType",
    "AtomicMode", "WatcherEvent", "LockMode", "PathSecurityLevel",
    "PagingMode", "FileEncoding", "TraversalMode", "StreamMode",
    "CodecIOMode", "FSScheme", "ArchiveFormat", "CompressionAlgorithm",
    "CompressionLevel", "ManagerMode",
    
    # Errors
    "XWFileNotFoundError", "XWPermissionError",
    "FileLockError", "FileReadError", "FileWriteError",
    
    # Interfaces
    "IFile", "IFolder", "IPath", "IStream", "IAsyncIO",
    "IAtomicOperations", "IBackupOperations", "ITemporaryOperations",
    "IUnifiedIO", "IFileManager",
    "IDataSource", "IPagedDataSource",
    "ICodecIO", "IPagedCodecIO",
    "IFileWatcher", "IFileLock", "IFileSystem",
    "IArchiver", "IArchiveFile", "ICompression",
    
    # Base classes
    "AFile", "AFolder", "APath", "AStream", "AAsyncIO",
    "AAtomicOperations", "ABackupOperations", "ATemporaryOperations",
    "AUnifiedIO", "AFileManager",
    
    # Common utilities
    "AtomicFileWriter", "FileOperationError",
    "safe_read_bytes", "safe_read_text", "safe_read_with_fallback",
    "safe_write_bytes", "safe_write_text",
    "PathManager", "FileWatcher", "FileLock",
    
    # File operations
    "FileDataSource", "PagedFileSource", "XWFile",
    "BytePagingStrategy", "LinePagingStrategy", "RecordPagingStrategy",
    "PagingStrategyRegistry", "get_global_paging_registry",
    "register_paging_strategy", "get_paging_strategy", "auto_detect_paging_strategy",
    
    # Folder operations
    "XWFolder",
    
    # Stream operations
    "CodecIO", "PagedCodecIO", "AsyncAtomicFileWriter",
    
    # Filesystem
    "LocalFileSystem",
    
    # Archive + Compression
    "Archive", "Compression",
    "ZipArchiver", "TarArchiver",
    "ZipFile", "TarFile",
    "ArchiveFormatRegistry", "get_global_archive_registry",
    "register_archive_format", "get_archiver_for_file",
    
    # Facade (MANDATORY)
    "XWIO",
    
    # Codec system
    "ICodec", "ICodecMetadata", "ACodec",
    "UniversalCodecRegistry", "get_registry",
    "EncodeOptions", "DecodeOptions",
    "Serializer", "Formatter",
    
    # Serialization module (29+ formats)
    "serialization",
    "ISerialization", "ASerialization",
    "SerializationRegistry", "get_serialization_registry",
]
