#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Base classes and registries for archive system.

Like codec/base.py: Contains abstracts + ArchiveFormatRegistry!

Priority 1 (Security): Safe base implementations
Priority 2 (Usability): Auto-detection like codec!
Priority 3 (Maintainability): Clean registry pattern
Priority 4 (Performance): Fast format lookup
Priority 5 (Extensibility): Easy to add 7z, RAR, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional, Union, Any
from pathlib import Path

from ..contracts import IArchiveFormat, ICompressor, IArchiveMetadata, IArchiver, IArchiveFile, EncodeOptions, DecodeOptions
from ..codec.base import ACodec
from ..base import AFile
from ..defs import ArchiveFormat as ArchiveFormatEnum, CompressionAlgorithm, CodecCapability

__all__ = [
    'AArchiveFormat',
    'ACompressor',
    'AArchiver',
    'AArchiveFile',
    'ArchiveFormatRegistry',
    'CompressionRegistry',
    'get_global_archive_registry',
    'get_global_compression_registry',
]


class AArchiveFormat(IArchiveFormat, ABC):
    """Abstract base for archive format handlers."""
    
    @property
    @abstractmethod
    def format_id(self) -> str:
        """Unique format identifier."""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        pass
    
    @property
    def mime_types(self) -> list[str]:
        """Supported MIME types."""
        return []  # Default: no MIME types


class ACompressor(ICompressor, ABC):
    """Abstract base for compression algorithms."""
    
    @property
    @abstractmethod
    def algorithm_id(self) -> str:
        """Unique algorithm identifier."""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        pass


# ============================================================================
# ARCHIVE CODEC ABSTRACT BASE CLASS (I→A→XW Pattern)
# ============================================================================

class AArchiver(ACodec[Any, bytes], IArchiver, ABC):
    """
    Abstract base class for archive codecs - follows I→A→XW pattern.
    
    I: IArchiver (interface)
    A: AArchiver (abstract base - this class)
    XW: XWArchiver implementations (ZipArchiver, TarArchiver, etc.)
    
    Provides default implementations of compress()/extract() that delegate
    to encode()/decode(). Subclasses only need to implement encode/decode
    and metadata properties.
    
    This is for in-memory archive operations - works on data in RAM, not files.
    """
    
    @abstractmethod
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> bytes:
        """Encode data to archive bytes - must implement in subclass."""
        pass
    
    @abstractmethod
    def decode(self, repr: bytes, *, options: Optional[DecodeOptions] = None) -> Any:
        """Decode archive bytes to data - must implement in subclass."""
        pass
    
    @property
    @abstractmethod
    def codec_id(self) -> str:
        """Codec identifier (e.g., 'zip', 'tar')."""
        pass
    
    @property
    @abstractmethod
    def media_types(self) -> list[str]:
        """Supported MIME types."""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        pass
    
    @property
    def capabilities(self) -> CodecCapability:
        """Archive codecs support bidirectional operations."""
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        """Default aliases from codec_id."""
        return [self.codec_id.lower(), self.codec_id.upper()]
    
    @property
    def codec_types(self) -> list[str]:
        """
        Archive codecs are archive type (default).
        
        Override in subclasses for specific types like:
        - ['archive', 'compression']: Archives with compression
        - ['compression']: Pure compression formats
        """
        return ["archive"]
    
    def compress(self, data: Any, **options) -> bytes:
        """
        Compress data to archive bytes (user-friendly API).
        
        Delegates to encode().
        
        Args:
            data: Data to compress (dict, bytes, str, list, etc.)
            **options: Compression options
        
        Returns:
            Archive bytes
        """
        return self.encode(data, options=options or None)
    
    def extract(self, archive_bytes: bytes, **options) -> Any:
        """
        Extract archive bytes to data (user-friendly API).
        
        Delegates to decode().
        
        Args:
            archive_bytes: Archive bytes to extract
            **options: Extraction options
        
        Returns:
            Extracted data
        """
        return self.decode(archive_bytes, options=options or None)


# ============================================================================
# ARCHIVE FILE ABSTRACT BASE CLASS (I→A→XW Pattern)
# ============================================================================

class AArchiveFile(AFile, IArchiveFile, ABC):
    """
    Abstract base class for archive file operations - follows I→A→XW pattern.
    
    I: IArchiveFile (interface)
    A: AArchiveFile (abstract base - this class)
    XW: XWArchiveFile implementations (ZipFile, TarFile, etc.)
    
    Extends AFile for file I/O and provides archive-specific methods.
    Uses composition pattern: contains an IArchiver instance for compression.
    
    This is for file-based archive operations - works on archive files on disk.
    """
    
    def __init__(self, file_path: Union[str, Path], archiver: Optional[IArchiver] = None):
        """
        Initialize archive file.
        
        Args:
            file_path: Path to archive file
            archiver: Optional archiver instance (if None, must be set by subclass)
        """
        super().__init__(file_path)
        self._archiver: Optional[IArchiver] = archiver
    
    @abstractmethod
    def get_archiver(self) -> IArchiver:
        """Get the underlying archiver codec - must implement in subclass."""
        pass
    
    @abstractmethod
    def add_files(self, files: list[Path], **options) -> None:
        """
        Add files to archive - must implement in subclass.
        
        Should use self.get_archiver().compress() internally.
        """
        pass
    
    @abstractmethod
    def extract_to(self, dest: Path, **options) -> list[Path]:
        """
        Extract archive to destination - must implement in subclass.
        
        Should use self.get_archiver().extract() internally.
        """
        pass
    
    @abstractmethod
    def list_contents(self) -> list[str]:
        """List files in archive - must implement in subclass."""
        pass


