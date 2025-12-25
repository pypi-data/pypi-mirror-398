#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for AsyncAtomicFileWriter.

Following GUIDE_TEST.md standards.
"""

import sys
from pathlib import Path

import pytest

from exonware.xwsystem.io.stream import AsyncAtomicFileWriter


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestAsyncAtomicFileWriter:
    """Test AsyncAtomicFileWriter class."""
    
    @pytest.mark.asyncio
    async def test_async_atomic_file_writer_basic(self, tmp_path):
        """Test basic async atomic file writing."""
        test_file = tmp_path / "async_test.txt"
        test_content = "Async test content"
        
        async_writer = AsyncAtomicFileWriter(test_file)
        await async_writer.start()
        await async_writer.write(test_content.encode('utf-8'))
        await async_writer.commit()
        
        assert test_file.exists()
        assert test_file.read_text() == test_content
    
    @pytest.mark.asyncio
    async def test_async_atomic_file_writer_context_manager(self, tmp_path):
        """Test async writer as context manager."""
        test_file = tmp_path / "async_context.txt"
        test_content = "Context test"
        
        async with AsyncAtomicFileWriter(test_file) as writer:
            await writer.write(test_content.encode('utf-8'))
        
        assert test_file.exists()
        assert test_file.read_text() == test_content

