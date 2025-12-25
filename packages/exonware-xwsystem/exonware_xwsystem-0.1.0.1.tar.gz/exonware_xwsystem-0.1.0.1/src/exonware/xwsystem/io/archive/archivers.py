#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/archivers.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Archive codecs - In-memory archive processors.

Following FormatAction naming: ZipArchiver, TarArchiver, 7zArchiver

IArchiver extends ICodec:
- Works on ANY data in RAM (not just files!)
- compress() / extract() delegates to encode() / decode()

Priority 1 (Security): Safe archive operations with validation
Priority 2 (Usability): Simple compress/extract API
Priority 3 (Maintainability): Clean codec pattern
Priority 4 (Performance): Efficient in-memory operations
Priority 5 (Extensibility): Easy to add new formats (7z, RAR, etc.)
"""

import zipfile
import tarfile
import io
from pathlib import Path
from typing import Any, Optional, Union

from ..archive.base import AArchiver
from ..contracts import IArchiver, EncodeOptions, DecodeOptions
from ..defs import ArchiveFormat, CodecCapability, CodecCategory
from ..errors import ArchiveError, EncodeError, DecodeError


class ZipArchiver(AArchiver):
    """
    Zip archive codec - operates in MEMORY.
    
    Follows I→A→XW pattern:
    - I: IArchiver (interface)
    - A: AArchiver (abstract base)
    - XW: XWZipArchiver (concrete implementation)
    
    Can compress:
    - bytes (raw data)
    - str (text)
    - dict/list (structured data)
    - Any Python objects
    
    NOT limited to files - works on data in RAM!
    
    Examples:
        >>> archiver = ZipArchiver()
        >>> 
        >>> # Compress dict in RAM
        >>> data = {"file1.txt": b"content1", "file2.txt": b"content2"}
        >>> zip_bytes = archiver.compress(data)
        >>> 
        >>> # Extract from RAM
        >>> extracted = archiver.extract(zip_bytes)
        >>> 
        >>> # Or use codec methods
        >>> zip_bytes = archiver.encode(data)
        >>> data = archiver.decode(zip_bytes)
    """
    
    # Codec metadata
    @property
    def codec_id(self) -> str:
        return "zip"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/zip", "application/x-zip-compressed"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".zip"]
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def category(self) -> CodecCategory:
        """Codec category: ARCHIVE."""
        return CodecCategory.ARCHIVE
    
    @property
    def aliases(self) -> list[str]:
        """Codec aliases."""
        return ["zip", "ZIP"]
    
    def supports_capability(self, capability: CodecCapability) -> bool:
        """Check capability support."""
        return capability in (CodecCapability.BIDIRECTIONAL, CodecCapability.COMPRESSION)
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> bytes:
        """
        Encode data to zip bytes (in RAM).
        
        Args:
            value: Data to archive (dict, bytes, list, etc.)
            options: Compression options
        
        Returns:
            Zip archive bytes
        """
        options = options or {}
        compression = options.get('compression', zipfile.ZIP_DEFLATED)
        
        try:
            # Create zip in memory
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', compression=compression) as zf:
                if isinstance(value, dict):
                    # dict: keys are filenames, values are contents
                    for filename, content in value.items():
                        if isinstance(content, str):
                            zf.writestr(filename, content)
                        else:
                            zf.writestr(filename, content)
                
                elif isinstance(value, bytes):
                    # Raw bytes: create single file
                    zf.writestr('data', value)
                
                elif isinstance(value, str):
                    # String: create single text file
                    zf.writestr('data.txt', value)
                
                else:
                    # Other: serialize as string
                    zf.writestr('data', str(value))
            
            return zip_buffer.getvalue()
            
        except Exception as e:
            raise EncodeError(f"Failed to create zip archive: {e}")
    
    def decode(self, repr: bytes, *, options: Optional[DecodeOptions] = None) -> Any:
        """
        Decode zip bytes to data (in RAM).
        
        Args:
            repr: Zip archive bytes
            options: Extraction options
        
        Returns:
            Extracted data (dict of filename → content)
        """
        try:
            # Extract zip from memory
            zip_buffer = io.BytesIO(repr)
            result = {}
            
            with zipfile.ZipFile(zip_buffer, 'r') as zf:
                for name in zf.namelist():
                    result[name] = zf.read(name)
            
            return result
            
        except Exception as e:
            raise DecodeError(f"Failed to extract zip archive: {e}")
    
    def compress(self, data: Any, **options) -> bytes:
        """
        User-friendly: Compress data to zip bytes.
        
        Delegates to encode().
        """
        return self.encode(data, options=options)
    
    def extract(self, archive_bytes: bytes, **options) -> Any:
        """
        User-friendly: Extract zip bytes to data.
        
        Delegates to decode().
        """
        return self.decode(archive_bytes, options=options)


class TarArchiver(AArchiver):
    """
    Tar archive codec - operates in MEMORY.
    
    Follows I→A→XW pattern:
    - I: IArchiver (interface)
    - A: AArchiver (abstract base)
    - XW: XWTarArchiver (concrete implementation)
    
    Similar to XWZipArchiver but uses tar format.
    Supports compression: gzip, bz2, xz
    """
    
    # Codec metadata
    @property
    def codec_id(self) -> str:
        return "tar"
    
    @property
    def media_types(self) -> list[str]:
        return ["application/x-tar", "application/x-gtar"]
    
    @property
    def file_extensions(self) -> list[str]:
        return [".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz"]
    
    @property
    def capabilities(self) -> CodecCapability:
        return CodecCapability.BIDIRECTIONAL
    
    @property
    def category(self) -> CodecCategory:
        """Codec category: ARCHIVE."""
        return CodecCategory.ARCHIVE
    
    @property
    def aliases(self) -> list[str]:
        """Codec aliases."""
        return ["tar", "TAR"]
    
    def supports_capability(self, capability: CodecCapability) -> bool:
        """Check capability support."""
        return capability in (CodecCapability.BIDIRECTIONAL, CodecCapability.COMPRESSION)
    
    def encode(self, value: Any, *, options: Optional[EncodeOptions] = None) -> bytes:
        """Encode data to tar bytes (in RAM)."""
        options = options or {}
        compression = options.get('compression', '')  # '', 'gz', 'bz2', 'xz'
        
        mode = f'w:{compression}' if compression else 'w'
        
        try:
            tar_buffer = io.BytesIO()
            
            with tarfile.open(fileobj=tar_buffer, mode=mode) as tf:
                if isinstance(value, dict):
                    for filename, content in value.items():
                        info = tarfile.TarInfo(name=filename)
                        if isinstance(content, str):
                            content = content.encode('utf-8')
                        info.size = len(content)
                        tf.addfile(info, io.BytesIO(content))
                
                elif isinstance(value, bytes):
                    info = tarfile.TarInfo(name='data')
                    info.size = len(value)
                    tf.addfile(info, io.BytesIO(value))
                
                else:
                    content = str(value).encode('utf-8')
                    info = tarfile.TarInfo(name='data')
                    info.size = len(content)
                    tf.addfile(info, io.BytesIO(content))
            
            return tar_buffer.getvalue()
            
        except Exception as e:
            raise EncodeError(f"Failed to create tar archive: {e}")
    
    def decode(self, repr: bytes, *, options: Optional[DecodeOptions] = None) -> Any:
        """Decode tar bytes to data (in RAM)."""
        try:
            tar_buffer = io.BytesIO(repr)
            result = {}
            
            with tarfile.open(fileobj=tar_buffer, mode='r:*') as tf:
                for member in tf.getmembers():
                    if member.isfile():
                        f = tf.extractfile(member)
                        if f:
                            result[member.name] = f.read()
            
            return result
            
        except Exception as e:
            raise DecodeError(f"Failed to extract tar archive: {e}")


    
    def compress(self, data: Any, **options) -> bytes:
        """User-friendly: Compress data to tar bytes."""
        return self.encode(data, options=options)
    
    def extract(self, archive_bytes: bytes, **options) -> Any:
        """User-friendly: Extract tar bytes to data."""
        return self.decode(archive_bytes, options=options)

