"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

Serialization contracts - ISerialization interface extending ICodec.

Following I→A→XW pattern:
- I: ISerialization (interface - this file)
- A: ASerialization (abstract base)
- XW: XW{Format}Serializer (concrete implementations)
"""

from abc import ABC, abstractmethod
from typing import Any, Union, Optional, BinaryIO, TextIO, AsyncIterator, Iterator
# Root cause: Migrating to Python 3.12 built-in generic syntax for consistency
# Priority #3: Maintainability - Modern type annotations improve code clarity
from pathlib import Path

from ..codec.contracts import ICodec, ICodecMetadata
from ..contracts import EncodeOptions, DecodeOptions
from ..defs import CodecCapability


class ISerialization(ICodec[Any, Union[bytes, str]]):
    """
    Serialization interface extending ICodec.
    
    Provides serialization-specific functionality on top of the universal codec interface.
    
    Type: ICodec[Any, Union[bytes, str]]
    - T (model type): Any (supports any Python object)
    - R (representation): Union[bytes, str] (can be text or binary)
    
    This interface extends ICodec with:
    - File I/O methods (save_file, load_file)
    - Format detection
    - Validation
    - Streaming support
    - Async operations
    
    All serializers in xwsystem implement this interface.
    """
    
    # ========================================================================
    # METADATA PROPERTIES (from ICodecMetadata)
    # ========================================================================
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Get the serialization format name (e.g., 'JSON', 'YAML')."""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """Get supported file extensions for this format."""
        pass
    
    @property
    @abstractmethod
    def mime_type(self) -> str:
        """Get the MIME type for this serialization format."""
        pass
    
    @property
    @abstractmethod
    def is_binary_format(self) -> bool:
        """Whether this is a binary or text-based format."""
        pass
    
    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether this format supports streaming serialization."""
        pass
    
    # ========================================================================
    # CORE CODEC METHODS (from ICodec)
    # ========================================================================
    
    @abstractmethod
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to representation (bytes or str).
        
        Core codec method - all serializers must implement.
        """
        pass
    
    @abstractmethod
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode representation (bytes or str) to data.
        
        Core codec method - all serializers must implement.
        """
        pass
    
    # ========================================================================
    # FILE I/O METHODS (Serialization-specific)
    # ========================================================================
    
    @abstractmethod
    def save_file(self, data: Any, file_path: Union[str, Path], **options) -> None:
        """
        Save data to file with atomic operations.
        
        Args:
            data: Data to serialize and save
            file_path: Path to save file
            **options: Format-specific options
        
        Raises:
            SerializationError: If save fails
        """
        pass
    
    @abstractmethod
    def load_file(self, file_path: Union[str, Path], **options) -> Any:
        """
        Load data from file.
        
        Args:
            file_path: Path to load from
            **options: Format-specific options
        
        Returns:
            Deserialized data
        
        Raises:
            SerializationError: If load fails
        """
        pass
    
    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================
    
    @abstractmethod
    def validate_data(self, data: Any) -> bool:
        """
        Validate data for serialization compatibility.
        
        Args:
            data: Data to validate
        
        Returns:
            True if data can be serialized
        
        Raises:
            SerializationError: If validation fails
        """
        pass
    
    # ========================================================================
    # STREAMING METHODS
    # ========================================================================
    
    @abstractmethod
    def iter_serialize(self, data: Any, chunk_size: int = 8192) -> Iterator[Union[str, bytes]]:
        """
        Stream serialize data in chunks.
        
        Args:
            data: Data to serialize
            chunk_size: Size of each chunk
        
        Yields:
            Serialized chunks
        """
        pass
    
    @abstractmethod
    def iter_deserialize(self, src: Union[TextIO, BinaryIO, Iterator[Union[str, bytes]]]) -> Any:
        """
        Stream deserialize data from chunks.
        
        Args:
            src: Source of data chunks
        
        Returns:
            Deserialized data
        """
        pass
    
    # ========================================================================
    # ASYNC METHODS
    # ========================================================================
    
    @abstractmethod
    async def save_file_async(self, data: Any, file_path: Union[str, Path], **options) -> None:
        """
        Async save data to file.
        
        Args:
            data: Data to serialize
            file_path: Path to save file
            **options: Format-specific options
        """
        pass
    
    @abstractmethod
    async def load_file_async(self, file_path: Union[str, Path], **options) -> Any:
        """
        Async load data from file.
        
        Args:
            file_path: Path to load from
            **options: Format-specific options
        
        Returns:
            Deserialized data
        """
        pass
    
    @abstractmethod
    async def stream_serialize(self, data: Any, chunk_size: int = 8192) -> AsyncIterator[Union[str, bytes]]:
        """
        Async stream serialize data in chunks.
        
        Args:
            data: Data to serialize
            chunk_size: Size of each chunk
        
        Yields:
            Serialized chunks
        """
        pass
    
    @abstractmethod
    async def stream_deserialize(self, data_stream: AsyncIterator[Union[str, bytes]]) -> Any:
        """
        Async stream deserialize data from chunks.
        
        Args:
            data_stream: Async iterator of data chunks
        
        Returns:
            Deserialized data
        """
        pass
    
    # ========================================================================
    # ADVANCED FEATURES (Optional - format-specific implementations)
    # ========================================================================
    
    @abstractmethod
    def atomic_update_path(
        self, 
        file_path: Union[str, Path], 
        path: str, 
        value: Any, 
        **options
    ) -> None:
        """
        Atomically update a single path in a file without loading the entire file.
        
        This method allows efficient updates to large files by only modifying
        the specific path (e.g., JSONPointer "/users/0/name") without loading
        the entire file into memory.
        
        Args:
            file_path: Path to the file to update
            path: Path expression (format-specific: JSONPointer, XPath, YAML path, etc.)
            value: Value to set at the specified path
            **options: Format-specific options (backup, atomic, etc.)
        
        Raises:
            NotImplementedError: If this format doesn't support path-based updates
            SerializationError: If the update operation fails
            ValueError: If the path is invalid or doesn't exist
        
        Example:
            >>> serializer.atomic_update_path("config.json", "/database/host", "localhost")
        """
        pass
    
    @abstractmethod
    def atomic_read_path(
        self, 
        file_path: Union[str, Path], 
        path: str, 
        **options
    ) -> Any:
        """
        Read a single path from a file without loading the entire file.
        
        This method allows efficient reads from large files by only accessing
        the specific path (e.g., JSONPointer "/users/0/name") without loading
        the entire file into memory.
        
        Args:
            file_path: Path to the file to read from
            path: Path expression (format-specific: JSONPointer, XPath, YAML path, etc.)
            **options: Format-specific options
        
        Returns:
            Value at the specified path
        
        Raises:
            NotImplementedError: If this format doesn't support path-based reads
            SerializationError: If the read operation fails
            ValueError: If the path is invalid or doesn't exist
            KeyError: If the path doesn't exist in the file
        
        Example:
            >>> host = serializer.atomic_read_path("config.json", "/database/host")
        """
        pass
    
    @abstractmethod
    def validate_with_schema(
        self, 
        data: Any, 
        schema: Any, 
        **options
    ) -> bool:
        """
        Validate data against a schema.
        
        Args:
            data: Data to validate
            schema: Schema definition (format-specific)
            **options: Validation options
        
        Returns:
            True if data is valid
        
        Raises:
            NotImplementedError: If this format doesn't support schema validation
            SerializationError: If validation fails
        """
        pass
    
    @abstractmethod
    def incremental_save(
        self, 
        items: Iterator[Any], 
        file_path: Union[str, Path], 
        **options
    ) -> None:
        """
        Incrementally save items to a file using true streaming (not chunked full-file).
        
        This method writes items one at a time as they're provided, enabling
        memory-efficient handling of large datasets.
        
        Args:
            items: Iterator of items to save
            file_path: Path to save file
            **options: Format-specific options
        
        Raises:
            NotImplementedError: If this format doesn't support incremental streaming
            SerializationError: If save operation fails
        """
        pass
    
    @abstractmethod
    def incremental_load(
        self, 
        file_path: Union[str, Path], 
        **options
    ) -> Iterator[Any]:
        """
        Incrementally load items from a file using true streaming.
        
        This method reads items one at a time as they're needed, enabling
        memory-efficient handling of large files.
        
        Args:
            file_path: Path to load from
            **options: Format-specific options
        
        Yields:
            Items from the file one at a time
        
        Raises:
            NotImplementedError: If this format doesn't support incremental streaming
            SerializationError: If load operation fails
        """
        pass
    
    @abstractmethod
    def query(
        self, 
        file_path: Union[str, Path], 
        query_expr: str, 
        **options
    ) -> Any:
        """
        Query/filter data from a file using format-specific query language.
        
        Supports query languages like JSONPath for JSON, XPath for XML, etc.
        
        Args:
            file_path: Path to the file to query
            query_expr: Query expression (format-specific: JSONPath, XPath, etc.)
            **options: Query options
        
        Returns:
            Query results (format-specific)
        
        Raises:
            NotImplementedError: If this format doesn't support queries
            SerializationError: If query operation fails
            ValueError: If query expression is invalid
        """
        pass
    
    @abstractmethod
    def merge(
        self, 
        file_path: Union[str, Path], 
        updates: dict[str, Any], 
        **options
    ) -> None:
        """
        Merge updates into a file.
        
        Performs deep or shallow merge depending on format capabilities.
        
        Args:
            file_path: Path to the file to update
            updates: Dictionary of updates to merge
            **options: Merge options (deep, shallow, etc.)
        
        Raises:
            NotImplementedError: If this format doesn't support merge operations
            SerializationError: If merge operation fails
        """
        pass

    # ========================================================================
    # RECORD-LEVEL OPERATIONS (Optional, generic defaults in ASerialization)
    # ========================================================================

    def stream_read_record(
        self,
        file_path: Union[str, Path],
        match: callable,
        projection: Optional[list[Any]] = None,
        **options: Any,
    ) -> Any:
        """
        Stream-style read of a single logical record from a file.

        Semantics:
        - Treat the underlying representation as a sequence of logical records
          (e.g., list elements, table rows, NDJSON records).
        - Return the first record that satisfies `match(record)`.
        - If `projection` is provided, return only that sub-structure.

        Concrete serializers may override this for efficient, true streaming
        (e.g., NDJSON line-by-line). The default implementation in ASerialization
        is allowed to load the full file and scan in memory.
        """
        raise NotImplementedError

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
        Stream-style update of logical records in a file.

        Semantics:
        - Apply `updater(record)` to each record for which `match(record)` is True.
        - When `atomic=True`, must preserve atomicity guarantees (temp file +
          replace, or equivalent) provided by the underlying serializer/I/O.
        - Returns the number of updated records.

        Concrete serializers may override this to avoid loading the full file.
        The default implementation in ASerialization may be full-load.
        """
        raise NotImplementedError

    def get_record_page(
        self,
        file_path: Union[str, Path],
        page_number: int,
        page_size: int,
        **options: Any,
    ) -> list[Any]:
        """
        Retrieve a logical page of records from a file.

        Semantics:
        - page_number is 1-based.
        - page_size is the number of records.
        - Returns a list of native records.

        Concrete serializers may override this to use indexes or streaming.
        The default implementation in ASerialization may load the entire file
        and slice a top-level list.
        """
        raise NotImplementedError

    def get_record_by_id(
        self,
        file_path: Union[str, Path],
        id_value: Any,
        *,
        id_field: str = "id",
        **options: Any,
    ) -> Any:
        """
        Retrieve a logical record by identifier (e.g., record[id_field] == id_value).

        Concrete serializers may override this to use an index or format-specific
        mechanisms. The default implementation in ASerialization may perform a
        linear scan over a top-level list.
        """
        raise NotImplementedError

