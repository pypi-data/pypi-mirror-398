#!/usr/bin/env python3
#exonware/xwsystem/src/exonware/xwsystem/io/archive/archive_files.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 30-Oct-2025

Archive FILES - File persistence for archives.

IArchiveFile extends IFile and USES IArchiver for compression.

Composition Pattern:
- ZipFile extends XWFile
- ZipFile USES ZipArchiver internally
- Separates file I/O from data transformation

Priority 1 (Security): Safe file operations
Priority 2 (Usability): Simple add_files/extract_to API
Priority 3 (Maintainability): Clear separation of concerns
Priority 4 (Performance): Efficient delegation
Priority 5 (Extensibility): Easy to add new formats
"""

import zipfile
import tarfile
from pathlib import Path
from typing import Any, Optional, Union

from ..archive.base import AArchiveFile
from ..contracts import IArchiveFile, IArchiver
from ..errors import ArchiveError
from .archivers import ZipArchiver, TarArchiver


class ZipFile(AArchiveFile):
    """
    Zip archive FILE - follows I→A→XW pattern.
    
    I: IArchiveFile (interface)
    A: AArchiveFile (abstract base)
    XW: ZipFile (concrete implementation)
    
    USES XWZipArchiver internally (composition).
    
    This handles:
    - File I/O with .zip files on disk
    - Adding files to archive
    - Extracting archive to destination
    
    Examples:
        >>> # Create zip file
        >>> zip_file = ZipFile("backup.zip")
        >>> 
        >>> # Add files to archive
        >>> zip_file.add_files([Path("file1.txt"), Path("file2.txt")])
        >>> 
        >>> # Extract archive
        >>> extracted = zip_file.extract_to(Path("output/"))
        >>> 
        >>> # List contents
        >>> files = zip_file.list_contents()
    """
    
    def __init__(self, path: Union[str, Path]):
        """Initialize zip archive file."""
        super().__init__(path, archiver=ZipArchiver())
        self._archiver = ZipArchiver()  # Composition!
    
    def add_files(self, files: list[Path], **options) -> None:
        """
        Add files to zip archive.
        
        Uses archiver internally:
        1. Read files from disk
        2. Use ZipArchiver.compress() to create archive bytes
        3. Save to disk using XWFile.save()
        """
        try:
            # Read files
            file_data = {}
            for file_path in files:
                if file_path.is_file():
                    file_data[file_path.name] = file_path.read_bytes()
            
            # Compress using archiver (in RAM)
            zip_bytes = self.get_archiver().compress(file_data, **options)
            
            # Save to disk using direct write
            self.file_path.write_bytes(zip_bytes)
            
        except Exception as e:
            raise ArchiveError(f"Failed to add files to zip: {e}")
    
    def extract_to(self, dest: Path, **options) -> list[Path]:
        """
        Extract zip archive to destination.
        
        Uses archiver internally:
        1. Load from disk using XWFile.load()
        2. Use ZipArchiver.extract() to get data
        3. Write files to destination
        """
        try:
            # Load from disk using direct read
            zip_bytes = self.file_path.read_bytes()
            
            # Extract using archiver (in RAM)
            file_data = self.get_archiver().extract(zip_bytes, **options)
            
            # Write to destination folder
            dest.mkdir(parents=True, exist_ok=True)
            extracted_files = []
            
            for filename, content in file_data.items():
                file_path = dest / filename
                file_path.write_bytes(content)
                extracted_files.append(file_path)
            
            return extracted_files
            
        except Exception as e:
            raise ArchiveError(f"Failed to extract zip: {e}")
    
    def list_contents(self) -> list[str]:
        """List files in zip archive."""
        try:
            with zipfile.ZipFile(self.file_path, 'r') as zf:
                return zf.namelist()
        except Exception as e:
            raise ArchiveError(f"Failed to list zip contents: {e}")
    
    def get_archiver(self) -> IArchiver:
        """Get the underlying archiver codec."""
        return self._archiver


class TarFile(AArchiveFile):
    """
    Tar archive FILE - follows I→A→XW pattern.
    
    I: IArchiveFile (interface)
    A: AArchiveFile (abstract base)
    XW: TarFile (concrete implementation)
    
    USES XWTarArchiver internally (composition).
    
    Similar to ZipFile but for tar format.
    Supports compression: gzip, bz2, xz
    """
    
    def __init__(self, path: Union[str, Path], compression: str = ''):
        """
        Initialize tar archive file.
        
        Args:
            path: Archive file path
            compression: Compression type ('', 'gz', 'bz2', 'xz')
        """
        super().__init__(path, archiver=TarArchiver())
        self._archiver = TarArchiver()  # Composition!
        self._compression = compression
    
    def add_files(self, files: list[Path], **options) -> None:
        """Add files to tar archive (uses archiver internally)."""
        try:
            # Read files
            file_data = {}
            for file_path in files:
                if file_path.is_file():
                    file_data[file_path.name] = file_path.read_bytes()
            
            # Compress using archiver (in RAM)
            options['compression'] = self._compression
            tar_bytes = self.get_archiver().compress(file_data, **options)
            
            # Save to disk using direct write
            self.file_path.write_bytes(tar_bytes)
            
        except Exception as e:
            raise ArchiveError(f"Failed to add files to tar: {e}")
    
    def extract_to(self, dest: Path, **options) -> list[Path]:
        """Extract tar archive to destination (uses archiver internally)."""
        try:
            # Load from disk using direct read
            tar_bytes = self.file_path.read_bytes()
            
            # Extract using archiver (in RAM)
            file_data = self.get_archiver().extract(tar_bytes, **options)
            
            # Write to destination folder
            dest.mkdir(parents=True, exist_ok=True)
            extracted_files = []
            
            for filename, content in file_data.items():
                file_path = dest / filename
                file_path.write_bytes(content)
                extracted_files.append(file_path)
            
            return extracted_files
            
        except Exception as e:
            raise ArchiveError(f"Failed to extract tar: {e}")
    
    def list_contents(self) -> list[str]:
        """List files in tar archive."""
        try:
            with tarfile.open(self.file_path, 'r:*') as tf:
                return [m.name for m in tf.getmembers() if m.isfile()]
        except Exception as e:
            raise ArchiveError(f"Failed to list tar contents: {e}")
    
    def get_archiver(self) -> IArchiver:
        """Get the underlying archiver codec."""
        return self._archiver



