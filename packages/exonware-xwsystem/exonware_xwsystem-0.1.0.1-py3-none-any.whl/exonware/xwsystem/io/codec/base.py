#!/usr/bin/env python3
# exonware/xwsystem/io/codec/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 30, 2025

Base classes, registry, adapters, and helper functions for codec system.
"""

from __future__ import annotations
from typing import Optional, Any, IO, Union
# Root cause: Migrating to Python 3.12 built-in generic syntax for consistency
# Priority #3: Maintainability - Modern type annotations improve code clarity
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod
import mimetypes
import sys

from .contracts import ICodec, ICodecMetadata
from ..contracts import Serializer, Formatter, EncodeOptions, DecodeOptions
from ..defs import CodecCapability
from ..errors import EncodeError, DecodeError, CodecNotFoundError, CodecRegistrationError, SerializationError

# Default safety limits to prevent infinite recursion and excessive memory usage
# Root cause: Some codecs (like JSON5) hang on very large/deep nested structures
# Solution: Add configurable limits at base class level
# Priority #1: Security - Prevent DoS via excessive nesting
# Priority #4: Performance - Prevent hangs on large data
DEFAULT_MAX_DEPTH = 100  # Maximum nesting depth
DEFAULT_MAX_SIZE_MB = 100  # Maximum estimated size in MB

__all__ = [
    'ACodec',
    'MediaKey',
    'CodecRegistry',
    'get_global_registry',
    'FormatterToSerializer',
    'SerializerToFormatter',
]


# ============================================================================
# MEDIA KEY
# ============================================================================

@dataclass(frozen=True)
class MediaKey:
    """
    Media type key for codec lookup (RFC 2046 compliant).
    
    Attributes:
        type: Media type string (e.g., "application/json")
    
    Examples:
        >>> MediaKey("application/json")
        >>> MediaKey("application/sql")
        >>> MediaKey("text/x-python")
    """
    
    type: str
    
    def __post_init__(self):
        # Normalize to lowercase
        object.__setattr__(self, 'type', self.type.lower())
    
    def __str__(self) -> str:
        return self.type
    
    @classmethod
    def from_extension(cls, ext: str) -> Optional[MediaKey]:
        """
        Create MediaKey from file extension.
        
        Args:
            ext: File extension (with or without dot)
        
        Returns:
            MediaKey if extension is recognized, None otherwise
        
        Examples:
            >>> MediaKey.from_extension('.json')
            MediaKey(type='application/json')
            
            >>> MediaKey.from_extension('sql')
            MediaKey(type='application/sql')
        """
        if not ext.startswith('.'):
            ext = f'.{ext}'
        
        mime_type = mimetypes.guess_type(f'file{ext}')[0]
        return cls(mime_type) if mime_type else None


# ============================================================================
# CODEC REGISTRY
# ============================================================================

class CodecRegistry:
    """
    Global codec registry with media-type based lookup.
    
    NO HARDCODING - codecs self-register with their metadata!
    
    Lookup strategies:
        1. Media type (primary): get(MediaKey("application/json"))
        2. File extension (convenience): get_by_extension(".json")
        3. Codec ID / alias (direct): get_by_id("json")
    
    Examples:
        >>> registry = CodecRegistry()
        >>> registry.register(JsonCodec)
        >>> 
        >>> codec = registry.get(MediaKey("application/json"))
        >>> codec = registry.get_by_extension('.json')
        >>> codec = registry.get_by_id('json')
    """
    
    def __init__(self) -> None:
        self._by_media_type: dict[MediaKey, type[ICodec]] = {}
        self._by_extension: dict[str, type[ICodec]] = {}
        self._by_id: dict[str, type[ICodec]] = {}
        self._instances: dict[str, ICodec] = {}  # Cached instances
    
    def register(self, codec_class: type[ICodec]) -> None:
        """
        Register a codec class.
        
        The codec must implement ICodecMetadata protocol to provide:
        - codec_id
        - media_types
        - file_extensions
        - aliases
        
        Args:
            codec_class: Codec class to register
        
        Raises:
            CodecRegistrationError: If codec doesn't implement ICodecMetadata
        
        Examples:
            >>> registry.register(JsonCodec)
            >>> registry.register(SqlFormatter)
        """
        # Create instance to read metadata
        try:
            instance = codec_class()
        except Exception as e:
            raise CodecRegistrationError(
                f"Failed to instantiate {codec_class.__name__}: {e}"
            ) from e
        
        # Verify it has metadata
        if not hasattr(instance, 'codec_id'):
            raise CodecRegistrationError(
                f"{codec_class.__name__} must implement ICodecMetadata protocol "
                f"(missing 'codec_id' property)"
            )
        
        codec_id = instance.codec_id
        
        # Register by media types
        if hasattr(instance, 'media_types'):
            for media_type in instance.media_types:
                key = MediaKey(media_type)
                self._by_media_type[key] = codec_class
        
        # Register by extensions
        if hasattr(instance, 'file_extensions'):
            for ext in instance.file_extensions:
                if not ext.startswith('.'):
                    ext = f'.{ext}'
                self._by_extension[ext.lower()] = codec_class
        
        # Register by ID and aliases
        self._by_id[codec_id.lower()] = codec_class
        if hasattr(instance, 'aliases'):
            for alias in instance.aliases:
                self._by_id[alias.lower()] = codec_class
    
    def get(self, key: MediaKey) -> Optional[ICodec]:
        """
        Get codec by media type key.
        
        Args:
            key: Media type key
        
        Returns:
            Codec instance (cached) or None if not found
        
        Examples:
            >>> codec = registry.get(MediaKey("application/json"))
            >>> codec.encode({"key": "value"})
        """
        codec_class = self._by_media_type.get(key)
        if not codec_class:
            return None
        
        # Return cached instance
        codec_id = codec_class().codec_id
        if codec_id not in self._instances:
            self._instances[codec_id] = codec_class()
        
        return self._instances[codec_id]
    
    def get_by_extension(self, ext: str) -> Optional[ICodec]:
        """
        Get codec by file extension.
        
        Args:
            ext: File extension (with or without dot) or file path
        
        Returns:
            Codec instance or None
        
        Examples:
            >>> codec = registry.get_by_extension('.json')
            >>> codec = registry.get_by_extension('sql')
            >>> codec = registry.get_by_extension('data.json')  # Extracts .json
        """
        # Extract extension if full path given
        path_obj = Path(ext)
        if path_obj.suffix:
            ext = path_obj.suffix
        
        if not ext.startswith('.'):
            ext = f'.{ext}'
        
        codec_class = self._by_extension.get(ext.lower())
        if not codec_class:
            return None
        
        codec_id = codec_class().codec_id
        if codec_id not in self._instances:
            self._instances[codec_id] = codec_class()
        
        return self._instances[codec_id]
    
    def get_by_id(self, codec_id: str) -> Optional[ICodec]:
        """
        Get codec by ID or alias.
        
        Args:
            codec_id: Codec identifier or alias (case-insensitive)
        
        Returns:
            Codec instance or None
        
        Examples:
            >>> codec = registry.get_by_id('json')
            >>> codec = registry.get_by_id('JSON')  # Case insensitive
        """
        codec_class = self._by_id.get(codec_id.lower())
        if not codec_class:
            return None
        
        actual_id = codec_class().codec_id
        if actual_id not in self._instances:
            self._instances[actual_id] = codec_class()
        
        return self._instances[actual_id]
    
    def list_media_types(self) -> list[str]:
        """List all registered media types."""
        return [str(k) for k in self._by_media_type.keys()]
    
    def list_extensions(self) -> list[str]:
        """List all registered file extensions."""
        return list(self._by_extension.keys())
    
    def list_codec_ids(self) -> list[str]:
        """List all registered codec IDs."""
        return [
            cls().codec_id 
            for cls in set(self._by_id.values())
        ]


# Global registry singleton
_global_registry: Optional[CodecRegistry] = None


def get_global_registry() -> CodecRegistry:
    """
    Get the global codec registry.
    
    Lazy-initializes on first access.
    
    Returns:
        Global CodecRegistry instance
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = CodecRegistry()
    
    return _global_registry


