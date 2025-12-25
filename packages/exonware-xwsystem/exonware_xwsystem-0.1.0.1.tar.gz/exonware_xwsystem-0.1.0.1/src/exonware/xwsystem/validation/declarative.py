"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Pydantic-style declarative validation with type hints and automatic coercion.
"""

import inspect
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union, get_type_hints, get_origin, get_args
from datetime import datetime, date
from pathlib import Path

from ..config.logging_setup import get_logger

logger = get_logger("xwsystem.validation.declarative")


class ValidationError(Exception):
    """Raised when validation fails."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, value: Any = None):
        super().__init__(message)
        self.field_name = field_name
        self.value = value
        self.errors = []
    
    def add_error(self, field: str, message: str, value: Any = None):
        """Add a field-specific error."""
        self.errors.append({
            'field': field,
            'message': message,
            'value': value
        })
    
    def __str__(self):
        if self.errors:
            error_msgs = []
            for error in self.errors:
                error_msgs.append(f"{error['field']}: {error['message']}")
            return f"Validation failed: {'; '.join(error_msgs)}"
        return super().__str__()


@dataclass
class Field:
    """Field configuration for validation and metadata."""
    
    default: Any = None
    default_factory: Optional[callable] = None
    alias: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    
    # Validation constraints
    gt: Optional[Union[int, float]] = None  # Greater than
    ge: Optional[Union[int, float]] = None  # Greater than or equal
    lt: Optional[Union[int, float]] = None  # Less than
    le: Optional[Union[int, float]] = None  # Less than or equal
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum: Optional[list[Any]] = None
    
    # String validation
    strip_whitespace: bool = True
    to_lower: bool = False
    to_upper: bool = False
    
    # Advanced constraints
    multiple_of: Optional[Union[int, float]] = None
    allow_inf_nan: bool = True
    
    # Metadata
    examples: Optional[list[Any]] = None
    deprecated: bool = False
    
    def __post_init__(self):
        """Validate field configuration."""
        if self.default is not None and self.default_factory is not None:
            raise ValueError("Cannot specify both default and default_factory")
        
        if self.gt is not None and self.ge is not None:
            raise ValueError("Cannot specify both gt and ge")
        
        if self.lt is not None and self.le is not None:
            raise ValueError("Cannot specify both lt and le")


class ModelMeta(type):
    """Metaclass for XModel to handle type hints and field processing."""
    
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Get type hints from the class
        annotations = namespace.get('__annotations__', {})
        
        # Process fields and create field registry
        fields = {}
        defaults = {}
        
        for field_name, field_type in annotations.items():
            if field_name.startswith('_'):
                continue
                
            # Check if there's a Field definition
            field_config = namespace.get(field_name)
            if isinstance(field_config, Field):
                fields[field_name] = field_config
                if field_config.default is not None:
                    defaults[field_name] = field_config.default
                elif field_config.default_factory is not None:
                    defaults[field_name] = field_config.default_factory
            else:
                # Create default Field
                fields[field_name] = Field(default=field_config)
                if field_config is not None:
                    defaults[field_name] = field_config
        
        # Store metadata on the class
        namespace['__fields__'] = fields
        namespace['__defaults__'] = defaults
        namespace['__field_types__'] = annotations
        
        return super().__new__(mcs, name, bases, namespace)


