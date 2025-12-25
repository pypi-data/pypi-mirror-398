#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/formats/tar.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

TAR archive format implementation.

Priority 1 (Security): Safe TAR operations
Priority 2 (Usability): Simple TAR API
Priority 3 (Maintainability): Clean TAR handling
Priority 4 (Performance): Efficient TAR operations
Priority 5 (Extensibility): Registered via registry
"""

import tarfile
from pathlib import Path
from typing import Optional

from ...contracts import IArchiveFormat


class TarArchiver(IArchiveFormat):
    """TAR archive format handler (supports tar, tar.gz, tar.bz2, tar.xz)."""
    
    @property
    def format_id(self) -> str:
        """Format identifier."""
        return "tar"
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported extensions."""
        return [".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz"]
    
    @property
    def mime_types(self) -> list[str]:
        """MIME types."""
        return [
            "application/x-tar",
            "application/x-gtar",
            "application/x-compressed-tar",
        ]
    
    def _determine_mode(self, path: Path, write: bool = True) -> str:
        """Determine TAR mode from file extension."""
        suffix = "".join(path.suffixes).lower()
        
        if write:
            if '.gz' in suffix or '.tgz' in suffix:
                return 'w:gz'
            elif '.bz2' in suffix or '.tbz' in suffix:
                return 'w:bz2'
            elif '.xz' in suffix or '.txz' in suffix:
                return 'w:xz'
            else:
                return 'w'
        else:
            return 'r:*'  # Auto-detect compression on read
    
    def create(self, files: list[Path], output: Path, **opts) -> None:
        """Create TAR archive."""
        output.parent.mkdir(parents=True, exist_ok=True)
        
        mode = self._determine_mode(output, write=True)
        
        with tarfile.open(output, mode) as tf:
            for file_path in files:
                arcname = opts.get('arcname', file_path.name)
                tf.add(file_path, arcname=arcname)
    
    def extract(self, archive: Path, output_dir: Path, members: Optional[list[str]] = None, **opts) -> list[Path]:
        """Extract TAR archive."""
        output_dir.mkdir(parents=True, exist_ok=True)
        extracted: list[Path] = []
        
        with tarfile.open(archive, 'r:*') as tf:
            if members:
                for member in members:
                    tf.extract(member, output_dir)
                    extracted.append(output_dir / member)
            else:
                tf.extractall(output_dir)
                extracted = [output_dir / member.name for member in tf.getmembers()]
        
        return extracted
    
    def list_contents(self, archive: Path) -> list[str]:
        """List TAR contents."""
        with tarfile.open(archive, 'r:*') as tf:
            return [member.name for member in tf.getmembers()]
    
    def add_file(self, archive: Path, file: Path, arcname: Optional[str] = None) -> None:
        """Add file to TAR archive."""
        arcname = arcname or file.name
        
        # Only support append to uncompressed TAR
        if archive.suffix == '.tar':
            with tarfile.open(archive, 'a') as tf:
                tf.add(file, arcname=arcname)
        else:
            raise NotImplementedError("Adding to compressed TAR archives not supported")

