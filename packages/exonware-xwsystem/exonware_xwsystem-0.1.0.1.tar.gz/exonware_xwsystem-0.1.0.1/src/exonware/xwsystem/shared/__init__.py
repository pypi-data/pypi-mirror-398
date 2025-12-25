#!/usr/bin/env python3
#exonware/xwsystem/shared/__init__.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 10-Sep-2025

Shared types and utilities for XWSystem modules.
"""

from .defs import (
    AuthType,
    CloneMode,
    CoreMode,
    CorePriority,
    CoreState,
    DataType,
    LogLevel,
    LockType,
    OperationResult,
    PathType,
    PerformanceLevel,
    ValidationLevel,
)
from .base import (
    AConfigurationBase,
    ACoreBase,
    AOperationBase,
    AResourceManagerBase,
    AValidationBase,
    BaseCore,
)
from .contracts import (
    ICloneable,
    IComparable,
    IContainer,
    ICore,
    IID,
    IFactory,
    IMetadata,
    INative,
    IStringable,
    ILifecycle,
    IIterable,
)
from .errors import (
    CoreConfigurationError,
    CoreDependencyError,
    CoreError,
    CoreInitializationError,
    CoreOperationError,
    CorePermissionError,
    CoreResourceError,
    CoreShutdownError,
    CoreStateError,
    CoreTimeoutError,
    CoreValidationError,
)

__all__ = [
    # Shared enums
    "ValidationLevel",
    "PerformanceLevel",
    "AuthType",
    "LockType",
    "PathType",
    "LogLevel",
    "OperationResult",
    "DataType",
    "CloneMode",
    "CoreState",
    "CoreMode",
    "CorePriority",
    # Base classes
    "ACoreBase",
    "AResourceManagerBase",
    "AConfigurationBase",
    "AValidationBase",
    "AOperationBase",
    "BaseCore",
    # Contracts
    "IID",
    "IStringable",
    "INative",
    "ICloneable",
    "IComparable",
    "IIterable",
    "IContainer",
    "IMetadata",
    "ILifecycle",
    "IFactory",
    "ICore",
    # Errors
    "CoreError",
    "CoreInitializationError",
    "CoreShutdownError",
    "CoreStateError",
    "CoreDependencyError",
    "CoreConfigurationError",
    "CoreResourceError",
    "CoreTimeoutError",
    "CorePermissionError",
    "CoreValidationError",
    "CoreOperationError",
]