# ============================================================================
# BASE CODEC CLASS WITH CONVENIENCE METHODS
# ============================================================================

class ACodec[T, R](ICodec[T, R], ICodecMetadata, ABC):
    """
    Base codec class with all convenience methods.
    
    Provides:
    - Core encode/decode (abstract - must implement)
    - All convenience aliases (dumps/loads/serialize/etc.)
    - File I/O helpers (save/load/export/import)
    - Stream operations (write/read)
    - Safety validation (depth and size limits with caching)
    
    Subclasses only need to implement:
    - encode()
    - decode()
    - Metadata properties (codec_id, media_types, etc.)
    
    Example:
        >>> class JsonCodec(ACodec[dict, bytes]):
        ...     codec_id = "json"
        ...     media_types = ["application/json"]
        ...     file_extensions = [".json"]
        ...     aliases = ["JSON"]
        ...     
        ...     def encode(self, value, *, options=None):
        ...         return json.dumps(value).encode('utf-8')
        ...     
        ...     def decode(self, repr, *, options=None):
        ...         return json.loads(repr.decode('utf-8'))
        ...     
        ...     def capabilities(self):
        ...         return CodecCapability.BIDIRECTIONAL | CodecCapability.TEXT
    """
    
    def __init__(self, max_depth: Optional[int] = None, max_size_mb: Optional[float] = None):
        """
        Initialize codec base.
        
        Args:
            max_depth: Maximum nesting depth allowed (default: DEFAULT_MAX_DEPTH)
            max_size_mb: Maximum estimated data size in MB (default: DEFAULT_MAX_SIZE_MB)
        
        Root cause: Codecs can hang on very large/deep nested structures.
        Solution: Add configurable limits to prevent infinite recursion and excessive memory.
        Priority #1: Security - Prevent DoS via excessive nesting
        Priority #4: Performance - Prevent hangs on large data
        """
        self._max_depth = max_depth if max_depth is not None else DEFAULT_MAX_DEPTH
        self._max_size_mb = max_size_mb if max_size_mb is not None else DEFAULT_MAX_SIZE_MB
        # Cache for depth/size calculations to avoid reprocessing same objects
        self._depth_cache: dict[int, int] = {}  # obj_id -> depth
        self._size_cache: dict[int, float] = {}  # obj_id -> size_mb
    
    # ========================================================================
    # SAFETY VALIDATION METHODS (Protect against infinite recursion)
    # ========================================================================
    
    def _get_data_depth(self, data: Any, cache: Optional[dict[int, int]] = None, visited: Optional[set] = None, current_depth: int = 0) -> int:
        """
        Calculate maximum nesting depth of data structure using caching.
        
        Root cause: Deeply nested structures can cause infinite recursion in parsers.
        Solution: Recursively calculate depth with cycle detection and caching.
        Priority #1: Security - Prevent DoS via excessive nesting
        Priority #4: Performance - Detect problematic structures early, cache results
        
        Args:
            data: Data structure to analyze
            cache: Optional cache dictionary (uses instance cache if None)
            visited: Set of object IDs currently being processed (for cycle detection)
            current_depth: Current recursion depth
        
        Returns:
            Maximum nesting depth found
        """
        if cache is None:
            cache = self._depth_cache
        if visited is None:
            visited = set()
        
        # Safety check: prevent infinite recursion
        if current_depth > self._max_depth * 2:  # Allow some overhead for cycle detection
            return current_depth
        
        # Handle primitive types (no nesting)
        if data is None or isinstance(data, (str, int, float, bool, bytes)):
            return current_depth
        
        obj_id = id(data)
        
        # Handle cycles (reference to currently-being-processed object)
        if obj_id in visited:
            return current_depth  # Cycle detected, don't count as additional depth
        
        # Check cache first (avoid reprocessing same object)
        if obj_id in cache:
            # Use cached depth (maximum depth from this object), add current_depth
            return cache[obj_id] + current_depth
        
        # Mark as being processed
        visited.add(obj_id)
        
        try:
            # Calculate maximum depth from this object (relative depth)
            max_relative_depth = 0
            
            if isinstance(data, dict):
                if data:  # Non-empty dict
                    child_depths = [
                        self._get_data_depth(v, cache, visited, current_depth + 1) - current_depth - 1
                        for v in data.values()
                    ]
                    max_relative_depth = max(child_depths) if child_depths else 1
                else:
                    max_relative_depth = 1  # Empty dict still counts as one level
            
            elif isinstance(data, (list, tuple)):
                if data:  # Non-empty list/tuple
                    child_depths = [
                        self._get_data_depth(item, cache, visited, current_depth + 1) - current_depth - 1
                        for item in data
                    ]
                    max_relative_depth = max(child_depths) if child_depths else 1
                else:
                    max_relative_depth = 1  # Empty list still counts as one level
            
            elif hasattr(data, '__dict__'):
                # Custom object with attributes
                child_depths = [
                    self._get_data_depth(v, cache, visited, current_depth + 1) - current_depth - 1
                    for v in vars(data).values()
                ]
                max_relative_depth = max(child_depths) if child_depths else 0
            
            # Cache the result (maximum relative depth from this object)
            cache[obj_id] = max_relative_depth
            
            return max_relative_depth + current_depth
        
        except RecursionError:
            # Fallback if recursion limit hit
            return current_depth
        finally:
            # Remove from visited when done processing
            visited.discard(obj_id)
    
    def _estimate_data_size_mb(self, data: Any, cache: Optional[dict[int, float]] = None) -> float:
        """
        Estimate data size in megabytes using caching.
        
        Root cause: Very large data structures can cause memory issues and hangs.
        Solution: Recursively estimate size with cycle detection and caching.
        Priority #4: Performance - Detect large structures early, cache results
        
        Args:
            data: Data structure to analyze
            cache: Optional cache dictionary (uses instance cache if None)
        
        Returns:
            Estimated size in megabytes
        """
        if cache is None:
            cache = self._size_cache
        
        # Check cache first (avoid reprocessing same object)
        obj_id = id(data)
        if obj_id in cache:
            return cache[obj_id]
        
        # Calculate size for this object
        size_bytes = 0.0
        
        if isinstance(data, (str, bytes)):
            size_bytes = len(data)
        elif isinstance(data, (int, float)):
            size_bytes = 8  # Approximate
        elif isinstance(data, bool):
            size_bytes = 1
        elif isinstance(data, dict):
            size_bytes = sys.getsizeof(data)
            for k, v in data.items():
                size_bytes += self._estimate_data_size_mb(k, cache) * 1024 * 1024
                size_bytes += self._estimate_data_size_mb(v, cache) * 1024 * 1024
        elif isinstance(data, (list, tuple)):
            size_bytes = sys.getsizeof(data)
            for item in data:
                size_bytes += self._estimate_data_size_mb(item, cache) * 1024 * 1024
        else:
            size_bytes = sys.getsizeof(data)
            if hasattr(data, '__dict__'):
                for v in vars(data).values():
                    size_bytes += self._estimate_data_size_mb(v, cache) * 1024 * 1024
        
        size_mb = size_bytes / (1024 * 1024)  # Convert to MB
        
        # Cache the result
        cache[obj_id] = size_mb
        
        return size_mb
    
    def _validate_data_limits(
        self, 
        data: Any, 
        operation: str = "encode",
        file_path: Optional[Union[str, Path]] = None,
        skip_size_check: bool = False
    ) -> None:
        """
        Validate data structure against safety limits.
        
        Root cause: Some codecs hang on very large/deep nested structures.
        Solution: Check depth (always) and size (only for in-memory data, not large files).
        Priority #1: Security - Prevent DoS via excessive nesting
        Priority #4: Performance - Prevent hangs on large data
        
        Args:
            data: Data structure to validate
            operation: Operation name for error messages (encode/decode)
            file_path: Optional file path - if provided and file is large, skip size check
            skip_size_check: If True, skip size validation (for large files that use lazy loading)
        
        Raises:
            SerializationError: If data exceeds safety limits
        
        Note:
            - Depth validation is ALWAYS performed (prevents infinite recursion)
            - Size validation is SKIPPED for large files (10GB+ files are expected)
            - Size validation is performed for in-memory data to catch problematic structures
        """
        # Clear caches for fresh calculation
        self._depth_cache.clear()
        self._size_cache.clear()
        
        # ALWAYS check depth - this prevents infinite recursion which is the real security issue
        depth = self._get_data_depth(data)
        if depth > self._max_depth:
            raise SerializationError(
                f"Data structure exceeds maximum nesting depth of {self._max_depth} "
                f"(found {depth} levels). This may cause infinite recursion in {self.codec_id} {operation}. "
                f"Consider flattening the data structure or using a different format.",
                format_name=getattr(self, 'format_name', self.codec_id)
            )
        
        # Size check: Skip for large files (they use lazy loading/streaming)
        # Only validate size for in-memory data structures
        if skip_size_check:
            return  # Skip size check (e.g., for atomic path operations on large files)
        
        # Check if file exists and is large - if so, skip size validation
        if file_path:
            try:
                path_obj = Path(file_path)
                if path_obj.exists():
                    file_size_mb = path_obj.stat().st_size / (1024 * 1024)
                    # If file is > 1GB, assume it's meant to be large and skip size validation
                    # Large files should use lazy loading/streaming features
                    if file_size_mb > 1024:  # 1GB threshold
                        return  # Skip size check for large files
            except (OSError, ValueError):
                pass  # If we can't check file size, proceed with validation
        
        # Check size for in-memory data (not from large files)
        size_mb = self._estimate_data_size_mb(data)
        if size_mb > self._max_size_mb:
            raise SerializationError(
                f"Data structure exceeds maximum size of {self._max_size_mb}MB "
                f"(estimated {size_mb:.1f}MB). This may cause memory issues or hangs. "
                f"For large files (10GB+), use lazy loading or streaming features. "
                f"Consider splitting the data or using a streaming format.",
                format_name=getattr(self, 'format_name', self.codec_id)
            )
    
    # ========================================================================
    # CORE METHODS (Must implement in subclasses)
    # ========================================================================
    
    @abstractmethod
    def encode(self, value: T, *, options: Optional[EncodeOptions] = None) -> R:
        """Encode value to representation. Must implement."""
        pass
    
    @abstractmethod
    def decode(self, repr: R, *, options: Optional[DecodeOptions] = None) -> T:
        """Decode representation to value. Must implement."""
        pass
    
    # ========================================================================
    # METADATA PROPERTIES (Must implement in subclasses)
    # ========================================================================
    
    @property
    @abstractmethod
    def codec_id(self) -> str:
        """Unique codec identifier."""
        pass
    
    @property
    @abstractmethod
    def media_types(self) -> list[str]:
        """Supported media types."""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """Supported file extensions."""
        pass
    
    @property
    def aliases(self) -> list[str]:
        """Alternative names (default: [codec_id])."""
        return [self.codec_id.lower(), self.codec_id.upper()]
    
    @abstractmethod
    def capabilities(self) -> CodecCapability:
        """Supported capabilities."""
        pass
    
    # ========================================================================
    # CONVENIENCE ALIASES - Memory Operations
    # ========================================================================
    
    def dumps(self, value: T, **opts) -> R:
        """Alias for encode() - Python convention."""
        return self.encode(value, options=opts or None)
    
    def loads(self, repr: R, **opts) -> T:
        """Alias for decode() - Python convention."""
        return self.decode(repr, options=opts or None)
    
    def serialize(self, value: T, **opts) -> R:
        """Alias for encode() - explicit intent."""
        return self.encode(value, options=opts or None)
    
    def deserialize(self, repr: R, **opts) -> T:
        """Alias for decode() - explicit intent."""
        return self.decode(repr, options=opts or None)
    
    # ========================================================================
    # FILE OPERATIONS
    # ========================================================================
    
    def save(self, value: T, path: Path | str, **opts) -> None:
        """
        Encode and write to file.
        
        Args:
            value: Value to encode
            path: File path to write to
            **opts: Encoding options
        
        Example:
            >>> codec.save(data, "output.json")
        """
        path = Path(path)
        repr = self.encode(value, options=opts or None)
        
        if isinstance(repr, bytes):
            path.write_bytes(repr)
        else:
            path.write_text(repr, encoding='utf-8')
    
    def load(self, path: Path | str, **opts) -> T:
        """
        Read from file and decode.
        
        Args:
            path: File path to read from
            **opts: Decoding options
        
        Returns:
            Decoded value
        
        Example:
            >>> data = codec.load("input.json")
        """
        path = Path(path)
        
        # Try to guess if binary or text based on codec type
        # This is a heuristic - subclasses can override
        try:
            # Try binary first
            repr = path.read_bytes()
            if isinstance(self._get_repr_type_hint(), str):
                # Text codec, decode bytes to str
                repr = repr.decode('utf-8')
        except:
            # Fall back to text
            repr = path.read_text(encoding='utf-8')
        
        return self.decode(repr, options=opts or None)
    
    def export(self, value: T, path: Path | str, **opts) -> None:
        """Alias for save() - business terminology."""
        return self.save(value, path, **opts)
    
    def import_(self, path: Path | str, **opts) -> T:
        """Alias for load() - business terminology (_ for keyword)."""
        return self.load(path, **opts)
    
    def to_file(self, value: T, path: Path | str, **opts) -> None:
        """Alias for save() - explicit direction."""
        return self.save(value, path, **opts)
    
    def from_file(self, path: Path | str, **opts) -> T:
        """Alias for load() - explicit direction."""
        return self.load(path, **opts)
    
    def save_as(self, value: T, path: Path | str, format: Optional[str] = None, **opts) -> None:
        """
        Save with optional format hint.
        
        Args:
            value: Value to save
            path: File path
            format: Optional format hint (added to options)
            **opts: Other encoding options
        """
        if format:
            opts['format'] = format
        return self.save(value, path, **opts)
    
    def load_as(self, path: Path | str, format: Optional[str] = None, **opts) -> T:
        """
        Load with optional format hint.
        
        Args:
            path: File path
            format: Optional format hint (added to options)
            **opts: Other decoding options
        """
        if format:
            opts['format'] = format
        return self.load(path, **opts)
    
    # ========================================================================
    # STREAM OPERATIONS
    # ========================================================================
    
    def write(self, value: T, stream: IO, **opts) -> None:
        """
        Encode and write to stream.
        
        Args:
            value: Value to encode
            stream: IO stream to write to
            **opts: Encoding options
        
        Example:
            >>> with open("output.json", "wb") as f:
            ...     codec.write(data, f)
        """
        repr = self.encode(value, options=opts or None)
        stream.write(repr)
    
    def read(self, stream: IO, **opts) -> T:
        """
        Read from stream and decode.
        
        Args:
            stream: IO stream to read from
            **opts: Decoding options
        
        Returns:
            Decoded value
        
        Example:
            >>> with open("input.json", "rb") as f:
            ...     data = codec.read(f)
        """
        repr = stream.read()
        return self.decode(repr, options=opts or None)
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _get_repr_type_hint(self) -> type:
        """Get representation type hint (bytes or str) from class."""
        # Try to extract from __orig_bases__ or default to bytes
        return bytes  # Default, subclasses can override


