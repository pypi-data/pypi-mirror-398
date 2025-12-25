#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/formats/wim_format.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: November 1, 2025

WIM (Windows Imaging) format - RANK #9 SYSTEM IMAGES.

**Used by Microsoft for system images**

Priority 1 (Security): System image integrity
Priority 2 (Usability): Windows deployment
Priority 3 (Maintainability): Clean WIM handling
Priority 4 (Performance): LZX compression
Priority 5 (Extensibility): Lazy installation of wimlib
"""

from pathlib import Path
from typing import Optional

from ...contracts import IArchiveFormat
from ...errors import ArchiveError

# Lazy import for wimlib - optional dependency
try:
    import wimlib
except ImportError:
    wimlib = None  # type: ignore


class WimArchiver(IArchiveFormat):
    """
    WIM archive format handler - RANK #9.
    
    FormatAction naming: WimArchiver
    
    Windows Imaging format with:
    - LZX compression
    - Hardware-independent imaging
    - Single-instance storage
    - Bootable images
    
    Examples:
        >>> archiver = WimArchiver()
        >>> # Create system image
        >>> archiver.create([Path("C:\\")], Path("system.wim"))
        >>> 
        >>> # Extract image
        >>> archiver.extract(Path("system.wim"), Path("restore/"))
    """
    
    @property
    def format_id(self) -> str:
        """Format identifier."""
        return "wim"
    
    @property
    def file_extensions(self) -> list[str]:
        """Supported extensions."""
        return [".wim", ".swm", ".esd"]
    
    @property
    def mime_types(self) -> list[str]:
        """MIME types."""
        return ["application/x-ms-wim"]
    
    def create(self, files: list[Path], output: Path, **opts) -> None:
        """
        Create WIM image.
        
        Options:
            compression: Compression type (none, xpress, lzx, lzms)
            boot: Make image bootable
        """
        if wimlib is None:
            raise ArchiveError("wimlib not available. Install wimlib-imagex package.")
        
        output.parent.mkdir(parents=True, exist_ok=True)
        
        compression = opts.get('compression', 'lzx')
        
        try:
            # Create WIM
            wim = wimlib.WIM(str(output), 'w')
            
            # Add each file/directory
            for file_path in files:
                if file_path.exists():
                    wim.add_image(str(file_path), file_path.name, compression=compression)
            
            wim.write()
        except Exception as e:
            raise ArchiveError(f"Failed to create WIM image: {e}")
    
    def extract(self, archive: Path, output_dir: Path, members: Optional[list[str]] = None, **opts) -> list[Path]:
        """Extract WIM image."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            wim = wimlib.WIM(str(archive), 'r')
            
            # Extract all images or specific ones
            image_index = opts.get('image', 1)  # Default: first image
            wim.extract_image(image_index, str(output_dir))
            
            return list(output_dir.rglob('*'))
        except Exception as e:
            raise ArchiveError(f"Failed to extract WIM image: {e}")
    
    def list_contents(self, archive: Path) -> list[str]:
        """List WIM contents."""
        try:
            wim = wimlib.WIM(str(archive), 'r')
            images = []
            
            for i in range(1, wim.get_num_images() + 1):
                info = wim.get_image_info(i)
                images.append(f"Image {i}: {info.get('NAME', 'Unnamed')}")
            
            return images
        except Exception as e:
            raise ArchiveError(f"Failed to list WIM contents: {e}")
    
    def add_file(self, archive: Path, file: Path, arcname: Optional[str] = None) -> None:
        """Add image to WIM."""
        try:
            wim = wimlib.WIM(str(archive), 'rw')
            wim.add_image(str(file), arcname or file.name)
            wim.write()
        except Exception as e:
            raise ArchiveError(f"Failed to add image to WIM: {e}")