class XModel(metaclass=ModelMeta):
    """
    Base class for declarative validation models (Pydantic-style).
    
    Features:
    - Type hint-based validation
    - Automatic type coercion
    - Field constraints and validation
    - JSON schema generation
    - Serialization/deserialization
    - IDE support and type checking
    """
    
    def __init__(self, **data):
        """Initialize model with data validation and coercion."""
        self.__dict__.update(self._validate_and_coerce(data))
    
    def _validate_and_coerce(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate and coerce input data."""
        validated = {}
        errors = ValidationError("Validation failed")
        
        # Get all field information
        fields = getattr(self.__class__, '__fields__', {})
        field_types = getattr(self.__class__, '__field_types__', {})
        defaults = getattr(self.__class__, '__defaults__', {})
        
        # Process each field
        for field_name, field_type in field_types.items():
            field_config = fields.get(field_name, Field())
            alias = field_config.alias or field_name
            
            # Get value from data
            if alias in data:
                value = data[alias]
            elif field_name in data:
                value = data[field_name]
            elif field_config.default is not None:
                value = field_config.default
            elif field_config.default_factory is not None:
                value = field_config.default_factory()
            elif field_name in defaults:
                default_val = defaults[field_name]
                value = default_val() if callable(default_val) else default_val
            else:
                # Check if field is optional
                if self._is_optional(field_type):
                    value = None
                else:
                    errors.add_error(field_name, "Field is required", None)
                    continue
            
            # Validate and coerce value
            try:
                validated_value = self._validate_field(field_name, value, field_type, field_config)
                validated[field_name] = validated_value
            except ValidationError as e:
                errors.add_error(field_name, str(e), value)
        
        # Check for extra fields
        all_field_names = set(field_types.keys())
        all_aliases = {fields[name].alias or name for name in all_field_names}
        provided_fields = set(data.keys())
        extra_fields = provided_fields - all_field_names - all_aliases
        
        if extra_fields:
            for extra_field in extra_fields:
                errors.add_error(extra_field, "Extra field not allowed", data[extra_field])
        
        if errors.errors:
            raise errors
        
        return validated
    
    def _validate_field(self, field_name: str, value: Any, field_type: type, field_config: Field) -> Any:
        """Validate and coerce a single field."""
        if value is None:
            if self._is_optional(field_type):
                return None
            else:
                raise ValidationError(f"None is not allowed for non-optional field")
        
        # Get the actual type (handle Optional, Union, etc.)
        actual_type = self._get_actual_type(field_type)
        
        # Type coercion
        coerced_value = self._coerce_type(value, actual_type, field_name)
        
        # Apply field constraints
        self._apply_constraints(coerced_value, field_config, field_name)
        
        return coerced_value
    
    @classmethod
    def _is_optional(cls, field_type: type) -> bool:
        """Check if field type is Optional."""
        origin = get_origin(field_type)
        if origin is Union:
            args = get_args(field_type)
            return type(None) in args
        return False
    
    @classmethod
    def _get_actual_type(cls, field_type: type) -> type:
        """Get actual type from Optional/Union types."""
        origin = get_origin(field_type)
        if origin is Union:
            args = get_args(field_type)
            # Filter out NoneType for Optional
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                return non_none_args[0]
            else:
                # Multiple non-None types, return the first one for now
                return non_none_args[0] if non_none_args else field_type
        return field_type
    
    def _coerce_type(self, value: Any, target_type: type, field_name: str) -> Any:
        """Coerce value to target type."""
        if isinstance(value, target_type):
            return value
        
        # String coercion
        if target_type == str:
            return str(value)
        
        # Integer coercion
        elif target_type == int:
            if isinstance(value, str):
                try:
                    return int(value)
                except ValueError:
                    try:
                        return int(float(value))  # Handle "42.0" -> 42
                    except ValueError:
                        raise ValidationError(f"Cannot convert '{value}' to int")
            elif isinstance(value, float):
                return int(value)
            elif isinstance(value, bool):
                return int(value)
            else:
                raise ValidationError(f"Cannot convert {type(value).__name__} to int")
        
        # Float coercion
        elif target_type == float:
            if isinstance(value, (str, int)):
                try:
                    return float(value)
                except ValueError:
                    raise ValidationError(f"Cannot convert '{value}' to float")
            elif isinstance(value, bool):
                return float(value)
            else:
                raise ValidationError(f"Cannot convert {type(value).__name__} to float")
        
        # Boolean coercion
        elif target_type == bool:
            if isinstance(value, str):
                lower_val = value.lower()
                if lower_val in ('true', '1', 'yes', 'on', 'y'):
                    return True
                elif lower_val in ('false', '0', 'no', 'off', 'n', ''):
                    return False
                else:
                    raise ValidationError(f"Cannot convert '{value}' to bool")
            elif isinstance(value, (int, float)):
                return bool(value)
            else:
                return bool(value)
        
        # List coercion
        elif target_type == list or (hasattr(target_type, '__origin__') and target_type.__origin__ is list):
            if isinstance(value, (list, tuple)):
                return list(value)
            elif isinstance(value, str):
                # Try to parse as JSON array
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    pass
                # Split by comma as fallback
                return [item.strip() for item in value.split(',') if item.strip()]
            else:
                raise ValidationError(f"Cannot convert {type(value).__name__} to list")
        
        # dict coercion
        elif target_type == dict or (hasattr(target_type, '__origin__') and target_type.__origin__ is dict):
            if isinstance(value, dict):
                return value
            elif isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    pass
                raise ValidationError(f"Cannot convert string '{value}' to dict")
            else:
                raise ValidationError(f"Cannot convert {type(value).__name__} to dict")
        
        # DateTime coercion
        elif target_type == datetime:
            if isinstance(value, str):
                # Try common datetime formats
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S.%fZ',
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                raise ValidationError(f"Cannot parse datetime '{value}'")
            elif isinstance(value, (int, float)):
                return datetime.fromtimestamp(value)
            else:
                raise ValidationError(f"Cannot convert {type(value).__name__} to datetime")
        
        # Date coercion
        elif target_type == date:
            if isinstance(value, str):
                try:
                    return datetime.strptime(value, '%Y-%m-%d').date()
                except ValueError:
                    raise ValidationError(f"Cannot parse date '{value}'")
            elif isinstance(value, datetime):
                return value.date()
            else:
                raise ValidationError(f"Cannot convert {type(value).__name__} to date")
        
        # Path coercion
        elif target_type == Path:
            if isinstance(value, (str, Path)):
                return Path(value)
            else:
                raise ValidationError(f"Cannot convert {type(value).__name__} to Path")
        
        # Enum coercion
        elif inspect.isclass(target_type) and issubclass(target_type, Enum):
            if isinstance(value, target_type):
                return value
            elif isinstance(value, str):
                try:
                    return target_type[value]
                except KeyError:
                    try:
                        return target_type(value)
                    except ValueError:
                        valid_values = [e.value for e in target_type]
                        raise ValidationError(f"Invalid enum value '{value}'. Valid values: {valid_values}")
            else:
                try:
                    return target_type(value)
                except ValueError:
                    raise ValidationError(f"Cannot convert {type(value).__name__} to {target_type.__name__}")
        
        # Default: try direct conversion
        else:
            try:
                return target_type(value)
            except (TypeError, ValueError) as e:
                raise ValidationError(f"Cannot convert {type(value).__name__} to {target_type.__name__}: {e}")
    
    def _apply_constraints(self, value: Any, field_config: Field, field_name: str) -> None:
        """Apply field constraints validation."""
        # Numeric constraints
        if isinstance(value, (int, float)):
            if field_config.gt is not None and value <= field_config.gt:
                raise ValidationError(f"Value must be greater than {field_config.gt}")
            if field_config.ge is not None and value < field_config.ge:
                raise ValidationError(f"Value must be greater than or equal to {field_config.ge}")
            if field_config.lt is not None and value >= field_config.lt:
                raise ValidationError(f"Value must be less than {field_config.lt}")
            if field_config.le is not None and value > field_config.le:
                raise ValidationError(f"Value must be less than or equal to {field_config.le}")
            if field_config.multiple_of is not None and value % field_config.multiple_of != 0:
                raise ValidationError(f"Value must be a multiple of {field_config.multiple_of}")
            if not field_config.allow_inf_nan and not (value != value or abs(value) == float('inf')):
                # Check for NaN or infinity
                import math
                if math.isnan(value) or math.isinf(value):
                    raise ValidationError("Infinite and NaN values are not allowed")
        
        # String constraints
        if isinstance(value, str):
            if field_config.min_length is not None and len(value) < field_config.min_length:
                raise ValidationError(f"String length must be at least {field_config.min_length}")
            if field_config.max_length is not None and len(value) > field_config.max_length:
                raise ValidationError(f"String length must not exceed {field_config.max_length}")
            if field_config.pattern is not None:
                import re
                if not re.match(field_config.pattern, value):
                    raise ValidationError(f"String does not match pattern: {field_config.pattern}")
        
        # Collection constraints
        if isinstance(value, (list, tuple, dict, set)):
            if field_config.min_length is not None and len(value) < field_config.min_length:
                raise ValidationError(f"Collection length must be at least {field_config.min_length}")
            if field_config.max_length is not None and len(value) > field_config.max_length:
                raise ValidationError(f"Collection length must not exceed {field_config.max_length}")
        
        # Enum constraint
        if field_config.enum is not None and value not in field_config.enum:
            raise ValidationError(f"Value must be one of: {field_config.enum}")
    
    @classmethod
    def model_validate(cls, data: dict[str, Any]) -> 'XModel':
        """Create and validate model from dictionary data."""
        return cls(**data)
    
    @classmethod
    def model_validate_json(cls, json_data: str) -> 'XModel':
        """Create and validate model from JSON string."""
        data = json.loads(json_data)
        return cls.model_validate(data)
    
    def model_dump(self, 
                   include: Optional[set] = None, 
                   exclude: Optional[set] = None,
                   by_alias: bool = False) -> dict[str, Any]:
        """Export model to dictionary."""
        data = {}
        fields = getattr(self.__class__, '__fields__', {})
        
        for field_name, value in self.__dict__.items():
            if include is not None and field_name not in include:
                continue
            if exclude is not None and field_name in exclude:
                continue
            
            field_config = fields.get(field_name, Field())
            key = field_config.alias if by_alias and field_config.alias else field_name
            
            # Convert complex types to serializable forms
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, date):
                data[key] = value.isoformat()
            elif isinstance(value, Path):
                data[key] = str(value)
            elif isinstance(value, Enum):
                data[key] = value.value
            elif hasattr(value, 'model_dump'):
                data[key] = value.model_dump()
            else:
                data[key] = value
        
        return data
    
    def model_dump_json(self, **kwargs) -> str:
        """Export model to JSON string."""
        data = self.model_dump(**kwargs)
        return json.dumps(data, default=str)
    
    @classmethod
    def model_json_schema(cls) -> dict[str, Any]:
        """Generate JSON Schema for the model."""
        schema = {
            "type": "object",
            "title": cls.__name__,
            "properties": {},
            "required": []
        }
        
        fields = getattr(cls, '__fields__', {})
        field_types = getattr(cls, '__field_types__', {})
        
        for field_name, field_type in field_types.items():
            field_config = fields.get(field_name, Field())
            
            # Determine if field is required
            if not cls._is_optional(field_type) and field_config.default is None and field_config.default_factory is None:
                schema["required"].append(field_name)
            
            # Generate property schema
            prop_schema = cls._type_to_json_schema(field_type, field_config)
            
            # Add field metadata
            if field_config.title:
                prop_schema["title"] = field_config.title
            if field_config.description:
                prop_schema["description"] = field_config.description
            if field_config.examples:
                prop_schema["examples"] = field_config.examples
            if field_config.deprecated:
                prop_schema["deprecated"] = True
            
            schema["properties"][field_name] = prop_schema
        
        return schema
    
    @classmethod
    def _type_to_json_schema(cls, field_type: type, field_config: Field) -> dict[str, Any]:
        """Convert Python type to JSON Schema property."""
        # Handle Optional types
        if cls._is_optional(field_type):
            actual_type = cls._get_actual_type(field_type)
            schema = cls._type_to_json_schema(actual_type, field_config)
            schema["nullable"] = True
            return schema
        
        # Basic types
        if field_type == str:
            schema = {"type": "string"}
            if field_config.min_length is not None:
                schema["minLength"] = field_config.min_length
            if field_config.max_length is not None:
                schema["maxLength"] = field_config.max_length
            if field_config.pattern:
                schema["pattern"] = field_config.pattern
            if field_config.enum:
                schema["enum"] = field_config.enum
            return schema
        
        elif field_type == int:
            schema = {"type": "integer"}
            if field_config.gt is not None:
                schema["exclusiveMinimum"] = field_config.gt
            if field_config.ge is not None:
                schema["minimum"] = field_config.ge
            if field_config.lt is not None:
                schema["exclusiveMaximum"] = field_config.lt
            if field_config.le is not None:
                schema["maximum"] = field_config.le
            if field_config.multiple_of is not None:
                schema["multipleOf"] = field_config.multiple_of
            return schema
        
        elif field_type == float:
            schema = {"type": "number"}
            if field_config.gt is not None:
                schema["exclusiveMinimum"] = field_config.gt
            if field_config.ge is not None:
                schema["minimum"] = field_config.ge
            if field_config.lt is not None:
                schema["exclusiveMaximum"] = field_config.lt
            if field_config.le is not None:
                schema["maximum"] = field_config.le
            if field_config.multiple_of is not None:
                schema["multipleOf"] = field_config.multiple_of
            return schema
        
        elif field_type == bool:
            return {"type": "boolean"}
        
        elif field_type == list or (hasattr(field_type, '__origin__') and field_type.__origin__ is list):
            schema = {"type": "array"}
            if field_config.min_length is not None:
                schema["minItems"] = field_config.min_length
            if field_config.max_length is not None:
                schema["maxItems"] = field_config.max_length
            return schema
        
        elif field_type == dict or (hasattr(field_type, '__origin__') and field_type.__origin__ is dict):
            return {"type": "object"}
        
        elif field_type in (datetime, date):
            return {"type": "string", "format": "date-time" if field_type == datetime else "date"}
        
        elif field_type == Path:
            return {"type": "string", "format": "path"}
        
        elif inspect.isclass(field_type) and issubclass(field_type, Enum):
            enum_values = [e.value for e in field_type]
            return {"enum": enum_values}
        
        else:
            # Default to string for unknown types
            return {"type": "string"}
    
    def __repr__(self) -> str:
        """String representation of the model."""
        fields_str = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({fields_str})"
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__