# ============================================================================
# ADAPTERS (Bytes ↔ String)
# ============================================================================

class FormatterToSerializer[T]:
    """
    Adapter: Formatter[T, str] → Serializer[T, bytes].
    
    Wraps a string-based formatter to provide bytes interface via UTF-8 encoding.
    
    Use case: Language formatters (SQL, GraphQL) need to be saved to files
    as bytes, but work with strings internally.
    
    Example:
        >>> sql_formatter = SqlFormatter()  # Returns str
        >>> sql_serializer = FormatterToSerializer(sql_formatter)
        >>> bytes_data = sql_serializer.encode(query_ast)  # Returns bytes
        >>> with open('query.sql', 'wb') as f:
        ...     f.write(bytes_data)
    """
    
    def __init__(
        self, 
        formatter: Formatter[T, str], 
        encoding: str = "utf-8",
        errors: str = "strict"
    ) -> None:
        """
        Initialize adapter.
        
        Args:
            formatter: String formatter to wrap
            encoding: Text encoding (default: UTF-8)
            errors: Error handling strategy
        """
        self._formatter = formatter
        self._encoding = encoding
        self._errors = errors
    
    def encode(self, value: T, *, options: Optional[EncodeOptions] = None) -> bytes:
        """Encode to bytes via string."""
        text = self._formatter.encode(value, options=options)
        return text.encode(self._encoding, errors=self._errors)
    
    def decode(self, repr: bytes, *, options: Optional[DecodeOptions] = None) -> T:
        """Decode from bytes via string."""
        text = repr.decode(self._encoding, errors=self._errors)
        return self._formatter.decode(text, options=options)


