#!/usr/bin/env python3
#exonware/xwsystem/serialization/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

Serialization types and enums for XWSystem.
"""

from enum import Enum, Flag, auto


# ============================================================================
# SERIALIZATION ENUMS
# ============================================================================

class SerializationFormat(Enum):
    """Supported serialization formats."""
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    TOML = "toml"
    PICKLE = "pickle"
    MSGPACK = "msgpack"
    CBOR = "cbor"
    BSON = "bson"
    PROTOBUF = "protobuf"
    AVRO = "avro"
    NATIVE = "native"


class SerializationMode(Enum):
    """Serialization modes."""
    COMPACT = "compact"
    PRETTY = "pretty"
    BINARY = "binary"
    TEXT = "text"


class SerializationType(Enum):
    """Serialization types."""
    OBJECT = "object"
    ARRAY = "array"
    PRIMITIVE = "primitive"
    CUSTOM = "custom"


class SerializationCapability(Flag):
    """Serialization capabilities for introspection."""
    STREAMING = auto()
    PARTIAL_ACCESS = auto()
    TYPED_DECODE = auto()
    ZERO_COPY = auto()
    CANONICAL = auto()
    RANDOM_ACCESS = auto()
    # Advanced features (added in ADR-001)
    PATH_BASED_UPDATES = auto()  # Supports JSONPointer/XPath/YAML path updates
    ATOMIC_PATH_WRITE = auto()  # Can atomically update paths without loading full file
    SCHEMA_VALIDATION = auto()  # Supports schema validation
    INCREMENTAL_STREAMING = auto()  # True incremental streaming (not chunked full-file)
    MULTI_DOCUMENT = auto()  # Supports multiple documents in one file
    QUERY_SUPPORT = auto()  # Supports query/filter operations (JSONPath, XPath)
    MERGE_OPERATIONS = auto()  # Supports merge/update operations
    LAZY_LOADING = auto()  # Supports lazy loading for large files


class CompatibilityLevel(Enum):
    """Schema compatibility levels."""
    NONE = "NONE"
    BACKWARD = "BACKWARD"
    BACKWARD_TRANSITIVE = "BACKWARD_TRANSITIVE"
    FORWARD = "FORWARD"
    FORWARD_TRANSITIVE = "FORWARD_TRANSITIVE"
    FULL = "FULL"
    FULL_TRANSITIVE = "FULL_TRANSITIVE"