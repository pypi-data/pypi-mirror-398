#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for shared error classes.

Following GUIDE_TEST.md standards.
"""

import sys

import pytest

from exonware.xwsystem.shared import (
    CoreError,
    CoreInitializationError,
    CoreShutdownError,
    CoreStateError,
    CoreDependencyError,
    CoreConfigurationError,
    CoreResourceError,
    CoreTimeoutError,
    CorePermissionError,
    CoreValidationError,
    CoreOperationError,
)


@pytest.mark.xwsystem_unit
class TestCoreError:
    """Test CoreError base exception."""
    
    def test_core_error_instantiation(self):
        """Test CoreError can be instantiated."""
        error = CoreError("Test error message")
        assert str(error) == "Test error message"
    
    def test_core_error_raise(self):
        """Test CoreError can be raised."""
        with pytest.raises(CoreError):
            raise CoreError("Test")


@pytest.mark.xwsystem_unit
class TestCoreInitializationError:
    """Test CoreInitializationError."""
    
    def test_core_initialization_error(self):
        """Test CoreInitializationError."""
        error = CoreInitializationError("Init failed")
        assert "Init failed" in str(error)
        assert isinstance(error, CoreError)


@pytest.mark.xwsystem_unit
class TestCoreShutdownError:
    """Test CoreShutdownError."""
    
    def test_core_shutdown_error(self):
        """Test CoreShutdownError."""
        error = CoreShutdownError("Shutdown failed")
        assert "Shutdown failed" in str(error)
        assert isinstance(error, CoreError)


@pytest.mark.xwsystem_unit
class TestCoreStateError:
    """Test CoreStateError."""
    
    def test_core_state_error(self):
        """Test CoreStateError."""
        error = CoreStateError("State invalid")
        assert "State invalid" in str(error)
        assert isinstance(error, CoreError)


@pytest.mark.xwsystem_unit
class TestOtherCoreErrors:
    """Test other core error classes."""
    
    def test_core_dependency_error(self):
        """Test CoreDependencyError."""
        error = CoreDependencyError("Missing dependency")
        assert isinstance(error, CoreError)
    
    def test_core_configuration_error(self):
        """Test CoreConfigurationError."""
        error = CoreConfigurationError("Config invalid")
        assert isinstance(error, CoreError)
    
    def test_core_resource_error(self):
        """Test CoreResourceError."""
        error = CoreResourceError("Resource unavailable")
        assert isinstance(error, CoreError)
    
    def test_core_timeout_error(self):
        """Test CoreTimeoutError."""
        error = CoreTimeoutError("Operation timed out")
        assert isinstance(error, CoreError)
    
    def test_core_permission_error(self):
        """Test CorePermissionError."""
        error = CorePermissionError("Permission denied")
        assert isinstance(error, CoreError)
    
    def test_core_validation_error(self):
        """Test CoreValidationError."""
        error = CoreValidationError("Validation failed")
        assert isinstance(error, CoreError)
    
    def test_core_operation_error(self):
        """Test CoreOperationError."""
        error = CoreOperationError("Operation failed")
        assert isinstance(error, CoreError)

