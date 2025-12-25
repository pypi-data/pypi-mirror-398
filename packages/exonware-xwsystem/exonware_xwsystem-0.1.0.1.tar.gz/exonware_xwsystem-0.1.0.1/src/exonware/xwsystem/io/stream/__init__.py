#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/stream/__init__.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Stream operations and codec-integrated I/O.

Following codec/ pattern + THE KILLER FEATURE (CodecIO)!

Priority 1 (Security): Safe streaming with validation
Priority 2 (Usability): Seamless codec integration - auto-detect format!
Priority 3 (Maintainability): Clean codec + I/O separation
Priority 4 (Performance): Memory-efficient streaming
Priority 5 (Extensibility): Works with any codec + any source
"""

from ..contracts import ICodecIO, IPagedCodecIO
from ..defs import StreamMode, CodecIOMode
from .base import ACodecIO, APagedCodecIO
from ..errors import StreamError, CodecIOError, AsyncIOError
from .codec_io import CodecIO, PagedCodecIO
from .async_operations import AsyncAtomicFileWriter

__all__ = [
    # Contracts
    "ICodecIO",
    "IPagedCodecIO",
    
    # Definitions
    "StreamMode",
    "CodecIOMode",
    
    # Base classes
    "ACodecIO",
    "APagedCodecIO",
    
    # Errors
    "StreamError",
    "CodecIOError",
    "AsyncIOError",
    
    # Concrete implementations
    "CodecIO",
    "PagedCodecIO",
    "AsyncAtomicFileWriter",
]
