"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

XWIO - Main facade for all I/O operations (MANDATORY facade pattern).

This is the primary entry point for the IO module, following GUIDELINES_DEV.md.
"""

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Optional, Union, BinaryIO, TextIO

from .base import AUnifiedIO
from .contracts import FileMode, FileType, PathType, OperationResult, LockType, IUnifiedIO
from .common.atomic import AtomicFileWriter
from .stream.async_operations import AsyncAtomicFileWriter
from ..config.logging_setup import get_logger
from ..security.path_validator import PathValidator
from ..validation.data_validator import DataValidator
from ..monitoring.performance_monitor import performance_monitor

logger = get_logger(__name__)


class XWIO(AUnifiedIO):
    """
    Main I/O Facade - Primary entry point for all I/O operations.
    
    This is the MANDATORY facade pattern implementation per GUIDELINES_DEV.md.
    Provides unified interface to all I/O capabilities:
    
    Features:
    - File operations (via XWFile delegation)
    - Directory operations (via XWFolder delegation)
    - Path operations with validation
    - Stream operations with context management
    - Async operations with aiofiles integration
    - Atomic operations with backup support
    - Backup operations with cleanup
    - Temporary operations with automatic cleanup
    - Codec integration for seamless data persistence
    - Archive operations (via archiver delegation)
    
    Design Pattern: FACADE (MANDATORY)
    - Simplifies complex subsystems
    - Single entry point for all I/O
    - Delegates to specialized components
    """
    
    def __init__(self, file_path: Optional[Union[str, Path]] = None, **config):
        """
        Initialize XWIO facade.
        
        Args:
            file_path: Optional file path for file operations
            **config: Configuration options for I/O operations
        """
        super().__init__(file_path, **config)
        
        # Initialize xwsystem utilities
        self._path_validator = PathValidator()
        self._data_validator = DataValidator()
        
        # Configuration
        self.auto_create_dirs = config.get('auto_create_dirs', True)
        self.auto_backup = config.get('auto_backup', True)
        self.auto_cleanup = config.get('auto_cleanup', True)
        self.max_file_size = config.get('max_file_size', 100 * 1024 * 1024)  # 100MB
        self.timeout_seconds = config.get('timeout_seconds', 30)
        
        logger.debug(f"XWIO facade initialized for path: {file_path}")
    
    # ============================================================================
    # FILE OPERATIONS
    # ============================================================================
    
    def open_file(self, file_path: Optional[Union[str, Path]] = None, mode: FileMode = FileMode.READ) -> None:
        """Open file with validation and monitoring."""
        target_path = Path(file_path) if file_path else self.file_path
        if not target_path:
            raise ValueError("No file path specified")
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        with performance_monitor("file_open"):
            # Ensure parent directory exists
            if self.auto_create_dirs and mode in [FileMode.WRITE, FileMode.APPEND, FileMode.WRITE_READ]:
                target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Open file
            self._handle = open(target_path, mode.value)
            self.file_path = target_path
            logger.debug(f"File opened: {target_path} in mode {mode.value}")
    
    def open_stream(self, stream: Union[BinaryIO, TextIO]) -> None:
        """Open stream for stream operations."""
        self._stream = stream
        self._position = 0
        logger.debug("Stream opened")
    
    # ============================================================================
    # ABSTRACT METHOD IMPLEMENTATIONS (from AFile)
    # ============================================================================
    
    # Keep open() for backward compatibility - delegate to file operations
    def open(self, mode: FileMode = FileMode.READ) -> None:
        """Open file with validation and monitoring (alias for open_file())."""
        self.open_file(mode=mode)
    
    def read(self, size: Optional[int] = None) -> Union[str, bytes]:
        """
        Read from file (implements AFile abstract method).
        
        Delegates to read_file() for file operations.
        For stream operations, use read() after open_stream().
        """
        if self._stream:
            # Stream operation
            if not self._stream:
                raise ValueError("Stream not initialized")
            data = self._stream.read(size)
            self._position += len(data) if data else 0
            return data
        else:
            # File operation  
            return self.read_file(size)
    
    def write(self, data: Union[str, bytes]) -> int:
        """
        Write to file (implements AFile abstract method).
        
        Delegates to write_file() for file operations.
        For stream operations, use write() after open_stream().
        """
        if self._stream:
            # Stream operation
            if not self._stream:
                raise ValueError("Stream not initialized")
            result = self._stream.write(data)
            self._position += result
            return result
        else:
            # File operation
            return self.write_file(data)
    
    def save_as(self, path: Union[str, Path], data: Any, **kwargs) -> bool:
        """
        Save data to specific path (implements AFile abstract method).
        
        Args:
            path: Target file path
            data: Data to save
            **kwargs: Additional options
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.save(data, file_path=path, **kwargs)
            return True
        except Exception as e:
            logger.error(f"Failed to save data to {path}: {e}")
            return False
    
    def to_file(self, path: Union[str, Path], **kwargs) -> bool:
        """
        Write current data to file (implements AFile abstract method).
        
        Args:
            path: Target file path
            **kwargs: Additional options
            
        Returns:
            True if successful, False otherwise
        """
        # If we have current data buffered, save it
        current_data = getattr(self, '_current_data', None)
        if current_data is not None:
            return self.save_as(path, current_data, **kwargs)
        
        # If file is open, copy current file to target
        if self.file_path and self.file_path.exists():
            try:
                shutil.copy2(self.file_path, path)
                return True
            except Exception as e:
                logger.error(f"Failed to copy file to {path}: {e}")
                return False
        
        logger.warning("No data to write to file")
        return False
    
    def from_file(self, path: Union[str, Path], **kwargs) -> 'XWIO':
        """
        Load data from file and return new XWIO instance (implements AFile abstract method).
        
        Args:
            path: Source file path
            **kwargs: Additional options
            
        Returns:
            New XWIO instance with loaded data
        """
        new_instance = XWIO(file_path=path, **self.__dict__.get('_config', {}))
        new_instance._current_data = new_instance.load(file_path=path, **kwargs)
        return new_instance
    
    def read_file(self, size: Optional[int] = None) -> Union[str, bytes]:
        """Read from file with validation."""
        if not self.is_open():
            raise ValueError("File not open")
        
        with performance_monitor("file_read"):
            data = self._handle.read(size)
            
            if self.validate_data and isinstance(data, (str, bytes)):
                self._data_validator.validate_data(data)
            
            return data
    
    def write_file(self, data: Union[str, bytes]) -> int:
        """Write to file with validation."""
        if not self.is_open():
            raise ValueError("File not open")
        
        if self.validate_data:
            self._data_validator.validate_data(data)
        
        with performance_monitor("file_write"):
            return self._handle.write(data)
    
    
    def save(self, data: Any, file_path: Optional[Union[str, Path]] = None) -> None:
        """Save data to file with atomic operations."""
        target_path = Path(file_path) if file_path else self.file_path
        if not target_path:
            raise ValueError("No file path specified")
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        if self.validate_data:
            self._data_validator.validate_data(data)
        
        with performance_monitor("file_save"):
            if self.use_atomic_operations:
                # Use atomic file writer
                with AtomicFileWriter(target_path, backup=self.auto_backup) as writer:
                    if isinstance(data, str):
                        writer.write(data.encode('utf-8'))
                    else:
                        writer.write(data)
            else:
                # Direct write
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, 'wb' if isinstance(data, bytes) else 'w') as f:
                    f.write(data)
    
    def load(self, file_path: Optional[Union[str, Path]] = None) -> Any:
        """Load data from file with validation."""
        target_path = Path(file_path) if file_path else self.file_path
        if not target_path:
            raise ValueError("No file path specified")
        
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {target_path}")
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        with performance_monitor("file_load"):
            # Try to read as text first, then binary
            try:
                with open(target_path, 'r', encoding='utf-8') as f:
                    data = f.read()
            except UnicodeDecodeError:
                with open(target_path, 'rb') as f:
                    data = f.read()
            
            if self.validate_data:
                self._data_validator.validate_data(data)
            
            return data
    
    def close_file(self) -> None:
        """Close file handle."""
        if self._handle and not self._handle.closed:
            self._handle.close()
            logger.debug(f"File closed: {self.file_path}")
    
    
    # ============================================================================
    # DIRECTORY OPERATIONS
    # ============================================================================
    
    def create(self, parents: bool = True, exist_ok: bool = True) -> bool:
        """Create directory with validation."""
        if not self.dir_path:
            raise ValueError("No directory path specified")
        
        if self.validate_paths:
            self._path_validator.validate_path(self.dir_path)
        
        with performance_monitor("directory_create"):
            try:
                self.dir_path.mkdir(parents=parents, exist_ok=exist_ok)
                logger.debug(f"Directory created: {self.dir_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to create directory {self.dir_path}: {e}")
                return False
    
    def delete(self, recursive: bool = False) -> bool:
        """Delete directory with validation."""
        if not self.dir_path:
            raise ValueError("No directory path specified")
        
        if self.validate_paths:
            self._path_validator.validate_path(self.dir_path)
        
        with performance_monitor("directory_delete"):
            try:
                if recursive:
                    shutil.rmtree(self.dir_path)
                else:
                    self.dir_path.rmdir()
                logger.debug(f"Directory deleted: {self.dir_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete directory {self.dir_path}: {e}")
                return False
    
    # ============================================================================
    # ATOMIC OPERATIONS
    # ============================================================================
    
    def atomic_write(self, file_path: Union[str, Path], data: Union[str, bytes], 
                    backup: bool = True) -> OperationResult:
        """Atomically write data to file."""
        target_path = Path(file_path)
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        if self.validate_data:
            self._data_validator.validate_data(data)
        
        with performance_monitor("atomic_write"):
            try:
                with AtomicFileWriter(target_path, backup=backup) as writer:
                    if isinstance(data, str):
                        writer.write(data.encode('utf-8'))
                    else:
                        writer.write(data)
                return OperationResult.SUCCESS
            except Exception as e:
                logger.error(f"Atomic write failed for {target_path}: {e}")
                return OperationResult.FAILED
    
    def atomic_copy(self, source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically copy file."""
        source_path = Path(source)
        dest_path = Path(destination)
        
        if self.validate_paths:
            self._path_validator.validate_path(source_path)
            self._path_validator.validate_path(dest_path)
        
        with performance_monitor("atomic_copy"):
            try:
                # Use atomic file writer for destination
                with open(source_path, 'rb') as src:
                    with AtomicFileWriter(dest_path) as writer:
                        shutil.copyfileobj(src, writer)
                return OperationResult.SUCCESS
            except Exception as e:
                logger.error(f"Atomic copy failed from {source_path} to {dest_path}: {e}")
                return OperationResult.FAILED
    
    def atomic_move(self, source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically move file."""
        source_path = Path(source)
        dest_path = Path(destination)
        
        if self.validate_paths:
            self._path_validator.validate_path(source_path)
            self._path_validator.validate_path(dest_path)
        
        with performance_monitor("atomic_move"):
            try:
                # Ensure destination directory exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Use atomic move (copy + delete)
                with open(source_path, 'rb') as src:
                    with AtomicFileWriter(dest_path) as writer:
                        shutil.copyfileobj(src, writer)
                
                # Delete source after successful copy
                source_path.unlink()
                return OperationResult.SUCCESS
            except Exception as e:
                logger.error(f"Atomic move failed from {source_path} to {dest_path}: {e}")
                return OperationResult.FAILED
    
    def atomic_delete(self, file_path: Union[str, Path], backup: bool = True) -> OperationResult:
        """Atomically delete file."""
        target_path = Path(file_path)
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        with performance_monitor("atomic_delete"):
            try:
                if backup and target_path.exists():
                    self.create_backup(target_path)
                
                if target_path.exists():
                    target_path.unlink()
                
                return OperationResult.SUCCESS
            except Exception as e:
                logger.error(f"Atomic delete failed for {target_path}: {e}")
                return OperationResult.FAILED
    
    def atomic_rename(self, old_path: Union[str, Path], new_path: Union[str, Path]) -> OperationResult:
        """Atomically rename file."""
        old_file = Path(old_path)
        new_file = Path(new_path)
        
        if self.validate_paths:
            self._path_validator.validate_path(old_file)
            self._path_validator.validate_path(new_file)
        
        with performance_monitor("atomic_rename"):
            try:
                # Ensure new directory exists
                new_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Use atomic move for rename
                return self.atomic_move(old_file, new_file)
            except Exception as e:
                logger.error(f"Atomic rename failed from {old_file} to {new_file}: {e}")
                return OperationResult.FAILED
    
    # ============================================================================
    # BACKUP OPERATIONS
    # ============================================================================
    
    def create_backup(self, source: Union[str, Path], backup_dir: Union[str, Path]) -> Optional[Path]:
        """Create backup of file or directory."""
        source_path = Path(source)
        backup_path = Path(backup_dir)
        
        if self.validate_paths:
            self._path_validator.validate_path(source_path)
            self._path_validator.validate_path(backup_path)
        
        with performance_monitor("backup_create"):
            try:
                backup_path.mkdir(parents=True, exist_ok=True)
                
                if source_path.is_file():
                    # File backup
                    backup_file = backup_path / f"{source_path.name}.backup.{int(time.time())}"
                    shutil.copy2(source_path, backup_file)
                    return backup_file
                elif source_path.is_dir():
                    # Directory backup
                    backup_dir = backup_path / f"{source_path.name}.backup.{int(time.time())}"
                    shutil.copytree(source_path, backup_dir)
                    return backup_dir
                else:
                    return None
            except Exception as e:
                logger.error(f"Backup creation failed for {source_path}: {e}")
                return None
    
    def restore_backup(self, backup_path: Union[str, Path], target: Union[str, Path]) -> OperationResult:
        """Restore from backup."""
        backup = Path(backup_path)
        target_path = Path(target)
        
        if self.validate_paths:
            self._path_validator.validate_path(backup)
            self._path_validator.validate_path(target_path)
        
        with performance_monitor("backup_restore"):
            try:
                if backup.is_file():
                    # File restore
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup, target_path)
                elif backup.is_dir():
                    # Directory restore
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.copytree(backup, target_path)
                else:
                    return OperationResult.FAILED
                
                return OperationResult.SUCCESS
            except Exception as e:
                logger.error(f"Backup restore failed from {backup} to {target_path}: {e}")
                return OperationResult.FAILED
    
    # ============================================================================
    # TEMPORARY OPERATIONS
    # ============================================================================
    
    def create_temp_file(self, suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary file."""
        with performance_monitor("temp_file_create"):
            try:
                # Create temporary file
                fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, 
                                               dir=self.get_temp_base_dir())
                os.close(fd)  # Close file descriptor
                
                temp_file = Path(temp_path)
                self._temp_files.append(temp_file)
                
                logger.debug(f"Temporary file created: {temp_file}")
                return temp_file
            except Exception as e:
                logger.error(f"Failed to create temporary file: {e}")
                raise
    
    def create_temp_directory(self, suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary directory."""
        with performance_monitor("temp_dir_create"):
            try:
                temp_path = tempfile.mkdtemp(suffix=suffix, prefix=prefix,
                                           dir=self.get_temp_base_dir())
                temp_dir = Path(temp_path)
                self._temp_dirs.append(temp_dir)
                
                logger.debug(f"Temporary directory created: {temp_dir}")
                return temp_dir
            except Exception as e:
                logger.error(f"Failed to create temporary directory: {e}")
                raise
    
    # ============================================================================
    # ASYNC OPERATIONS
    # ============================================================================
    
    async def aread(self, size: Optional[int] = None) -> Union[str, bytes]:
        """Async read operation."""
        if not self._async_stream:
            raise ValueError("Async stream not initialized")
        
        with performance_monitor("async_read"):
            return await self._async_stream.read(size)
    
    async def awrite(self, data: Union[str, bytes]) -> int:
        """Async write operation."""
        if not self._async_stream:
            raise ValueError("Async stream not initialized")
        
        if self.validate_data:
            self._data_validator.validate_data(data)
        
        with performance_monitor("async_write"):
            return await self._async_stream.write(data)
    
    async def aseek(self, position: int, whence: int = 0) -> int:
        """Async seek operation."""
        if not self._async_stream:
            raise ValueError("Async stream not initialized")
        
        return await self._async_stream.seek(position, whence)
    
    async def atell(self) -> int:
        """Async tell operation."""
        if not self._async_stream:
            raise ValueError("Async stream not initialized")
        
        return await self._async_stream.tell()
    
    async def aflush(self) -> None:
        """Async flush operation."""
        if not self._async_stream:
            raise ValueError("Async stream not initialized")
        
        await self._async_stream.flush()
    
    async def aclose(self) -> None:
        """Async close operation."""
        if self._async_stream:
            await self._async_stream.close()
            self._async_stream = None
            self._closed = True
    
    # ============================================================================
    # STREAM OPERATIONS
    # ============================================================================
    
    
    def seek(self, position: int, whence: int = 0) -> int:
        """Seek stream position."""
        if not self._stream:
            raise ValueError("Stream not initialized")
        
        new_position = self._stream.seek(position, whence)
        self._position = new_position
        return new_position
    
    def tell(self) -> int:
        """Get current stream position."""
        if not self._stream:
            raise ValueError("Stream not initialized")
        
        self._position = self._stream.tell()
        return self._position
    
    def flush(self) -> None:
        """Flush stream buffer."""
        if not self._stream:
            raise ValueError("Stream not initialized")
        
        self._stream.flush()
    
    def close(self) -> None:
        """Close stream."""
        if self._stream:
            self._stream.close()
            self._stream = None
            self._closed = True
    
    # ============================================================================
    # CODEC INTEGRATION (UniversalCodecRegistry)
    # ============================================================================
    
    def serialize(self, data: Any, format_id: str, **options) -> Union[bytes, str]:
        """
        Serialize data using specified format.
        
        Uses UniversalCodecRegistry for codec lookup.
        
        Args:
            data: Data to serialize
            format_id: Format identifier (e.g., 'json', 'yaml', 'msgpack')
            **options: Format-specific options
        
        Returns:
            Serialized data (bytes or str depending on format)
        
        Examples:
            >>> io = XWIO()
            >>> json_str = io.serialize({"key": "value"}, "json")
            >>> yaml_str = io.serialize(config, "yaml", indent=2)
        """
        from .codec.registry import get_registry
        
        registry = get_registry()
        codec = registry.get_by_id(format_id)
        
        if codec is None:
            raise ValueError(f"Unknown format: {format_id}")
        
        return codec.encode(data, options=options or None)
    
    def deserialize(self, data: Union[bytes, str], format_id: str, **options) -> Any:
        """
        Deserialize data using specified format.
        
        Uses UniversalCodecRegistry for codec lookup.
        
        Args:
            data: Serialized data
            format_id: Format identifier (e.g., 'json', 'yaml', 'msgpack')
            **options: Format-specific options
        
        Returns:
            Deserialized data
        
        Examples:
            >>> io = XWIO()
            >>> data = io.deserialize(json_str, "json")
            >>> config = io.deserialize(yaml_bytes, "yaml")
        """
        from .codec.registry import get_registry
        
        registry = get_registry()
        codec = registry.get_by_id(format_id)
        
        if codec is None:
            raise ValueError(f"Unknown format: {format_id}")
        
        return codec.decode(data, options=options or None)
    
    def save_serialized(self, data: Any, file_path: Union[str, Path], format_id: Optional[str] = None, **options) -> None:
        """
        Serialize and save data to file.
        
        Auto-detects format from file extension if format_id not provided.
        
        Args:
            data: Data to serialize
            file_path: Path to save file
            format_id: Optional format identifier (auto-detected if None)
            **options: Format-specific options
        
        Examples:
            >>> io = XWIO()
            >>> io.save_serialized({"key": "value"}, "data.json")  # Auto-detect
            >>> io.save_serialized(config, "config.yaml", "yaml", indent=2)
        """
        from .codec.registry import get_registry
        from .serialization import ISerialization
        
        path = Path(file_path)
        registry = get_registry()
        
        # Auto-detect format if not provided
        if format_id is None:
            codec = registry.detect(path)
            if codec is None:
                raise ValueError(f"Cannot detect format from: {path}")
        else:
            codec = registry.get_by_id(format_id)
            if codec is None:
                raise ValueError(f"Unknown format: {format_id}")
        
        # Use save_file if it's a serializer
        if isinstance(codec, ISerialization):
            codec.save_file(data, path, **options)
        else:
            # Fallback to encode + write
            repr_data = codec.encode(data, options=options or None)
            if isinstance(repr_data, bytes):
                path.write_bytes(repr_data)
            else:
                path.write_text(repr_data, encoding='utf-8')
    
    def load_serialized(self, file_path: Union[str, Path], format_id: Optional[str] = None, **options) -> Any:
        """
        Load and deserialize data from file.
        
        Auto-detects format from file extension if format_id not provided.
        
        Args:
            file_path: Path to load from
            format_id: Optional format identifier (auto-detected if None)
            **options: Format-specific options
        
        Returns:
            Deserialized data
        
        Examples:
            >>> io = XWIO()
            >>> data = io.load_serialized("data.json")  # Auto-detect
            >>> config = io.load_serialized("config.yaml", "yaml")
        """
        from .codec.registry import get_registry
        from .serialization import ISerialization
        
        path = Path(file_path)
        registry = get_registry()
        
        # Auto-detect format if not provided
        if format_id is None:
            codec = registry.detect(path)
            if codec is None:
                raise ValueError(f"Cannot detect format from: {path}")
        else:
            codec = registry.get_by_id(format_id)
            if codec is None:
                raise ValueError(f"Unknown format: {format_id}")
        
        # Use load_file if it's a serializer
        if isinstance(codec, ISerialization):
            return codec.load_file(path, **options)
        else:
            # Fallback to read + decode
            repr_data = path.read_bytes()
            return codec.decode(repr_data, options=options or None)
    
    # ============================================================================
    # CONVENIENCE ALIASES (User-friendly API)
    # ============================================================================
    
    def load_as(self, file_path: Union[str, Path], format_id: str, **options) -> Any:
        """
        Load data from file using specified format (convenience alias).
        
        Alias for load_serialized() with explicit format.
        
        Args:
            file_path: Path to load from
            format_id: Format identifier (e.g., 'json', 'yaml', 'xml')
            **options: Format-specific options
        
        Returns:
            Deserialized data
        
        Examples:
            >>> io = XWIO()
            >>> data = io.load_as("config.yml", "yaml")
            >>> users = io.load_as("users.xml", "xml")
        """
        return self.load_serialized(file_path, format_id=format_id, **options)
    
    def save_as(self, file_path: Union[str, Path], data: Any, format_id: str, **options) -> None:
        """
        Save data to file using specified format (convenience alias).
        
        Alias for save_serialized() with explicit format.
        
        Args:
            file_path: Path to save to
            data: Data to serialize
            format_id: Format identifier (e.g., 'json', 'yaml', 'xml')
            **options: Format-specific options
        
        Examples:
            >>> io = XWIO()
            >>> io.save_as("config.yml", config_dict, "yaml", indent=2)
            >>> io.save_as("users.xml", users_list, "xml", pretty=True)
        """
        self.save_serialized(data, file_path, format_id=format_id, **options)
    
    def read_as(self, file_path: Union[str, Path], format_id: Optional[str] = None, **options) -> Any:
        """
        Read and deserialize file (auto-detect or explicit format).
        
        Alias for load_serialized(). More intuitive name for reading files.
        
        Args:
            file_path: Path to read from
            format_id: Optional format identifier (auto-detected if None)
            **options: Format-specific options
        
        Returns:
            Deserialized data
        
        Examples:
            >>> io = XWIO()
            >>> data = io.read_as("data.json")  # Auto-detect
            >>> config = io.read_as("config.ini", "ini")
        """
        return self.load_serialized(file_path, format_id=format_id, **options)
    
    def write_as(self, file_path: Union[str, Path], data: Any, format_id: Optional[str] = None, **options) -> None:
        """
        Serialize and write to file (auto-detect or explicit format).
        
        Alias for save_serialized(). More intuitive name for writing files.
        
        Args:
            file_path: Path to write to
            data: Data to serialize
            format_id: Optional format identifier (auto-detected if None)
            **options: Format-specific options
        
        Examples:
            >>> io = XWIO()
            >>> io.write_as("output.json", data_dict)  # Auto-detect
            >>> io.write_as("config.toml", config, "toml")
        """
        self.save_serialized(data, file_path, format_id=format_id, **options)
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def get_info(self) -> dict[str, Any]:
        """Get comprehensive I/O information."""
        return {
            'file_path': str(self.file_path) if self.file_path else None,
            'dir_path': str(self.dir_path) if hasattr(self, 'dir_path') and self.dir_path else None,
            'is_open': self.is_open(),
            'is_closed': self.is_closed(),
            'position': self._position,
            'validate_paths': self.validate_paths,
            'validate_data': self.validate_data,
            'enable_monitoring': self.enable_monitoring,
            'use_atomic_operations': self.use_atomic_operations,
            'enable_backups': self.enable_backups,
            'cleanup_temp_on_exit': self.cleanup_temp_on_exit,
            'temp_files_count': len(self._temp_files),
            'temp_dirs_count': len(self._temp_dirs)
        }
    
    def cleanup_all_resources(self) -> int:
        """Cleanup all resources (files, directories, temp files)."""
        cleaned_count = 0
        
        # Close file handle
        if self.is_open():
            self.close()
            cleaned_count += 1
        
        # Close async stream
        if self._async_stream:
            # Note: This should be called in async context
            logger.warning("Async stream still open - call aclose() in async context")
        
        # Cleanup temporary resources
        cleaned_count += self._cleanup_all_temporary()
        
        logger.debug(f"Cleaned up {cleaned_count} resources")
        return cleaned_count
