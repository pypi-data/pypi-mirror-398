"""
Unit tests for io.defs module

Tests all IO enums and type definitions.
Following GUIDELINES_TEST.md structure and eXonware testing standards.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

import pytest
from enum import Enum
from exonware.xwsystem.io.defs import (
    FileMode,
    FileType,
    PathType,
    OperationResult,
    LockType,
    CodecCapability,
    ArchiveFormat,
    CompressionAlgorithm,
    CompressionLevel,
)


@pytest.mark.xwsystem_unit
class TestFileEnums:
    """Test file-related enums."""
    
    def test_file_mode_is_enum(self):
        """Test FileMode is an Enum."""
        assert issubclass(FileMode, Enum)
    
    def test_file_mode_has_basic_modes(self):
        """Test FileMode has READ, WRITE, APPEND."""
        assert hasattr(FileMode, 'READ')
        assert hasattr(FileMode, 'WRITE')
        assert hasattr(FileMode, 'APPEND')
    
    def test_file_type_is_enum(self):
        """Test FileType is an Enum."""
        assert issubclass(FileType, Enum)
    
    def test_file_type_has_text_and_binary(self):
        """Test FileType has TEXT and BINARY."""
        assert hasattr(FileType, 'TEXT')
        assert hasattr(FileType, 'BINARY')
    
    def test_path_type_is_enum(self):
        """Test PathType is an Enum."""
        assert issubclass(PathType, Enum)


@pytest.mark.xwsystem_unit
class TestOperationEnums:
    """Test operation-related enums."""
    
    def test_operation_result_is_enum(self):
        """Test OperationResult is an Enum."""
        assert issubclass(OperationResult, Enum)
    
    def test_operation_result_has_success_and_failure(self):
        """Test OperationResult has SUCCESS and FAILURE."""
        assert hasattr(OperationResult, 'SUCCESS')
        assert hasattr(OperationResult, 'FAILURE')
    
    def test_lock_type_is_enum(self):
        """Test LockType is an Enum."""
        assert issubclass(LockType, Enum)


@pytest.mark.xwsystem_unit
class TestCodecEnums:
    """Test codec-related enums."""
    
    def test_codec_capability_is_enum(self):
        """Test CodecCapability is an Enum."""
        assert issubclass(CodecCapability, Enum)


@pytest.mark.xwsystem_unit
class TestArchiveEnums:
    """Test archive-related enums."""
    
    def test_archive_format_is_enum(self):
        """Test ArchiveFormat is an Enum."""
        assert issubclass(ArchiveFormat, Enum)
    
    def test_archive_format_has_zip_and_tar(self):
        """Test ArchiveFormat has ZIP and TAR."""
        assert hasattr(ArchiveFormat, 'ZIP')
        assert hasattr(ArchiveFormat, 'TAR')
    
    def test_compression_algorithm_is_enum(self):
        """Test CompressionAlgorithm is an Enum."""
        assert issubclass(CompressionAlgorithm, Enum)
    
    def test_compression_level_is_enum(self):
        """Test CompressionLevel is an Enum."""
        assert issubclass(CompressionLevel, Enum)


@pytest.mark.xwsystem_unit
class TestEnumValues:
    """Test that enums have consistent values."""
    
    def test_enum_values_are_unique(self):
        """Test that enum values within each enum are unique."""
        # FileMode
        file_modes = [mode.value for mode in FileMode]
        assert len(file_modes) == len(set(file_modes))
        
        # FileType
        file_types = [ft.value for ft in FileType]
        assert len(file_types) == len(set(file_types))
        
        # OperationResult
        results = [result.value for result in OperationResult]
        assert len(results) == len(set(results))