class SerializerToFormatter[T]:
    """
    Adapter: Serializer[T, bytes] → Formatter[T, str].
    
    Wraps a bytes-based serializer to provide string interface via UTF-8 decoding.
    
    Use case: Text serializers (JSON, YAML) may work with bytes internally but
    need to provide string interface for templating/generation.
    
    Example:
        >>> json_serializer = JsonSerializer()  # Returns bytes
        >>> json_formatter = SerializerToFormatter(json_serializer)
        >>> text = json_formatter.encode({"key": "value"})  # Returns str
        >>> template = f"const data = {text};"
    """
    
    def __init__(
        self, 
        serializer: Serializer[T, bytes], 
        encoding: str = "utf-8",
        errors: str = "strict"
    ) -> None:
        """
        Initialize adapter.
        
        Args:
            serializer: Bytes serializer to wrap
            encoding: Text encoding (default: UTF-8)
            errors: Error handling strategy
        """
        self._serializer = serializer
        self._encoding = encoding
        self._errors = errors
    
    def encode(self, value: T, *, options: Optional[EncodeOptions] = None) -> str:
        """Encode to string via bytes."""
        data = self._serializer.encode(value, options=options)
        return data.decode(self._encoding, errors=self._errors)
    
    def decode(self, repr: str, *, options: Optional[DecodeOptions] = None) -> T:
        """Decode from string via bytes."""
        data = repr.encode(self._encoding, errors=self._errors)
        return self._serializer.decode(data, options=options)

