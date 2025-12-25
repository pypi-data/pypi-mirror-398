#exonware\xwsystem\serialization\auto_serializer.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Automatic serializer that detects format and delegates to appropriate serializer.
"""

from pathlib import Path
from typing import Any, Optional, Union

from .format_detector import FormatDetector, detect_format
from .contracts import ISerialization
from ...config.logging_setup import get_logger

logger = get_logger("xwsystem.serialization.auto_serializer")


class AutoSerializer:
    """
    Intelligent auto-serializer that automatically detects format and 
    delegates to the appropriate specialized serializer.
    """
    
    __slots__ = ('_detector', '_serializer_cache', '_default_format')
    
    def __init__(self, default_format: str = 'JSON', confidence_threshold: float = 0.7):
        """
        Initialize auto-serializer.
        
        Args:
            default_format: Default format when detection fails
            confidence_threshold: Minimum confidence for format detection
        """
        self._detector = FormatDetector(confidence_threshold)
        self._serializer_cache: dict[str, ISerialization] = {}
        self._default_format = default_format
    
    def _get_serializer_class(self, format_name: str) -> type[ISerialization]:
        """
        Get serializer class for format name.
        
        Args:
            format_name: Format name (e.g., 'JSON', 'YAML')
            
        Returns:
            Serializer class
            
        Raises:
            ImportError: If format not available
        """
        # Dynamic import to avoid circular dependencies.
        # Root cause fix: import concrete serializers from the canonical
        # xwsystem.io.serialization.formats packages instead of a parallel
        # exonware.xwsystem.serialization namespace (which should not exist).
        module_map = {
            # Text formats
            'JSON': ('io.serialization.formats.text.json', 'JsonSerializer'),
            'JSONL': ('io.serialization.formats.text.jsonlines', 'JsonLinesSerializer'),
            'NDJSON': ('io.serialization.formats.text.jsonlines', 'JsonLinesSerializer'),
            'YAML': ('io.serialization.formats.text.yaml', 'YamlSerializer'),
            'TOML': ('io.serialization.formats.text.toml', 'TomlSerializer'),
            'XML': ('io.serialization.formats.text.xml', 'XmlSerializer'),
            'CSV': ('io.serialization.formats.text.csv', 'CsvSerializer'),
            'ConfigParser': ('io.serialization.formats.text.configparser', 'ConfigParserSerializer'),
            'FormData': ('io.serialization.formats.text.formdata', 'FormDataSerializer'),
            'Multipart': ('io.serialization.formats.text.multipart', 'MultipartSerializer'),

            # Binary / database formats
            'BSON': ('io.serialization.formats.binary.bson', 'BsonSerializer'),
            'MessagePack': ('io.serialization.formats.binary.msgpack', 'MsgPackSerializer'),
            'CBOR': ('io.serialization.formats.binary.cbor', 'CborSerializer'),
            'Pickle': ('io.serialization.formats.binary.pickle', 'PickleSerializer'),
            'Marshal': ('io.serialization.formats.binary.marshal', 'MarshalSerializer'),
            'SQLite3': ('io.serialization.formats.database.sqlite3', 'Sqlite3Serializer'),
            'DBM': ('io.serialization.formats.database.dbm', 'DbmSerializer'),
            'Shelve': ('io.serialization.formats.database.shelve', 'ShelveSerializer'),
            'Plistlib': ('io.serialization.formats.binary.plistlib', 'PlistSerializer'),

            # Schema-based / advanced formats (placeholders for future modules)
            # These entries intentionally point to non-existent modules today.
            # The lazy installation system will handle installing/adding them
            # when the corresponding format implementations are introduced.
            'Avro': ('io.serialization.formats.schema.avro', 'AvroSerializer'),
            'Protobuf': ('io.serialization.formats.schema.protobuf', 'ProtobufSerializer'),
            'Thrift': ('io.serialization.formats.schema.thrift', 'ThriftSerializer'),
            'Parquet': ('io.serialization.formats.scientific.parquet', 'ParquetSerializer'),
            'ORC': ('io.serialization.formats.scientific.orc', 'OrcSerializer'),
            'CapnProto': ('io.serialization.formats.schema.capnproto', 'CapnProtoSerializer'),
            'FlatBuffers': ('io.serialization.formats.schema.flatbuffers', 'FlatBuffersSerializer'),
        }
        
        if format_name not in module_map:
            raise ValueError(f"Unknown format: {format_name}")
        
        module_name, class_name = module_map[format_name]
        
        try:
            # Import from canonical xwsystem.io serialization path
            module = __import__(f'exonware.xwsystem.{module_name}',
                                fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            # Lazy installation system will handle missing dependencies
            raise ImportError(f"Serializer for {format_name} failed to load: {e}")
    
    def _get_serializer(self, format_name: str) -> ISerialization:
        """
        Get cached serializer instance for format.
        
        Args:
            format_name: Format name
            
        Returns:
            Serializer instance
        """
        if format_name not in self._serializer_cache:
            serializer_class = self._get_serializer_class(format_name)
            self._serializer_cache[format_name] = serializer_class()
            logger.debug(f"Created serializer for format: {format_name}")
        
        return self._serializer_cache[format_name]
    
    def detect_and_serialize(
        self, 
        data: Any, 
        file_path: Optional[Union[str, Path]] = None,
        format_hint: Optional[str] = None,
        **opts
    ) -> Union[str, bytes]:
        """
        Auto-detect format and serialize data.
        
        Args:
            data: Data to serialize
            file_path: Optional file path for format detection
            format_hint: Optional format hint to use
            **opts: Additional serializer-specific options (pretty, indent, etc.)
            
        Returns:
            Serialized data
        """
        # Use format hint if provided
        if format_hint:
            format_name = format_hint.upper()
            logger.debug(f"Using format hint: {format_name}")
        else:
            # Try to detect from file extension
            format_name = self._detector.get_best_format(file_path=file_path)
            
            if not format_name:
                format_name = self._default_format
                logger.debug(f"Using default format: {format_name}")
        
        serializer = self._get_serializer(format_name)
        return serializer.dumps(data, **opts)
    
    def detect_and_deserialize(
        self, 
        data: Union[str, bytes], 
        file_path: Optional[Union[str, Path]] = None,
        format_hint: Optional[str] = None
    ) -> Any:
        """
        Auto-detect format and deserialize data.
        
        Args:
            data: Data to deserialize
            file_path: Optional file path for format detection
            format_hint: Optional format hint to use
            
        Returns:
            Deserialized object
        """
        # Use format hint if provided
        if format_hint:
            format_name = format_hint.upper()
            logger.debug(f"Using format hint: {format_name}")
        else:
            # Try multiple detection methods
            format_name = self._detector.get_best_format(
                file_path=file_path, 
                content=data,
                data=data if isinstance(data, bytes) else None
            )
            
            if not format_name:
                format_name = self._default_format
                logger.debug(f"Using default format: {format_name}")
        
        serializer = self._get_serializer(format_name)
        return serializer.loads(data)
    
    def auto_save_file(
        self, 
        data: Any, 
        file_path: Union[str, Path], 
        format_hint: Optional[str] = None
    ) -> None:
        """
        Auto-detect format and save to file.
        
        Args:
            data: Data to save
            file_path: File path (format detected from extension)
            format_hint: Optional format hint to override detection
        """
        # Use format hint if provided
        if format_hint:
            format_name = format_hint.upper()
        else:
            format_name = self._detector.get_best_format(file_path=file_path)
            
            if not format_name:
                format_name = self._default_format
                logger.warning(f"Could not detect format from {file_path}, using {format_name}")
        
        serializer = self._get_serializer(format_name)
        serializer.save_file(data, file_path)
        logger.info(f"Saved data to {file_path} using {format_name} format")
    
    def auto_load_file(
        self, 
        file_path: Union[str, Path], 
        format_hint: Optional[str] = None
    ) -> Any:
        """
        Auto-detect format and load from file.
        
        Args:
            file_path: File path to load
            format_hint: Optional format hint to override detection
            
        Returns:
            Loaded data
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Use format hint if provided
        if format_hint:
            format_name = format_hint.upper()
        else:
            # Try to read a small sample for content detection
            try:
                if self._detector.is_binary_format(
                    self._detector.get_best_format(file_path=file_path) or ''
                ):
                    with open(path, 'rb') as f:
                        sample = f.read(1024)
                    format_name = self._detector.get_best_format(
                        file_path=file_path, 
                        data=sample
                    )
                else:
                    with open(path, 'r', encoding='utf-8') as f:
                        sample = f.read(1024)
                    format_name = self._detector.get_best_format(
                        file_path=file_path, 
                        content=sample
                    )
            except (UnicodeDecodeError, PermissionError):
                # Fallback to extension-based detection
                format_name = self._detector.get_best_format(file_path=file_path)
            
            if not format_name:
                format_name = self._default_format
                logger.warning(f"Could not detect format from {file_path}, using {format_name}")
        
        serializer = self._get_serializer(format_name)
        result = serializer.load_file(file_path)
        logger.info(f"Loaded data from {file_path} using {format_name} format")
        return result
    
    async def auto_save_file_async(
        self, 
        data: Any, 
        file_path: Union[str, Path], 
        format_hint: Optional[str] = None
    ) -> None:
        """
        Auto-detect format and save to file asynchronously.
        
        Args:
            data: Data to save
            file_path: File path (format detected from extension)
            format_hint: Optional format hint to override detection
        """
        # Use format hint if provided
        if format_hint:
            format_name = format_hint.upper()
        else:
            format_name = self._detector.get_best_format(file_path=file_path)
            
            if not format_name:
                format_name = self._default_format
        
        serializer = self._get_serializer(format_name)
        await serializer.save_file_async(data, file_path)
        logger.info(f"Async saved data to {file_path} using {format_name} format")
    
    async def auto_load_file_async(
        self, 
        file_path: Union[str, Path], 
        format_hint: Optional[str] = None
    ) -> Any:
        """
        Auto-detect format and load from file asynchronously.
        
        Args:
            file_path: File path to load
            format_hint: Optional format hint to override detection
            
        Returns:
            Loaded data
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Use format hint if provided
        if format_hint:
            format_name = format_hint.upper()
        else:
            # For async, we'll primarily rely on extension detection
            # to avoid blocking I/O for content sampling
            format_name = self._detector.get_best_format(file_path=file_path)
            
            if not format_name:
                format_name = self._default_format
        
        serializer = self._get_serializer(format_name)
        result = await serializer.load_file_async(file_path)
        logger.info(f"Async loaded data from {file_path} using {format_name} format")
        return result
    
    def get_format_suggestions(
        self, 
        data: Union[str, bytes], 
        file_path: Optional[Union[str, Path]] = None
    ) -> list[tuple[str, float]]:
        """
        Get format suggestions for given data.
        
        Args:
            data: Data to analyze
            file_path: Optional file path
            
        Returns:
            List of (format_name, confidence) tuples
        """
        return self._detector.get_format_suggestions(
            file_path=file_path,
            content=data,
            data=data if isinstance(data, bytes) else None
        )
    
    def clear_cache(self) -> None:
        """Clear serializer cache."""
        self._serializer_cache.clear()
        logger.debug("Cleared serializer cache")


# Global auto-serializer instance
_global_auto_serializer = AutoSerializer()

def auto_serialize(
    data: Any, 
    file_path: Optional[Union[str, Path]] = None,
    format_hint: Optional[str] = None,
    **opts
) -> Union[str, bytes]:
    """
    Convenience function for auto-serialization.
    
    Args:
        data: Data to serialize
        file_path: Optional file path for format detection
        format_hint: Optional format hint
        **opts: Additional serializer options
        
    Returns:
        Serialized data
    """
    return _global_auto_serializer.detect_and_serialize(data, file_path, format_hint, **opts)

def auto_deserialize(
    data: Union[str, bytes], 
    file_path: Optional[Union[str, Path]] = None,
    format_hint: Optional[str] = None
) -> Any:
    """
    Convenience function for auto-deserialization.
    
    Args:
        data: Data to deserialize
        file_path: Optional file path for format detection
        format_hint: Optional format hint
        
    Returns:
        Deserialized object
    """
    return _global_auto_serializer.detect_and_deserialize(data, file_path, format_hint)

def auto_save_file(
    data: Any, 
    file_path: Union[str, Path], 
    format_hint: Optional[str] = None
) -> None:
    """
    Convenience function for auto-saving files.
    
    Args:
        data: Data to save
        file_path: File path
        format_hint: Optional format hint
    """
    return _global_auto_serializer.auto_save_file(data, file_path, format_hint)

def auto_load_file(
    file_path: Union[str, Path], 
    format_hint: Optional[str] = None
) -> Any:
    """
    Convenience function for auto-loading files.
    
    Args:
        file_path: File path to load
        format_hint: Optional format hint
        
    Returns:
        Loaded data
    """
    return _global_auto_serializer.auto_load_file(file_path, format_hint)
