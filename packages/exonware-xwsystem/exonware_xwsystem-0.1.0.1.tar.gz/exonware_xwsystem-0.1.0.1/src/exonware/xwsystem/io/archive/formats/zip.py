#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/formats/zip.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

ZIP archive format implementation.

Priority 1 (Security): Safe ZIP operations
Priority 2 (Usability): Simple ZIP API
Priority 3 (Maintainability): Clean ZIP handling
Priority 4 (Performance): Efficient ZIP operations
Priority 5 (Extensibility): Registered via registry
"""

import zipfile
from pathlib import Path
from typing import Optional

from ...contracts import IArchiveFormat


class ZipArchiver(IArchiveFormat):
    """ZIP archive format handler."""
    
    @property
    def format_id(self) -> str:
        """Format identifier."""
        return "zip"
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported extensions."""
        return [".zip", ".jar", ".war", ".ear"]
    
    @property
    def mime_types(self) -> list[str]:
        """MIME types."""
        return ["application/zip", "application/java-archive"]
    
    def create(self, files: list[Path], output: Path, **opts) -> None:
        """Create ZIP archive."""
        output.parent.mkdir(parents=True, exist_ok=True)
        
        compression = opts.get('compression', zipfile.ZIP_DEFLATED)
        compresslevel = opts.get('compresslevel', 6)
        
        with zipfile.ZipFile(output, 'w', compression=compression, compresslevel=compresslevel) as zf:
            for file_path in files:
                if file_path.is_file():
                    arcname = opts.get('arcname', file_path.name)
                    zf.write(file_path, arcname=arcname)
                elif file_path.is_dir():
                    # Add directory recursively
                    for item in file_path.rglob('*'):
                        if item.is_file():
                            arcname = str(item.relative_to(file_path.parent))
                            zf.write(item, arcname=arcname)
    
    def extract(self, archive: Path, output_dir: Path, members: Optional[list[str]] = None, **opts) -> list[Path]:
        """Extract ZIP archive."""
        output_dir.mkdir(parents=True, exist_ok=True)
        extracted: list[Path] = []
        
        with zipfile.ZipFile(archive, 'r') as zf:
            if members:
                for member in members:
                    zf.extract(member, output_dir)
                    extracted.append(output_dir / member)
            else:
                zf.extractall(output_dir)
                extracted = [output_dir / name for name in zf.namelist()]
        
        return extracted
    
    def list_contents(self, archive: Path) -> list[str]:
        """List ZIP contents."""
        with zipfile.ZipFile(archive, 'r') as zf:
            return zf.namelist()
    
    def add_file(self, archive: Path, file: Path, arcname: Optional[str] = None) -> None:
        """Add file to ZIP archive."""
        arcname = arcname or file.name
        with zipfile.ZipFile(archive, 'a') as zf:
            zf.write(file, arcname=arcname)

