#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/archive.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Archive facade using registry pattern.

Like get_codec_for_file() - auto-detects format!

Priority 1 (Security): Safe archive operations
Priority 2 (Usability): Auto-detect format from extension
Priority 3 (Maintainability): Clean facade over registry
Priority 4 (Performance): Fast format lookup
Priority 5 (Extensibility): Add formats via registry!
"""

from pathlib import Path
from typing import Optional

# IArchive removed - using IArchiver and IArchiveFile instead
from .formats import get_archiver_for_file, get_archiver_by_id


class Archive:
    """
    Archive facade using registry (LIKE get_codec!).
    
    Auto-detects format from file extension.
    Delegates to format-specific handlers.
    
    Examples:
        >>> archive = Archive()
        >>> 
        >>> # Auto-detect format
        >>> archive.create([Path("file.txt")], Path("backup.zip"))  # Uses ZipArchiver
        >>> archive.create([Path("file.txt")], Path("backup.tar.gz"))  # Uses TarArchiver
        >>> 
        >>> # Future: 7z automatically supported when registered!
        >>> archive.create([Path("file.txt")], Path("backup.7z"))  # Uses 7zArchiver
    """
    
    def create(self, files: list[Path], output: Path, format: str = 'zip', **opts) -> None:
        """
        Create archive - auto-detects handler.
        
        Args:
            files: List of files to archive
            output: Output archive path
            format: Format hint (default: auto-detect from output path)
            **opts: Format-specific options
        """
        # Get archiver from registry
        if format:
            archiver = get_archiver_by_id(format)
        else:
            archiver = get_archiver_for_file(str(output))
        
        if archiver is None:
            raise ValueError(f"No archiver found for format: {format} or {output.suffix}")
        
        # Delegate to format-specific handler
        archiver.create(files, output, **opts)
    
    def extract(self, archive: Path, output_dir: Path, members: Optional[list[str]] = None, **opts) -> list[Path]:
        """
        Extract archive - auto-detects handler.
        """
        # Auto-detect format from archive extension
        archiver = get_archiver_for_file(str(archive))
        
        if archiver is None:
            raise ValueError(f"No archiver found for: {archive.suffix}")
        
        # Delegate to format-specific handler
        return archiver.extract(archive, output_dir, members, **opts)
    
    def list_contents(self, archive: Path) -> list[str]:
        """
        List archive contents - auto-detects handler.
        """
        # Auto-detect format
        archiver = get_archiver_for_file(str(archive))
        
        if archiver is None:
            raise ValueError(f"No archiver found for: {archive.suffix}")
        
        return archiver.list_contents(archive)
    
    def add_file(self, archive: Path, file: Path, arcname: Optional[str] = None) -> None:
        """
        Add file to archive - auto-detects handler.
        """
        # Auto-detect format
        archiver = get_archiver_for_file(str(archive))
        
        if archiver is None:
            raise ValueError(f"No archiver found for: {archive.suffix}")
        
        archiver.add_file(archive, file, arcname)
