#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/formats/zstandard.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 1, 2025

Zstandard (.zst) compression format - RANK #2 MODERN STANDARD.

**Fastest balanced modern compression - ideal for backups & databases**

Priority 1 (Security): Safe compression
Priority 2 (Usability): Fast compression/decompression
Priority 3 (Maintainability): Clean zstd handling
Priority 4 (Performance): Best speed/ratio balance
Priority 5 (Extensibility): Lazy installation of zstandard
"""

import tarfile
from pathlib import Path
from typing import Optional

from ...contracts import IArchiveFormat
from ...errors import ArchiveError

# Lazy import for zstandard - optional dependency
try:
    import zstandard
except ImportError:
    zstandard = None  # type: ignore


class ZstandardArchiver(IArchiveFormat):
    """
    Zstandard (.zst) archive format handler - RANK #2.
    
    FormatAction naming: ZstandardArchiver
    
    Modern compression with:
    - Very fast compression/decompression
    - Excellent compression ratio
    - Streaming support
    - Dictionary compression
    - Ideal for databases and backups
    
    Examples:
        >>> archiver = ZstandardArchiver()
        >>> archiver.create([Path("database.db")], Path("backup.tar.zst"))
        >>> 
        >>> # High compression
        >>> archiver.create(files, output, level=22)
        >>> 
        >>> # Fast compression
        >>> archiver.create(files, output, level=1)
    """
    
    @property
    def format_id(self) -> str:
        """Format identifier."""
        return "zst"
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported extensions."""
        return [".zst", ".tar.zst", ".tzst"]
    
    @property
    def mime_types(self) -> list[str]:
        """MIME types."""
        return ["application/zstd", "application/x-zstd"]
    
    def create(self, files: list[Path], output: Path, **opts) -> None:
        """
        Create Zstandard-compressed tar archive.
        
        Options:
            level: Compression level (1-22, default: 3)
            threads: Number of threads for compression
        """
        if zstandard is None:
            raise ArchiveError("zstandard not installed. Install with: pip install zstandard")
        
        output.parent.mkdir(parents=True, exist_ok=True)
        
        level = opts.get('level', 3)  # Default: fast balanced
        threads = opts.get('threads', 0)  # 0 = auto
        
        try:
            # Create compressor
            cctx = zstandard.ZstdCompressor(level=level, threads=threads)
            
            # Create tar.zst archive
            with output.open('wb') as f:
                with cctx.stream_writer(f) as compressor:
                    with tarfile.open(fileobj=compressor, mode='w|') as tar:
                        for file_path in files:
                            if file_path.exists():
                                tar.add(file_path, arcname=file_path.name)
        except Exception as e:
            raise ArchiveError(f"Failed to create zst archive: {e}")
    
    def extract(self, archive: Path, output_dir: Path, members: Optional[list[str]] = None, **opts) -> list[Path]:
        """Extract Zstandard archive."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Create decompressor
            dctx = zstandard.ZstdDecompressor()
            
            extracted = []
            with archive.open('rb') as f:
                with dctx.stream_reader(f) as decompressor:
                    with tarfile.open(fileobj=decompressor, mode='r|') as tar:
                        if members:
                            for member in members:
                                tar.extract(member, output_dir)
                                extracted.append(output_dir / member)
                        else:
                            tar.extractall(output_dir)
                            extracted = [output_dir / m.name for m in tar.getmembers()]
            
            return extracted
        except Exception as e:
            raise ArchiveError(f"Failed to extract zst archive: {e}")
    
    def list_contents(self, archive: Path) -> list[str]:
        """List Zstandard archive contents."""
        try:
            dctx = zstandard.ZstdDecompressor()
            
            with archive.open('rb') as f:
                with dctx.stream_reader(f) as decompressor:
                    with tarfile.open(fileobj=decompressor, mode='r|') as tar:
                        return [m.name for m in tar.getmembers()]
        except Exception as e:
            raise ArchiveError(f"Failed to list zst contents: {e}")
    
    def add_file(self, archive: Path, file: Path, arcname: Optional[str] = None) -> None:
        """Not supported for streaming format - recreate archive instead."""
        raise ArchiveError("Zstandard streaming format doesn't support append mode. Recreate the archive.")

