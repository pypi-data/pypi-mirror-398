"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 2, 2025

CSV serialization - Comma-separated values format.

Following I→A pattern:
- I: ISerialization (interface)
- A: ASerialization (abstract base)
- Concrete: CsvSerializer
"""

import csv
import io
from typing import Any, Optional, Union
from pathlib import Path

from ...base import ASerialization
from ....contracts import EncodeOptions, DecodeOptions
from ....defs import CodecCapability
from ....errors import SerializationError


class CsvSerializer(ASerialization):
    """
    CSV serializer - follows the I→A pattern.
    
    I: ISerialization (interface)
    A: ASerialization (abstract base)
    Concrete: CsvSerializer
    
    Uses Python's built-in csv module.
    
    Examples:
        >>> serializer = CsvSerializer()
        >>> 
        >>> # Encode list of dicts
        >>> csv_str = serializer.encode([
        ...     {"name": "John", "age": 30},
        ...     {"name": "Jane", "age": 25}
        ... ])
        >>> 
        >>> # Decode to list of dicts
        >>> data = serializer.decode(csv_str)
        >>> 
        >>> # Save to file
        >>> serializer.save_file(rows, "data.csv")
        >>> 
        >>> # Load from file
        >>> rows = serializer.load_file("data.csv")
    """
    
    # ========================================================================
    # CODEC METADATA
    # ========================================================================
    
    @property
    def codec_id(self) -> str:
        return "csv"
    
    @property
    def media_types(self) -> list[str]:
        return ["text/csv", "application/csv"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".csv", ".tsv", ".psv"]
    
    @property
    def format_name(self) -> str:
        return "CSV"
    
    @property
    def mime_type(self) -> str:
        return "text/csv"
    
    @property
    def is_binary_format(self) -> bool:
        return False  # CSV is text-based
    
    @property
    def supports_streaming(self) -> bool:
        return True  # CSV naturally supports streaming (row by row)
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def aliases(self) -> list[str]:
        return ["csv", "CSV", "tsv", "TSV"]
    
    @property
    def codec_types(self) -> list[str]:
        """CSV is primarily a data exchange format."""
        return ["data"]
    
    # ========================================================================
    # CORE ENCODE/DECODE (Using csv module)
    # ========================================================================
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> Union[bytes, str]:
        """
        Encode data to CSV string.
        
        Uses csv.DictWriter or csv.writer.
        
        Args:
            value: Data to serialize (list of dicts or list of lists)
            options: CSV options (delimiter, quoting, etc.)
        
        Returns:
            CSV string
        
        Raises:
            SerializationError: If encoding fails
        """
        try:
            opts = options or {}
            
            # Get CSV options
            delimiter = opts.get('delimiter', ',')
            quoting = opts.get('quoting', csv.QUOTE_MINIMAL)
            
            # Create string buffer
            output = io.StringIO()
            
            if isinstance(value, list) and value:
                if isinstance(value[0], dict):
                    # List of dicts - use DictWriter
                    fieldnames = opts.get('fieldnames', list(value[0].keys()))
                    writer = csv.DictWriter(
                        output,
                        fieldnames=fieldnames,
                        delimiter=delimiter,
                        quoting=quoting
                    )
                    
                    # Write header
                    if opts.get('header', True):
                        writer.writeheader()
                    
                    # Write rows
                    writer.writerows(value)
                else:
                    # List of lists - use regular writer
                    writer = csv.writer(
                        output,
                        delimiter=delimiter,
                        quoting=quoting
                    )
                    writer.writerows(value)
            
            return output.getvalue()
            
        except Exception as e:
            raise SerializationError(
                f"Failed to encode CSV: {e}",
                format_name=self.format_name,
                original_error=e
            )
    
    def decode(self, repr: Union[bytes, str], *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode CSV string to data.
        
        Uses csv.DictReader or csv.reader.
        
        Args:
            repr: CSV string (bytes or str)
            options: CSV options (delimiter, has_header, etc.)
        
        Returns:
            List of dicts (if header) or list of lists
        
        Raises:
            SerializationError: If decoding fails
        """
        try:
            # Convert bytes to str if needed
            if isinstance(repr, bytes):
                repr = repr.decode('utf-8')
            
            opts = options or {}
            
            # Get CSV options
            delimiter = opts.get('delimiter', ',')
            has_header = opts.get('header', True)
            
            # Create string buffer
            input_stream = io.StringIO(repr)
            
            if has_header:
                # Use DictReader for header-based CSV
                reader = csv.DictReader(input_stream, delimiter=delimiter)
                data = list(reader)
            else:
                # Use regular reader for headerless CSV
                reader = csv.reader(input_stream, delimiter=delimiter)
                data = list(reader)
            
            return data
            
        except (Exception, UnicodeDecodeError) as e:
            raise SerializationError(
                f"Failed to decode CSV: {e}",
                format_name=self.format_name,
                original_error=e
            )

