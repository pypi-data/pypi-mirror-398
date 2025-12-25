"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

YAML serialization - Human-readable data serialization format.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: YamlSerializer
"""

from typing import Any, Optional, Union, Iterator
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError

# Lazy import for yaml (PyYAML)
# The lazy hook will automatically handle ImportError and install PyYAML if missing
import yaml


class YamlSerializer(ASerialization):
    """
    YAML serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: YamlSerializer
    
    Uses PyYAML library for YAML handling.
    
    Examples:
        >>> serializer = YamlSerializer()
        >>> 
        >>> # Encode data
        >>> yaml_str = serializer.encode({"key": "value"})
        >>> 
        >>> # Decode data
        >>> data = serializer.decode("key: value")
        >>> 
        >>> # Save to file
        >>> serializer.save_file({"database": {"host": "localhost"}}, "config.yaml")
        >>> 
        >>> # Load from file
        >>> config = serializer.load_file("config.yaml")
    """
    
    def __init__(self):
        """Initialize YAML serializer."""
        super().__init__()
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "yaml"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/x-yaml", "text/yaml", "text/x-yaml"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".yaml", ".yml", ".clang-format", ".travis.yml", ".gitlab-ci.yml"]
    
    @property
    def format_name(self) -> str:
        return "YAML"
    
    @property
    def mime_type(self) -> str:
        return "application/x-yaml"
    
    @property
    def is_binary_format(self) -> bool:
        return False  # YAML is text-based
    
    @property
    def supports_streaming(self) -> bool:
        return True  # YAML supports multiple documents
    
    @property
    def supports_incremental_streaming(self) -> bool:
        return True  # YAML supports multi-document streaming
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["yaml", "YAML", "yml", "YML"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using PyYAML library)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to YAML string.
        
        Uses PyYAML's yaml.dump().
        
        Args:
            value: Data to serialize
            options: YAML options (default_flow_style, sort_keys, etc.)
        
        Returns:
            YAML string
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            opts = options or {}
            
            # Common YAML options
            default_flow_style = opts.get('default_flow_style', False)
            sort_keys = opts.get('sort_keys', False)
            indent = opts.get('indent', 2)
            
            # Encode to YAML string
            yaml_str = yaml.dump(
                value,
                default_flow_style=default_flow_style,
                sort_keys=sort_keys,
                indent=indent,
                allow_unicode=opts.get('allow_unicode', True),
                Dumper=opts.get('Dumper', yaml.SafeDumper)
            )
            
            return yaml_str
            
        except (yaml.YAMLError, TypeError) as e:
            raise SerializationError(
                f"Failed to encode YAML: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode YAML string to data.
        
        Uses PyYAML's yaml.safe_load() for security.
        
        Args:
            repr: YAML string (bytes or str)
            options: YAML options (Loader, etc.)
        
        Returns:
            Decoded Python object
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # Convert bytes to str if needed
            if isinstance(repr, bytes):
                repr = repr.decode('utf-8')
            
            opts = options or {}
            
            # Decode from YAML string (using safe_load for security)
            loader = opts.get('Loader', yaml.SafeLoader)
            data = yaml.load(repr, Loader=loader)
            
            return data
            
        except (yaml.YAMLError, UnicodeDecodeError) as e:
            raise SerializationError(
                f"Failed to decode YAML: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    # ========================================================================
    # INCREMENTAL STREAMING
    # ========================================================================
    
    def incremental_load(
        self,
        file_path: Union[str, Path],
        **options: Any,
    ) -> Iterator[Any]:
        """
        Stream YAML documents one at a time (supports multi-document YAML).
        
        Uses PyYAML's safe_load_all() for true streaming without loading
        entire file into memory.
        
        Args:
            file_path: Path to the YAML file
            **options: YAML options (Loader, etc.)
            
        Yields:
            Each document from the YAML file one at a time
            
        Raises:
            FileNotFoundError: If file doesn't exist
            SerializationError: If parsing fails
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        opts = options or {}
        loader = opts.get('Loader', yaml.SafeLoader)
        
        try:
            with path.open("r", encoding="utf-8") as f:
                # Use safe_load_all for multi-document streaming
                for document in yaml.safe_load_all(f):
                    if document is not None:  # Skip empty documents
                        yield document
        except (yaml.YAMLError, UnicodeDecodeError) as e:
            raise SerializationError(
                f"Failed to incrementally load YAML: {e}",
                format_name=self.format_name,
                original_error=e
            ) from e

