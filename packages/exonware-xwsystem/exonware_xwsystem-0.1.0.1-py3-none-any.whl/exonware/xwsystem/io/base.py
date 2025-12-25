"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

IO module base classes - abstract classes for input/output functionality.
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Any, Optional, Union, BinaryIO, TextIO
from pathlib import Path
from .contracts import FileMode, FileType, PathType, OperationResult, LockType, IFile, IFolder, IPath, IStream, IAsyncIO, IAtomicOperations, IBackupOperations, ITemporaryOperations, IUnifiedIO, IFileManager


# ============================================================================
# FILE ABSTRACT BASE CLASS
# ============================================================================

class AFile(IFile, ABC):
    """Abstract base class for file operations with both static and instance methods."""
    
    def __init__(self, file_path: Union[str, Path]):
        """Initialize file base."""
        self.file_path = Path(file_path)
        self._handle: Optional[Union[TextIO, BinaryIO]] = None
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    def open(self, mode: FileMode = FileMode.READ) -> None:
        """Open file with specified mode."""
        pass
    
    @abstractmethod
    def read(self, size: Optional[int] = None) -> Union[str, bytes]:
        """Read from file."""
        pass
    
    @abstractmethod
    def write(self, data: Union[str, bytes]) -> int:
        """Write to file."""
        pass
    
    def close(self) -> None:
        """Close file."""
        if self._handle and not self._handle.closed:
            self._handle.close()
    
    @abstractmethod
    def save(self, data: Any, **kwargs) -> bool:
        """Save data to file."""
        pass
    
    @abstractmethod
    def load(self, **kwargs) -> Any:
        """Load data from file."""
        pass
    
    @abstractmethod
    def save_as(self, path: Union[str, Path], data: Any, **kwargs) -> bool:
        """Save data to specific path."""
        pass
    
    @abstractmethod
    def to_file(self, path: Union[str, Path], **kwargs) -> bool:
        """Write current object to file."""
        pass
    
    @abstractmethod
    def from_file(self, path: Union[str, Path], **kwargs) -> 'AFile':
        """Load object from file."""
        pass
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    def exists(path: Union[str, Path]) -> bool:
        """Check if file exists."""
        return Path(path).exists() and Path(path).is_file()
    
    @staticmethod
    def size(path: Union[str, Path]) -> int:
        """Get file size."""
        if AFile.exists(path):
            return Path(path).stat().st_size
        return 0
    
    @staticmethod
    def delete(path: Union[str, Path]) -> bool:
        """Delete file."""
        try:
            if AFile.exists(path):
                Path(path).unlink()
                return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def copy(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Copy file."""
        try:
            import shutil
            shutil.copy2(source, destination)
            return True
        except Exception:
            return False
    
    @staticmethod
    def move(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Move file."""
        try:
            import shutil
            shutil.move(str(source), str(destination))
            return True
        except Exception:
            return False
    
    @staticmethod
    def rename(old_path: Union[str, Path], new_path: Union[str, Path]) -> bool:
        """Rename file."""
        return AFile.move(old_path, new_path)
    
    @staticmethod
    def get_modified_time(path: Union[str, Path]) -> float:
        """Get file modification time."""
        if AFile.exists(path):
            return Path(path).stat().st_mtime
        return 0.0
    
    @staticmethod
    def get_created_time(path: Union[str, Path]) -> float:
        """Get file creation time."""
        if AFile.exists(path):
            return Path(path).stat().st_ctime
        return 0.0
    
    @staticmethod
    def get_permissions(path: Union[str, Path]) -> int:
        """Get file permissions."""
        if AFile.exists(path):
            return Path(path).stat().st_mode
        return 0
    
    @staticmethod
    def is_readable(path: Union[str, Path]) -> bool:
        """Check if file is readable."""
        return AFile.exists(path) and os.access(path, os.R_OK)
    
    @staticmethod
    def is_writable(path: Union[str, Path]) -> bool:
        """Check if file is writable."""
        return AFile.exists(path) and os.access(path, os.W_OK)
    
    @staticmethod
    def is_executable(path: Union[str, Path]) -> bool:
        """Check if file is executable."""
        return AFile.exists(path) and os.access(path, os.X_OK)
    
    @staticmethod
    def read_text(path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Read file as text."""
        with open(path, 'r', encoding=encoding) as f:
            return f.read()
    
    @staticmethod
    def read_bytes(path: Union[str, Path]) -> bytes:
        """Read file as bytes."""
        with open(path, 'rb') as f:
            return f.read()
    
    @staticmethod
    def write_text(path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """Write text to file."""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    @staticmethod
    def write_bytes(path: Union[str, Path], content: bytes) -> bool:
        """Write bytes to file."""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'wb') as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    @staticmethod
    def safe_read_text(path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
        """Safely read text file, returning None on error."""
        try:
            return AFile.read_text(path, encoding)
        except Exception:
            return None
    
    @staticmethod
    def safe_read_bytes(path: Union[str, Path]) -> Optional[bytes]:
        """Safely read binary file, returning None on error."""
        try:
            return AFile.read_bytes(path)
        except Exception:
            return None
    
    @staticmethod
    def safe_write_text(path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """Safely write text to file."""
        return AFile.write_text(path, content, encoding)
    
    @staticmethod
    def safe_write_bytes(path: Union[str, Path], content: bytes) -> bool:
        """Safely write bytes to file."""
        return AFile.write_bytes(path, content)
    
    # ============================================================================
    # STATIC UTILITY METHODS (File Manager Features)
    # ============================================================================
    
    @staticmethod
    def atomic_write(file_path: Union[str, Path], data: Union[str, bytes], 
                    backup: bool = True) -> OperationResult:
        """Atomically write data to file (static version)."""
        from .common.atomic import AtomicFileWriter
        try:
            with AtomicFileWriter(Path(file_path), backup=backup) as writer:
                if isinstance(data, str):
                    writer.write(data.encode('utf-8'))
                else:
                    writer.write(data)
            return OperationResult.SUCCESS
        except Exception:
            return OperationResult.FAILED
    
    @staticmethod
    def atomic_copy(source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically copy file (static version)."""
        from .common.atomic import AtomicFileWriter
        import shutil
        try:
            with open(source, 'rb') as src:
                with AtomicFileWriter(Path(destination)) as writer:
                    shutil.copyfileobj(src, writer)
            return OperationResult.SUCCESS
        except Exception:
            return OperationResult.FAILED
    
    @staticmethod
    def atomic_move(source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically move file (static version)."""
        result = AFile.atomic_copy(source, destination)
        if result == OperationResult.SUCCESS:
            try:
                Path(source).unlink()
                return OperationResult.SUCCESS
            except Exception:
                return OperationResult.FAILED
        return OperationResult.FAILED
    
    @staticmethod
    def atomic_delete(file_path: Union[str, Path], backup: bool = True) -> OperationResult:
        """Atomically delete file (static version)."""
        target = Path(file_path)
        try:
            if backup and target.exists():
                backup_path = target.with_suffix(target.suffix + f'.backup.{int(time.time())}')
                import shutil
                shutil.copy2(target, backup_path)
            
            if target.exists():
                target.unlink()
            return OperationResult.SUCCESS
        except Exception:
            return OperationResult.FAILED
    
    @staticmethod
    def create_backup(source: Union[str, Path], backup_dir: Union[str, Path]) -> Optional[Path]:
        """Create backup of file (static version)."""
        import shutil
        source_path = Path(source)
        backup_path = Path(backup_dir)
        
        try:
            backup_path.mkdir(parents=True, exist_ok=True)
            if source_path.is_file():
                backup_file = backup_path / f"{source_path.name}.backup.{int(time.time())}"
                shutil.copy2(source_path, backup_file)
                return backup_file
            return None
        except Exception:
            return None
    
    @staticmethod
    def restore_backup(backup_path: Union[str, Path], target: Union[str, Path]) -> OperationResult:
        """Restore from backup (static version)."""
        import shutil
        try:
            Path(target).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, target)
            return OperationResult.SUCCESS
        except Exception:
            return OperationResult.FAILED
    
    @staticmethod
    def create_temp_file(suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary file (static version)."""
        import tempfile
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)
        return Path(temp_path)
    
    @staticmethod
    def create_temp_directory(suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary directory (static version)."""
        import tempfile
        temp_path = tempfile.mkdtemp(suffix=suffix, prefix=prefix)
        return Path(temp_path)


# ============================================================================
# FOLDER ABSTRACT BASE CLASS
# ============================================================================

class AFolder(IFolder, ABC):
    """Abstract base class for folder operations with both static and instance methods."""
    
    def __init__(self, dir_path: Union[str, Path]):
        """Initialize folder base."""
        self.dir_path = Path(dir_path)
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    def create(self, parents: bool = True, exist_ok: bool = True) -> bool:
        """Create directory."""
        pass
    
    @abstractmethod
    def delete(self, recursive: bool = False) -> bool:
        """Delete directory."""
        pass
    
    def list_files(self, pattern: Optional[str] = None, recursive: bool = False) -> list[Path]:
        """List files in directory."""
        return AFolder.list_files_static(self.dir_path, pattern, recursive)
    
    def list_directories(self, recursive: bool = False) -> list[Path]:
        """List subdirectories."""
        return AFolder.list_directories_static(self.dir_path, recursive)
    
    def walk(self) -> list[tuple[Path, list[str], list[str]]]:
        """Walk directory tree."""
        return AFolder.walk_static(self.dir_path)
    
    def get_size(self) -> int:
        """Get directory size."""
        return AFolder.get_size_static(self.dir_path)
    
    def is_empty(self) -> bool:
        """Check if directory is empty."""
        return AFolder.is_empty_static(self.dir_path)
    
    def copy_to(self, destination: Union[str, Path]) -> bool:
        """Copy directory to destination."""
        return AFolder.copy_dir(self.dir_path, destination)
    
    def move_to(self, destination: Union[str, Path]) -> bool:
        """Move directory to destination."""
        return AFolder.move_dir(self.dir_path, destination)
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    def exists(path: Union[str, Path]) -> bool:
        """Check if directory exists."""
        return Path(path).exists() and Path(path).is_dir()
    
    @staticmethod
    def create_dir(path: Union[str, Path], parents: bool = True, exist_ok: bool = True) -> bool:
        """Create directory."""
        try:
            Path(path).mkdir(parents=parents, exist_ok=exist_ok)
            return True
        except Exception:
            return False
    
    @staticmethod
    def delete_dir(path: Union[str, Path], recursive: bool = False) -> bool:
        """Delete directory."""
        try:
            if recursive:
                import shutil
                shutil.rmtree(path)
            else:
                Path(path).rmdir()
            return True
        except Exception:
            return False
    
    @staticmethod
    def list_files_static(path: Union[str, Path], pattern: Optional[str] = None, recursive: bool = False) -> list[Path]:
        """List files in directory."""
        if not AFolder.exists(path):
            return []
        
        if recursive:
            if pattern:
                return list(Path(path).rglob(pattern))
            else:
                return [p for p in Path(path).rglob('*') if p.is_file()]
        else:
            if pattern:
                return list(Path(path).glob(pattern))
            else:
                return [p for p in Path(path).iterdir() if p.is_file()]
    
    @staticmethod
    def list_directories_static(path: Union[str, Path], recursive: bool = False) -> list[Path]:
        """List subdirectories."""
        if not AFolder.exists(path):
            return []
        
        if recursive:
            return [p for p in Path(path).rglob('*') if p.is_dir() and p != Path(path)]
        else:
            return [p for p in Path(path).iterdir() if p.is_dir()]
    
    @staticmethod
    def walk_static(path: Union[str, Path]) -> list[tuple[Path, list[str], list[str]]]:
        """Walk directory tree."""
        if not AFolder.exists(path):
            return []
        
        result = []
        for root, dirs, files in os.walk(path):
            result.append((Path(root), dirs, files))
        return result
    
    @staticmethod
    def get_size_static(path: Union[str, Path]) -> int:
        """Get directory size."""
        if not AFolder.exists(path):
            return 0
        
        total_size = 0
        for file_path in Path(path).rglob('*'):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except (OSError, IOError):
                    pass
        return total_size
    
    @staticmethod
    def is_empty_static(path: Union[str, Path]) -> bool:
        """Check if directory is empty."""
        if not AFolder.exists(path):
            return True
        
        try:
            return not any(Path(path).iterdir())
        except (OSError, IOError):
            return True
    
    @staticmethod
    def copy_dir(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Copy directory."""
        try:
            import shutil
            shutil.copytree(source, destination, dirs_exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def move_dir(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Move directory."""
        try:
            import shutil
            shutil.move(str(source), str(destination))
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_permissions(path: Union[str, Path]) -> int:
        """Get directory permissions."""
        if AFolder.exists(path):
            return Path(path).stat().st_mode
        return 0
    
    @staticmethod
    def is_readable(path: Union[str, Path]) -> bool:
        """Check if directory is readable."""
        return AFolder.exists(path) and os.access(path, os.R_OK)
    
    @staticmethod
    def is_writable(path: Union[str, Path]) -> bool:
        """Check if directory is writable."""
        return AFolder.exists(path) and os.access(path, os.W_OK)
    
    @staticmethod
    def is_executable(path: Union[str, Path]) -> bool:
        """Check if directory is executable."""
        return AFolder.exists(path) and os.access(path, os.X_OK)


# ============================================================================
# PATH ABSTRACT BASE CLASS
# ============================================================================

class APath(IPath, ABC):
    """Abstract base class for path operations with static methods."""
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    def normalize(path: Union[str, Path]) -> Path:
        """Normalize path."""
        return Path(path).resolve()
    
    @staticmethod
    def resolve(path: Union[str, Path]) -> Path:
        """Resolve path."""
        return Path(path).resolve()
    
    @staticmethod
    def absolute(path: Union[str, Path]) -> Path:
        """Get absolute path."""
        return Path(path).absolute()
    
    @staticmethod
    def relative(path: Union[str, Path], start: Optional[Union[str, Path]] = None) -> Path:
        """Get relative path."""
        if start is None:
            start = Path.cwd()
        return Path(path).relative_to(Path(start))
    
    @staticmethod
    def join(*paths: Union[str, Path]) -> Path:
        """Join paths."""
        return Path(*paths)
    
    @staticmethod
    def split(path: Union[str, Path]) -> tuple[Path, str]:
        """Split path into directory and filename."""
        p = Path(path)
        return p.parent, p.name
    
    @staticmethod
    def get_extension(path: Union[str, Path]) -> str:
        """Get file extension."""
        return Path(path).suffix
    
    @staticmethod
    def get_stem(path: Union[str, Path]) -> str:
        """Get file stem (name without extension)."""
        return Path(path).stem
    
    @staticmethod
    def get_name(path: Union[str, Path]) -> str:
        """Get file/directory name."""
        return Path(path).name
    
    @staticmethod
    def get_parent(path: Union[str, Path]) -> Path:
        """Get parent directory."""
        return Path(path).parent
    
    @staticmethod
    def is_absolute(path: Union[str, Path]) -> bool:
        """Check if path is absolute."""
        return Path(path).is_absolute()
    
    @staticmethod
    def is_relative(path: Union[str, Path]) -> bool:
        """Check if path is relative."""
        return not Path(path).is_absolute()
    
    @staticmethod
    def get_parts(path: Union[str, Path]) -> tuple:
        """Get path parts."""
        return Path(path).parts
    
    @staticmethod
    def match(path: Union[str, Path], pattern: str) -> bool:
        """Check if path matches pattern."""
        return Path(path).match(pattern)
    
    @staticmethod
    def with_suffix(path: Union[str, Path], suffix: str) -> Path:
        """Get path with new suffix."""
        return Path(path).with_suffix(suffix)
    
    @staticmethod
    def with_name(path: Union[str, Path], name: str) -> Path:
        """Get path with new name."""
        return Path(path).with_name(name)


# ============================================================================
# STREAM ABSTRACT BASE CLASS
# ============================================================================

class AStream(IStream, ABC):
    """Abstract base class for stream operations with both static and instance methods."""
    
    def __init__(self):
        """Initialize stream base."""
        self._closed = False
        self._position = 0
        self._stream: Optional[Union[TextIO, BinaryIO]] = None
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    def read(self, size: Optional[int] = None) -> Union[str, bytes]:
        """Read from stream."""
        pass
    
    @abstractmethod
    def write(self, data: Union[str, bytes]) -> int:
        """Write to stream."""
        pass
    
    @abstractmethod
    def seek(self, position: int, whence: int = 0) -> int:
        """Seek stream position."""
        pass
    
    @abstractmethod
    def tell(self) -> int:
        """Get current stream position."""
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Flush stream buffer."""
        pass
    
    def close(self) -> None:
        """Close stream."""
        if self._stream:
            self._stream.close()
            self._stream = None
            self._closed = True
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    def open_file(path: Union[str, Path], mode: str = 'r', encoding: Optional[str] = None) -> Union[TextIO, BinaryIO]:
        """Open file as stream."""
        return open(path, mode, encoding=encoding)
    
    @staticmethod
    def is_closed(stream: Union[TextIO, BinaryIO]) -> bool:
        """Check if stream is closed."""
        return stream.closed
    
    @staticmethod
    def readable(stream: Union[TextIO, BinaryIO]) -> bool:
        """Check if stream is readable."""
        return hasattr(stream, 'readable') and stream.readable()
    
    @staticmethod
    def writable(stream: Union[TextIO, BinaryIO]) -> bool:
        """Check if stream is writable."""
        return hasattr(stream, 'writable') and stream.writable()
    
    @staticmethod
    def seekable(stream: Union[TextIO, BinaryIO]) -> bool:
        """Check if stream is seekable."""
        return hasattr(stream, 'seekable') and stream.seekable()


# ============================================================================
# ASYNC I/O ABSTRACT BASE CLASS
# ============================================================================

class AAsyncIO(IAsyncIO, ABC):
    """Abstract base class for async I/O operations with both static and instance methods."""
    
    def __init__(self):
        """Initialize async I/O base."""
        self._closed = False
        self._position = 0
        self._async_stream: Optional[Any] = None
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    async def aread(self, size: Optional[int] = None) -> Union[str, bytes]:
        """Async read operation."""
        pass
    
    @abstractmethod
    async def awrite(self, data: Union[str, bytes]) -> int:
        """Async write operation."""
        pass
    
    @abstractmethod
    async def aseek(self, position: int, whence: int = 0) -> int:
        """Async seek operation."""
        pass
    
    @abstractmethod
    async def atell(self) -> int:
        """Async tell operation."""
        pass
    
    @abstractmethod
    async def aflush(self) -> None:
        """Async flush operation."""
        pass
    
    async def aclose(self) -> None:
        """Async close operation."""
        if self._async_stream:
            await self._async_stream.close()
            self._async_stream = None
            self._closed = True
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    async def aopen_file(path: Union[str, Path], mode: str = 'r', encoding: Optional[str] = None) -> Any:
        """Async open file."""
        # Lazy installation system will handle aiofiles if missing
        import aiofiles
        return await aiofiles.open(path, mode, encoding=encoding)
    
    @staticmethod
    async def aread_text(path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Async read text file."""
        # Lazy installation system will handle aiofiles if missing
        import aiofiles
        async with aiofiles.open(path, 'r', encoding=encoding) as f:
            return await f.read()
    
    @staticmethod
    async def aread_bytes(path: Union[str, Path]) -> bytes:
        """Async read binary file."""
        # Lazy installation system will handle aiofiles if missing
        import aiofiles
        async with aiofiles.open(path, 'rb') as f:
            return await f.read()
    
    @staticmethod
    async def awrite_text(path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """Async write text to file."""
        try:
            # Lazy installation system will handle aiofiles if missing
            import aiofiles
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(path, 'w', encoding=encoding) as f:
                await f.write(content)
            return True
        except Exception:
            return False
    
    @staticmethod
    async def awrite_bytes(path: Union[str, Path], content: bytes) -> bool:
        """Async write bytes to file."""
        try:
            # Lazy installation system will handle aiofiles if missing
            import aiofiles
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(path, 'wb') as f:
                await f.write(content)
            return True
        except Exception:
            return False


# ============================================================================
# ATOMIC OPERATIONS ABSTRACT BASE CLASS
# ============================================================================

class AAtomicOperations(IAtomicOperations, ABC):
    """Abstract base class for atomic operations with both static and instance methods."""
    
    def __init__(self):
        """Initialize atomic operations base."""
        self._temp_dir: Optional[Path] = None
        self._backup_dir: Optional[Path] = None
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    def atomic_write(self, file_path: Union[str, Path], data: Union[str, bytes], 
                    backup: bool = True) -> OperationResult:
        """Atomically write data to file."""
        pass
    
    @abstractmethod
    def atomic_copy(self, source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically copy file."""
        pass
    
    @abstractmethod
    def atomic_move(self, source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically move file."""
        pass
    
    @abstractmethod
    def atomic_delete(self, file_path: Union[str, Path], backup: bool = True) -> OperationResult:
        """Atomically delete file."""
        pass
    
    @abstractmethod
    def atomic_rename(self, old_path: Union[str, Path], new_path: Union[str, Path]) -> OperationResult:
        """Atomically rename file."""
        pass
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    def atomic_write_static(file_path: Union[str, Path], data: Union[str, bytes], 
                           backup: bool = True) -> OperationResult:
        """Atomically write data to file."""
        try:
            from .atomic_file import AtomicFileWriter
            with AtomicFileWriter(file_path, backup=backup) as writer:
                if isinstance(data, str):
                    writer.write(data.encode('utf-8'))
                else:
                    writer.write(data)
            return OperationResult.SUCCESS
        except Exception:
            return OperationResult.FAILED
    
    @staticmethod
    def atomic_copy_static(source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically copy file."""
        try:
            from .atomic_file import AtomicFileWriter
            with open(source, 'rb') as src:
                with AtomicFileWriter(destination) as writer:
                    import shutil
                    shutil.copyfileobj(src, writer)
            return OperationResult.SUCCESS
        except Exception:
            return OperationResult.FAILED
    
    @staticmethod
    def atomic_move_static(source: Union[str, Path], destination: Union[str, Path]) -> OperationResult:
        """Atomically move file."""
        try:
            from .atomic_file import AtomicFileWriter
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(source, 'rb') as src:
                with AtomicFileWriter(destination) as writer:
                    import shutil
                    shutil.copyfileobj(src, writer)
            
            Path(source).unlink()
            return OperationResult.SUCCESS
        except Exception:
            return OperationResult.FAILED
    
    @staticmethod
    def atomic_delete_static(file_path: Union[str, Path], backup: bool = True) -> OperationResult:
        """Atomically delete file."""
        try:
            if backup and Path(file_path).exists():
                ABackupOperations.create_backup_static(file_path, Path(file_path).parent / '.backups')
            
            if Path(file_path).exists():
                Path(file_path).unlink()
            
            return OperationResult.SUCCESS
        except Exception:
            return OperationResult.FAILED
    
    @staticmethod
    def atomic_rename_static(old_path: Union[str, Path], new_path: Union[str, Path]) -> OperationResult:
        """Atomically rename file."""
        return AAtomicOperations.atomic_move_static(old_path, new_path)


# ============================================================================
# BACKUP OPERATIONS ABSTRACT BASE CLASS
# ============================================================================

class ABackupOperations(IBackupOperations, ABC):
    """Abstract base class for backup operations with both static and instance methods."""
    
    def __init__(self):
        """Initialize backup operations base."""
        self._backup_dir: Optional[Path] = None
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    def create_backup(self, source: Union[str, Path], backup_dir: Union[str, Path]) -> Optional[Path]:
        """Create backup of file or directory."""
        pass
    
    @abstractmethod
    def restore_backup(self, backup_path: Union[str, Path], target: Union[str, Path]) -> OperationResult:
        """Restore from backup."""
        pass
    
    def list_backups(self, backup_dir: Union[str, Path]) -> list[Path]:
        """List available backups."""
        return ABackupOperations.list_backups_static(backup_dir)
    
    def cleanup_backups(self, backup_dir: Union[str, Path], max_age_days: int = 30) -> int:
        """Cleanup old backups."""
        return ABackupOperations.cleanup_backups_static(backup_dir, max_age_days)
    
    def verify_backup(self, backup_path: Union[str, Path]) -> bool:
        """Verify backup integrity."""
        return ABackupOperations.verify_backup_static(backup_path)
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    def create_backup_static(source: Union[str, Path], backup_dir: Union[str, Path]) -> Optional[Path]:
        """Create backup of file or directory."""
        try:
            source_path = Path(source)
            backup_path = Path(backup_dir)
            
            backup_path.mkdir(parents=True, exist_ok=True)
            
            if source_path.is_file():
                backup_file = backup_path / f"{source_path.name}.backup.{int(time.time())}"
                import shutil
                shutil.copy2(source_path, backup_file)
                return backup_file
            elif source_path.is_dir():
                backup_dir = backup_path / f"{source_path.name}.backup.{int(time.time())}"
                import shutil
                shutil.copytree(source_path, backup_dir)
                return backup_dir
            else:
                return None
        except Exception:
            return None
    
    @staticmethod
    def restore_backup_static(backup_path: Union[str, Path], target: Union[str, Path]) -> OperationResult:
        """Restore from backup."""
        try:
            backup = Path(backup_path)
            target_path = Path(target)
            
            if backup.is_file():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(backup, target_path)
            elif backup.is_dir():
                if target_path.exists():
                    import shutil
                    shutil.rmtree(target_path)
                import shutil
                shutil.copytree(backup, target_path)
            else:
                return OperationResult.FAILED
            
            return OperationResult.SUCCESS
        except Exception:
            return OperationResult.FAILED
    
    @staticmethod
    def list_backups_static(backup_dir: Union[str, Path]) -> list[Path]:
        """List available backups."""
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return []
            
            return [p for p in backup_path.iterdir() if p.is_file() and p.suffix == '.backup']
        except Exception:
            return []
    
    @staticmethod
    def cleanup_backups_static(backup_dir: Union[str, Path], max_age_days: int = 30) -> int:
        """Cleanup old backups."""
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return 0
            
            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            removed_count = 0
            
            for backup_file in backup_path.iterdir():
                if backup_file.is_file() and backup_file.suffix == '.backup':
                    if backup_file.stat().st_mtime < cutoff_time:
                        backup_file.unlink()
                        removed_count += 1
            
            return removed_count
        except Exception:
            return 0
    
    @staticmethod
    def verify_backup_static(backup_path: Union[str, Path]) -> bool:
        """Verify backup integrity."""
        try:
            backup = Path(backup_path)
            return backup.exists() and backup.is_file() and backup.stat().st_size > 0
        except Exception:
            return False


# ============================================================================
# TEMPORARY OPERATIONS ABSTRACT BASE CLASS
# ============================================================================

class ATemporaryOperations(ITemporaryOperations, ABC):
    """Abstract base class for temporary operations with both static and instance methods."""
    
    def __init__(self):
        """Initialize temporary operations base."""
        self._temp_files: list[Path] = []
        self._temp_dirs: list[Path] = []
        self._temp_base_dir: Optional[Path] = None
    
    # ============================================================================
    # INSTANCE METHODS
    # ============================================================================
    
    @abstractmethod
    def create_temp_file(self, suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary file."""
        pass
    
    @abstractmethod
    def create_temp_directory(self, suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary directory."""
        pass
    
    def cleanup_temp(self, path: Union[str, Path]) -> bool:
        """Cleanup temporary file or directory."""
        return ATemporaryOperations.cleanup_temp_static(path)
    
    def cleanup_all_temp(self) -> int:
        """Cleanup all temporary files and directories."""
        cleaned_count = 0
        
        for temp_file in self._temp_files[:]:
            if ATemporaryOperations.cleanup_temp_static(temp_file):
                cleaned_count += 1
        
        for temp_dir in self._temp_dirs[:]:
            if ATemporaryOperations.cleanup_temp_static(temp_dir):
                cleaned_count += 1
        
        return cleaned_count
    
    # ============================================================================
    # STATIC METHODS
    # ============================================================================
    
    @staticmethod
    def create_temp_file_static(suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary file."""
        import tempfile
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)
        return Path(temp_path)
    
    @staticmethod
    def create_temp_directory_static(suffix: Optional[str] = None, prefix: Optional[str] = None) -> Path:
        """Create temporary directory."""
        import tempfile
        temp_path = tempfile.mkdtemp(suffix=suffix, prefix=prefix)
        return Path(temp_path)
    
    @staticmethod
    def cleanup_temp_static(path: Union[str, Path]) -> bool:
        """Cleanup temporary file or directory."""
        try:
            temp_path = Path(path)
            if temp_path.exists():
                if temp_path.is_file():
                    temp_path.unlink()
                elif temp_path.is_dir():
                    import shutil
                    shutil.rmtree(temp_path)
                return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_temp_base_dir() -> Path:
        """Get temporary base directory."""
        import tempfile
        return Path(tempfile.gettempdir())
    
    @staticmethod
    def is_temp(path: Union[str, Path]) -> bool:
        """Check if path is temporary."""
        temp_path = Path(path)
        temp_base = ATemporaryOperations.get_temp_base_dir()
        return str(temp_path).startswith(str(temp_base))


# ============================================================================
# UNIFIED I/O ABSTRACT BASE CLASS
# ============================================================================

class AUnifiedIO(AFile, AFolder, APath, AStream, AAsyncIO, AAtomicOperations, ABackupOperations, ATemporaryOperations, ABC):
    """
    Abstract base class for unified I/O operations combining all existing I/O capabilities.
    
    This abstract class combines all existing I/O abstract classes into a single,
    comprehensive abstract base that provides complete I/O functionality with
    xwsystem integration for security, validation, and monitoring.
    
    Features:
    - File operations (AFile)
    - Directory operations (AFolder)
    - Path operations (APath)
    - Stream operations (AStream)
    - Async operations (AAsyncIO)
    - Atomic operations (AAtomicOperations)
    - Backup operations (ABackupOperations)
    - Temporary operations (ATemporaryOperations)
    - xwsystem integration (security, validation, monitoring)
    """
    
    def __init__(self, file_path: Optional[Union[str, Path]] = None, **config):
        """
        Initialize unified I/O with xwsystem integration.
        
        Args:
            file_path: Optional file path for file operations
            **config: Configuration options for I/O operations
        """
        # Initialize parent classes
        if file_path:
            super().__init__(file_path)
        else:
            # Initialize without file path for general I/O operations
            self.file_path = None
        
        # Initialize xwsystem utilities
        self._path_validator = None  # Will be set by subclasses
        self._data_validator = None  # Will be set by subclasses
        self._performance_monitor = None  # Will be set by subclasses
        
        # Configuration
        self.validate_paths = config.get('validate_paths', True)
        self.validate_data = config.get('validate_data', True)
        self.enable_monitoring = config.get('enable_monitoring', True)
        self.use_atomic_operations = config.get('use_atomic_operations', True)
        self.enable_backups = config.get('enable_backups', True)
        self.cleanup_temp_on_exit = config.get('cleanup_temp_on_exit', True)
        
        # Track temporary files for cleanup
        self._temp_files: list[Path] = []
        self._temp_dirs: list[Path] = []
    
    def __enter__(self):
        """Enter context manager for resource management."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, cleaning up resources."""
        if self.cleanup_temp_on_exit:
            self.cleanup_all_temp()


# ============================================================================
# FILE MANAGER ABSTRACT BASE CLASS
# ============================================================================

class AFileManager(AFile, AFolder, APath, AAtomicOperations, ABackupOperations, ATemporaryOperations, ABC):
    """
    Abstract base class for file manager operations combining all file-related capabilities.
    
    This abstract class combines all file-related abstract classes into a single,
    comprehensive abstract base that provides complete file management functionality
    with xwsystem integration for security, validation, and monitoring.
    
    Features:
    - File operations (AFile)
    - Directory operations (AFolder)
    - Path operations (APath)
    - Atomic operations (AAtomicOperations)
    - Backup operations (ABackupOperations)
    - Temporary operations (ATemporaryOperations)
    - xwsystem integration (security, validation, monitoring)
    - Format detection and intelligent handling
    """
    
    def __init__(self, base_path: Optional[Union[str, Path]] = None, **config):
        """
        Initialize file manager with xwsystem integration.
        
        Args:
            base_path: Optional base path for file operations
            **config: Configuration options for file operations
        """
        # Initialize parent classes
        if base_path:
            super().__init__(base_path)
        else:
            # Initialize without base path for general file operations
            self.file_path = None
        
        # Initialize xwsystem utilities
        self._path_validator = None  # Will be set by subclasses
        self._data_validator = None  # Will be set by subclasses
        self._performance_monitor = None  # Will be set by subclasses
        
        # Configuration
        self.validate_paths = config.get('validate_paths', True)
        self.validate_data = config.get('validate_data', True)
        self.enable_monitoring = config.get('enable_monitoring', True)
        self.use_atomic_operations = config.get('use_atomic_operations', True)
        self.enable_backups = config.get('enable_backups', True)
        self.cleanup_temp_on_exit = config.get('cleanup_temp_on_exit', True)
        self.auto_detect_format = config.get('auto_detect_format', True)
        self.max_file_size = config.get('max_file_size', 100 * 1024 * 1024)  # 100MB
        
        # Track temporary files for cleanup
        self._temp_files: list[Path] = []
        self._temp_dirs: list[Path] = []
    
    def __enter__(self):
        """Enter context manager for resource management."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager, cleaning up resources."""
        if self.cleanup_temp_on_exit:
            self.cleanup_all_temp()
    
    def detect_file_type(self, file_path: Union[str, Path]) -> str:
        """
        Detect file type from extension and content.
        
        Args:
            file_path: Path to file
            
        Returns:
            Detected file type
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        
        type_mappings = {
            # Documents
            '.txt': 'text', '.md': 'markdown', '.doc': 'word', '.docx': 'word',
            '.pdf': 'pdf', '.rtf': 'rtf',
            
            # Data formats
            '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml', '.xml': 'xml',
            '.csv': 'csv', '.tsv': 'tsv', '.toml': 'toml', '.ini': 'ini',
            '.cfg': 'config', '.conf': 'config',
            
            # Images
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image',
            '.bmp': 'image', '.tiff': 'image', '.svg': 'image', '.webp': 'image',
            
            # Videos
            '.mp4': 'video', '.avi': 'video', '.mov': 'video', '.wmv': 'video',
            '.flv': 'video', '.webm': 'video', '.mkv': 'video',
            
            # Audio
            '.mp3': 'audio', '.wav': 'audio', '.flac': 'audio', '.aac': 'audio',
            '.ogg': 'audio',
            
            # Archives
            '.zip': 'archive', '.rar': 'archive', '.7z': 'archive', '.tar': 'archive',
            '.gz': 'archive',
            
            # Code
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.java': 'java',
            '.cpp': 'cpp', '.c': 'c', '.h': 'header', '.cs': 'csharp', '.php': 'php',
            '.rb': 'ruby', '.go': 'go', '.rs': 'rust',
        }
        
        return type_mappings.get(ext, 'unknown')
    
    def get_file_info(self, file_path: Union[str, Path]) -> dict[str, Any]:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to file
            
        Returns:
            File information dictionary
        """
        path = Path(file_path)
        
        if not path.exists():
            return {'exists': False, 'path': str(path)}
        
        try:
            stat = path.stat()
            return {
                'exists': True,
                'path': str(path),
                'name': path.name,
                'stem': path.stem,
                'suffix': path.suffix,
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'accessed': stat.st_atime,
                'permissions': stat.st_mode,
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'is_symlink': path.is_symlink(),
                'file_type': self.detect_file_type(path),
                'parent': str(path.parent),
                'absolute': str(path.absolute()),
                'relative': str(path.relative_to(Path.cwd())) if path.is_relative_to(Path.cwd()) else None
            }
        except Exception as e:
            return {
                'exists': True,
                'path': str(path),
                'error': str(e)
            }
    
    def is_safe_to_process(self, file_path: Union[str, Path]) -> bool:
        """
        Check if file is safe to process (not too large, accessible, etc.).
        
        Args:
            file_path: Path to file
            
        Returns:
            True if safe to process
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return False
            
            if not path.is_file():
                return False
            
            # Check file size
            if path.stat().st_size > self.max_file_size:
                return False
            
            # Check if readable
            if not os.access(path, os.R_OK):
                return False
            
            return True
        except Exception:
            return False