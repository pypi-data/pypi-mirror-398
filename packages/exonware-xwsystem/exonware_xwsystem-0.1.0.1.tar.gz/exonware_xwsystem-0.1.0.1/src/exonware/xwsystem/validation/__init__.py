"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

XSystem Validation Package

Declarative validation with type hints, automatic coercion, and Pydantic-style models.
"""

from .declarative import XModel, Field, ValidationError
from .type_safety import validate_untrusted_data

__all__ = [
    "XModel",
    "Field", 
    "ValidationError",
    "validate_untrusted_data",
]
