"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

XWSerializer - Unified intelligent serializer with I/O integration and auto-serialization.
"""

import os
import time
from pathlib import Path
from typing import Any, Optional, Union, Callable

from .base import ASerialization
from .contracts import ISerialization
from .errors import SerializationError
from .format_detector import FormatDetector
from ..facade import XWIO
from ..file.file import XWFile
from ..contracts import OperationResult
from ...config.logging_setup import get_logger
from ...security.path_validator import PathValidator
from ...validation.data_validator import DataValidator
from ...monitoring.performance_monitor import performance_monitor

logger = get_logger(__name__)


class XWSerializer(ASerialization):
    """
    Unified intelligent serializer with I/O integration and auto-serialization.
    
    This class combines the best of both worlds:
    1. Self-transforming intelligent serialization (from XWSerialization)
    2. Enhanced I/O integration and file management (from XWSerializer)
    
    Key Features:
    - Intelligent format detection and self-transformation
    - Auto-serialization with format detection
    - File manager integration for universal file support
    - Unified I/O operations with atomic safety
    - Backup and restore capabilities
    - Performance monitoring and validation
    - Support for any file type (docx, json, photo, movie, etc.)
    
    This replaces both XWSerialization and the old XWSerializer concept.
    """
    
    def __init__(self, confidence_threshold: float = 0.7, **config):
        """
        Initialize unified XWSerializer.
        
        Args:
            confidence_threshold: Minimum confidence for format detection
            **config: Configuration options for serialization and I/O
        """
        super().__init__()
        
        # Initialize format detection (from XWSerialization)
        self._detector = FormatDetector(confidence_threshold)
        self._specialized_serializer: Optional[ISerialization] = None
        self._detected_format: Optional[str] = None
        self._confidence_threshold = confidence_threshold
        
        # Initialize I/O components (from XWSerializer)
        self._file_manager = XWFileManager(**config)
        self._unified_io = XWUnifiedIO(**config)
        
        # Initialize xwsystem utilities
        self._path_validator = PathValidator()
        self._data_validator = DataValidator()
        
        # Configuration
        self.auto_serialize = config.get('auto_serialize', True)
        self.auto_detect_format = config.get('auto_detect_format', True)
        self.use_file_manager = config.get('use_file_manager', True)
        self.use_unified_io = config.get('use_unified_io', True)
        self.enable_backups = config.get('enable_backups', True)
        self.use_atomic_operations = config.get('use_atomic_operations', True)
        self.validate_paths = config.get('validate_paths', True)
        self.validate_data = config.get('validate_data', True)
        self.enable_monitoring = config.get('enable_monitoring', True)
        
        # Auto-serialization settings
        self.auto_serialize_formats = config.get('auto_serialize_formats', [
            'json', 'yaml', 'xml', 'csv', 'toml', 'ini', 'config'
        ])
        self.auto_serialize_extensions = config.get('auto_serialize_extensions', [
            '.json', '.yaml', '.yml', '.xml', '.csv', '.toml', '.ini', '.cfg', '.conf'
        ])
        
        logger.debug("XWSerializer initialized with unified functionality")
    
    # ============================================================================
    # FORMAT DETECTION AND TRANSFORMATION (from XWSerialization)
    # ============================================================================
    
    def _get_serializer_class(self, format_name: str) -> type[ISerialization]:
        """Get serializer class for format name."""
        module_map = {
            'JSON': ('json', 'JsonSerializer'),
            'YAML': ('yaml', 'YamlSerializer'),
            'TOML': ('toml', 'TomlSerializer'),
            'XML': ('xml', 'XmlSerializer'),
            'CSV': ('csv', 'CsvSerializer'),
            'ConfigParser': ('configparser', 'ConfigParserSerializer'),
            'FormData': ('formdata', 'FormDataSerializer'),
            'Multipart': ('multipart', 'MultipartSerializer'),
            
            # Binary formats
            'BSON': ('bson', 'BsonSerializer'),
            'MessagePack': ('msgpack', 'MsgPackSerializer'),
            'CBOR': ('cbor', 'CborSerializer'),
            'Pickle': ('pickle', 'PickleSerializer'),
            'Marshal': ('marshal', 'MarshalSerializer'),
            'SQLite3': ('sqlite3', 'Sqlite3Serializer'),
            'DBM': ('dbm', 'DbmSerializer'),
            'Shelve': ('shelve', 'ShelveSerializer'),
            'Plistlib': ('plistlib', 'PlistSerializer'),
            
            # Schema-based formats
            'Avro': ('avro', 'AvroSerializer'),
            'Protobuf': ('protobuf', 'ProtobufSerializer'),
            'Thrift': ('thrift', 'ThriftSerializer'),
            'Parquet': ('parquet', 'ParquetSerializer'),
            'ORC': ('orc', 'OrcSerializer'),
            'CapnProto': ('capnproto', 'CapnProtoSerializer'),
            'FlatBuffers': ('flatbuffers', 'FlatBuffersSerializer'),
        }
        
        if format_name not in module_map:
            raise ValueError(f"Unknown format: {format_name}")
        
        module_name, class_name = module_map[format_name]
        
        try:
            # Import from current package
            module = __import__(f'exonware.xwsystem.serialization.{module_name}', 
                              fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            # Lazy installation system will handle missing dependencies
            raise ImportError(f"Serializer for {format_name} failed to load: {e}")
    
    def _transform_to_specialized(
        self, 
        format_name: str, 
        file_path: Optional[Union[str, Path]] = None,
        content: Optional[Union[str, bytes]] = None,
        data: Optional[bytes] = None
    ) -> None:
        """Transform this instance into a specialized serializer."""
        try:
            serializer_class = self._get_serializer_class(format_name)
            
            # Create specialized serializer with same configuration
            self._specialized_serializer = serializer_class(
                validate_input=self.validate_input,
                max_depth=self.max_depth,
                max_size_mb=self.max_size_mb,
                use_atomic_writes=self.use_atomic_writes,
                validate_paths=self.validate_paths,
                text_encoding=self.text_encoding,
                base64_encoding=self.base64_encoding,
            )
            
            self._detected_format = format_name
            
            logger.info(f"XWSerializer transformed to {format_name}Serializer")
            
        except Exception as e:
            logger.error(f"Failed to transform to {format_name}: {e}")
            # Fallback to JSON serializer
            from .json import JsonSerializer
            self._specialized_serializer = JsonSerializer()
            self._detected_format = 'JSON'
            logger.warning("Fallback to JsonSerializer due to transformation failure")
    
    def _detect_and_transform(
        self, 
        data: Optional[Any] = None,
        file_path: Optional[Union[str, Path]] = None,
        content: Optional[Union[str, bytes]] = None,
        binary_data: Optional[bytes] = None,
        format_hint: Optional[str] = None
    ) -> None:
        """Detect format and transform to specialized serializer."""
        if self._specialized_serializer is not None:
            return  # Already transformed
        
        # Use format hint if provided
        if format_hint:
            format_name = format_hint.upper()
            logger.debug(f"Using format hint: {format_name}")
        else:
            # Auto-detect format
            format_name = self._detector.get_best_format(
                file_path=file_path,
                content=content,
                data=binary_data
            )
            
            if not format_name:
                # Try to infer from data type if no other clues
                if data is not None:
                    if isinstance(data, (dict, list)):
                        format_name = 'JSON'  # Most common for structured data
                    elif isinstance(data, str):
                        format_name = 'JSON'  # Assume JSON string
                    elif isinstance(data, bytes):
                        format_name = 'MessagePack'  # Good binary default
                    else:
                        format_name = 'JSON'  # Safe default
                else:
                    format_name = 'JSON'  # Ultimate fallback
                
                logger.debug(f"Auto-detected format: {format_name}")
        
        # Transform to specialized serializer
        self._transform_to_specialized(format_name, file_path, content, binary_data)
    
    def _ensure_specialized(self, **detection_kwargs) -> ISerialization:
        """Ensure we have a specialized serializer, detecting if needed."""
        if self._specialized_serializer is None:
            self._detect_and_transform(**detection_kwargs)
        
        return self._specialized_serializer
    
    # ============================================================================
    # AUTO-SERIALIZATION METHODS (Enhanced)
    # ============================================================================
    
    def auto_serialize(self, data: Any, file_path: Union[str, Path], 
                      format_hint: Optional[str] = None) -> bool:
        """Automatically serialize data to file with format detection."""
        if not self.auto_serialize:
            return False
        
        target_path = Path(file_path)
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        if self.validate_data:
            self._data_validator.validate_data(data)
        
        with performance_monitor("auto_serialize"):
            try:
                # Detect format if not provided
                if not format_hint:
                    format_hint = self._detect_format_from_path(target_path)
                
                # Check if format supports auto-serialization
                if format_hint and format_hint.lower() in self.auto_serialize_formats:
                    # Use specialized serializer for supported formats
                    specialized = self._ensure_specialized(
                        data=data,
                        file_path=target_path,
                        format_hint=format_hint
                    )
                    specialized.save_file(data, target_path)
                    logger.debug(f"Auto-serialized to {target_path} as {format_hint}")
                    return True
                else:
                    # Use file manager for other formats
                    if self.use_file_manager:
                        self._file_manager.save(data, target_path)
                        logger.debug(f"Auto-saved to {target_path} using file manager")
                        return True
                    else:
                        # Fallback to direct file write
                        self._unified_io.save(data, target_path)
                        logger.debug(f"Auto-saved to {target_path} using unified I/O")
                        return True
                        
            except Exception as e:
                logger.error(f"Auto-serialization failed for {target_path}: {e}")
                return False
    
    def auto_deserialize(self, file_path: Union[str, Path], 
                        format_hint: Optional[str] = None) -> Any:
        """Automatically deserialize data from file with format detection."""
        if not self.auto_serialize:
            raise SerializationError("Auto-serialization is disabled")
        
        target_path = Path(file_path)
        
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {target_path}")
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        with performance_monitor("auto_deserialize"):
            try:
                # Detect format if not provided
                if not format_hint:
                    format_hint = self._detect_format_from_path(target_path)
                
                # Check if format supports auto-deserialization
                if format_hint and format_hint.lower() in self.auto_serialize_formats:
                    # Use specialized serializer for supported formats
                    specialized = self._ensure_specialized(
                        file_path=target_path,
                        format_hint=format_hint
                    )
                    data = specialized.load_file(target_path)
                    logger.debug(f"Auto-deserialized from {target_path} as {format_hint}")
                    return data
                else:
                    # Use file manager for other formats
                    if self.use_file_manager:
                        data = self._file_manager.load(target_path)
                        logger.debug(f"Auto-loaded from {target_path} using file manager")
                        return data
                    else:
                        # Fallback to direct file read
                        data = self._unified_io.load(target_path)
                        logger.debug(f"Auto-loaded from {target_path} using unified I/O")
                        return data
                        
            except Exception as e:
                logger.error(f"Auto-deserialization failed for {target_path}: {e}")
                raise SerializationError(f"Auto-deserialization failed: {e}")
    
    def _detect_format_from_path(self, file_path: Path) -> Optional[str]:
        """Detect format from file path extension."""
        ext = file_path.suffix.lower()
        
        format_mappings = {
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.csv': 'csv',
            '.tsv': 'csv',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
            '.conf': 'ini',
            '.pickle': 'pickle',
            '.pkl': 'pickle',
            '.msgpack': 'msgpack',
            '.mp': 'msgpack',
            '.bson': 'bson',
            '.cbor': 'cbor',
            '.avro': 'avro',
            '.parquet': 'parquet',
            '.feather': 'feather',
            '.hdf5': 'hdf5',
            '.h5': 'hdf5',
            '.zarr': 'zarr',
            '.db': 'sqlite3',
            '.sqlite': 'sqlite3',
            '.sqlite3': 'sqlite3',
        }
        
        return format_mappings.get(ext)
    
    # ============================================================================
    # CORE SERIALIZATION METHODS (Unified)
    # ============================================================================
    
    def dumps(self, data: Any, file_path: Optional[Union[str, Path]] = None, 
              format_hint: Optional[str] = None) -> Union[str, bytes]:
        """Unified serialize with I/O integration."""
        if file_path and self.auto_serialize:
            # Use auto-serialization for file operations
            if self.auto_serialize(data, file_path, format_hint):
                return b"Auto-serialized to file"
        
        # Use specialized serializer for in-memory serialization
        specialized = self._ensure_specialized(
            data=data, 
            file_path=file_path, 
            format_hint=format_hint
        )
        return specialized.dumps(data)
    
    def loads(self, data: Union[str, bytes], format_hint: Optional[str] = None) -> Any:
        """Unified deserialize with I/O integration."""
        specialized = self._ensure_specialized(
            content=data,
            binary_data=data if isinstance(data, bytes) else None,
            format_hint=format_hint
        )
        return specialized.loads(data)
    
    def save_file(self, data: Any, file_path: Union[str, Path], 
                  format_hint: Optional[str] = None) -> None:
        """Enhanced save file with backup and atomic operations."""
        target_path = Path(file_path)
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        if self.validate_data:
            self._data_validator.validate_data(data)
        
        with performance_monitor("save_file"):
            try:
                # Create backup if enabled
                if self.enable_backups and target_path.exists():
                    backup_path = self._file_manager.create_backup(
                        target_path, target_path.parent / '.backups'
                    )
                    if backup_path:
                        logger.debug(f"Created backup: {backup_path}")
                
                # Use auto-serialization if enabled
                if self.auto_serialize:
                    if self.auto_serialize(data, target_path, format_hint):
                        return
                
                # Fallback to specialized serializer
                specialized = self._ensure_specialized(
                    data=data,
                    file_path=target_path,
                    format_hint=format_hint
                )
                specialized.save_file(data, target_path)
                
            except Exception as e:
                logger.error(f"Save file failed for {target_path}: {e}")
                raise SerializationError(f"Save file failed: {e}")
    
    def load_file(self, file_path: Union[str, Path], 
                  format_hint: Optional[str] = None) -> Any:
        """Enhanced load file with validation and monitoring."""
        target_path = Path(file_path)
        
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {target_path}")
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        with performance_monitor("load_file"):
            try:
                # Use auto-deserialization if enabled
                if self.auto_serialize:
                    return self.auto_deserialize(target_path, format_hint)
                
                # Fallback to specialized serializer
                specialized = self._ensure_specialized(
                    file_path=target_path,
                    format_hint=format_hint
                )
                return specialized.load_file(target_path)
                
            except Exception as e:
                logger.error(f"Load file failed for {target_path}: {e}")
                raise SerializationError(f"Load file failed: {e}")
    
    # ============================================================================
    # PROPERTY DELEGATION (from XWSerialization)
    # ============================================================================
    
    @property
    def format_name(self) -> str:
        """Get format name - detects if needed."""
        if self._specialized_serializer is None:
            return "Auto-Detect"
        return self._specialized_serializer.format_name
    
    @property
    def file_extensions(self) -> list[str]:
        """Get file extensions - detects if needed."""
        if self._specialized_serializer is None:
            return []  # Unknown until detection
        return self._specialized_serializer.file_extensions
    
    @property
    def mime_type(self) -> str:
        """Get MIME type - detects if needed."""
        if self._specialized_serializer is None:
            return "application/octet-stream"  # Generic until detection
        return self._specialized_serializer.mime_type
    
    @property
    def is_binary_format(self) -> bool:
        """Check if binary format - detects if needed."""
        if self._specialized_serializer is None:
            return False  # Assume text until detection
        return self._specialized_serializer.is_binary_format
    
    @property
    def supports_streaming(self) -> bool:
        """Check streaming support - detects if needed."""
        if self._specialized_serializer is None:
            return False  # Unknown until detection
        return self._specialized_serializer.supports_streaming
    
    # ============================================================================
    # FILE MANAGER INTEGRATION
    # ============================================================================
    
    def process_file(self, file_path: Union[str, Path], operation: str = 'info') -> dict[str, Any]:
        """Process file using file manager."""
        return self._file_manager.process_file(file_path, operation)
    
    def get_file_info(self, file_path: Union[str, Path]) -> dict[str, Any]:
        """Get comprehensive file information."""
        return self._file_manager.get_file_info(file_path)
    
    def detect_file_type(self, file_path: Union[str, Path]) -> str:
        """Detect file type."""
        return self._file_manager.detect_file_type(file_path)
    
    def is_safe_to_process(self, file_path: Union[str, Path]) -> bool:
        """Check if file is safe to process."""
        return self._file_manager.is_safe_to_process(file_path)
    
    # ============================================================================
    # UNIFIED I/O INTEGRATION
    # ============================================================================
    
    def atomic_save(self, data: Any, file_path: Union[str, Path], 
                   backup: bool = True) -> OperationResult:
        """Atomically save data with backup."""
        target_path = Path(file_path)
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        if self.validate_data:
            self._data_validator.validate_data(data)
        
        with performance_monitor("atomic_save"):
            try:
                # Convert data to bytes for atomic write
                if isinstance(data, str):
                    data_bytes = data.encode('utf-8')
                elif isinstance(data, bytes):
                    data_bytes = data
                else:
                    data_bytes = str(data).encode('utf-8')
                
                return self._unified_io.atomic_write(target_path, data_bytes, backup)
                
            except Exception as e:
                logger.error(f"Atomic save failed for {target_path}: {e}")
                return OperationResult.FAILED
    
    def atomic_load(self, file_path: Union[str, Path]) -> Any:
        """Atomically load data."""
        target_path = Path(file_path)
        
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {target_path}")
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        with performance_monitor("atomic_load"):
            try:
                # Load data
                data = self._unified_io.load(target_path)
                
                # Try to deserialize if it's a supported format
                if self.auto_serialize:
                    format_hint = self._detect_format_from_path(target_path)
                    if format_hint and format_hint.lower() in self.auto_serialize_formats:
                        specialized = self._ensure_specialized(
                            content=data,
                            format_hint=format_hint
                        )
                        return specialized.loads(data)
                
                return data
                
            except Exception as e:
                logger.error(f"Atomic load failed for {target_path}: {e}")
                raise SerializationError(f"Atomic load failed: {e}")
    
    # ============================================================================
    # ADVANCED FEATURES DELEGATION
    # ============================================================================
    
    def atomic_update_path(
        self, 
        file_path: Union[str, Path], 
        path: str, 
        value: Any, 
        **options
    ) -> None:
        """
        Atomically update a single path in a file (delegates to specialized serializer).
        
        Detects format from file path and delegates to specialized serializer if it
        supports path-based updates. Falls back gracefully if not supported.
        
        Args:
            file_path: Path to the file to update
            path: Path expression (format-specific)
            value: Value to set at the specified path
            **options: Format-specific options
        
        Raises:
            NotImplementedError: If format doesn't support path-based updates
            SerializationError: If update fails
        """
        target_path = Path(file_path)
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        with performance_monitor("atomic_update_path"):
            try:
                # Detect format and get specialized serializer
                format_hint = self._detect_format_from_path(target_path)
                specialized = self._ensure_specialized(
                    file_path=target_path,
                    format_hint=format_hint
                )
                
                # Delegate to specialized serializer
                specialized.atomic_update_path(target_path, path, value, **options)
                logger.debug(f"Atomically updated path '{path}' in {target_path}")
                
            except NotImplementedError:
                raise
            except Exception as e:
                logger.error(f"Atomic path update failed for {target_path}: {e}")
                raise SerializationError(f"Atomic path update failed: {e}") from e
    
    def atomic_read_path(
        self, 
        file_path: Union[str, Path], 
        path: str, 
        **options
    ) -> Any:
        """
        Read a single path from a file (delegates to specialized serializer).
        
        Detects format from file path and delegates to specialized serializer if it
        supports path-based reads. Falls back gracefully if not supported.
        
        Args:
            file_path: Path to the file to read from
            path: Path expression (format-specific)
            **options: Format-specific options
        
        Returns:
            Value at the specified path
        
        Raises:
            NotImplementedError: If format doesn't support path-based reads
            SerializationError: If read fails
            KeyError: If path doesn't exist
        """
        target_path = Path(file_path)
        
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {target_path}")
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        with performance_monitor("atomic_read_path"):
            try:
                # Detect format and get specialized serializer
                format_hint = self._detect_format_from_path(target_path)
                specialized = self._ensure_specialized(
                    file_path=target_path,
                    format_hint=format_hint
                )
                
                # Delegate to specialized serializer
                result = specialized.atomic_read_path(target_path, path, **options)
                logger.debug(f"Read path '{path}' from {target_path}")
                return result
                
            except (NotImplementedError, KeyError, FileNotFoundError):
                raise
            except Exception as e:
                logger.error(f"Atomic path read failed for {target_path}: {e}")
                raise SerializationError(f"Atomic path read failed: {e}") from e
    
    def query(
        self, 
        file_path: Union[str, Path], 
        query_expr: str, 
        **options
    ) -> Any:
        """
        Query a file using format-specific query language (delegates to specialized serializer).
        
        Detects format from file path and delegates to specialized serializer if it
        supports queries. Falls back gracefully if not supported.
        
        Args:
            file_path: Path to the file to query
            query_expr: Query expression (format-specific: JSONPath, XPath, etc.)
            **options: Query options
        
        Returns:
            Query results
        
        Raises:
            NotImplementedError: If format doesn't support queries
            SerializationError: If query fails
        """
        target_path = Path(file_path)
        
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {target_path}")
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        with performance_monitor("query"):
            try:
                # Detect format and get specialized serializer
                format_hint = self._detect_format_from_path(target_path)
                specialized = self._ensure_specialized(
                    file_path=target_path,
                    format_hint=format_hint
                )
                
                # Delegate to specialized serializer
                result = specialized.query(target_path, query_expr, **options)
                logger.debug(f"Queried {target_path} with expression '{query_expr}'")
                return result
                
            except (NotImplementedError, ValueError, FileNotFoundError):
                raise
            except Exception as e:
                logger.error(f"Query failed for {target_path}: {e}")
                raise SerializationError(f"Query failed: {e}") from e
    
    def merge(
        self, 
        file_path: Union[str, Path], 
        updates: dict[str, Any], 
        **options
    ) -> None:
        """
        Merge updates into a file (delegates to specialized serializer).
        
        Detects format from file path and delegates to specialized serializer if it
        supports merge operations. Falls back gracefully if not supported.
        
        Args:
            file_path: Path to the file to update
            updates: Dictionary of updates to merge
            **options: Merge options
        
        Raises:
            NotImplementedError: If format doesn't support merge operations
            SerializationError: If merge fails
        """
        target_path = Path(file_path)
        
        if self.validate_paths:
            self._path_validator.validate_path(target_path)
        
        with performance_monitor("merge"):
            try:
                # Detect format and get specialized serializer
                format_hint = self._detect_format_from_path(target_path)
                specialized = self._ensure_specialized(
                    file_path=target_path,
                    format_hint=format_hint
                )
                
                # Delegate to specialized serializer
                specialized.merge(target_path, updates, **options)
                logger.debug(f"Merged updates into {target_path}")
                
            except NotImplementedError:
                raise
            except Exception as e:
                logger.error(f"Merge failed for {target_path}: {e}")
                raise SerializationError(f"Merge failed: {e}") from e

    # ============================================================================
    # RECORD-LEVEL OPERATIONS (delegated to specialized serializers)
    # ============================================================================

    def stream_read_record(
        self,
        file_path: Union[str, Path],
        match: callable,
        projection: Optional[list[Any]] = None,
        **options: Any,
    ) -> Any:
        """
        Stream-style read of a single logical record.

        Delegates to the specialized serializer when available (e.g. JSONL /
        NDJSON), falling back to the generic ASerialization implementation
        which may load the entire file and scan in memory.
        """
        target_path = Path(file_path)

        if self.validate_paths:
            self._path_validator.validate_path(target_path)

        format_hint = self._detect_format_from_path(target_path)
        specialized = self._ensure_specialized(
            file_path=target_path,
            format_hint=format_hint,
        )

        try:
            return specialized.stream_read_record(
                target_path,
                match,
                projection=projection,
                **options,
            )
        except NotImplementedError:
            # Fallback to generic full-load behavior from ASerialization
            return super().stream_read_record(
                target_path,
                match,
                projection=projection,
                **options,
            )

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
        Stream-style update of logical records.

        Delegates to the specialized serializer when it provides a streaming
        implementation (e.g. JSONL). Falls back to the generic
        ASerialization implementation that may load the full file, but still
        honours atomic save semantics.
        """
        target_path = Path(file_path)

        if self.validate_paths:
            self._path_validator.validate_path(target_path)

        format_hint = self._detect_format_from_path(target_path)
        specialized = self._ensure_specialized(
            file_path=target_path,
            format_hint=format_hint,
        )

        try:
            return specialized.stream_update_record(
                target_path,
                match,
                updater,
                atomic=atomic,
                **options,
            )
        except NotImplementedError:
            return super().stream_update_record(
                target_path,
                match,
                updater,
                atomic=atomic,
                **options,
            )

    def get_record_page(
        self,
        file_path: Union[str, Path],
        page_number: int,
        page_size: int,
        **options: Any,
    ) -> list[Any]:
        """
        Retrieve a logical page of records from a file.

        Delegates to the specialized serializer when supported (for example,
        JSONL can implement true streaming paging). Falls back to the generic
        ASerialization implementation, which may load the entire file and
        slice a top-level list.
        """
        target_path = Path(file_path)

        if self.validate_paths:
            self._path_validator.validate_path(target_path)

        format_hint = self._detect_format_from_path(target_path)
        specialized = self._ensure_specialized(
            file_path=target_path,
            format_hint=format_hint,
        )

        try:
            return specialized.get_record_page(
                target_path,
                page_number,
                page_size,
                **options,
            )
        except NotImplementedError:
            return super().get_record_page(
                target_path,
                page_number,
                page_size,
                **options,
            )

    def get_record_by_id(
        self,
        file_path: Union[str, Path],
        id_value: Any,
        *,
        id_field: str = "id",
        **options: Any,
    ) -> Any:
        """
        Retrieve a logical record by identifier.

        Delegates to the specialized serializer where possible; falls back to
        the generic ASerialization implementation which performs a linear scan
        over a top-level list.
        """
        target_path = Path(file_path)

        if self.validate_paths:
            self._path_validator.validate_path(target_path)

        format_hint = self._detect_format_from_path(target_path)
        specialized = self._ensure_specialized(
            file_path=target_path,
            format_hint=format_hint,
        )

        try:
            return specialized.get_record_by_id(
                target_path,
                id_value,
                id_field=id_field,
                **options,
            )
        except NotImplementedError:
            return super().get_record_by_id(
                target_path,
                id_value,
                id_field=id_field,
                **options,
            )
    
    # ============================================================================
    # BATCH OPERATIONS
    # ============================================================================
    
    def batch_save(self, data_dict: dict[Union[str, Path], Any], 
                   format_hint: Optional[str] = None) -> dict[str, bool]:
        """Save multiple files in batch."""
        results = {}
        
        with performance_monitor("batch_save"):
            for file_path, data in data_dict.items():
                try:
                    self.save_file(data, file_path, format_hint)
                    results[str(file_path)] = True
                except Exception as e:
                    logger.error(f"Batch save failed for {file_path}: {e}")
                    results[str(file_path)] = False
        
        return results
    
    def batch_load(self, file_paths: list[Union[str, Path]], 
                   format_hint: Optional[str] = None) -> dict[str, Any]:
        """Load multiple files in batch."""
        results = {}
        
        with performance_monitor("batch_load"):
            for file_path in file_paths:
                try:
                    data = self.load_file(file_path, format_hint)
                    results[str(file_path)] = data
                except Exception as e:
                    logger.error(f"Batch load failed for {file_path}: {e}")
                    results[str(file_path)] = None
        
        return results
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def get_serializer_info(self) -> dict[str, Any]:
        """Get comprehensive serializer information."""
        return {
            'auto_serialize': self.auto_serialize,
            'auto_detect_format': self.auto_detect_format,
            'use_file_manager': self.use_file_manager,
            'use_unified_io': self.use_unified_io,
            'enable_backups': self.enable_backups,
            'use_atomic_operations': self.use_atomic_operations,
            'validate_paths': self.validate_paths,
            'validate_data': self.validate_data,
            'enable_monitoring': self.enable_monitoring,
            'auto_serialize_formats': self.auto_serialize_formats,
            'auto_serialize_extensions': self.auto_serialize_extensions,
            'detected_format': self._detected_format,
            'is_transformed': self.is_transformed(),
            'file_manager_info': self._file_manager.get_manager_info(),
            'unified_io_info': self._unified_io.get_info()
        }
    
    def cleanup_all_resources(self) -> int:
        """Cleanup all resources."""
        cleaned_count = 0
        
        # Cleanup file manager resources
        cleaned_count += self._file_manager.cleanup_all_resources()
        
        # Cleanup unified I/O resources
        cleaned_count += self._unified_io.cleanup_all_resources()
        
        logger.debug(f"XWSerializer cleaned up {cleaned_count} resources")
        return cleaned_count
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, cleaning up resources."""
        self.cleanup_all_resources()
    
    # ============================================================================
    # INTROSPECTION METHODS (from XWSerialization)
    # ============================================================================
    
    def get_detected_format(self) -> Optional[str]:
        """Get the detected format name."""
        return self._detected_format
    
    def is_transformed(self) -> bool:
        """Check if this serializer has been transformed to a specialized one."""
        return self._specialized_serializer is not None
    
    def get_specialized_serializer(self) -> Optional[ISerialization]:
        """Get the underlying specialized serializer."""
        return self._specialized_serializer
    
    def force_format(self, format_name: str) -> None:
        """Force transformation to a specific format."""
        self._transform_to_specialized(format_name.upper())
        logger.info(f"Forced transformation to {format_name}")
    
    # ============================================================================
    # DELEGATION METHODS - Pass through to specialized serializer
    # ============================================================================
    
    def dumps_text(self, data: Any) -> str:
        """Serialize to text."""
        specialized = self._ensure_specialized(data=data)
        return specialized.dumps_text(data)
    
    def dumps_binary(self, data: Any) -> bytes:
        """Serialize to binary."""
        specialized = self._ensure_specialized(data=data)
        return specialized.dumps_binary(data)
    
    def loads_text(self, data: str) -> Any:
        """Deserialize from text."""
        specialized = self._ensure_specialized(content=data)
        return specialized.loads_text(data)
    
    def loads_bytes(self, data: bytes) -> Any:
        """Deserialize from bytes."""
        specialized = self._ensure_specialized(binary_data=data)
        return specialized.loads_bytes(data)
    
    def validate_data(self, data: Any) -> bool:
        """Validate data."""
        specialized = self._ensure_specialized(data=data)
        return specialized.validate_data(data)
    
    def get_schema_info(self) -> dict[str, Any]:
        """Get schema info."""
        if self._specialized_serializer is None:
            return {
                "format": "Auto-Detect",
                "status": "Not yet detected",
                "description": "Unified intelligent serializer with I/O integration"
            }
        return self._specialized_serializer.get_schema_info()
    
    def estimate_size(self, data: Any) -> int:
        """Estimate size."""
        specialized = self._ensure_specialized(data=data)
        return specialized.estimate_size(data)
    
    def configure(self, **options: Any) -> None:
        """Configure serializer."""
        if self._specialized_serializer is not None:
            self._specialized_serializer.configure(**options)
        else:
            # Store for when we transform
            for key, value in options.items():
                if hasattr(self, key):
                    setattr(self, key, value)
    
    def reset_configuration(self) -> None:
        """Reset configuration."""
        if self._specialized_serializer is not None:
            self._specialized_serializer.reset_configuration()
        else:
            # Reset our own configuration
            super().__init__()


# Convenience functions
def create_xw_serializer(confidence_threshold: float = 0.7, **config) -> XWSerializer:
    """
    Create a new XWSerializer instance.
    
    Args:
        confidence_threshold: Minimum confidence for format detection
        **config: Configuration options
        
    Returns:
        New XWSerializer instance
    """
    return XWSerializer(confidence_threshold, **config)


# Global instance for convenience - will be created on first use
_global_xw_serializer = None

def _get_global_serializer() -> XWSerializer:
    """Get or create global serializer instance."""
    global _global_xw_serializer
    if _global_xw_serializer is None:
        _global_xw_serializer = XWSerializer()
    return _global_xw_serializer

# Static functions - clean API without prefixes
def auto_serialize(data: Any, file_path: Union[str, Path], format_hint: Optional[str] = None) -> bool:
    """Auto-serialize data to file with format detection."""
    return _get_global_serializer().auto_serialize(data, file_path, format_hint)

def auto_deserialize(file_path: Union[str, Path], format_hint: Optional[str] = None) -> Any:
    """Auto-deserialize data from file with format detection."""
    return _get_global_serializer().auto_deserialize(file_path, format_hint)

def atomic_save(data: Any, file_path: Union[str, Path], backup: bool = True) -> OperationResult:
    """Atomically save data with backup."""
    return _get_global_serializer().atomic_save(data, file_path, backup)

def atomic_load(file_path: Union[str, Path]) -> Any:
    """Atomically load data."""
    return _get_global_serializer().atomic_load(file_path)

def dumps(data: Any, file_path: Optional[Union[str, Path]] = None, format_hint: Optional[str] = None) -> Union[str, bytes]:
    """Smart serialization function that auto-detects format."""
    return _get_global_serializer().dumps(data, file_path, format_hint)

def loads(data: Union[str, bytes], format_hint: Optional[str] = None) -> Any:
    """Smart deserialization function that auto-detects format."""
    return _get_global_serializer().loads(data, format_hint)

def save_file(data: Any, file_path: Union[str, Path], format_hint: Optional[str] = None) -> None:
    """Smart file saving that auto-detects format from extension."""
    return _get_global_serializer().save_file(data, file_path, format_hint)

def load_file(file_path: Union[str, Path], format_hint: Optional[str] = None) -> Any:
    """Smart file loading that auto-detects format from extension and content."""
    return _get_global_serializer().load_file(file_path, format_hint)