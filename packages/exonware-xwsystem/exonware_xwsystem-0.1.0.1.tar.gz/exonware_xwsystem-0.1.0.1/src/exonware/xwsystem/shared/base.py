#exonware/xwsystem/shared/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Shared base classes (merged from the former core module).
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from .contracts import CoreMode, CorePriority, CoreState


class ACoreBase(ABC):
    """Abstract base class for core functionality."""

    def __init__(self, mode: CoreMode = CoreMode.DEVELOPMENT):
        """
        Initialize core base.

        Args:
            mode: Core operation mode
        """
        self.mode = mode
        self.state = CoreState.INITIALIZING
        self._dependencies: list[str] = []
        self._resources: dict[str, Any] = {}

    @abstractmethod
    def initialize(self) -> None:
        """Initialize core functionality."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown core functionality."""
        pass

    @abstractmethod
    def get_state(self) -> CoreState:
        """Get current core state."""
        pass

    @abstractmethod
    def set_state(self, state: CoreState) -> None:
        """Set core state."""
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if core is initialized."""
        pass

    @abstractmethod
    def is_shutdown(self) -> bool:
        """Check if core is shutdown."""
        pass

    @abstractmethod
    def add_dependency(self, dependency: str) -> None:
        """Add core dependency."""
        pass

    @abstractmethod
    def remove_dependency(self, dependency: str) -> None:
        """Remove core dependency."""
        pass

    @abstractmethod
    def get_dependencies(self) -> list[str]:
        """Get all dependencies."""
        pass

    @abstractmethod
    def check_dependencies(self) -> bool:
        """Check if all dependencies are satisfied."""
        pass


class AResourceManagerBase(ABC):
    """Abstract base class for resource management."""

    def __init__(self, max_resources: int = 100):
        """
        Initialize resource manager.

        Args:
            max_resources: Maximum number of resources
        """
        self.max_resources = max_resources
        self._resources: dict[str, Any] = {}
        self._resource_locks: dict[str, bool] = {}

    @abstractmethod
    def acquire_resource(
        self, resource_id: str, priority: CorePriority = CorePriority.NORMAL
    ) -> Any:
        """Acquire resource."""
        pass

    @abstractmethod
    def release_resource(self, resource_id: str) -> None:
        """Release resource."""
        pass

    @abstractmethod
    def is_resource_available(self, resource_id: str) -> bool:
        """Check if resource is available."""
        pass

    @abstractmethod
    def get_resource_count(self) -> int:
        """Get number of managed resources."""
        pass

    @abstractmethod
    def list_resources(self) -> list[str]:
        """List all resource IDs."""
        pass

    @abstractmethod
    def cleanup_resources(self) -> None:
        """Cleanup all resources."""
        pass


class AConfigurationBase(ABC):
    """Abstract base class for core configuration."""

    def __init__(self):
        """Initialize configuration base."""
        self._config: dict[str, Any] = {}
        self._defaults: dict[str, Any] = {}

    @abstractmethod
    def load_config(self, config_data: dict[str, Any]) -> None:
        """Load configuration data."""
        pass

    @abstractmethod
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass

    @abstractmethod
    def set_config_value(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate configuration."""
        pass

    @abstractmethod
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        pass

    @abstractmethod
    def export_config(self) -> dict[str, Any]:
        """Export configuration as dictionary."""
        pass


class AValidationBase(ABC):
    """Abstract base class for core validation."""

    @abstractmethod
    def validate_input(self, data: Any) -> bool:
        """Validate input data."""
        pass

    @abstractmethod
    def validate_output(self, data: Any) -> bool:
        """Validate output data."""
        pass

    @abstractmethod
    def validate_operation(self, operation: str, **kwargs) -> bool:
        """Validate operation."""
        pass

    @abstractmethod
    def get_validation_errors(self) -> list[str]:
        """Get validation errors."""
        pass

    @abstractmethod
    def clear_validation_errors(self) -> None:
        """Clear validation errors."""
        pass


class AOperationBase(ABC):
    """Abstract base class for core operations."""

    def __init__(self, timeout: Optional[int] = None):
        """
        Initialize operation base.

        Args:
            timeout: Operation timeout in seconds
        """
        self.timeout = timeout
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute operation."""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Check if operation is running."""
        pass

    @abstractmethod
    def is_completed(self) -> bool:
        """Check if operation is completed."""
        pass

    @abstractmethod
    def is_failed(self) -> bool:
        """Check if operation failed."""
        pass

    @abstractmethod
    def get_duration(self) -> Optional[float]:
        """Get operation duration."""
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Cancel operation."""
        pass

    @abstractmethod
    def get_result(self) -> Any:
        """Get operation result."""
        pass

    @abstractmethod
    def get_error(self) -> Optional[Exception]:
        """Get operation error."""
        pass


class BaseCore(ACoreBase):
    """Base implementation of core functionality."""

    def __init__(self, mode: CoreMode = CoreMode.DEVELOPMENT):
        """Initialize base core."""
        super().__init__(mode)
        self._initialized = False
        self._shutdown = False

    def initialize(self) -> None:
        """Initialize core functionality."""
        self.state = CoreState.INITIALIZING
        self._initialized = True
        self.state = CoreState.INITIALIZED

    def shutdown(self) -> None:
        """Shutdown core functionality."""
        self.state = CoreState.SHUTTING_DOWN
        self._shutdown = True
        self.state = CoreState.SHUTDOWN

    def get_state(self) -> CoreState:
        """Get current core state."""
        return self.state

    def set_state(self, state: CoreState) -> None:
        """Set core state."""
        self.state = state

    def is_initialized(self) -> bool:
        """Check if core is initialized."""
        return self._initialized

    def is_shutdown(self) -> bool:
        """Check if core is shutdown."""
        return self._shutdown

    def add_dependency(self, dependency: str) -> None:
        """Add core dependency."""
        if dependency not in self._dependencies:
            self._dependencies.append(dependency)

    def remove_dependency(self, dependency: str) -> None:
        """Remove core dependency."""
        if dependency in self._dependencies:
            self._dependencies.remove(dependency)

    def get_dependencies(self) -> list[str]:
        """Get all dependencies."""
        return self._dependencies.copy()

    def check_dependencies(self) -> bool:
        """Check if all dependencies are satisfied."""
        # Basic implementation - can be overridden
        return True

