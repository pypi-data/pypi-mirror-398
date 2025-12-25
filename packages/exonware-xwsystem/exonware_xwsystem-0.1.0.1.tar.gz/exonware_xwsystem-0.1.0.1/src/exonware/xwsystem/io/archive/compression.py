#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/compression.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Compression operations for gzip, bz2, and lzma.

Priority 1 (Security): Safe compression/decompression
Priority 2 (Usability): Auto-detect compression algorithm
Priority 3 (Maintainability): Clean compression logic
Priority 4 (Performance): Efficient compression with levels
Priority 5 (Extensibility): Easy to add new algorithms
"""

import gzip
import bz2
from pathlib import Path
from typing import Optional

# lzma is standard library (Python 3.3+)
import lzma

from ..contracts import ICompression


class Compression(ICompression):
    """
    Compression operations (gzip, bz2, lzma)
    
    Use cases:
    - Compress large files
    - Network transfer
    - Storage optimization
    - Backup compression
    
    Examples:
        >>> comp = Compression()
        >>> 
        >>> # Compress data
        >>> data = b"Hello" * 1000
        >>> compressed = comp.compress(data, algorithm='gzip')
        >>> 
        >>> # Decompress
        >>> original = comp.decompress(compressed)
        >>> 
        >>> # Compress file
        >>> comp.compress_file(Path("data.txt"))
        >>> # Creates data.txt.gz
    """
    
    def compress(self, data: bytes, algorithm: str = 'gzip', level: int = 6) -> bytes:
        """
        Compress bytes.
        
        Args:
            data: Data to compress
            algorithm: Compression algorithm (gzip, bz2, lzma)
            level: Compression level (1-9, higher = more compression)
        
        Returns:
            Compressed bytes
        """
        if algorithm == 'gzip':
            return gzip.compress(data, compresslevel=level)
        
        elif algorithm == 'bz2':
            return bz2.compress(data, compresslevel=level)
        
        elif algorithm == 'lzma':
            if lzma is None:
                raise ImportError("lzma module not available")
            return lzma.compress(data, preset=level)
        
        else:
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")
    
    def decompress(self, data: bytes, algorithm: Optional[str] = None) -> bytes:
        """
        Decompress bytes.
        
        Args:
            data: Compressed data
            algorithm: Algorithm (None = auto-detect)
        
        Returns:
            Decompressed bytes
        """
        if algorithm is None:
            # Try to auto-detect
            if data.startswith(b'\x1f\x8b'):
                algorithm = 'gzip'
            elif data.startswith(b'BZ'):
                algorithm = 'bz2'
            elif data.startswith(b'\xfd7zXZ\x00'):
                algorithm = 'lzma'
            else:
                # Try gzip first
                try:
                    return gzip.decompress(data)
                except Exception:
                    pass
                raise ValueError("Cannot auto-detect compression algorithm")
        
        if algorithm == 'gzip':
            return gzip.decompress(data)
        
        elif algorithm == 'bz2':
            return bz2.decompress(data)
        
        elif algorithm == 'lzma':
            if lzma is None:
                raise ImportError("lzma module not available")
            return lzma.decompress(data)
        
        else:
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")
    
    def compress_file(self, path: Path, algorithm: str = 'gzip', level: int = 6, **opts) -> Path:
        """
        Compress file.
        
        Args:
            path: File to compress
            algorithm: Compression algorithm
            level: Compression level
            **opts: Algorithm-specific options (output path)
        
        Returns:
            Path to compressed file (e.g., file.txt.gz)
        """
        # Determine output path
        output = opts.get('output')
        if output is None:
            if algorithm == 'gzip':
                output = Path(str(path) + '.gz')
            elif algorithm == 'bz2':
                output = Path(str(path) + '.bz2')
            elif algorithm == 'lzma':
                output = Path(str(path) + '.xz')
            else:
                output = Path(str(path) + f'.{algorithm}')
        else:
            output = Path(output)
        
        # Read and compress
        data = path.read_bytes()
        compressed = self.compress(data, algorithm=algorithm, level=level)
        
        # Write compressed data
        output.write_bytes(compressed)
        
        return output
    
    def decompress_file(self, path: Path, output: Optional[Path] = None) -> Path:
        """
        Decompress file.
        
        Args:
            path: Compressed file
            output: Output path (None = auto-generate from input)
        
        Returns:
            Path to decompressed file
        """
        # Determine output path
        if output is None:
            # Remove compression extension
            if path.suffix in ['.gz', '.bz2', '.xz']:
                output = path.with_suffix('')
            else:
                output = Path(str(path) + '.decompressed')
        else:
            output = Path(output)
        
        # Read and decompress
        data = path.read_bytes()
        decompressed = self.decompress(data)
        
        # Write decompressed data
        output.write_bytes(decompressed)
        
        return output

