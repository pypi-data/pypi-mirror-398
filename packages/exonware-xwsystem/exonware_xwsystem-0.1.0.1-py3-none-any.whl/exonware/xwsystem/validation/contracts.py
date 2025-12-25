#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Validation protocol interfaces for XWSystem.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Iterator, Callable, Protocol
from typing_extensions import runtime_checkable

# Import enums from types module
from .defs import (
    ValidationLevel,
    ValidationType,
    ValidationResult
)


# ============================================================================
# VALIDATION INTERFACES
# ============================================================================

class IValidatable(ABC):
    """
    Interface for objects that can be validated.
    
    Enforces consistent validation behavior across XWSystem.
    """
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate this object.
        
        Returns:
            True if valid
        """
        pass
    
    @abstractmethod
    def is_valid(self) -> bool:
        """
        Check if object is valid.
        
        Returns:
            True if valid
        """
        pass
    
    @abstractmethod
    def get_errors(self) -> list[str]:
        """
        Get validation errors.
        
        Returns:
            List of error messages
        """
        pass
    
    @abstractmethod
    def clear_errors(self) -> None:
        """
        Clear validation errors.
        """
        pass
    
    @abstractmethod
    def has_errors(self) -> bool:
        """
        Check if object has validation errors.
        
        Returns:
            True if has errors
        """
        pass
    
    @abstractmethod
    def add_error(self, error: str) -> None:
        """
        Add validation error.
        
        Args:
            error: Error message
        """
        pass


# ============================================================================
# VALIDATION MANAGER INTERFACES
# ============================================================================

class IValidationManager(ABC):
    """
    Interface for validation management.
    
    Enforces consistent validation management across XWSystem.
    """
    
    @abstractmethod
    def add_validator(self, name: str, validator: Callable[[Any], bool]) -> None:
        """
        Add validator function.
        
        Args:
            name: Validator name
            validator: Validator function
        """
        pass
    
    @abstractmethod
    def remove_validator(self, name: str) -> bool:
        """
        Remove validator.
        
        Args:
            name: Validator name
            
        Returns:
            True if removed
        """
        pass
    
    @abstractmethod
    def validate_object(self, obj: Any, validators: list[str]) -> tuple[bool, list[str]]:
        """
        Validate object with specified validators.
        
        Args:
            obj: Object to validate
            validators: List of validator names
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass
    
    @abstractmethod
    def get_validators(self) -> list[str]:
        """
        Get list of available validators.
        
        Returns:
            List of validator names
        """
        pass


# ============================================================================
# SCHEMA VALIDATION INTERFACES
# ============================================================================

class ISchemaValidator(ABC):
    """
    Interface for schema validation.
    
    Enforces consistent schema validation across XWSystem.
    """
    
    @abstractmethod
    def validate_schema(self, data: Any, schema: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate data against schema.
        
        Args:
            data: Data to validate
            schema: Schema definition
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass
    
    @abstractmethod
    def create_schema(self, data: Any) -> dict[str, Any]:
        """
        Create schema from data.
        
        Args:
            data: Data to create schema from
            
        Returns:
            Schema definition
        """
        pass
    
    @abstractmethod
    def validate_type(self, data: Any, expected_type: str) -> bool:
        """
        Validate data type.
        
        Args:
            data: Data to validate
            expected_type: Expected type name
            
        Returns:
            True if type matches
        """
        pass
    
    @abstractmethod
    def validate_range(self, data: Any, min_value: Any, max_value: Any) -> bool:
        """
        Validate data range.
        
        Args:
            data: Data to validate
            min_value: Minimum value
            max_value: Maximum value
            
        Returns:
            True if in range
        """
        pass
    
    @abstractmethod
    def validate_pattern(self, data: str, pattern: str) -> bool:
        """
        Validate string pattern.
        
        Args:
            data: String to validate
            pattern: Regex pattern
            
        Returns:
            True if pattern matches
        """
        pass


# ============================================================================
# VALIDATION PROTOCOLS
# ============================================================================

@runtime_checkable
class Validatable(Protocol):
    """Protocol for objects that support data validation."""
    
    def validate(self, data: Any, **kwargs: Any) -> bool:
        """Validate data against rules."""
        ...
    
    def get_errors(self) -> list[dict[str, Any]]:
        """Get validation errors."""
        ...
