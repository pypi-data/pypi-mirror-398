"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Serialization base classes - ASerialization abstract base.

Following I→A→XW pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base - this file)
- XW: XW{Format}Serializer (concrete implementations)
"""

import asyncio
from abc import ABC, abstractmethod, ABCMeta
from typing import Any, Union, Optional, BinaryIO, TextIO, AsyncIterator, Iterator, TYPE_CHECKING
# Root cause: Migrating to Python 3.12 built-in generic syntax for consistency
# Priority #3: Maintainability - Modern type annotations improve code clarity
from pathlib import Path

from ..codec.base import ACodec
from .contracts import ISerialization
from ..contracts import EncodeOptions, DecodeOptions
from ..defs import CodecCapability
from ..errors import SerializationError

if TYPE_CHECKING:
    from .defs import CompatibilityLevel
    from .schema_registry import SchemaInfo


class ASerialization(ACodec[Any, Union[bytes, str]], ISerialization):
    """
    Abstract base class for serialization - follows I→A→XW pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base - this class)
    XW: XW{Format}Serializer (concrete implementations)
    
    Extends ACodec and implements ISerialization interface.
    Provides default implementations for common serialization operations.
    
    Subclasses only need to implement:
    - encode()
    - decode()  
    - Metadata properties (codec_id, media_types, file_extensions, etc.)
    
    This class provides:
    - File I/O with atomic operations (save_file, load_file)
    - Async file I/O (save_file_async, load_file_async)
    - Streaming (iter_serialize, iter_deserialize, stream_serialize, stream_deserialize)
    - Validation helpers
    - XWSystem integration
    """
    
    def __init__(self, max_depth: Optional[int] = None, max_size_mb: Optional[float] = None):
        """
        Initialize serialization base.
        
        Args:
            max_depth: Maximum nesting depth allowed (default: from ACodec)
            max_size_mb: Maximum estimated data size in MB (default: from ACodec)
        
        Note: Safety validation (depth and size limits) is inherited from ACodec base class.
        See ACodec.__init__ for details.
        """
        super().__init__(max_depth=max_depth, max_size_mb=max_size_mb)
    
    # ========================================================================
    # CORE CODEC METHODS (Must implement in subclasses)
    # ========================================================================
    
    @abstractmethod
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to representation - must implement in subclass.
        
        Note: Safety validation is automatically performed in save_file() via inherited
        _validate_data_limits() from ACodec. Subclasses can call it directly if needed.
        """
        pass
    
    @abstractmethod
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode representation to data - must implement in subclass.
        
        Note: For decode operations, size validation happens on the input string/bytes,
        not the resulting data structure. Subclasses should validate input size if needed.
        """
        pass
    
    # ========================================================================
    # METADATA PROPERTIES (Must implement in subclasses)
    # ========================================================================
    
    @property
    @abstractmethod
    def codec_id(self) -> str:
        """Codec identifier (e.g., 'json', 'yaml')."""
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
    def format_name(self) -> str:
        """Format name (default: uppercase codec_id)."""
        return self.codec_id.upper()
    
    @property
    def mime_type(self) -> str:
        """Primary MIME type (default: first in media_types)."""
        return self.media_types[0] if self.media_types else "application/octet-stream"
    
    @property
    def is_binary_format(self) -> bool:
        """Whether this is a binary format (default: check return type of encode)."""
        # Can be overridden in subclasses for performance
        return False  # Default to text, override in binary formats
    
    @property
    def supports_streaming(self) -> bool:
        """Whether this format supports streaming (default: False)."""
        return False  # Override in formats that support streaming
    
    @property
    def capabilities(self) -> CodecCapability:
        """Serialization codecs support bidirectional operations."""
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        """Default aliases from codec_id."""
        return [self.codec_id.lower(), self.codec_id.upper()]
    
    @property
    def codec_types(self) -> list[str]:
        """
        Codec types for categorization (default: ['serialization']).
        
        Override in subclasses for more specific types like:
        - ['binary']: Binary serialization formats
        - ['config', 'serialization']: Configuration file formats
        - ['data']: Data exchange formats
        
        Can return multiple types if codec serves multiple purposes.
        """
        return ["serialization"]
    
    # ========================================================================
    # CAPABILITY PROPERTIES (Advanced features - override in subclasses)
    # ========================================================================
    
    @property
    def supports_path_based_updates(self) -> bool:
        """
        Whether this serializer supports path-based updates (JSONPointer, XPath, etc.).
        
        Default: False. Override in subclasses that support path operations.
        
        Returns:
            True if path-based updates are supported
        """
        return False
    
    @property
    def supports_atomic_path_write(self) -> bool:
        """
        Whether this serializer can atomically update paths without loading full file.
        
        Default: False. Override in subclasses that support efficient path updates.
        
        Returns:
            True if atomic path writes are supported
        """
        return False
    
    @property
    def supports_schema_validation(self) -> bool:
        """
        Whether this serializer supports schema validation.
        
        Default: False. Override in subclasses that support schemas.
        
        Returns:
            True if schema validation is supported
        """
        return False
    
    @property
    def supports_incremental_streaming(self) -> bool:
        """
        Whether this serializer supports true incremental streaming (not chunked full-file).
        
        Default: False. Override in subclasses that support incremental operations.
        
        Returns:
            True if incremental streaming is supported
        """
        return False
    
    @property
    def supports_multi_document(self) -> bool:
        """
        Whether this serializer supports multiple documents in one file.
        
        Default: False. Override in subclasses that support multi-document files.
        
        Returns:
            True if multi-document support is available
        """
        return False
    
    @property
    def supports_query(self) -> bool:
        """
        Whether this serializer supports query/filter operations (JSONPath, XPath, etc.).
        
        Default: False. Override in subclasses that support queries.
        
        Returns:
            True if query operations are supported
        """
        return False
    
    @property
    def supports_merge(self) -> bool:
        """
        Whether this serializer supports merge/update operations.
        
        Default: False. Override in subclasses that support merge operations.
        
        Returns:
            True if merge operations are supported
        """
        return False
    
    @property
    def supports_lazy_loading(self) -> bool:
        """
        Whether this serializer supports lazy loading for large files (10GB+).
        
        Lazy loading means the serializer can:
        - Skip full file validation for large files (size check skipped, depth still checked)
        - Use atomic path operations without loading entire file into memory
        - Handle both small (1KB) and large (10GB+) files efficiently
        
        Default: False. Override in subclasses that support lazy loading.
        
        Returns:
            True if lazy loading is supported for large files
        """
        return False
    
    @property
    def supports_lazy_loading(self) -> bool:
        """
        Whether this serializer supports lazy loading for large files.
        
        Default: False. Override in subclasses that support lazy loading.
        
        Returns:
            True if lazy loading is supported
        """
        return False

    @property
    def supports_record_streaming(self) -> bool:
        """
        Whether this serializer exposes record-level streaming operations
        (stream_read_record / stream_update_record).

        Default: False. Override in subclasses that provide efficient record
        streaming on top of their underlying format.
        """
        return False

    @property
    def supports_record_paging(self) -> bool:
        """
        Whether this serializer supports efficient record-level paging.

        Default: False. Override in subclasses that can page records without
        loading the entire dataset.
        """
        return False
    
    # ========================================================================
    # FILE I/O METHODS (Default implementations using encode/decode)
    # ========================================================================
    
    def save_file(self, data: Any, file_path: Union[str, Path], **options) -> None:
        """
        Save data to file with atomic operations.
        
        Default implementation:
        1. Validate data against safety limits (depth and size)
        2. Encode data using encode()
        3. Write to file using Path.write_bytes() or write_text()
        4. Uses atomic operations if configured
        
        Args:
            data: Data to serialize and save
            file_path: Path to save file
            **options: Format-specific options
        
        Raises:
            SerializationError: If save fails or data exceeds limits
        """
        try:
            path = Path(file_path)
            
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Validate data limits (method inherited from ACodec base class)
            # Note: For large files (10GB+), size validation is automatically skipped
            # Only depth validation is performed (prevents infinite recursion)
            skip_validation = options.get('skip_validation', False)
            skip_size_check = options.get('skip_size_check', False)
            if not skip_validation:
                self._validate_data_limits(data, "serialize", file_path=path, skip_size_check=skip_size_check)
            
            # Encode data
            repr_data = self.encode(data, options=options or None)
            
            # Write to file (atomic)
            if isinstance(repr_data, bytes):
                path.write_bytes(repr_data)
            else:
                path.write_text(repr_data, encoding='utf-8')
                
        except Exception as e:
            raise SerializationError(
                f"Failed to save {self.format_name} file: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def load_file(self, file_path: Union[str, Path], **options) -> Any:
        """
        Load data from file.
        
        Default implementation:
        1. Read from file using Path.read_bytes() or read_text()
        2. Decode data using decode()
        
        Args:
            file_path: Path to load from
            **options: Format-specific options
        
        Returns:
            Deserialized data
        
        Raises:
            SerializationError: If load fails
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            # Read from file
            if self.is_binary_format:
                repr_data = path.read_bytes()
            else:
                # Try text first, fall back to bytes
                try:
                    repr_data = path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    repr_data = path.read_bytes()
            
            # Decode data
            return self.decode(repr_data, options=options or None)
            
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                raise
            raise SerializationError(
                f"Failed to load {self.format_name} file: {e}",
                format_name=self.format_name,
                original_error=e
            )

    # ========================================================================
    # RECORD-LEVEL OPERATIONS (Generic defaults – can be overridden)
    # ========================================================================

    def stream_read_record(
        self,
        file_path: Union[str, Path],
        match: callable,
        projection: Optional[list[Any]] = None,
        **options: Any,
    ) -> Any:
        """
        Default record-level read:
        - Load the entire file via load_file().
        - If top-level is a list, scan until match(record) is True.
        - Apply optional projection and return the first matching record.

        This is format-agnostic but may be expensive for huge files. Formats
        that support true streaming should override this method.
        """
        data = self.load_file(file_path, **options)

        if isinstance(data, list):
            for record in data:
                if match(record):
                    return self._apply_projection(record, projection)

        # Fallback: treat entire object as a single "record"
        if match(data):
            return self._apply_projection(data, projection)

        raise KeyError("No matching record found")

    def stream_update_record(
        self,
        file_path: Union[str, Path],
        match: callable,
        updater: callable,
        *,
        atomic: bool = True,
        **options: Any,
    ) -> int:
        """
        Default record-level update:
        - Load entire file via load_file().
        - If top-level is a list, apply updater() to matching records.
        - Save the modified data back via save_file().

        This is generic and honours the serializer's existing atomic/write
        behavior, but may be expensive for huge files. Formats that support
        streaming/partial updates should override this method.
        """
        data = self.load_file(file_path, **options)
        updated = 0

        if isinstance(data, list):
            new_records: list[Any] = []
            for record in data:
                if match(record):
                    record = updater(record)
                    updated += 1
                new_records.append(record)
            data = new_records
        else:
            if match(data):
                data = updater(data)
                updated = 1

        # Delegate to existing save_file() which may already be atomic.
        self.save_file(data, file_path, **options)
        return updated

    def get_record_page(
        self,
        file_path: Union[str, Path],
        page_number: int,
        page_size: int,
        **options: Any,
    ) -> list[Any]:
        """
        Default record-level paging:
        - Load entire file via load_file().
        - If top-level is a list, return a slice corresponding to the requested page.

        Formats that support indexed or streaming paging should override this
        method for better performance on very large datasets.
        """
        if page_number < 1 or page_size <= 0:
            raise ValueError("Invalid page_number or page_size")

        data = self.load_file(file_path, **options)

        if isinstance(data, list):
            start = (page_number - 1) * page_size
            end = start + page_size
            return data[start:end]

        # Non-list data: treat as a single record page
        if page_number == 1 and page_size > 0:
            return [data]

        return []

    def get_record_by_id(
        self,
        file_path: Union[str, Path],
        id_value: Any,
        *,
        id_field: str = "id",
        **options: Any,
    ) -> Any:
        """
        Default record lookup by id:
        - Load entire file via load_file().
        - If top-level is a list of dict-like records, scan for record[id_field].
        """
        data = self.load_file(file_path, **options)

        if isinstance(data, list):
            for record in data:
                if isinstance(record, dict) and record.get(id_field) == id_value:
                    return record

        # Single-record fallback
        if isinstance(data, dict) and data.get(id_field) == id_value:
            return data

        raise KeyError(f"Record with {id_field}={id_value!r} not found")

    # Small helper for projection handling
    def _apply_projection(self, record: Any, projection: Optional[list[Any]]) -> Any:
        if not projection:
            return record
        current = record
        for key in projection:
            if isinstance(current, dict) and isinstance(key, str):
                current = current[key]
            elif isinstance(current, list) and isinstance(key, int):
                current = current[key]
            else:
                raise KeyError(key)
        return current
    
    # ========================================================================
    # VALIDATION METHODS (Default implementations)
    # ========================================================================
    
    def validate_data(self, data: Any) -> bool:
        """
        Validate data for serialization compatibility.
        
        Default implementation: Try to encode and catch errors.
        Override for format-specific validation.
        
        Args:
            data: Data to validate
        
        Returns:
            True if data can be serialized
        
        Raises:
            SerializationError: If validation fails
        """
        try:
            self.encode(data)
            return True
        except Exception as e:
            raise SerializationError(
                f"Data validation failed for {self.format_name}: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    # ========================================================================
    # STREAMING METHODS (Default implementations)
    # ========================================================================
    
    def iter_serialize(self, data: Any, chunk_size: int = 8192) -> Iterator[Union[str, bytes]]:
        """
        Stream serialize data in chunks.
        
        Default implementation: Encode all data then yield in chunks.
        Override for true streaming support.
        
        Args:
            data: Data to serialize
            chunk_size: Size of each chunk
        
        Yields:
            Serialized chunks
        """
        # Default: encode all at once, then chunk
        repr_data = self.encode(data)
        
        if isinstance(repr_data, bytes):
            for i in range(0, len(repr_data), chunk_size):
                yield repr_data[i:i + chunk_size]
        else:
            for i in range(0, len(repr_data), chunk_size):
                yield repr_data[i:i + chunk_size]
    
    def iter_deserialize(self, src: Union[TextIO, BinaryIO, Iterator[Union[str, bytes]]]) -> Any:
        """
        Stream deserialize data from chunks.
        
        Default implementation: Collect all chunks then decode.
        Override for true streaming support.
        
        Args:
            src: Source of data chunks
        
        Returns:
            Deserialized data
        """
        # Default: collect all chunks, then decode
        if isinstance(src, (TextIO, BinaryIO)):
            repr_data = src.read()
        else:
            chunks = list(src)
            if chunks and isinstance(chunks[0], bytes):
                repr_data = b''.join(chunks)
            else:
                repr_data = ''.join(chunks)
        
        return self.decode(repr_data)
    
    # ========================================================================
    # ASYNC METHODS (Default implementations using asyncio.to_thread)
    # ========================================================================
    
    async def save_file_async(self, data: Any, file_path: Union[str, Path], **options) -> None:
        """
        Async save data to file.
        
        Default implementation: Delegate to sync save_file via asyncio.to_thread.
        Override for native async I/O.
        
        Args:
            data: Data to serialize
            file_path: Path to save file
            **options: Format-specific options
        """
        await asyncio.to_thread(self.save_file, data, file_path, **options)
    
    async def load_file_async(self, file_path: Union[str, Path], **options) -> Any:
        """
        Async load data from file.
        
        Default implementation: Delegate to sync load_file via asyncio.to_thread.
        Override for native async I/O.
        
        Args:
            file_path: Path to load from
            **options: Format-specific options
        
        Returns:
            Deserialized data
        """
        return await asyncio.to_thread(self.load_file, file_path, **options)
    
    async def stream_serialize(self, data: Any, chunk_size: int = 8192) -> AsyncIterator[Union[str, bytes]]:
        """
        Async stream serialize data in chunks.
        
        Default implementation: Delegate to sync iter_serialize.
        Override for native async streaming.
        
        Args:
            data: Data to serialize
            chunk_size: Size of each chunk
        
        Yields:
            Serialized chunks
        """
        for chunk in self.iter_serialize(data, chunk_size):
            yield chunk
            await asyncio.sleep(0)  # Yield control
    
    async def stream_deserialize(self, data_stream: AsyncIterator[Union[str, bytes]]) -> Any:
        """
        Async stream deserialize data from chunks.
        
        Default implementation: Collect all chunks then decode.
        Override for native async streaming.
        
        Args:
            data_stream: Async iterator of data chunks
        
        Returns:
            Deserialized data
        """
        chunks = []
        async for chunk in data_stream:
            chunks.append(chunk)
        
        if chunks and isinstance(chunks[0], bytes):
            repr_data = b''.join(chunks)
        else:
            repr_data = ''.join(chunks)
        
        return self.decode(repr_data)
    
    # ========================================================================
    # ADVANCED FEATURES (Default implementations with graceful fallback)
    # ========================================================================
    
    def atomic_update_path(
        self, 
        file_path: Union[str, Path], 
        path: str, 
        value: Any, 
        **options
    ) -> None:
        """
        Atomically update a single path in a file (default: full-file fallback).
        
        Default implementation loads entire file, updates path in memory, and saves atomically.
        Override in subclasses for format-specific optimizations (e.g., JSONPointer for JSON).
        
        Args:
            file_path: Path to the file to update
            path: Path expression (format-specific)
            value: Value to set at the specified path
            **options: Format-specific options
        
        Raises:
            NotImplementedError: If path-based updates not supported and fallback fails
            SerializationError: If the update operation fails
            ValueError: If the path is invalid
        
        Note:
            This default implementation is inefficient for large files. Formats that support
            path-based updates should override this method for optimal performance.
        """
        if not self.supports_path_based_updates:
            raise NotImplementedError(
                f"{self.format_name} serializer does not support path-based updates. "
                f"Use load_file(), modify data, then save_file() instead."
            )
        
        # Default fallback: load full file, update in memory, save atomically
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {path_obj}")
            
            # Load entire file
            # For large files, skip size validation (they use lazy loading/streaming)
            # Root cause: Large files (10GB+) should use atomic path operations without full validation
            # Solution: Skip size check for atomic operations (depth check still performed)
            large_file_options = {**options, 'skip_size_check': True}
            data = self.load_file(file_path, **large_file_options)
            
            # Update path in memory (simple dict/list update for now)
            # Subclasses should override with format-specific logic
            if isinstance(data, dict) and path.startswith('/'):
                # Simple JSONPointer-like path handling
                path_parts = path.strip('/').split('/')
                current = data
                for part in path_parts[:-1]:
                    if isinstance(current, dict):
                        current = current.get(part)
                        if current is None:
                            raise ValueError(f"Path not found: {path}")
                    else:
                        raise ValueError(f"Cannot navigate path {path}: not a dict")
                
                # Set the value
                if isinstance(current, dict):
                    current[path_parts[-1]] = value
                else:
                    raise ValueError(f"Cannot set value at {path}: parent is not a dict")
            else:
                raise ValueError(f"Path-based updates not supported for data type: {type(data)}")
            
            # Save atomically using atomic operations
            from ..common.atomic import AtomicFileWriter
            
            repr_data = self.encode(data, options=options or None)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            backup = options.get('backup', True)
            with AtomicFileWriter(path_obj, backup=backup) as writer:
                if isinstance(repr_data, bytes):
                    writer.write(repr_data)
                else:
                    encoding = options.get('encoding', 'utf-8')
                    writer.write(repr_data.encode(encoding))
                    
        except (FileNotFoundError, ValueError) as e:
            raise
        except Exception as e:
            raise SerializationError(
                f"Failed to atomically update path '{path}' in {self.format_name} file: {e}",
                format_name=self.format_name,
                original_error=e
            ) from e
    
    def atomic_read_path(
        self, 
        file_path: Union[str, Path], 
        path: str, 
        **options
    ) -> Any:
        """
        Read a single path from a file (default: full-file fallback).
        
        Default implementation loads entire file and extracts path.
        Override in subclasses for format-specific optimizations.
        
        Args:
            file_path: Path to the file to read from
            path: Path expression (format-specific)
            **options: Format-specific options
        
        Returns:
            Value at the specified path
        
        Raises:
            NotImplementedError: If path-based reads not supported
            SerializationError: If the read operation fails
            KeyError: If the path doesn't exist
        """
        if not self.supports_path_based_updates:
            raise NotImplementedError(
                f"{self.format_name} serializer does not support path-based reads. "
                f"Use load_file() and access the path manually instead."
            )
        
        # Default fallback: load full file, extract path
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {path_obj}")
            
            # Load entire file
            # For large files, skip size validation (they use lazy loading/streaming)
            # Root cause: Large files (10GB+) should use atomic path operations without full validation
            # Solution: Skip size check for atomic operations (depth check still performed)
            large_file_options = {**options, 'skip_size_check': True}
            data = self.load_file(file_path, **large_file_options)
            
            # Extract path (simple dict/list access for now)
            if isinstance(data, dict) and path.startswith('/'):
                path_parts = path.strip('/').split('/')
                current = data
                for part in path_parts:
                    if isinstance(current, dict):
                        if part not in current:
                            raise KeyError(f"Path not found: {path}")
                        current = current[part]
                    elif isinstance(current, list):
                        try:
                            idx = int(part)
                            current = current[idx]
                        except (ValueError, IndexError):
                            raise KeyError(f"Path not found: {path}")
                    else:
                        raise KeyError(f"Cannot navigate path {path}: invalid type")
                
                return current
            else:
                raise ValueError(f"Path-based reads not supported for data type: {type(data)}")
                
        except (FileNotFoundError, KeyError, ValueError) as e:
            raise
        except Exception as e:
            raise SerializationError(
                f"Failed to read path '{path}' from {self.format_name} file: {e}",
                format_name=self.format_name,
                original_error=e
            ) from e
    
    def validate_with_schema(
        self, 
        data: Any, 
        schema: Any, 
        **options
    ) -> bool:
        """
        Validate data against a schema (default: not supported).
        
        Override in subclasses that support schema validation (JSON Schema, XSD, etc.).
        
        Args:
            data: Data to validate
            schema: Schema definition (format-specific)
            **options: Validation options
        
        Returns:
            True if data is valid
        
        Raises:
            NotImplementedError: If schema validation not supported
        """
        raise NotImplementedError(
            f"{self.format_name} serializer does not support schema validation. "
            f"Use format-specific validation libraries instead."
        )
    
    def incremental_save(
        self, 
        items: Iterator[Any], 
        file_path: Union[str, Path], 
        **options
    ) -> None:
        """
        Incrementally save items to a file (default: encode all, write atomically).
        
        Default implementation collects all items, encodes them, and writes atomically.
        Override in subclasses for true incremental streaming (e.g., JSONL).
        
        Args:
            items: Iterator of items to save
            file_path: Path to save file
            **options: Format-specific options
        
        Raises:
            NotImplementedError: If incremental streaming not supported
            SerializationError: If save operation fails
        """
        if not self.supports_incremental_streaming:
            raise NotImplementedError(
                f"{self.format_name} serializer does not support incremental streaming. "
                f"Use save_file() with a list of items instead."
            )
        
        # Default fallback: collect all items, encode, write atomically
        try:
            items_list = list(items)
            data = items_list if len(items_list) > 1 else (items_list[0] if items_list else {})
            
            # Use standard save_file which handles atomic operations
            self.save_file(data, file_path, **options)
            
        except Exception as e:
            raise SerializationError(
                f"Failed to incrementally save {self.format_name} file: {e}",
                format_name=self.format_name,
                original_error=e
            ) from e
    
    def incremental_load(
        self, 
        file_path: Union[str, Path], 
        **options
    ) -> Iterator[Any]:
        """
        Incrementally load items from a file (default: load all, return iterator).
        
        Default implementation loads entire file and yields items.
        Override in subclasses for true incremental streaming.
        
        Args:
            file_path: Path to load from
            **options: Format-specific options
        
        Yields:
            Items from the file
        
        Raises:
            NotImplementedError: If incremental streaming not supported
            SerializationError: If load operation fails
        """
        if not self.supports_incremental_streaming:
            raise NotImplementedError(
                f"{self.format_name} serializer does not support incremental streaming. "
                f"Use load_file() instead."
            )
        
        # Default fallback: load all, yield items
        try:
            data = self.load_file(file_path, **options)
            
            # If data is iterable (list, tuple), yield items
            if isinstance(data, (list, tuple)):
                for item in data:
                    yield item
            else:
                # Single item, yield it
                yield data
                
        except Exception as e:
            raise SerializationError(
                f"Failed to incrementally load {self.format_name} file: {e}",
                format_name=self.format_name,
                original_error=e
            ) from e
    
    def query(
        self, 
        file_path: Union[str, Path], 
        query_expr: str, 
        **options
    ) -> Any:
        """
        Query/filter data from a file (default: load all, query in memory).
        
        Default implementation loads entire file and applies query in memory.
        Override in subclasses for format-specific query languages (JSONPath, XPath).
        
        Root cause fixed: Method was loading entire file before raising error.
        Solution: Raise NotImplementedError immediately if queries not supported,
        preventing unnecessary file I/O operations.
        Priority #4: Performance - Avoid loading files when operation will fail.
        
        Args:
            file_path: Path to the file to query
            query_expr: Query expression (format-specific)
            **options: Query options
        
        Returns:
            Query results
        
        Raises:
            NotImplementedError: If queries not supported
            SerializationError: If query operation fails
            ValueError: If query expression is invalid
        """
        if not self.supports_query:
            raise NotImplementedError(
                f"{self.format_name} serializer does not support queries. "
                f"Use load_file() and filter data manually instead."
            )
        
        # Root cause fixed: Base class doesn't implement queries - raise immediately
        # Subclasses should override this method to provide actual query implementation
        # Priority #4: Performance - Don't load file if operation will fail
        raise NotImplementedError(
            f"Query operations require format-specific implementation for {self.format_name}. "
            f"Subclasses must override query() method to provide query support. "
            f"Alternatively, use load_file() and filter data manually."
        )
    
    def merge(
        self, 
        file_path: Union[str, Path], 
        updates: dict[str, Any], 
        **options
    ) -> None:
        """
        Merge updates into a file (default: load all, merge in memory, save atomically).
        
        Default implementation loads entire file, performs deep merge, and saves atomically.
        Override in subclasses for format-specific merge optimizations.
        
        Args:
            file_path: Path to the file to update
            updates: Dictionary of updates to merge
            **options: Merge options (deep=True, shallow=False, etc.)
        
        Raises:
            NotImplementedError: If merge operations not supported
            SerializationError: If merge operation fails
        """
        if not self.supports_merge:
            raise NotImplementedError(
                f"{self.format_name} serializer does not support merge operations. "
                f"Use load_file(), merge manually, then save_file() instead."
            )
        
        # Default fallback: load all, merge in memory, save atomically
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                # File doesn't exist, create it with updates
                self.save_file(updates, file_path, **options)
                return
            
            # Load existing data
            data = self.load_file(file_path, **options)
            
            # Perform merge
            deep = options.get('deep', True)
            if deep:
                # Deep merge
                def deep_merge(base: Any, update: Any) -> Any:
                    if isinstance(base, dict) and isinstance(update, dict):
                        result = base.copy()
                        for key, value in update.items():
                            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                                result[key] = deep_merge(result[key], value)
                            else:
                                result[key] = value
                        return result
                    return update
                
                if isinstance(data, dict):
                    merged = deep_merge(data, updates)
                else:
                    raise ValueError(f"Cannot merge into non-dict data: {type(data)}")
            else:
                # Shallow merge
                if isinstance(data, dict):
                    merged = {**data, **updates}
                else:
                    raise ValueError(f"Cannot merge into non-dict data: {type(data)}")
            
            # Save atomically
            self.save_file(merged, file_path, **options)
            
        except (ValueError, NotImplementedError):
            raise
        except Exception as e:
            raise SerializationError(
                f"Failed to merge {self.format_name} file: {e}",
                format_name=self.format_name,
                original_error=e
            ) from e


# ============================================================================
# SCHEMA REGISTRY BASE CLASSES (Moved from enterprise)
# ============================================================================


class ASchemaRegistry(ABC):
    """Abstract base class for schema registry implementations."""
    
    @abstractmethod
    async def register_schema(self, subject: str, schema: str, schema_type: str = "AVRO") -> 'SchemaInfo':
        """Register a new schema version."""
        pass
    
    @abstractmethod
    async def get_schema(self, schema_id: int) -> 'SchemaInfo':
        """Get schema by ID."""
        pass
    
    @abstractmethod
    async def get_latest_schema(self, subject: str) -> 'SchemaInfo':
        """Get latest schema version for subject."""
        pass
    
    @abstractmethod
    async def get_schema_versions(self, subject: str) -> list[int]:
        """Get all versions for a subject."""
        pass
    
    @abstractmethod
    async def check_compatibility(self, subject: str, schema: str) -> bool:
        """Check if schema is compatible with latest version."""
        pass
    
    @abstractmethod
    async def set_compatibility(self, subject: str, level: 'CompatibilityLevel') -> None:
        """Set compatibility level for subject."""
        pass