# ============================================================================
# ARCHIVE FORMAT REGISTRY (Like CodecRegistry!)
# ============================================================================

class ArchiveFormatRegistry:
    """
    Registry for archive formats - LIKE CodecRegistry!
    
    Manages available archive formats and enables auto-detection.
    
    Examples:
        >>> registry = ArchiveFormatRegistry()
        >>> registry.register(ZipArchiver)
        >>> archiver = registry.get_by_extension("backup.zip")  # Auto-detect!
        >>> archiver = registry.get_by_id("zip")
    """
    
    def __init__(self):
        """Initialize registry."""
        self._formats: dict[str, type[IArchiveFormat]] = {}
        self._instances: dict[str, IArchiveFormat] = {}
        self._extension_map: dict[str, str] = {}  # .zip → "zip"
    
    def register(self, format_class: type[IArchiveFormat]) -> None:
        """
        Register an archive format.
        
        Args:
            format_class: Archive format class to register
        
        Example:
            >>> registry.register(ZipArchiver)
        """
        # Instantiate to get metadata
        instance = format_class()
        format_id = instance.format_id
        
        # Store
        self._formats[format_id] = format_class
        self._instances[format_id] = instance
        
        # Map extensions to format ID
        for ext in instance.file_extensions:
            self._extension_map[ext.lower()] = format_id
    
    def get_by_id(self, format_id: str) -> Optional[IArchiveFormat]:
        """Get archiver by format ID."""
        return self._instances.get(format_id)
    
    def get_by_extension(self, path: Union[str, Path]) -> Optional[IArchiveFormat]:
        """
        Get archiver by file extension (AUTO-DETECTION!).
        
        Args:
            path: File path
        
        Returns:
            Archiver instance or None
        
        Example:
            >>> archiver = registry.get_by_extension("backup.zip")
            >>> archiver = registry.get_by_extension("data.tar.gz")
        """
        path_obj = Path(path)
        
        # Check full suffix first (for .tar.gz, .tar.bz2, etc.)
        full_suffix = "".join(path_obj.suffixes).lower()
        if full_suffix in self._extension_map:
            format_id = self._extension_map[full_suffix]
            return self._instances.get(format_id)
        
        # Check single suffix
        suffix = path_obj.suffix.lower()
        if suffix in self._extension_map:
            format_id = self._extension_map[suffix]
            return self._instances.get(format_id)
        
        return None
    
    def list_formats(self) -> list[str]:
        """List all registered format IDs."""
        return list(self._formats.keys())


# ============================================================================
# COMPRESSION REGISTRY
# ============================================================================

class CompressionRegistry:
    """Registry for compression algorithms."""
    
    def __init__(self):
        """Initialize registry."""
        self._algorithms: dict[str, type[ICompressor]] = {}
        self._instances: dict[str, ICompressor] = {}
    
    def register(self, compressor_class: type[ICompressor]) -> None:
        """Register a compression algorithm."""
        instance = compressor_class()
        algo_id = instance.algorithm_id
        
        self._algorithms[algo_id] = compressor_class
        self._instances[algo_id] = instance
    
    def get(self, algorithm_id: str) -> Optional[ICompressor]:
        """Get compressor by algorithm ID."""
        return self._instances.get(algorithm_id)
    
    def auto_detect(self, data: bytes) -> Optional[ICompressor]:
        """Auto-detect compression algorithm from data."""
        for compressor in self._instances.values():
            if compressor.can_handle(data):
                return compressor
        return None
    
    def list_algorithms(self) -> list[str]:
        """List all registered algorithm IDs."""
        return list(self._algorithms.keys())


# Global registries
_global_archive_registry: Optional[ArchiveFormatRegistry] = None
_global_compression_registry: Optional[CompressionRegistry] = None


def get_global_archive_registry() -> ArchiveFormatRegistry:
    """Get or create global archive format registry."""
    global _global_archive_registry
    if _global_archive_registry is None:
        _global_archive_registry = ArchiveFormatRegistry()
        # Auto-register built-in formats (will be done in formats/__init__.py)
    return _global_archive_registry


def get_global_compression_registry() -> CompressionRegistry:
    """Get or create global compression registry."""
    global _global_compression_registry
    if _global_compression_registry is None:
        _global_compression_registry = CompressionRegistry()
        # Auto-register built-in compressors (will be done in compression/__init__.py)
    return _global_compression_registry

