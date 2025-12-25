#!/usr/bin/env python3
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: October 26, 2025

Fluent validator with chainable API for data validation.
"""

from typing import Any, Callable, Optional, Union
from .errors import ValidationError
from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.validation.fluent_validator")


class FluentValidator:
    """
    Fluent validator with chainable API for data validation.
    
    Features:
    - Chainable validation methods
    - Custom validator support
    - Error collection (all errors before raising)
    - Type checking and range validation
    - Required field validation
    - Custom error messages
    """
    
    def __init__(self, data: Any = None):
        """
        Initialize fluent validator.
        
        Args:
            data: Data to validate (optional, can be set later)
        """
        self.data = data
        self.errors: list[str] = []
        self.rules: list[dict[str, Any]] = []
    
    def require(self, field_name: str, message: Optional[str] = None) -> 'FluentValidator':
        """
        Require a field to be present and not None.
        
        Args:
            field_name: Name of field to check
            message: Custom error message
            
        Returns:
            Self for method chaining
        """
        try:
            if isinstance(self.data, dict):
                if field_name not in self.data or self.data[field_name] is None:
                    error_msg = message or f"Field '{field_name}' is required"
                    self.errors.append(error_msg)
            else:
                error_msg = message or f"Data must be a dictionary to check field '{field_name}'"
                self.errors.append(error_msg)
        except Exception as e:
            error_msg = message or f"Error checking required field '{field_name}': {e}"
            self.errors.append(error_msg)
        
        return self
    
    def type_check(self, expected_type: type, message: Optional[str] = None) -> 'FluentValidator':
        """
        Check if data is of expected type.
        
        Args:
            expected_type: Expected type
            message: Custom error message
            
        Returns:
            Self for method chaining
        """
        try:
            if not isinstance(self.data, expected_type):
                error_msg = message or f"Expected {expected_type.__name__}, got {type(self.data).__name__}"
                self.errors.append(error_msg)
        except Exception as e:
            error_msg = message or f"Error checking type: {e}"
            self.errors.append(error_msg)
        
        return self
    
    def range_check(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        message: Optional[str] = None
    ) -> 'FluentValidator':
        """
        Check if numeric data is within range.
        
        Args:
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            message: Custom error message
            
        Returns:
            Self for method chaining
        """
        try:
            if not isinstance(self.data, (int, float)):
                error_msg = message or "Range check requires numeric data"
                self.errors.append(error_msg)
                return self
            
            if min_value is not None and self.data < min_value:
                error_msg = message or f"Value {self.data} is below minimum {min_value}"
                self.errors.append(error_msg)
            
            if max_value is not None and self.data > max_value:
                error_msg = message or f"Value {self.data} is above maximum {max_value}"
                self.errors.append(error_msg)
        
        except Exception as e:
            error_msg = message or f"Error checking range: {e}"
            self.errors.append(error_msg)
        
        return self
    
    def length_check(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        message: Optional[str] = None
    ) -> 'FluentValidator':
        """
        Check if data length is within range.
        
        Args:
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            message: Custom error message
            
        Returns:
            Self for method chaining
        """
        try:
            if not hasattr(self.data, '__len__'):
                error_msg = message or "Length check requires data with length"
                self.errors.append(error_msg)
                return self
            
            length = len(self.data)
            
            if min_length is not None and length < min_length:
                error_msg = message or f"Length {length} is below minimum {min_length}"
                self.errors.append(error_msg)
            
            if max_length is not None and length > max_length:
                error_msg = message or f"Length {length} is above maximum {max_length}"
                self.errors.append(error_msg)
        
        except Exception as e:
            error_msg = message or f"Error checking length: {e}"
            self.errors.append(error_msg)
        
        return self
    
    def pattern_check(self, pattern: str, message: Optional[str] = None) -> 'FluentValidator':
        """
        Check if string data matches pattern (regex).
        
        Args:
            pattern: Regular expression pattern
            message: Custom error message
            
        Returns:
            Self for method chaining
        """
        try:
            import re
            
            if not isinstance(self.data, str):
                error_msg = message or "Pattern check requires string data"
                self.errors.append(error_msg)
                return self
            
            if not re.match(pattern, self.data):
                error_msg = message or f"String '{self.data}' does not match pattern '{pattern}'"
                self.errors.append(error_msg)
        
        except Exception as e:
            error_msg = message or f"Error checking pattern: {e}"
            self.errors.append(error_msg)
        
        return self
    
    def add_rule(self, validator_func: Callable[[Any], bool], message: Optional[str] = None) -> 'FluentValidator':
        """
        Add custom validation rule.
        
        Args:
            validator_func: Function that takes data and returns True if valid
            message: Custom error message
            
        Returns:
            Self for method chaining
        """
        try:
            if not validator_func(self.data):
                error_msg = message or "Custom validation rule failed"
                self.errors.append(error_msg)
        except Exception as e:
            error_msg = message or f"Custom validation rule error: {e}"
            self.errors.append(error_msg)
        
        return self
    
    def is_valid(self) -> bool:
        """Check if data is valid (no errors)."""
        return len(self.errors) == 0
    
    def validate(self) -> 'FluentValidator':
        """
        Validate data and raise ValidationError if invalid.
        
        Returns:
            Self if valid
            
        Raises:
            ValidationError: If validation fails
        """
        if not self.is_valid():
            raise ValidationError(f"Validation failed: {'; '.join(self.errors)}")
        return self
    
    def get_errors(self) -> list[str]:
        """Get list of validation errors."""
        return self.errors.copy()
    
    def clear_errors(self) -> 'FluentValidator':
        """Clear all validation errors."""
        self.errors.clear()
        return self
    
    def set_data(self, data: Any) -> 'FluentValidator':
        """Set data to validate."""
        self.data = data
        return self
    
    def validate_field(
        self,
        field_name: str,
        field_data: Any,
        rules: list[Callable[['FluentValidator'], 'FluentValidator']]
    ) -> 'FluentValidator':
        """
        Validate a specific field with rules.
        
        Args:
            field_name: Name of field being validated
            field_data: Data for the field
            rules: List of validation rules to apply
            
        Returns:
            Self for method chaining
        """
        try:
            # Create temporary validator for field
            field_validator = FluentValidator(field_data)
            
            # Apply rules
            for rule in rules:
                rule(field_validator)
            
            # Collect errors with field prefix
            for error in field_validator.get_errors():
                self.errors.append(f"Field '{field_name}': {error}")
        
        except Exception as e:
            self.errors.append(f"Field '{field_name}' validation error: {e}")
        
        return self
    
    def validate_dict_fields(
        self,
        field_rules: dict[str, list[Callable[['FluentValidator'], 'FluentValidator']]]
    ) -> 'FluentValidator':
        """
        Validate multiple fields in a dictionary.
        
        Args:
            field_rules: Dictionary mapping field names to validation rules
            
        Returns:
            Self for method chaining
        """
        if not isinstance(self.data, dict):
            self.errors.append("Data must be a dictionary for field validation")
            return self
        
        for field_name, rules in field_rules.items():
            field_data = self.data.get(field_name)
            self.validate_field(field_name, field_data, rules)
        
        return self


# Convenience functions
def validate_data(data: Any) -> FluentValidator:
    """
    Create a fluent validator for data.
    
    Args:
        data: Data to validate
        
    Returns:
        FluentValidator instance
    """
    return FluentValidator(data)


def validate_dict(data: dict[str, Any]) -> FluentValidator:
    """
    Create a fluent validator for dictionary data.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        FluentValidator instance
    """
    return FluentValidator(data)


def validate_string(data: str) -> FluentValidator:
    """
    Create a fluent validator for string data.
    
    Args:
        data: String to validate
        
    Returns:
        FluentValidator instance
    """
    return FluentValidator(data)


def validate_numeric(data: Union[int, float]) -> FluentValidator:
    """
    Create a fluent validator for numeric data.
    
    Args:
        data: Numeric data to validate
        
    Returns:
        FluentValidator instance
    """
    return FluentValidator(data)


# Common validation rules
def is_required(field_name: str) -> Callable[[FluentValidator], FluentValidator]:
    """Create a required field rule."""
    return lambda v: v.require(field_name)


def is_type(expected_type: type) -> Callable[[FluentValidator], FluentValidator]:
    """Create a type check rule."""
    return lambda v: v.type_check(expected_type)


def is_in_range(min_val: Optional[Union[int, float]] = None, max_val: Optional[Union[int, float]] = None) -> Callable[[FluentValidator], FluentValidator]:
    """Create a range check rule."""
    return lambda v: v.range_check(min_val, max_val)


def has_length(min_len: Optional[int] = None, max_len: Optional[int] = None) -> Callable[[FluentValidator], FluentValidator]:
    """Create a length check rule."""
    return lambda v: v.length_check(min_len, max_len)


def matches_pattern(pattern: str) -> Callable[[FluentValidator], FluentValidator]:
    """Create a pattern check rule."""
    return lambda v: v.pattern_check(pattern)


__all__ = [
    "FluentValidator",
    "validate_data",
    "validate_dict",
    "validate_string",
    "validate_numeric",
    "is_required",
    "is_type",
    "is_in_range",
    "has_length",
    "matches_pattern",
]
