"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Asynchronous I/O operations for non-blocking file handling.
"""

import asyncio
import os
import shutil
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncContextManager, BinaryIO, Optional, TextIO, Union

# Import aiofiles - lazy installation system will handle it if missing
import aiofiles
import aiofiles.os

from ...config.logging_setup import get_logger
from ..common.atomic import FileOperationError

logger = get_logger("xwsystem.io.async_operations")


class AsyncAtomicFileWriter:
    """
    Provides asynchronous atomic file writing operations to prevent data corruption.
    
    This class ensures that file writes are atomic by writing to a temporary
    file first and then moving it to the target location. All operations are
    non-blocking and async-compatible.
    """

    def __init__(
        self,
        target_path: Union[str, Path],
        mode: str = "w",
        encoding: Optional[str] = "utf-8",
        backup: bool = False,
        temp_dir: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize async atomic file writer.

        Args:
            target_path: Final path where file should be written
            mode: File open mode ('w', 'wb', 'w+', etc.)
            encoding: Text encoding (for text modes)
            backup: Whether to create backup of existing file
            temp_dir: Directory for temporary files (defaults to same as target)
        """
        self.target_path = Path(target_path)
        self.mode = mode
        self.encoding = encoding if "b" not in mode else None
        self.backup = backup
        self.temp_dir = Path(temp_dir) if temp_dir else self.target_path.parent

        self.temp_path: Optional[Path] = None
        self.backup_path: Optional[Path] = None
        self.file_handle: Optional[Any] = None  # aiofiles handle
        self._committed = False
        self._started = False

    async def __aenter__(self) -> Any:
        """Async context manager entry - create temporary file."""
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - commit or rollback based on success."""
        if exc_type is None:
            # No exception occurred, commit the write
            await self.commit()
        else:
            # Exception occurred, rollback
            await self.rollback()
        return False  # Don't suppress exceptions

    async def start(self) -> Any:
        """
        Start the async atomic write operation.

        Returns:
            Async file handle for writing
        """
        # Lazy installation system will handle aiofiles if missing
            
        if self._started:
            raise FileOperationError("Async atomic write operation already started")

        self._started = True

        try:
            # Ensure temp directory exists
            await aiofiles.os.makedirs(self.temp_dir, exist_ok=True)

            # Create backup if requested and target exists
            if self.backup and await aiofiles.os.path.exists(self.target_path):
                await self._create_backup()

            # Create temporary file in same directory as target
            # This ensures they're on the same filesystem for atomic move
            fd, temp_path_str = tempfile.mkstemp(
                prefix=f".{self.target_path.name}_", suffix=".tmp", dir=self.temp_dir
            )

            self.temp_path = Path(temp_path_str)

            # Close the file descriptor and reopen with aiofiles
            os.close(fd)

            # Open with aiofiles with the requested mode and encoding
            if self.encoding:
                self.file_handle = await aiofiles.open(
                    self.temp_path, self.mode, encoding=self.encoding
                )
            else:
                self.file_handle = await aiofiles.open(self.temp_path, self.mode)

            logger.debug(
                f"Started async atomic write: {self.target_path} via {self.temp_path}"
            )
            return self.file_handle

        except Exception as e:
            await self._cleanup()
            raise FileOperationError(f"Failed to start async atomic write: {e}") from e

    async def commit(self) -> None:
        """
        Commit the async atomic write operation.

        This closes the temporary file and atomically moves it to the target location.
        """
        if not self._started:
            raise FileOperationError("Async atomic write operation not started")

        if self._committed:
            return  # Already committed

        try:
            import os  # Import at the beginning of the method
            
            # Close the file handle
            if self.file_handle:
                await self.file_handle.close()

            # Verify temp file was written
            if not self.temp_path or not await aiofiles.os.path.exists(self.temp_path):
                raise FileOperationError(
                    "Temporary file was not created or was deleted"
                )

            # Get file stats for verification
            temp_stat = await aiofiles.os.stat(self.temp_path)
            if temp_stat.st_size == 0:
                logger.warning(f"Temporary file is empty: {self.temp_path}")

            # Atomic move to target location
            # On Windows, need to remove target first if it exists
            if os.name == "nt" and await aiofiles.os.path.exists(self.target_path):
                await aiofiles.os.remove(self.target_path)

            # Perform the atomic move (using sync operation as aiofiles doesn't have move)
            await asyncio.get_event_loop().run_in_executor(
                None, shutil.move, str(self.temp_path), str(self.target_path)
            )

            self._committed = True

            # Set file permissions to match original if backup exists
            if self.backup_path and await aiofiles.os.path.exists(self.backup_path):
                try:
                    backup_stat = await aiofiles.os.stat(self.backup_path)
                    # Use regular os.chmod since aiofiles doesn't have chmod
                    os.chmod(self.target_path, backup_stat.st_mode)
                except OSError:
                    pass  # Ignore permission errors

            logger.debug(f"Committed async atomic write: {self.target_path}")

        except Exception as e:
            # Try to rollback on commit failure
            await self.rollback()
            raise FileOperationError(f"Failed to commit async atomic write: {e}") from e

    async def rollback(self) -> None:
        """
        Rollback the async atomic write operation.

        This removes the temporary file and restores backup if available.
        """
        if not self._started:
            return

        logger.debug(f"Rolling back async atomic write: {self.target_path}")

        # Close file handle
        if self.file_handle:
            try:
                await self.file_handle.close()
            except Exception:
                pass  # Ignore close errors during rollback

        # Remove temporary file
        if self.temp_path and await aiofiles.os.path.exists(self.temp_path):
            try:
                await aiofiles.os.remove(self.temp_path)
                logger.debug(f"Removed temporary file: {self.temp_path}")
            except Exception as e:
                logger.warning(f"Could not remove temporary file {self.temp_path}: {e}")

        # Restore backup if needed and target was removed
        if (
            self.backup_path
            and await aiofiles.os.path.exists(self.backup_path)
            and not await aiofiles.os.path.exists(self.target_path)
        ):
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, shutil.move, str(self.backup_path), str(self.target_path)
                )
                logger.debug(
                    f"Restored backup: {self.backup_path} -> {self.target_path}"
                )
            except Exception as e:
                logger.error(f"Could not restore backup {self.backup_path}: {e}")

        await self._cleanup()

    async def _create_backup(self) -> None:
        """Create backup of existing target file."""
        if not await aiofiles.os.path.exists(self.target_path):
            return

        timestamp = int(time.time())
        backup_name = f"{self.target_path.name}.backup.{timestamp}"
        self.backup_path = self.target_path.parent / backup_name

        try:
            await asyncio.get_event_loop().run_in_executor(
                None, shutil.copy2, str(self.target_path), str(self.backup_path)
            )
            logger.debug(f"Created backup: {self.backup_path}")
        except Exception as e:
            logger.warning(f"Could not create backup: {e}")
            self.backup_path = None

    async def _cleanup(self) -> None:
        """Clean up temporary resources."""
        # Remove backup if commit was successful
        if self._committed and self.backup_path and await aiofiles.os.path.exists(self.backup_path):
            try:
                await aiofiles.os.remove(self.backup_path)
                logger.debug(f"Removed backup: {self.backup_path}")
            except Exception as e:
                logger.warning(f"Could not remove backup {self.backup_path}: {e}")

        # Reset state
        self.temp_path = None
        self.backup_path = None
        self.file_handle = None


@asynccontextmanager
async def async_atomic_write(
    target_path: Union[str, Path],
    mode: str = "w",
    encoding: Optional[str] = "utf-8",
    backup: bool = True,
    temp_dir: Optional[Union[str, Path]] = None,
) -> AsyncContextManager[Any]:
    """
    Async context manager for atomic file writing.

    Args:
        target_path: Final path where file should be written
        mode: File open mode
        encoding: Text encoding (for text modes)
        backup: Whether to create backup of existing file
        temp_dir: Directory for temporary files

    Yields:
        Async file handle for writing

    Example:
        async with async_atomic_write('data.json') as f:
            await f.write(json.dumps(data))
    """
    writer = AsyncAtomicFileWriter(
        target_path=target_path,
        mode=mode,
        encoding=encoding,
        backup=backup,
        temp_dir=temp_dir,
    )

    async with writer as f:
        yield f


async def async_safe_write_text(
    target_path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    backup: bool = True,
) -> None:
    """
    Safely write text content to a file atomically (async).

    Args:
        target_path: Path to write to
        content: Text content to write
        encoding: Text encoding
        backup: Whether to create backup
    """
    async with async_atomic_write(target_path, "w", encoding=encoding, backup=backup) as f:
        await f.write(content)


async def async_safe_write_bytes(
    target_path: Union[str, Path], content: bytes, backup: bool = True
) -> None:
    """
    Safely write binary content to a file atomically (async).

    Args:
        target_path: Path to write to
        content: Binary content to write
        backup: Whether to create backup
    """
    async with async_atomic_write(target_path, "wb", encoding=None, backup=backup) as f:
        await f.write(content)


async def async_safe_read_text(
    file_path: Union[str, Path], encoding: str = "utf-8", max_size_mb: float = 100.0
) -> str:
    """
    Safely read text content from a file with size validation (async).

    Args:
        file_path: Path to read from
        encoding: Text encoding
        max_size_mb: Maximum file size in MB (default 100MB)

    Returns:
        Text content of the file

    Raises:
        FileOperationError: If file is too large, doesn't exist, or can't be read
    """
    file_path = Path(file_path)

    # Check if file exists
    if not await aiofiles.os.path.exists(file_path):
        raise FileOperationError(f"File does not exist: {file_path}")

    # Check file size
    try:
        file_stat = await aiofiles.os.stat(file_path)
        file_size_bytes = file_stat.st_size
        file_size_mb = file_size_bytes / (1024 * 1024)

        if file_size_mb > max_size_mb:
            raise FileOperationError(
                f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed "
                f"({max_size_mb}MB): {file_path}"
            )

        logger.debug(f"Reading async text file {file_path} ({file_size_mb:.1f}MB)")

    except OSError as e:
        raise FileOperationError(
            f"Could not get file stats for {file_path}: {e}"
        ) from e

    # Read file content
    try:
        async with aiofiles.open(file_path, "r", encoding=encoding) as f:
            return await f.read()
    except UnicodeDecodeError as e:
        raise FileOperationError(
            f"Encoding error reading '{file_path}' with encoding '{encoding}': {e}"
        ) from e
    except IOError as e:
        raise FileOperationError(f"IOError reading file '{file_path}': {e}") from e


async def async_safe_read_bytes(file_path: Union[str, Path], max_size_mb: float = 100.0) -> bytes:
    """
    Safely read binary content from a file with size validation (async).

    Args:
        file_path: Path to read from
        max_size_mb: Maximum file size in MB (default 100MB)

    Returns:
        Binary content of the file

    Raises:
        FileOperationError: If file is too large, doesn't exist, or can't be read
    """
    file_path = Path(file_path)

    # Check if file exists
    if not await aiofiles.os.path.exists(file_path):
        raise FileOperationError(f"File does not exist: {file_path}")

    # Check file size
    try:
        file_stat = await aiofiles.os.stat(file_path)
        file_size_bytes = file_stat.st_size
        file_size_mb = file_size_bytes / (1024 * 1024)

        if file_size_mb > max_size_mb:
            raise FileOperationError(
                f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed "
                f"({max_size_mb}MB): {file_path}"
            )

        logger.debug(f"Reading async binary file {file_path} ({file_size_mb:.1f}MB)")

    except OSError as e:
        raise FileOperationError(
            f"Could not get file stats for {file_path}: {e}"
        ) from e

    # Read file content
    try:
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()
    except IOError as e:
        raise FileOperationError(f"IOError reading file '{file_path}': {e}") from e


async def async_safe_read_with_fallback(
    file_path: Union[str, Path],
    preferred_encoding: str = "utf-8",
    fallback_encodings: Optional[list[str]] = None,
    max_size_mb: float = 100.0,
) -> str:
    """
    Safely read text file with encoding fallback for robustness (async).

    Args:
        file_path: Path to read from
        preferred_encoding: Primary encoding to try
        fallback_encodings: List of fallback encodings to try if primary fails
        max_size_mb: Maximum file size in MB

    Returns:
        Text content of the file

    Raises:
        FileOperationError: If file can't be read with any encoding
    """
    if fallback_encodings is None:
        fallback_encodings = ["latin1", "cp1252", "iso-8859-1"]

    # Try preferred encoding first
    try:
        return await async_safe_read_text(file_path, preferred_encoding, max_size_mb)
    except FileOperationError as e:
        if "Encoding error" not in str(e):
            raise  # Re-raise non-encoding errors

    # Try fallback encodings
    for encoding in fallback_encodings:
        try:
            logger.debug(f"Trying fallback encoding {encoding} for {file_path}")
            return await async_safe_read_text(file_path, encoding, max_size_mb)
        except FileOperationError as e:
            if "Encoding error" not in str(e):
                raise  # Re-raise non-encoding errors
            continue  # Try next encoding

    # If all encodings failed, try binary read as last resort
    try:
        logger.warning(f"All text encodings failed for {file_path}, reading as binary")
        binary_content = await async_safe_read_bytes(file_path, max_size_mb)
        # Try to decode with errors='replace' to get some readable content
        return binary_content.decode(preferred_encoding, errors="replace")
    except Exception as e:
        raise FileOperationError(
            f"Could not read file '{file_path}' with any encoding: {e}"
        ) from e
