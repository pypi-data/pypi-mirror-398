#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/formats/squashfs_format.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 1, 2025

SquashFS filesystem format - RANK #10 EMBEDDED SYSTEMS.

**Embedded & system image use**

Priority 1 (Security): Read-only filesystem security
Priority 2 (Usability): Embedded systems
Priority 3 (Maintainability): Clean squashfs handling
Priority 4 (Performance): LZMA/LZ4 compression
Priority 5 (Extensibility): Binary tool integration
"""

from pathlib import Path
from typing import Optional
import subprocess
import shutil

from ...contracts import IArchiveFormat
from ...errors import ArchiveError


class SquashfsArchiver(IArchiveFormat):
    """
    SquashFS filesystem format handler - RANK #10.
    
    FormatAction naming: SquashfsArchiver
    
    Read-only compressed filesystem with:
    - LZMA/LZ4/LZO compression
    - Block deduplication
    - Extended attributes
    - Used in embedded systems, live CDs
    
    NOTE: Requires mksquashfs/unsquashfs binaries.
    
    Examples:
        >>> archiver = SquashfsArchiver()
        >>> # Create filesystem image
        >>> archiver.create([Path("rootfs/")], Path("system.squashfs"))
        >>> 
        >>> # Extract filesystem
        >>> archiver.extract(Path("system.squashfs"), Path("output/"))
    """
    
    @property
    def format_id(self) -> str:
        """Format identifier."""
        return "squashfs"
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported extensions."""
        return [".squashfs", ".sfs", ".sqfs"]
    
    @property
    def mime_types(self) -> list[str]:
        """MIME types."""
        return ["application/x-squashfs"]
    
    def _check_tools(self):
        """Check if squashfs tools are available."""
        mksquashfs = shutil.which("mksquashfs")
        unsquashfs = shutil.which("unsquashfs")
        
        if not mksquashfs or not unsquashfs:
            raise ArchiveError(
                "SquashFS tools not found. Install squashfs-tools package:\n"
                "  Ubuntu/Debian: sudo apt install squashfs-tools\n"
                "  Fedora: sudo dnf install squashfs-tools\n"
                "  macOS: brew install squashfs"
            )
        
        return Path(mksquashfs), Path(unsquashfs)
    
    def create(self, files: list[Path], output: Path, **opts) -> None:
        """
        Create SquashFS filesystem.
        
        Options:
            comp: Compression algorithm (gzip, lzma, lzo, lz4, xz, zstd)
            block_size: Block size (default: 128K)
        """
        output.parent.mkdir(parents=True, exist_ok=True)
        mksquashfs, _ = self._check_tools()
        
        comp = opts.get('comp', 'lzma')  # Default: LZMA
        block_size = opts.get('block_size', '128K')
        
        try:
            # Build mksquashfs command
            cmd = [str(mksquashfs)]
            
            for file_path in files:
                if file_path.exists():
                    cmd.append(str(file_path))
            
            cmd.extend([str(output), "-comp", comp, "-b", block_size])
            
            # Execute mksquashfs
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise ArchiveError(f"SquashFS creation failed: {e.stderr}")
        except Exception as e:
            raise ArchiveError(f"Failed to create squashfs: {e}")
    
    def extract(self, archive: Path, output_dir: Path, members: Optional[list[str]] = None, **opts) -> list[Path]:
        """Extract SquashFS filesystem."""
        output_dir.mkdir(parents=True, exist_ok=True)
        _, unsquashfs = self._check_tools()
        
        try:
            cmd = [str(unsquashfs), "-d", str(output_dir), str(archive)]
            
            if members:
                # Extract specific files
                cmd.extend(members)
            
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Return extracted files
            return list(output_dir.rglob('*'))
        except subprocess.CalledProcessError as e:
            raise ArchiveError(f"SquashFS extraction failed: {e.stderr}")
        except Exception as e:
            raise ArchiveError(f"Failed to extract squashfs: {e}")
    
    def list_contents(self, archive: Path) -> list[str]:
        """List SquashFS contents."""
        _, unsquashfs = self._check_tools()
        
        try:
            cmd = [str(unsquashfs), "-ll", str(archive)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse unsquashfs output
            lines = result.stdout.strip().split('\n')
            # Skip header lines and parse file list
            return [line.split()[-1] for line in lines if line and not line.startswith('squashfs-root')]
        except subprocess.CalledProcessError as e:
            raise ArchiveError(f"SquashFS list failed: {e.stderr}")
        except Exception as e:
            raise ArchiveError(f"Failed to list squashfs contents: {e}")
    
    def add_file(self, archive: Path, file: Path, arcname: Optional[str] = None) -> None:
        """SquashFS doesn't support append (read-only FS)."""
        raise ArchiveError("SquashFS is read-only. Recreate the filesystem to add files.")

