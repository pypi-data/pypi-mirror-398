#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/file/conversion.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 1, 2025

File Format Conversion - Convert between compatible formats.

Enables:
- file.convert("zip", "7z") - Archive conversion
- file.convert("json", "yaml") - Serialization conversion
- file.save_as(path, "7z") - Save with different format

Priority 1 (Security): Safe conversion validation
Priority 2 (Usability): Simple API
Priority 3 (Maintainability): Category-based compatibility
Priority 4 (Performance): Direct codec delegation
Priority 5 (Extensibility): Works with any registered codec
"""

from pathlib import Path
from typing import Any, Optional, Union

from ..codec.base import get_global_registry
from ..contracts import ICodec
from ..defs import CodecCategory
from ..errors import CodecError, CodecNotFoundError


class FormatConverter:
    """
    Format converter using codec registry.
    
    Validates category compatibility before conversion.
    
    Examples:
        >>> converter = FormatConverter()
        >>> 
        >>> # Archive conversion (both ARCHIVE category)
        >>> converter.convert_file(
        ...     Path("backup.zip"),
        ...     Path("backup.7z"),
        ...     source_format="zip",
        ...     target_format="7z"
        ... )
        >>> 
        >>> # Serialization conversion (both SERIALIZATION category)
        >>> converter.convert_file(
        ...     Path("data.json"),
        ...     Path("data.yaml"),
        ...     source_format="json",
        ...     target_format="yaml"
        ... )
        >>> 
        >>> # ERROR: Incompatible categories
        >>> converter.convert_file(
        ...     Path("data.json"),
        ...     Path("data.zip"),  # json=SERIALIZATION, zip=ARCHIVE
        ...     source_format="json",
        ...     target_format="zip"
        ... )
        # Raises: CodecError("Incompatible categories")
    """
    
    def __init__(self):
        """Initialize converter with codec registry."""
        self._registry = get_global_registry()
    
    def get_codec(self, format_id: str) -> ICodec:
        """Get codec by format ID."""
        codec = self._registry.get_by_id(format_id)
        if codec is None:
            raise CodecNotFoundError(
                f"Format '{format_id}' not found in registry. "
                f"Available formats: {', '.join(self._registry.list_codec_ids())}"
            )
        return codec
    
    def validate_compatibility(self, source_codec: ICodec, target_codec: ICodec) -> None:
        """
        Validate that formats are compatible for conversion.
        
        Rules:
        1. Both must have the same category (ARCHIVE, SERIALIZATION, etc.)
        2. Both must support BIDIRECTIONAL capability
        
        Raises:
            CodecError: If formats are incompatible
        """
        # Check categories
        if not hasattr(source_codec, 'category') or not hasattr(target_codec, 'category'):
            raise CodecError(
                "Codecs must have 'category' property for conversion validation"
            )
        
        source_category = source_codec.category
        target_category = target_codec.category
        
        if source_category != target_category:
            raise CodecError(
                f"Cannot convert between incompatible categories: "
                f"{source_category.value} → {target_category.value}. "
                f"Both formats must be in the same category (ARCHIVE, SERIALIZATION, etc.)"
            )
        
        # Check bidirectional support
        from ..defs import CodecCapability
        
        if hasattr(source_codec, 'supports_capability'):
            if not source_codec.supports_capability(CodecCapability.BIDIRECTIONAL):
                raise CodecError(f"Source codec '{source_codec.codec_id}' doesn't support decode")
        
        if hasattr(target_codec, 'supports_capability'):
            if not target_codec.supports_capability(CodecCapability.BIDIRECTIONAL):
                raise CodecError(f"Target codec '{target_codec.codec_id}' doesn't support encode")
    
    def convert_data(
        self,
        data: bytes,
        source_format: str,
        target_format: str,
        **options
    ) -> bytes:
        """
        Convert data from one format to another.
        
        Args:
            data: Source data bytes
            source_format: Source format ID (e.g., "zip", "json")
            target_format: Target format ID (e.g., "7z", "yaml")
            **options: Format-specific options
        
        Returns:
            Converted data bytes
        
        Raises:
            CodecNotFoundError: If format not found
            CodecError: If formats incompatible
        """
        # Get codecs
        source_codec = self.get_codec(source_format)
        target_codec = self.get_codec(target_format)
        
        # Validate compatibility
        self.validate_compatibility(source_codec, target_codec)
        
        # Convert: decode with source → encode with target
        intermediate = source_codec.decode(data, options=options.get('decode_options'))
        result = target_codec.encode(intermediate, options=options.get('encode_options'))
        
        return result
    
    def convert_file(
        self,
        source_path: Path,
        target_path: Path,
        source_format: Optional[str] = None,
        target_format: Optional[str] = None,
        **options
    ) -> None:
        """
        Convert file from one format to another.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            source_format: Source format ID (auto-detected if None)
            target_format: Target format ID (auto-detected if None)
            **options: Format-specific options
        
        Examples:
            >>> converter.convert_file(
            ...     Path("backup.zip"),
            ...     Path("backup.7z")
            ... )  # Auto-detects from extensions
            >>> 
            >>> converter.convert_file(
            ...     Path("data.json"),
            ...     Path("data.yaml"),
            ...     source_format="json",
            ...     target_format="yaml"
            ... )
        """
        # Auto-detect formats from extensions if not provided
        if source_format is None:
            source_codec = self._registry.get_by_extension(source_path.suffix)
            if source_codec is None:
                raise CodecNotFoundError(
                    f"Cannot auto-detect format from extension: {source_path.suffix}"
                )
            source_format = source_codec.codec_id
        
        if target_format is None:
            target_codec = self._registry.get_by_extension(target_path.suffix)
            if target_codec is None:
                raise CodecNotFoundError(
                    f"Cannot auto-detect format from extension: {target_path.suffix}"
                )
            target_format = target_codec.codec_id
        
        # Read source file
        source_data = source_path.read_bytes()
        
        # Convert
        target_data = self.convert_data(
            source_data,
            source_format,
            target_format,
            **options
        )
        
        # Write target file
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(target_data)


# Global instance
_converter = FormatConverter()


def convert_file(
    source_path: Path,
    target_path: Path,
    source_format: Optional[str] = None,
    target_format: Optional[str] = None,
    **options
) -> None:
    """
    Convenience function for file conversion.
    
    Examples:
        >>> from exonware.xwsystem.io.file.conversion import convert_file
        >>> 
        >>> # Archive conversion
        >>> convert_file(Path("backup.zip"), Path("backup.7z"))
        >>> 
        >>> # Serialization conversion
        >>> convert_file(Path("data.json"), Path("data.yaml"))
    """
    _converter.convert_file(source_path, target_path, source_format, target_format, **options)

