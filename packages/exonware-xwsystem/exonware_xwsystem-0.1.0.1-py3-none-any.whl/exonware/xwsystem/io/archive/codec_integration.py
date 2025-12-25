#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/codec_integration.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 1, 2025

Archive-Codec Integration - Register archivers with CodecRegistry.

This enables:
- file.convert("zip", "7z") - Convert between archive formats
- file.save_as(path, "7z") - Save with different format
- get_codec_by_id("7z") - Get archiver as codec

Priority 1 (Security): Safe format conversion
Priority 2 (Usability): Seamless integration
Priority 3 (Maintainability): Single registry
Priority 4 (Performance): Cached instances
Priority 5 (Extensibility): Auto-registration
"""

from ..codec.registry import get_registry
from .archivers import ZipArchiver, TarArchiver


def register_archivers_as_codecs():
    """
    Register all archivers with the UniversalCodecRegistry.
    
    This enables:
    1. get_registry().get_by_id("zip") → XWZipArchiver
    2. get_registry().get_by_id("tar") → XWTarArchiver
    3. Unified codec discovery across all formats
    
    NOTE: Archivers implement IArchiver (which extends ICodec) and follow
    the I→A→XW pattern with full codec metadata support.
    """
    registry = get_registry()
    
    # Register codec-based archivers with UniversalCodecRegistry
    try:
        registry.register(ZipArchiver)
    except Exception as e:
        import logging
        logging.debug(f"Failed to register XWZipArchiver: {e}")
    
    try:
        registry.register(TarArchiver)
    except Exception as e:
        import logging
        logging.debug(f"Failed to register XWTarArchiver: {e}")


# Auto-register on import
register_archivers_as_codecs()

