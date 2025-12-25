#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/formats/brotli_format.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 1, 2025

Brotli (.br) compression format - RANK #6 WEB COMPRESSION.

**Excellent for web & text assets**

Priority 1 (Security): Safe compression
Priority 2 (Usability): Excellent text compression
Priority 3 (Maintainability): Clean brotli handling
Priority 4 (Performance): Optimized for web
Priority 5 (Extensibility): Lazy installation of brotli
"""

import tarfile
from pathlib import Path
from typing import Optional

from ...contracts import IArchiveFormat
from ...errors import ArchiveError

# Lazy import for brotli - optional dependency
try:
    import brotli
except ImportError:
    brotli = None  # type: ignore


class BrotliArchiver(IArchiveFormat):
    """
    Brotli (.br) archive format handler - RANK #6.
    
    FormatAction naming: BrotliArchiver
    
    Web-optimized compression with:
    - Excellent text/HTML/JSON compression
    - Dictionary support
    - Quality levels 0-11
    - Widely supported in browsers
    
    Examples:
        >>> archiver = BrotliArchiver()
        >>> archiver.create([Path("index.html")], Path("website.tar.br"))
        >>> 
        >>> # Maximum compression for static assets
        >>> archiver.create(files, output, quality=11)
        >>> 
        >>> # Fast compression for dynamic content
        >>> archiver.create(files, output, quality=4)
    """
    
    @property
    def format_id(self) -> str:
        """Format identifier."""
        return "br"
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported extensions."""
        return [".br", ".tar.br", ".tbr"]
    
    @property
    def mime_types(self) -> list[str]:
        """MIME types."""
        return ["application/x-brotli"]
    
    def create(self, files: list[Path], output: Path, **opts) -> None:
        """
        Create Brotli-compressed tar archive.
        
        Options:
            quality: Compression quality (0-11, default: 11 for static)
            mode: Compression mode (generic, text, font)
        """
        if brotli is None:
            raise ArchiveError("brotli not installed. Install with: pip install brotli")
        
        output.parent.mkdir(parents=True, exist_ok=True)
        
        quality = opts.get('quality', 11)  # Max quality for static assets
        mode = opts.get('mode', brotli.MODE_GENERIC)
        
        try:
            # First create tar
            import io
            tar_buffer = io.BytesIO()
            
            with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
                for file_path in files:
                    if file_path.exists():
                        tar.add(file_path, arcname=file_path.name)
            
            # Then compress with brotli
            tar_data = tar_buffer.getvalue()
            compressed = brotli.compress(tar_data, quality=quality, mode=mode)
            
            output.write_bytes(compressed)
        except Exception as e:
            raise ArchiveError(f"Failed to create brotli archive: {e}")
    
    def extract(self, archive: Path, output_dir: Path, members: Optional[list[str]] = None, **opts) -> list[Path]:
        """Extract Brotli archive."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Decompress brotli
            compressed = archive.read_bytes()
            decompressed = brotli.decompress(compressed)
            
            # Extract tar
            import io
            tar_buffer = io.BytesIO(decompressed)
            
            extracted = []
            with tarfile.open(fileobj=tar_buffer, mode='r') as tar:
                if members:
                    for member in members:
                        tar.extract(member, output_dir)
                        extracted.append(output_dir / member)
                else:
                    tar.extractall(output_dir)
                    extracted = [output_dir / m.name for m in tar.getmembers()]
            
            return extracted
        except Exception as e:
            raise ArchiveError(f"Failed to extract brotli archive: {e}")
    
    def list_contents(self, archive: Path) -> list[str]:
        """List Brotli archive contents."""
        try:
            compressed = archive.read_bytes()
            decompressed = brotli.decompress(compressed)
            
            import io
            tar_buffer = io.BytesIO(decompressed)
            
            with tarfile.open(fileobj=tar_buffer, mode='r') as tar:
                return [m.name for m in tar.getmembers()]
        except Exception as e:
            raise ArchiveError(f"Failed to list brotli contents: {e}")
    
    def add_file(self, archive: Path, file: Path, arcname: Optional[str] = None) -> None:
        """Not supported - recreate archive instead."""
        raise ArchiveError("Brotli doesn't support append mode. Recreate the archive.")

