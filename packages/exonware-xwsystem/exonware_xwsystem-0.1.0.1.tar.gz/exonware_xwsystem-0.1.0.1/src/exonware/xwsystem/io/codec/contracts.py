"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Codec module contracts - interfaces for codec operations.
"""

from typing import Protocol, Optional, runtime_checkable
from pathlib import Path

from ..contracts import EncodeOptions, DecodeOptions, CodecCapability


# ============================================================================
# CODEC INTERFACES
# ============================================================================

@runtime_checkable
class ICodec[T, R](Protocol):
    """
    Universal codec interface for bidirectional transformation.
    
    A codec transforms between a model (T) and its representation (R).
    This is the minimal contract that all codecs must implement.
    
    Type Parameters:
        T: Model type (e.g., dict, AST, dataclass)
        R: Representation type (bytes or str)
    
    Examples:
        JSON serializer:  ICodec[dict, bytes]
        SQL formatter:    ICodec[QueryAST, str]
        Pickle:           ICodec[Any, bytes]
        Python unparser:  ICodec[ast.AST, str]
    
    Design Principles:
        - Bidirectional by default (encode/decode)
        - Options-based configuration (not constructor pollution)
        - Representation-type specific (bytes OR str, not both)
        - Composable via adapters
    """
    
    def encode(self, value: T, *, options: Optional[EncodeOptions] = None) -> R:
        """
        Encode a model to its representation.
        
        Args:
            value: Model instance to encode
            options: Format-specific encoding options (e.g., {'pretty': True})
        
        Returns:
            Representation (bytes or str depending on codec type)
        
        Raises:
            EncodeError: If encoding fails
        
        Examples:
            >>> codec = JsonSerializer()
            >>> codec.encode({"key": "value"})
            b'{"key":"value"}'
            
            >>> formatter = SqlFormatter()
            >>> formatter.encode(select_ast, options={"pretty": True})
            'SELECT *\\nFROM users\\nWHERE id = 1'
        """
        ...
    
    def decode(self, repr: R, *, options: Optional[DecodeOptions] = None) -> T:
        """
        Decode a representation to a model.
        
        Args:
            repr: Representation to decode (bytes or str)
            options: Format-specific decoding options (e.g., {'strict': False})
        
        Returns:
            Model instance
        
        Raises:
            DecodeError: If decoding fails
        
        Examples:
            >>> codec = JsonSerializer()
            >>> codec.decode(b'{"key":"value"}')
            {'key': 'value'}
            
            >>> formatter = SqlFormatter()
            >>> formatter.decode('SELECT * FROM users')
            QueryAST(...)
        """
        ...


@runtime_checkable
class ICodecMetadata(Protocol):
    """
    Metadata protocol for codec discovery and registration.
    
    Codecs that implement this protocol can self-register and be
    discovered by the registry system with no hardcoding.
    
    Example:
        >>> class JsonCodec:
        ...     codec_id = "json"
        ...     media_types = ["application/json", "text/json"]
        ...     file_extensions = [".json", ".jsonl"]
        ...     aliases = ["JSON"]
        ...     
        ...     def capabilities(self):
        ...         return CodecCapability.BIDIRECTIONAL | CodecCapability.TEXT
    """
    
    @property
    def codec_id(self) -> str:
        """
        Unique codec identifier.
        
        Should be lowercase, alphanumeric + dash/underscore.
        
        Examples:
            - "json"
            - "sql"
            - "protobuf"
            - "python-ast"
        """
        ...
    
    @property
    def media_types(self) -> list[str]:
        """
        Supported media types / content types (RFC 2046).
        
        Used for content negotiation and HTTP Content-Type headers.
        
        Examples:
            - JSON: ["application/json", "text/json"]
            - SQL: ["application/sql", "text/x-sql"]
            - Protobuf: ["application/protobuf", "application/x-protobuf"]
        """
        ...
    
    @property
    def file_extensions(self) -> list[str]:
        """
        Supported file extensions (with leading dot).
        
        Used for auto-detection from file paths.
        
        Examples:
            - JSON: [".json", ".jsonl"]
            - SQL: [".sql", ".ddl", ".dml"]
            - Python: [".py", ".pyi"]
        """
        ...
    
    @property
    def aliases(self) -> list[str]:
        """
        Alternative names for this codec.
        
        Used for flexible lookup (case-insensitive matching).
        
        Examples:
            - JSON: ["json", "JSON"]
            - SQL: ["sql", "SQL", "structured-query"]
        """
        ...
    
    @property
    def codec_types(self) -> list[str]:
        """
        Codec categories for classification and filtering (can be multiple).
        
        Used to group codecs by their purposes. A codec can belong to multiple categories.
        
        Standard types:
            - "serialization": Data serialization formats (JSON, YAML, XML, etc.)
            - "archive": Archive/compression formats (ZIP, TAR, GZ, etc.)
            - "compression": Pure compression formats (GZIP, BZIP2, etc.)
            - "query": Query language parsers (SQL, GraphQL, Cypher, etc.)
            - "syntax": Programming language syntax (Python, JavaScript, etc.)
            - "binary": Binary formats (Protobuf, MessagePack, etc.)
            - "markup": Markup languages (HTML, Markdown, XML, etc.)
            - "schema": Schema definition languages (JSON Schema, XSD, etc.)
            - "config": Configuration formats (INI, ENV, TOML, etc.)
            - "data": Data exchange formats (CSV, Excel, etc.)
        
        Examples:
            - JSON codec: ["serialization"]
            - XML codec: ["serialization", "markup"]
            - TOML codec: ["config", "serialization"]
            - ZIP codec: ["archive"]
            - SQL codec: ["query"]
            - Python codec: ["syntax"]
        """
        ...
    
    def capabilities(self) -> CodecCapability:
        """
        Get capabilities supported by this codec.
        
        Returns:
            Flag combination of supported features
        
        Example:
            >>> codec.capabilities()
            CodecCapability.BIDIRECTIONAL | CodecCapability.TEXT | CodecCapability.SCHEMA
        """
        ...

