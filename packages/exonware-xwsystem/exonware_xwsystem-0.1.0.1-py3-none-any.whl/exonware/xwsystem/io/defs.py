"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

IO module definitions - ALL enums and types in ONE place.

Consolidated from all submodules for maintainability.
"""

from enum import Enum, IntEnum, Flag, IntFlag, auto
from typing import Any, Optional
from dataclasses import dataclass


# From ROOT
class FileMode(Enum):
    """File operation modes."""
    READ = "r"
    WRITE = "w"
    APPEND = "a"
    READ_WRITE = "r+"
    WRITE_READ = "w+"
    APPEND_READ = "a+"
    BINARY_READ = "rb"
    BINARY_WRITE = "wb"
    BINARY_APPEND = "ab"
    BINARY_READ_WRITE = "rb+"
    BINARY_WRITE_READ = "wb+"
    BINARY_APPEND_READ = "ab+"


# From ROOT
class FileType(Enum):
    """File types."""
    TEXT = "text"
    BINARY = "binary"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    CSV = "csv"
    CONFIG = "config"
    LOG = "log"
    TEMP = "temp"
    BACKUP = "backup"


# From ROOT
class PathType(Enum):
    """Path types."""
    FILE = "file"
    DIRECTORY = "directory"
    LINK = "link"
    UNKNOWN = "unknown"


# From ROOT  
class OperationResult(Enum):
    """Operation result status."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    SKIPPED = "skipped"


# From ROOT
class LockType(Enum):
    """Lock types for file operations."""
    SHARED = "shared"
    EXCLUSIVE = "exclusive"
    NONE = "none"


# From common
class AtomicMode(Enum):
    """Atomic operation modes."""
    WRITE = "write"              # Write with temp file
    WRITE_BACKUP = "write_backup"  # Write with backup
    MOVE = "move"                # Atomic move
    COPY = "copy"                # Atomic copy


# From common
class WatcherEvent(Enum):
    """File watcher event types."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


# From common
class LockMode(Enum):
    """File lock modes."""
    EXCLUSIVE = "exclusive"      # Exclusive lock
    SHARED = "shared"            # Shared lock
    BLOCKING = "blocking"        # Block until acquired
    NON_BLOCKING = "non_blocking"  # Return immediately


# From common
class PathSecurityLevel(Enum):
    """Path validation security levels."""
    STRICT = "strict"            # Maximum validation
    MODERATE = "moderate"        # Standard validation
    RELAXED = "relaxed"          # Minimal validation
    DISABLED = "disabled"        # No validation (unsafe!)



# From file
class PagingMode(Enum):
    """Paging strategies for file reading."""
    BYTE = "byte"                # Page by byte offsets
    LINE = "line"                # Page by line counts
    RECORD = "record"            # Page by record boundaries
    SMART = "smart"              # Adaptive paging
    AUTO = "auto"                # Auto-detect best strategy


# From file
class FileEncoding(Enum):
    """Common file encodings."""
    UTF8 = "utf-8"
    UTF16 = "utf-16"
    UTF32 = "utf-32"
    ASCII = "ascii"
    LATIN1 = "latin-1"
    CP1252 = "cp1252"



# From folder
class TraversalMode(Enum):
    """Directory traversal modes."""
    DEPTH_FIRST = "depth_first"
    BREADTH_FIRST = "breadth_first"
    FILES_ONLY = "files_only"
    DIRS_ONLY = "dirs_only"



# From stream
class StreamMode(Enum):
    """Stream operation modes."""
    SYNC = "sync"
    ASYNC = "async"


# From stream
class CodecIOMode(Enum):
    """Codec I/O modes."""
    FULL = "full"        # Load entire file
    PAGED = "paged"      # Page by page
    STREAMING = "streaming"  # Stream items



# From filesystem
class FSScheme(Enum):
    """Filesystem scheme types."""
    FILE = "file"        # Local filesystem
    S3 = "s3"            # Amazon S3
    FTP = "ftp"          # FTP
    SFTP = "sftp"        # SFTP
    HTTP = "http"        # HTTP
    ZIP = "zip"          # ZIP archive as FS
    MEM = "mem"          # In-memory FS



# From archive
class ArchiveFormat(Enum):
    """
    Archive format types.
    
    Current: ZIP, TAR
    Future: 7Z, RAR, CAB, ISO, etc.
    """
    ZIP = "zip"
    TAR = "tar"
    TAR_GZ = "tar.gz"
    TAR_BZ2 = "tar.bz2"
    TAR_XZ = "tar.xz"
    
    # Future formats (extensible!)
    SEVEN_ZIP = "7z"        # 7-Zip
    RAR = "rar"             # WinRAR
    CAB = "cab"             # Cabinet
    ISO = "iso"             # ISO image
    ARJ = "arj"             # ARJ
    LZH = "lzh"             # LHA/LZH
    ACE = "ace"             # ACE


# From archive
class CompressionAlgorithm(Enum):
    """
    Compression algorithm types.
    
    Current: gzip, bz2, lzma
    Future: zstd, brotli, snappy, lz4, etc.
    """
    NONE = "none"
    GZIP = "gzip"
    BZ2 = "bz2"
    LZMA = "lzma"
    
    # Future algorithms (extensible!)
    ZSTD = "zstd"           # Zstandard (faster than gzip)
    BROTLI = "brotli"       # Brotli (Google)
    SNAPPY = "snappy"       # Snappy (fast)
    LZ4 = "lz4"             # LZ4 (very fast)
    XZ = "xz"               # XZ (high compression)


# From archive
class CompressionLevel(Enum):
    """Compression level presets."""
    FAST = 1                # Fastest compression
    BALANCED = 6            # Balance speed/size
    BEST = 9                # Best compression



# From manager
class ManagerMode(Enum):
    """Manager operation modes."""
    STRICT = "strict"
    RELAXED = "relaxed"


# From codec
class CodecCapability(Flag):
    """Codec capabilities for introspection."""
    STREAMING = auto()
    BIDIRECTIONAL = auto()
    SCHEMA_BASED = auto()
    BINARY_OUTPUT = auto()
    TEXT_OUTPUT = auto()
    COMPRESSION = auto()


class CodecCategory(Enum):
    """
    Codec categories for format conversion compatibility.
    
    Formats can only convert within the same category:
    - ARCHIVE: zip ↔ 7z ✓ (both archives)
    - SERIALIZATION: json ↔ yaml ✓ (both serialization)
    - ARCHIVE ↔ SERIALIZATION: ✗ (incompatible)
    """
    SERIALIZATION = "serialization"  # json, yaml, xml, toml, pickle
    ARCHIVE = "archive"              # zip, 7z, tar, rar, zst
    FORMATTER = "formatter"          # sql, html, markdown
    ENCRYPTION = "encryption"        # aes, rsa
    ENCODING = "encoding"            # base64, hex, url
    COMPRESSION = "compression"      # gzip, bz2, lzma (raw compression)
