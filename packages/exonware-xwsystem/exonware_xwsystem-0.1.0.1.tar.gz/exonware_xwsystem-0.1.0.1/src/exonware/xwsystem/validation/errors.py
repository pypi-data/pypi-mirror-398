#exonware/xwsystem/validation/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Validation module errors - exception classes for validation functionality.
"""


class ValidationError(Exception):
    """Base exception for validation errors."""
    pass


class PathValidationError(ValidationError):
    """Raised when path validation fails."""
    pass


class DepthValidationError(ValidationError):
    """Raised when depth validation fails."""
    pass


class MemoryValidationError(ValidationError):
    """Raised when memory validation fails."""
    pass


class DataValidationError(ValidationError):
    """Raised when data validation fails."""
    pass


class TypeValidationError(ValidationError):
    """Raised when type validation fails."""
    pass


class ValueValidationError(ValidationError):
    """Raised when value validation fails."""
    pass


class RangeValidationError(ValidationError):
    """Raised when range validation fails."""
    pass


class FormatValidationError(ValidationError):
    """Raised when format validation fails."""
    pass


class PatternValidationError(ValidationError):
    """Raised when pattern validation fails."""
    pass


class ConstraintValidationError(ValidationError):
    """Raised when constraint validation fails."""
    pass


class SchemaValidationError(ValidationError):
    """Raised when schema validation fails."""
    pass


class FieldValidationError(ValidationError):
    """Raised when field validation fails."""
    pass


class RequiredFieldError(FieldValidationError):
    """Raised when required field is missing."""
    pass


class OptionalFieldError(FieldValidationError):
    """Raised when optional field validation fails."""
    pass


class DeclarativeValidationError(ValidationError):
    """Raised when declarative validation fails."""
    pass


class TypeSafetyError(ValidationError):
    """Raised when type safety check fails."""
    pass


class TypeCoercionError(ValidationError):
    """Raised when type coercion fails."""
    pass


class ValidationRuleError(ValidationError):
    """Raised when validation rule fails."""
    pass


class ValidationContextError(ValidationError):
    """Raised when validation context is invalid."""
    pass


class ValidationConfigurationError(ValidationError):
    """Raised when validation configuration is invalid."""
    pass
