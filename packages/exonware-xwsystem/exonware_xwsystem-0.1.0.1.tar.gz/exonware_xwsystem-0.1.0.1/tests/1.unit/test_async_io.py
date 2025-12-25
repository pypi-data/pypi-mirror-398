"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: January 31, 2025

Unit tests for async I/O operations.
"""

import asyncio
import os
import tempfile
import pytest
from pathlib import Path

from exonware.xwsystem.io.stream.async_operations import (
    AsyncAtomicFileWriter,
    async_atomic_write,
    async_safe_write_text,
    async_safe_write_bytes,
    async_safe_read_text,
    async_safe_read_bytes,
    async_safe_read_with_fallback,
)
from exonware.xwsystem.io.common.atomic import FileOperationError


class TestAsyncAtomicFileWriter:
    """Test AsyncAtomicFileWriter class."""

    @pytest.mark.asyncio
    async def test_basic_write(self):
        """Test basic async atomic write."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Hello, async world!"
            
            writer = AsyncAtomicFileWriter(file_path)
            async with writer as f:
                await f.write(content)
            
            # Verify file was written
            assert file_path.exists()
            with open(file_path, 'r', encoding='utf-8') as f:
                assert f.read() == content

    @pytest.mark.asyncio
    async def test_binary_write(self):
        """Test binary async atomic write."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.bin"
            content = b"Binary content"
            
            writer = AsyncAtomicFileWriter(file_path, mode="wb", encoding=None)
            async with writer as f:
                await f.write(content)
            
            # Verify file was written
            assert file_path.exists()
            with open(file_path, 'rb') as f:
                assert f.read() == content

    @pytest.mark.asyncio
    async def test_backup_creation(self):
        """Test backup creation during write."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            original_content = "Original content"
            new_content = "New content"
            
            # Create original file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Write new content with backup
            writer = AsyncAtomicFileWriter(file_path, backup=True)
            async with writer as f:
                await f.write(new_content)
            
            # Verify new content
            with open(file_path, 'r', encoding='utf-8') as f:
                assert f.read() == new_content
            
            # Backup should be cleaned up after successful write
            backup_files = list(Path(temp_dir).glob("*.backup.*"))
            assert len(backup_files) == 0

    @pytest.mark.asyncio
    async def test_rollback_on_exception(self):
        """Test rollback when exception occurs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            original_content = "Original content"
            
            # Create original file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Attempt write that will fail
            writer = AsyncAtomicFileWriter(file_path, backup=True)
            try:
                async with writer as f:
                    await f.write("Partial content")
                    raise ValueError("Simulated error")
            except ValueError:
                pass  # Expected
            
            # Original content should be preserved
            with open(file_path, 'r', encoding='utf-8') as f:
                assert f.read() == original_content


class TestAsyncConvenienceFunctions:
    """Test async convenience functions."""

    @pytest.mark.asyncio
    async def test_async_safe_write_text(self):
        """Test async_safe_write_text function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Test content with unicode: 🚀"
            
            await async_safe_write_text(file_path, content)
            
            assert file_path.exists()
            with open(file_path, 'r', encoding='utf-8') as f:
                assert f.read() == content

    @pytest.mark.asyncio
    async def test_async_safe_write_bytes(self):
        """Test async_safe_write_bytes function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.bin"
            content = b"Binary test content"
            
            await async_safe_write_bytes(file_path, content)
            
            assert file_path.exists()
            with open(file_path, 'rb') as f:
                assert f.read() == content

    @pytest.mark.asyncio
    async def test_async_safe_read_text(self):
        """Test async_safe_read_text function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Test content with unicode: 🌟"
            
            # Write file first
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Read with async function
            result = await async_safe_read_text(file_path)
            assert result == content

    @pytest.mark.asyncio
    async def test_async_safe_read_bytes(self):
        """Test async_safe_read_bytes function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.bin"
            content = b"Binary test content"
            
            # Write file first
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Read with async function
            result = await async_safe_read_bytes(file_path)
            assert result == content

    @pytest.mark.asyncio
    async def test_async_safe_read_nonexistent_file(self):
        """Test reading non-existent file raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.txt"
            
            with pytest.raises(FileOperationError, match="File does not exist"):
                await async_safe_read_text(file_path)

    @pytest.mark.asyncio
    async def test_async_safe_read_with_size_limit(self):
        """Test reading with size limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "large.txt"
            content = "x" * 1000  # 1KB content
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Should succeed with default limit (100MB)
            result = await async_safe_read_text(file_path)
            assert result == content
            
            # Should fail with very small limit
            with pytest.raises(FileOperationError, match="exceeds maximum allowed"):
                await async_safe_read_text(file_path, max_size_mb=0.0001)

    @pytest.mark.asyncio
    async def test_async_safe_read_with_fallback(self):
        """Test async_safe_read_with_fallback function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Test content"
            
            # Write file with UTF-8
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Should read successfully
            result = await async_safe_read_with_fallback(file_path)
            assert result == content

    @pytest.mark.asyncio
    async def test_async_atomic_write_context_manager(self):
        """Test async_atomic_write context manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Context manager content"
            
            async with async_atomic_write(file_path) as f:
                await f.write(content)
            
            assert file_path.exists()
            with open(file_path, 'r', encoding='utf-8') as f:
                assert f.read() == content


class TestAsyncIOErrorHandling:
    """Test error handling in async I/O operations."""

    @pytest.mark.asyncio
    async def test_invalid_encoding(self):
        """Test handling of invalid encoding."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            
            # Write binary data
            with open(file_path, 'wb') as f:
                f.write(b'\xff\xfe\xfd')  # Invalid UTF-8
            
            # Should raise encoding error
            with pytest.raises(FileOperationError, match="Encoding error"):
                await async_safe_read_text(file_path, encoding='utf-8')

    @pytest.mark.asyncio
    async def test_permission_error(self):
        """Test handling of permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "readonly.txt"
            
            # Create file and make it read-only
            with open(file_path, 'w') as f:
                f.write("test")
            
            os.chmod(file_path, 0o444)  # Read-only
            
            try:
                # Should handle permission error gracefully
                with pytest.raises(FileOperationError):
                    await async_safe_write_text(file_path, "new content")
            finally:
                # Restore permissions for cleanup
                os.chmod(file_path, 0o644)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent async operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = []
            
            # Create multiple concurrent write operations
            for i in range(10):
                file_path = Path(temp_dir) / f"test_{i}.txt"
                content = f"Content for file {i}"
                task = async_safe_write_text(file_path, content)
                tasks.append(task)
            
            # Wait for all operations to complete
            await asyncio.gather(*tasks)
            
            # Verify all files were written correctly
            for i in range(10):
                file_path = Path(temp_dir) / f"test_{i}.txt"
                assert file_path.exists()
                
                content = await async_safe_read_text(file_path)
                assert content == f"Content for file {i}"


if __name__ == "__main__":
    pytest.main([__file__])
