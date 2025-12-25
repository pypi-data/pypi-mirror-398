#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core tests for shared module.

Tests base classes, contracts, enums, and error classes.

Following GUIDE_TEST.md standards.
"""

import sys

import pytest

from exonware.xwsystem.shared import (
    # Enums
    ValidationLevel,
    PerformanceLevel,
    CoreState,
    CoreMode,
    CorePriority,
    OperationResult,
    # Base classes
    ACoreBase,
    AResourceManagerBase,
    AConfigurationBase,
    BaseCore,
    # Contracts
    ICloneable,
    IComparable,
    ICore,
    # Errors
    CoreError,
    CoreInitializationError,
    CoreStateError,
)


@pytest.mark.xwsystem_core
class TestSharedEnums:
    """Test shared enums."""
    
    def test_validation_level_enum(self):
        """Test ValidationLevel enum."""
        assert ValidationLevel is not None
        # Test enum values exist
        assert hasattr(ValidationLevel, 'NONE') or hasattr(ValidationLevel, 'BASIC')
    
    def test_performance_level_enum(self):
        """Test PerformanceLevel enum."""
        assert PerformanceLevel is not None
    
    def test_core_state_enum(self):
        """Test CoreState enum."""
        assert CoreState is not None
    
    def test_operation_result_enum(self):
        """Test OperationResult enum."""
        assert OperationResult is not None


@pytest.mark.xwsystem_core
class TestSharedBaseClasses:
    """Test shared base classes."""
    
    def test_acore_base_exists(self):
        """Test ACoreBase class exists."""
        assert ACoreBase is not None
    
    def test_aresource_manager_base_exists(self):
        """Test AResourceManagerBase class exists."""
        assert AResourceManagerBase is not None
    
    def test_aconfiguration_base_exists(self):
        """Test AConfigurationBase class exists."""
        assert AConfigurationBase is not None
    
    def test_base_core_exists(self):
        """Test BaseCore class exists."""
        assert BaseCore is not None


@pytest.mark.xwsystem_core
class TestSharedContracts:
    """Test shared contracts/interfaces."""
    
    def test_icloneable_exists(self):
        """Test ICloneable interface exists."""
        assert ICloneable is not None
    
    def test_icomparable_exists(self):
        """Test IComparable interface exists."""
        assert IComparable is not None
    
    def test_icore_exists(self):
        """Test ICore interface exists."""
        assert ICore is not None


@pytest.mark.xwsystem_core
class TestSharedErrors:
    """Test shared error classes."""
    
    def test_core_error(self):
        """Test CoreError exception."""
        error = CoreError("Test error")
        assert str(error) == "Test error"
    
    def test_core_initialization_error(self):
        """Test CoreInitializationError exception."""
        error = CoreInitializationError("Init failed")
        assert "Init failed" in str(error)
    
    def test_core_state_error(self):
        """Test CoreStateError exception."""
        error = CoreStateError("State error")
        assert "State error" in str(error)


@pytest.mark.xwsystem_core
class TestSharedIntegration:
    """Test shared types integration across modules."""
    
    def test_enum_usage_in_operations(self):
        """Test shared enums used in operations module."""
        from exonware.xwsystem.shared import OperationResult
        
        # Verify enum can be imported and used
        assert OperationResult is not None
    
    def test_error_usage_across_modules(self):
        """Test shared errors used across modules."""
        from exonware.xwsystem.shared import CoreError
        
        # Verify error can be raised
        try:
            raise CoreError("Test")
        except CoreError as e:
            assert "Test" in str(e)

