#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/serialization/formats/binary/__init__.py
"""Binary serialization formats (core lightweight formats)."""

# Core binary formats
from .msgpack import MsgPackSerializer
from .pickle import PickleSerializer
from .bson import BsonSerializer
from .marshal import MarshalSerializer
from .cbor import CborSerializer
from .plistlib import PlistSerializer

__all__ = [
    "MsgPackSerializer",
    "PickleSerializer",
    "BsonSerializer",
    "MarshalSerializer",
    "CborSerializer",
    "PlistSerializer",
]

# NOTE: Enterprise binary formats moved to xwformats:
# - UBJSON (py-ubjson library, ~100 KB)
# 
# Install with: pip install exonware-xwformats
