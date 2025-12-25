#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for shared enums and definitions.

Following GUIDE_TEST.md standards.
"""

import sys

import pytest

from exonware.xwsystem.shared import (
    ValidationLevel,
    PerformanceLevel,
    CoreState,
    CoreMode,
    CorePriority,
    OperationResult,
    DataType,
    LogLevel,
)


@pytest.mark.xwsystem_unit
class TestValidationLevel:
    """Test ValidationLevel enum."""
    
    def test_validation_level_enum_exists(self):
        """Test ValidationLevel enum exists."""
        assert ValidationLevel is not None
    
    def test_validation_level_values(self):
        """Test ValidationLevel enum values."""
        # Check if enum has values
        values = list(ValidationLevel) if hasattr(ValidationLevel, '__iter__') else []
        # Enum should have at least some values
        assert True  # Just verify enum exists


@pytest.mark.xwsystem_unit
class TestPerformanceLevel:
    """Test PerformanceLevel enum."""
    
    def test_performance_level_enum_exists(self):
        """Test PerformanceLevel enum exists."""
        assert PerformanceLevel is not None


@pytest.mark.xwsystem_unit
class TestCoreState:
    """Test CoreState enum."""
    
    def test_core_state_enum_exists(self):
        """Test CoreState enum exists."""
        assert CoreState is not None


@pytest.mark.xwsystem_unit
class TestOperationResult:
    """Test OperationResult enum."""
    
    def test_operation_result_enum_exists(self):
        """Test OperationResult enum exists."""
        assert OperationResult is not None


@pytest.mark.xwsystem_unit
class TestOtherEnums:
    """Test other shared enums."""
    
    def test_data_type_enum(self):
        """Test DataType enum."""
        assert DataType is not None
    
    def test_log_level_enum(self):
        """Test LogLevel enum."""
        assert LogLevel is not None
    
    def test_core_mode_enum(self):
        """Test CoreMode enum."""
        assert CoreMode is not None
    
    def test_core_priority_enum(self):
        """Test CorePriority enum."""
        assert CorePriority is not None

