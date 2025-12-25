#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/formats/rar.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 1, 2025

RAR5 archive format implementation - RANK #3 PROPRIETARY COMPRESSION.

**Strong compression + recovery record + multi-volume**

Priority 1 (Security): Strong encryption
Priority 2 (Usability): Recovery records
Priority 3 (Maintainability): Clean RAR handling
Priority 4 (Performance): Strong compression
Priority 5 (Extensibility): Optional rarfile dependency
"""

from pathlib import Path
from typing import Optional

from ...contracts import IArchiveFormat
from ...errors import ArchiveError

# Lazy import for rarfile - optional dependency
try:
    import rarfile
except ImportError:
    rarfile = None  # type: ignore


class RarArchiver(IArchiveFormat):
    """
    RAR5 archive format handler - RANK #3.
    
    FormatAction naming: RarArchiver
    
    NOTE: Extraction only (requires UnRAR binary for creation).
    RAR is proprietary - use for extraction of existing RAR files.
    
    Features:
    - Strong compression
    - Recovery records
    - Multi-volume archives
    - AES encryption
    
    Examples:
        >>> archiver = RarArchiver()
        >>> # Extract existing RAR
        >>> archiver.extract(Path("archive.rar"), Path("output/"))
        >>> 
        >>> # With password
        >>> archiver.extract(archive, output, password="secret")
    """
    
    @property
    def format_id(self) -> str:
        """Format identifier."""
        return "rar"
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported extensions."""
        return [".rar", ".r00", ".r01"]
    
    @property
    def mime_types(self) -> list[str]:
        """MIME types."""
        return ["application/vnd.rar", "application/x-rar-compressed"]
    
    def create(self, files: list[Path], output: Path, **opts) -> None:
        """
        RAR creation not supported (proprietary).
        
        Use 7z or Zstandard for compression instead.
        """
        raise ArchiveError(
            "RAR creation requires WinRAR/RAR binary (proprietary). "
            "Use SevenZipArchiver or ZstandardArchiver instead for creation."
        )
    
    def extract(self, archive: Path, output_dir: Path, members: Optional[list[str]] = None, **opts) -> list[Path]:
        """
        Extract RAR archive.
        
        Options:
            password: Decryption password
        """
        if rarfile is None:
            raise ArchiveError("rarfile not installed. Install with: pip install rarfile")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        password = opts.get('password')
        
        try:
            with rarfile.RarFile(archive) as rf:
                if password:
                    rf.setpassword(password)
                
                if members:
                    for member in members:
                        rf.extract(member, output_dir)
                else:
                    rf.extractall(output_dir)
                
                return [output_dir / info.filename for info in rf.infolist()]
        except Exception as e:
            raise ArchiveError(f"Failed to extract RAR archive: {e}")
    
    def list_contents(self, archive: Path) -> list[str]:
        """List RAR contents."""
        if rarfile is None:
            raise ArchiveError("rarfile not installed. Install with: pip install rarfile")
        
        try:
            with rarfile.RarFile(archive) as rf:
                return rf.namelist()
        except Exception as e:
            raise ArchiveError(f"Failed to list RAR contents: {e}")
    
    def add_file(self, archive: Path, file: Path, arcname: Optional[str] = None) -> None:
        """RAR append not supported (requires WinRAR binary)."""
        raise ArchiveError("RAR append requires WinRAR/RAR binary (proprietary).")

