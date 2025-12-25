#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/formats/zpaq_format.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 1, 2025

ZPAQ journaled compression format - RANK #8 EXTREME COMPRESSION.

**Extreme compression ratio, slow, archival only**

Priority 1 (Security): Journaled integrity
Priority 2 (Usability): Extreme compression
Priority 3 (Maintainability): Clean zpaq handling
Priority 4 (Performance): Slow (archival only)
Priority 5 (Extensibility): Lazy installation of zpaq
"""

from pathlib import Path
from typing import Optional
import subprocess
import shutil

from ...contracts import IArchiveFormat
from ...errors import ArchiveError


class ZpaqArchiver(IArchiveFormat):
    """
    ZPAQ archive format handler - RANK #8.
    
    FormatAction naming: ZpaqArchiver
    
    Extreme archival compression with:
    - Best compression ratio (PAQ algorithm)
    - Journaled incremental backups
    - Deduplication
    - Very slow (archival only)
    
    NOTE: Requires zpaq binary installed on system.
    
    Examples:
        >>> archiver = ZpaqArchiver()
        >>> # Create archive (very slow!)
        >>> archiver.create([Path("data/")], Path("archive.zpaq"))
        >>> 
        >>> # Extract
        >>> archiver.extract(Path("archive.zpaq"), Path("output/"))
    """
    
    @property
    def format_id(self) -> str:
        """Format identifier."""
        return "zpaq"
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported extensions."""
        return [".zpaq"]
    
    @property
    def mime_types(self) -> list[str]:
        """MIME types."""
        return ["application/x-zpaq"]
    
    def _check_zpaq(self) -> Path:
        """Check if zpaq binary is available."""
        zpaq_path = shutil.which("zpaq")
        if not zpaq_path:
            raise ArchiveError(
                "ZPAQ binary not found. Install from: http://mattmahoney.net/dc/zpaq.html"
            )
        return Path(zpaq_path)
    
    def create(self, files: list[Path], output: Path, **opts) -> None:
        """
        Create ZPAQ archive.
        
        Options:
            method: Compression method (0-5, default: 3)
            incremental: Enable incremental backup
        """
        output.parent.mkdir(parents=True, exist_ok=True)
        zpaq = self._check_zpaq()
        
        method = opts.get('method', 3)
        
        try:
            # Build zpaq command
            cmd = [str(zpaq), "add", str(output), "-method", str(method)]
            
            for file_path in files:
                if file_path.exists():
                    cmd.append(str(file_path))
            
            # Execute zpaq
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise ArchiveError(f"ZPAQ creation failed: {e.stderr}")
        except Exception as e:
            raise ArchiveError(f"Failed to create zpaq archive: {e}")
    
    def extract(self, archive: Path, output_dir: Path, members: Optional[list[str]] = None, **opts) -> list[Path]:
        """Extract ZPAQ archive."""
        output_dir.mkdir(parents=True, exist_ok=True)
        zpaq = self._check_zpaq()
        
        try:
            cmd = [str(zpaq), "extract", str(archive), "-to", str(output_dir)]
            
            if members:
                # ZPAQ supports wildcard extraction
                cmd.extend(members)
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Return extracted files
            return list(output_dir.rglob('*'))
        except subprocess.CalledProcessError as e:
            raise ArchiveError(f"ZPAQ extraction failed: {e.stderr}")
        except Exception as e:
            raise ArchiveError(f"Failed to extract zpaq archive: {e}")
    
    def list_contents(self, archive: Path) -> list[str]:
        """List ZPAQ contents."""
        zpaq = self._check_zpaq()
        
        try:
            cmd = [str(zpaq), "list", str(archive)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse zpaq list output
            lines = result.stdout.strip().split('\n')
            return [line.split()[-1] for line in lines if line.strip()]
        except subprocess.CalledProcessError as e:
            raise ArchiveError(f"ZPAQ list failed: {e.stderr}")
        except Exception as e:
            raise ArchiveError(f"Failed to list zpaq contents: {e}")
    
    def add_file(self, archive: Path, file: Path, arcname: Optional[str] = None) -> None:
        """Add file to ZPAQ archive (incremental)."""
        zpaq = self._check_zpaq()
        
        try:
            cmd = [str(zpaq), "add", str(archive), str(file)]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise ArchiveError(f"ZPAQ add failed: {e.stderr}")
        except Exception as e:
            raise ArchiveError(f"Failed to add file to zpaq: {e}")

