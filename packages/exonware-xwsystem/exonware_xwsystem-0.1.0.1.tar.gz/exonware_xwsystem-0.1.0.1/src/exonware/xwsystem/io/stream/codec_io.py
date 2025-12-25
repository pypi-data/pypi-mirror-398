#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/stream/codec_io.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Codec-integrated I/O - THE KILLER FEATURE!

Seamless integration of codec + data source for automatic encoding/decoding.

Priority 1 (Security): Safe encoding/decoding with validation
Priority 2 (Usability): Auto-detect codec from file extension - zero config!
Priority 3 (Maintainability): Clean separation of codec and I/O
Priority 4 (Performance): Memory-efficient paging for huge files
Priority 5 (Extensibility): Works with ANY codec + ANY data source
"""

from pathlib import Path
from typing import Union, Optional, Iterator, Any

from ..contracts import ICodecIO, IPagedCodecIO, IDataSource, IPagedDataSource


class CodecIO[T, R](ICodecIO[T, R]):
    """
    I/O operations with integrated codec - THE KILLER FEATURE!
    
    Combines codec + data source for seamless persistence. No more manual
    encode/decode/write glue code!
    
    Type Parameters:
        T: Model type (your data structure)
        R: Representation type (bytes or str)
    
    Examples:
        >>> # Auto-detect codec from file extension
        >>> io = CodecIO.from_file("config.json")
        >>> io.save({"key": "value"})
        >>> data = io.load()
        
        >>> # Explicit codec
        >>> from exonware.xwsystem.io.codec import get_codec_by_id
        >>> codec = get_codec_by_id("json")
        >>> source = FileDataSource("data.json")
        >>> io = CodecIO(codec, source)
        >>> io.save(my_dict, pretty=True)
    """
    
    def __init__(self, codec, source: IDataSource[R]):
        """
        Initialize CodecIO.
        
        Args:
            codec: ICodec[T, R] instance
            source: Data source (file, HTTP, etc.)
        """
        self._codec = codec
        self._source = source
    
    @property
    def codec(self):
        """The codec used for encoding/decoding."""
        return self._codec
    
    @property
    def source(self) -> IDataSource[R]:
        """The data source."""
        return self._source
    
    def save(self, value: T, **opts) -> None:
        """
        Encode value and write to source.
        
        Equivalent to: source.write(codec.encode(value))
        
        Args:
            value: Value to save
            **opts: Encoding options (passed to codec.encode)
        
        Example:
            io.save({"key": "value"}, pretty=True)
        """
        try:
            # Separate codec options from source options
            codec_opts = {k: v for k, v in opts.items() if k not in ['atomic', 'backup', 'encoding']}
            source_opts = {k: v for k, v in opts.items() if k in ['atomic', 'backup', 'encoding']}
            
            # Encode
            encoded = self._codec.encode(value, options=codec_opts if codec_opts else None)
            
            # Write
            self._source.write(encoded, **source_opts)
        except Exception as e:
            raise IOError(f"Failed to save via CodecIO: {e}")
    
    def load(self, **opts) -> T:
        """
        Read from source and decode value.
        
        Equivalent to: codec.decode(source.read())
        
        Args:
            **opts: Decoding options (passed to codec.decode)
        
        Returns:
            Decoded value
        
        Example:
            data = io.load()
        """
        try:
            # Separate codec options from source options
            codec_opts = {k: v for k, v in opts.items() if k not in ['encoding']}
            source_opts = {k: v for k, v in opts.items() if k in ['encoding']}
            
            # Read
            data = self._source.read(**source_opts)
            
            # Decode
            return self._codec.decode(data, options=codec_opts if codec_opts else None)
        except Exception as e:
            raise IOError(f"Failed to load via CodecIO: {e}")
    
    def exists(self) -> bool:
        """Check if source exists."""
        return self._source.exists()
    
    def delete(self) -> None:
        """Delete source."""
        self._source.delete()
    
    def update_path(self, path: str, value: Any, **opts) -> None:
        """
        Update a single path in the file using atomic path operations if supported.
        
        Checks if the codec (serializer) supports atomic path updates. If supported,
        uses atomic_update_path for efficient updates. Otherwise, falls back to
        full-file load/modify/save.
        
        Args:
            path: Path expression (format-specific: JSONPointer, XPath, etc.)
            value: Value to set at the specified path
            **opts: Options (backup, atomic, etc.)
        
        Raises:
            NotImplementedError: If path updates not supported and fallback fails
            IOError: If update operation fails
        
        Example:
            >>> io = CodecIO.from_file("config.json")
            >>> io.update_path("/database/host", "localhost")
        """
        # Check if codec supports atomic path operations
        if hasattr(self._codec, 'supports_atomic_path_write') and self._codec.supports_atomic_path_write:
            # Get file path from source
            if hasattr(self._source, '_path'):
                file_path = self._source._path
                # Use atomic path update
                self._codec.atomic_update_path(file_path, path, value, **opts)
                return
        
        # Fallback: load full file, update in memory, save
        data = self.load(**opts)
        
        # Simple path update (subclasses should override for format-specific logic)
        if isinstance(data, dict) and path.startswith('/'):
            from ..serialization.utils.path_ops import set_value_by_path
            set_value_by_path(data, path, value, create=opts.get('create', False))
        else:
            raise NotImplementedError(
                f"Path updates not supported for codec {type(self._codec).__name__} "
                f"and data type {type(data)}"
            )
        
        # Save updated data
        self.save(data, **opts)
    
    def read_path(self, path: str, **opts) -> Any:
        """
        Read a single path from the file using atomic path operations if supported.
        
        Checks if the codec (serializer) supports atomic path reads. If supported,
        uses atomic_read_path for efficient reads. Otherwise, falls back to
        full-file load and path extraction.
        
        Args:
            path: Path expression (format-specific: JSONPointer, XPath, etc.)
            **opts: Options
        
        Returns:
            Value at the specified path
        
        Raises:
            NotImplementedError: If path reads not supported
            KeyError: If path doesn't exist
            IOError: If read operation fails
        
        Example:
            >>> io = CodecIO.from_file("config.json")
            >>> host = io.read_path("/database/host")
        """
        # Check if codec supports atomic path operations
        if hasattr(self._codec, 'supports_atomic_path_write') and self._codec.supports_atomic_path_write:
            # Get file path from source
            if hasattr(self._source, '_path'):
                file_path = self._source._path
                # Use atomic path read
                return self._codec.atomic_read_path(file_path, path, **opts)
        
        # Fallback: load full file, extract path
        data = self.load(**opts)
        
        # Simple path extraction (subclasses should override for format-specific logic)
        if isinstance(data, dict) and path.startswith('/'):
            from ..serialization.utils.path_ops import get_value_by_path
            return get_value_by_path(data, path)
        else:
            raise NotImplementedError(
                f"Path reads not supported for codec {type(self._codec).__name__} "
                f"and data type {type(data)}"
            )
    
    @staticmethod
    def from_file(path: Union[str, Path], mode: str = 'rb', encoding: Optional[str] = None):
        """
        Create CodecIO with auto-detected codec from file extension.
        
        Args:
            path: File path
            mode: File mode ('rb' or 'r')
            encoding: Text encoding (for text mode)
        
        Returns:
            CodecIO instance with appropriate codec
        
        Raises:
            CodecNotFoundError: If no codec found for file extension
        
        Example:
            >>> io = CodecIO.from_file("data.json")
            >>> io.save({"key": "value"})
        """
        from ..codec import get_codec_for_file, CodecNotFoundError
        from ..file.source import FileDataSource
        
        # Get codec by file extension
        codec = get_codec_for_file(str(path))
        if codec is None:
            raise CodecNotFoundError(f"No codec found for file: {path}")
        
        # Create data source
        source = FileDataSource(path, mode=mode, encoding=encoding)
        
        return CodecIO(codec, source)


class PagedCodecIO[T, R](CodecIO[T, R], IPagedCodecIO[T, R]):
    """
    CodecIO with paging support - for BIG data files!
    
    Memory-efficient processing of huge files:
    - 10GB SQL dumps
    - Million-row CSVs
    - Large JSONL files
    
    Combines paged reading + codec decoding for seamless large file handling.
    
    Type Parameters:
        T: Model type (record, row, statement, etc.)
        R: Representation type (bytes or str)
    
    Examples:
        >>> # Process 10GB SQL file without loading it all
        >>> sql_io = PagedCodecIO.from_file("dump.sql")
        >>> for query_ast in sql_io.iter_items(page_size=100):
        ...     execute(query_ast)  # Already decoded!
        
        >>> # Load specific page from huge CSV
        >>> csv_io = PagedCodecIO.from_file("big_data.csv")
        >>> rows = csv_io.load_page(page=5, page_size=1000)
    """
    
    def __init__(self, codec, source: IPagedDataSource[R]):
        """
        Initialize PagedCodecIO.
        
        Args:
            codec: ICodec[T, R] instance
            source: Paged data source
        """
        super().__init__(codec, source)
        if not isinstance(source, IPagedDataSource):
            raise TypeError("PagedCodecIO requires IPagedDataSource")
    
    @property
    def paged_source(self) -> IPagedDataSource[R]:
        """Get underlying paged data source."""
        return self._source
    
    def iter_items(self, page_size: int = 1000, **opts) -> Iterator[T]:
        """
        Iterate over decoded items page by page.
        
        NOTE: This assumes the codec can decode individual items from chunks.
        For line-based formats (JSONL, CSV), this works naturally.
        For formats that require complete documents (JSON), use load() instead.
        
        Args:
            page_size: Items per page
            **opts: Codec decode options
        
        Yields:
            Decoded items one by one
        
        Example:
            # Process 10GB JSONL file without loading it all
            jsonl_io = PagedCodecIO.from_file("huge.jsonl")
            for record in jsonl_io.iter_items(page_size=100):
                process(record)  # Already decoded!
        """
        for page_content in self.paged_source.iter_pages(page_size, **opts):
            # Decode the page
            try:
                decoded = self._codec.decode(page_content, options=opts if opts else None)
                # If decoded is iterable (e.g., list of records), yield each item
                if hasattr(decoded, '__iter__') and not isinstance(decoded, (str, bytes)):
                    for item in decoded:
                        yield item
                else:
                    yield decoded
            except Exception:
                # Skip invalid chunks
                continue
    
    def load_page(self, page: int, page_size: int, **opts) -> list[T]:
        """
        Load and decode specific page.
        
        Args:
            page: Page number (0-based)
            page_size: Items per page
            **opts: Codec decode options
        
        Returns:
            List of decoded items for that page
        
        Example:
            # Load rows 5000-5999 from huge CSV
            csv_io = PagedCodecIO.from_file("big_data.csv")
            rows = csv_io.load_page(page=5, page_size=1000)
        """
        page_content = self.paged_source.read_page(page, page_size, **opts)
        decoded = self._codec.decode(page_content, options=opts if opts else None)
        
        # Return as list if not already
        if isinstance(decoded, list):
            return decoded
        elif hasattr(decoded, '__iter__') and not isinstance(decoded, (str, bytes)):
            return list(decoded)
        else:
            return [decoded]
    
    def save_batch(self, items: list[T], append: bool = True, **opts) -> None:
        """
        Encode and save multiple items efficiently.
        
        Args:
            items: List of items to save
            append: Whether to append or overwrite
            **opts: Codec encode options
        
        Example:
            io.save_batch(records, append=True)
        """
        encoded_items = []
        for item in items:
            encoded = self._codec.encode(item, options=opts if opts else None)
            encoded_items.append(encoded)
        
        # Combine encoded items
        if encoded_items and isinstance(encoded_items[0], bytes):
            combined = b'\n'.join(encoded_items)
        else:
            combined = '\n'.join(encoded_items)
        
        # Write - update source mode temporarily if needed
        if hasattr(self._source, '_mode'):
            write_mode = 'ab' if append and isinstance(combined, bytes) else 'a' if append else 'wb' if isinstance(combined, bytes) else 'w'
            old_mode = self._source._mode
            self._source._mode = write_mode
            try:
                self._source.write(combined, **opts)
            finally:
                self._source._mode = old_mode
        else:
            self._source.write(combined, **opts)
    
    @staticmethod
    def from_file(path: Union[str, Path], mode: str = 'rb', encoding: Optional[str] = None):
        """
        Create PagedCodecIO with auto-detected codec from file extension.
        
        Args:
            path: File path
            mode: File mode ('rb' or 'r')
            encoding: Text encoding (for text mode)
        
        Returns:
            PagedCodecIO instance with appropriate codec
        
        Raises:
            CodecNotFoundError: If no codec found for file extension
        
        Example:
            >>> io = PagedCodecIO.from_file("huge.csv")
            >>> for rows in io.iter_items(page_size=1000):
            ...     process(rows)
        """
        from ..codec import get_codec_for_file, CodecNotFoundError
        from ..file.paged_source import PagedFileSource
        
        # Get codec by file extension
        codec = get_codec_for_file(str(path))
        if codec is None:
            raise CodecNotFoundError(f"No codec found for file: {path}")
        
        # Create paged data source
        source = PagedFileSource(path, mode=mode, encoding=encoding)
        
        return PagedCodecIO(codec, source)

