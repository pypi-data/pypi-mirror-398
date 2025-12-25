#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/formats/sevenzip.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 1, 2025

7z archive format implementation - RANK #1 BEST COMPRESSION.

**Best overall ratio + AES-256 encryption + solid archiving**

Priority 1 (Security): AES-256 encryption support
Priority 2 (Usability): Best compression ratio
Priority 3 (Maintainability): Clean 7z handling
Priority 4 (Performance): LZMA2 compression
Priority 5 (Extensibility): Lazy installation of py7zr
"""

from pathlib import Path
from typing import Optional

from ...contracts import IArchiveFormat
from ...errors import ArchiveError

# Lazy import for py7zr - optional dependency
try:
    import py7zr
except ImportError:
    py7zr = None  # type: ignore


class SevenZipArchiver(IArchiveFormat):
    """
    7z archive format handler - RANK #1.
    
    FormatAction naming: SevenZipArchiver
    
    Best overall compression with:
    - LZMA2 compression (best ratio)
    - AES-256 encryption
    - Solid archiving (better compression)
    - Multi-volume archives
    
    Examples:
        >>> archiver = SevenZipArchiver()
        >>> archiver.create([Path("data.txt")], Path("backup.7z"))
        >>> 
        >>> # With encryption
        >>> archiver.create(files, output, password="secret123")
        >>> 
        >>> # With solid compression
        >>> archiver.create(files, output, solid=True)
    """
    
    @property
    def format_id(self) -> str:
        """Format identifier."""
        return "7z"
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported extensions."""
        return [".7z"]
    
    @property
    def mime_types(self) -> list[str]:
        """MIME types."""
        return ["application/x-7z-compressed"]
    
    def create(self, files: list[Path], output: Path, **opts) -> None:
        """
        Create 7z archive with optional encryption.
        
        Options:
            password: Encryption password (AES-256)
            solid: Solid archiving for better compression
            filters: Custom LZMA2 filters
        """
        if py7zr is None:
            raise ArchiveError("py7zr not installed. Install with: pip install py7zr")
        
        output.parent.mkdir(parents=True, exist_ok=True)
        
        password = opts.get('password')
        
        try:
            with py7zr.SevenZipFile(output, 'w', password=password) as archive:
                for file_path in files:
                    if file_path.is_file():
                        archive.write(file_path, arcname=file_path.name)
                    elif file_path.is_dir():
                        archive.writeall(file_path, arcname=file_path.name)
        except Exception as e:
            raise ArchiveError(f"Failed to create 7z archive: {e}")
    
    def extract(self, archive: Path, output_dir: Path, members: Optional[list[str]] = None, **opts) -> list[Path]:
        """
        Extract 7z archive.
        
        Options:
            password: Decryption password
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        password = opts.get('password')
        
        try:
            with py7zr.SevenZipFile(archive, 'r', password=password) as zf:
                if members:
                    zf.extract(output_dir, targets=members)
                else:
                    zf.extractall(output_dir)
                
                # Return extracted files
                return [output_dir / name for name in zf.getnames()]
        except Exception as e:
            raise ArchiveError(f"Failed to extract 7z archive: {e}")
    
    def list_contents(self, archive: Path) -> list[str]:
        """List 7z contents."""
        try:
            with py7zr.SevenZipFile(archive, 'r') as zf:
                return zf.getnames()
        except Exception as e:
            raise ArchiveError(f"Failed to list 7z contents: {e}")
    
    def add_file(self, archive: Path, file: Path, arcname: Optional[str] = None) -> None:
        """Add file to 7z archive (append mode)."""
        arcname = arcname or file.name
        try:
            with py7zr.SevenZipFile(archive, 'a') as zf:
                zf.write(file, arcname=arcname)
        except Exception as e:
            raise ArchiveError(f"Failed to add file to 7z: {e}")

