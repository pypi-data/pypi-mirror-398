#exonware/xwsystem/shared/contracts.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 10, 2025

Shared protocol interfaces (merged from the former core module).
"""

from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional, Union

from .defs import CloneMode, CoreMode, CorePriority, CoreState, DataType


# ============================================================================
# CORE IDENTITY INTERFACES
# ============================================================================


class IID(ABC):
    """
    Interface for objects that have unique identification.

    Enforces consistent ID management across XWSystem components.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Get the primary identifier.

        Returns:
            Primary ID string
        """
        pass

    @property
    @abstractmethod
    def uid(self) -> str:
        """
        Get the unique identifier (UUID).

        Returns:
            UUID string
        """
        pass

    @abstractmethod
    def generate_id(self) -> str:
        """
        Generate a new ID.

        Returns:
            New ID string
        """
        pass

    @abstractmethod
    def validate_id(self, id_value: str) -> bool:
        """
        Validate an ID format.

        Args:
            id_value: ID to validate

        Returns:
            True if valid
        """
        pass

    @abstractmethod
    def is_same_id(self, other: "IID") -> bool:
        """
        Check if this object has the same ID as another.

        Args:
            other: Another IID object

        Returns:
            True if same ID
        """
        pass


# ============================================================================
# NATIVE DATA CONVERSION INTERFACES
# ============================================================================


class IStringable(ABC):
    """
    Interface for objects that can convert to/from string representation.

    Enforces consistent string conversion behavior across XWSystem.
    """

    @abstractmethod
    def to_string(self) -> str:
        """
        Convert object to string representation.

        Returns:
            String representation of the object
        """
        pass

    @abstractmethod
    def from_string(self, string: str) -> bool:
        """
        Initialize object from string representation.

        Args:
            string: String representation to parse

        Returns:
            True if parsing was successful, False otherwise
        """
        pass


class INative(ABC):
    """
    Interface for objects that can convert to/from native Python types.

    Enforces consistent native data conversion across XWSystem.
    """

    @abstractmethod
    def to_native(self) -> Any:
        """
        Convert to native Python object.

        Returns:
            Native Python object (dict, list, str, int, float, bool, etc.)
        """
        pass

    @abstractmethod
    def from_native(self, data: Any) -> "INative":
        """
        Create from native Python object.

        Args:
            data: Native Python object

        Returns:
            New instance created from native data
        """
        pass

    @abstractmethod
    def is_native_compatible(self, data: Any) -> bool:
        """
        Check if data is compatible with native conversion.

        Args:
            data: Data to check

        Returns:
            True if compatible
        """
        pass

    @abstractmethod
    def get_native_type(self) -> DataType:
        """
        Get the native data type.

        Returns:
            DataType enum value
        """
        pass


# ============================================================================
# CLONING INTERFACES
# ============================================================================


class ICloneable(ABC):
    """
    Interface for objects that can be cloned.

    Enforces consistent cloning behavior across XWSystem.
    """

    @abstractmethod
    def clone(self, mode: CloneMode = CloneMode.DEEP) -> "ICloneable":
        """
        Create a clone of this object.

        Args:
            mode: Cloning mode

        Returns:
            Cloned object
        """
        pass

    @abstractmethod
    def deep_clone(self) -> "ICloneable":
        """
        Create a deep clone.

        Returns:
            Deep cloned object
        """
        pass

    @abstractmethod
    def shallow_clone(self) -> "ICloneable":
        """
        Create a shallow clone.

        Returns:
            Shallow cloned object
        """
        pass

    @abstractmethod
    def reference_clone(self) -> "ICloneable":
        """
        Create a reference clone (same object, different reference).

        Returns:
            Reference cloned object
        """
        pass

    @abstractmethod
    def is_cloneable(self, mode: CloneMode = CloneMode.DEEP) -> bool:
        """
        Check if object can be cloned in given mode.

        Args:
            mode: Cloning mode to check

        Returns:
            True if cloneable
        """
        pass


# ============================================================================
# COMPARISON INTERFACES
# ============================================================================


class IComparable(ABC):
    """
    Interface for objects that can be compared.

    Enforces consistent comparison behavior across XWSystem.
    """

    @abstractmethod
    def equals(self, other: Any) -> bool:
        """
        Check if this object equals another.

        Args:
            other: Object to compare

        Returns:
            True if equal
        """
        pass

    @abstractmethod
    def compare_to(self, other: Any) -> int:
        """
        Compare this object to another.

        Args:
            other: Object to compare

        Returns:
            -1 if less than, 0 if equal, 1 if greater than
        """
        pass

    @abstractmethod
    def hash_code(self) -> int:
        """
        Get hash code for this object.

        Returns:
            Hash code
        """
        pass

    @abstractmethod
    def is_comparable(self, other: Any) -> bool:
        """
        Check if this object can be compared to another.

        Args:
            other: Object to check

        Returns:
            True if comparable
        """
        pass


# ============================================================================
# ITERATION INTERFACES
# ============================================================================


class IIterable(ABC):
    """
    Interface for objects that can be iterated.

    Enforces consistent iteration behavior across XWSystem.
    """

    @abstractmethod
    def __iter__(self) -> Iterator[Any]:
        """
        Get iterator for this object.

        Returns:
            Iterator
        """
        pass

    @abstractmethod
    def __len__(self) -> int:
        """
        Get length of this object.

        Returns:
            Length
        """
        pass

    @abstractmethod
    def __contains__(self, item: Any) -> bool:
        """
        Check if object contains item.

        Args:
            item: Item to check

        Returns:
            True if contains
        """
        pass

    @abstractmethod
    def is_iterable(self) -> bool:
        """
        Check if object is iterable.

        Returns:
            True if iterable
        """
        pass

    @abstractmethod
    def get_iterator_type(self) -> str:
        """
        Get the type of iterator this object provides.

        Returns:
            Iterator type name
        """
        pass


# ============================================================================
# CONTAINER INTERFACES
# ============================================================================


class IContainer(ABC):
    """
    Interface for objects that act as containers.

    Enforces consistent container behavior across XWSystem.
    """

    @abstractmethod
    def add(self, item: Any) -> bool:
        """
        Add item to container.

        Args:
            item: Item to add

        Returns:
            True if added successfully
        """
        pass

    @abstractmethod
    def remove(self, item: Any) -> bool:
        """
        Remove item from container.

        Args:
            item: Item to remove

        Returns:
            True if removed successfully
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clear all items from container.
        """
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        """
        Check if container is empty.

        Returns:
            True if empty
        """
        pass

    @abstractmethod
    def size(self) -> int:
        """
        Get size of container.

        Returns:
            Number of items
        """
        pass

    @abstractmethod
    def contains(self, item: Any) -> bool:
        """
        Check if container contains item.

        Args:
            item: Item to check

        Returns:
            True if contains
        """
        pass


# ============================================================================
# METADATA INTERFACES
# ============================================================================


class IMetadata(ABC):
    """
    Interface for objects that have metadata.

    Enforces consistent metadata handling across XWSystem.
    """

    @abstractmethod
    def get_metadata(self, key: str) -> Any:
        """
        Get metadata value by key.

        Args:
            key: Metadata key

        Returns:
            Metadata value
        """
        pass

    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata value by key.

        Args:
            key: Metadata key
            value: Metadata value
        """
        pass

    @abstractmethod
    def has_metadata(self, key: str) -> bool:
        """
        Check if metadata key exists.

        Args:
            key: Metadata key

        Returns:
            True if exists
        """
        pass

    @abstractmethod
    def remove_metadata(self, key: str) -> bool:
        """
        Remove metadata by key.

        Args:
            key: Metadata key

        Returns:
            True if removed
        """
        pass

    @abstractmethod
    def get_all_metadata(self) -> dict[str, Any]:
        """
        Get all metadata.

        Returns:
            Dictionary of all metadata
        """
        pass

    @abstractmethod
    def clear_metadata(self) -> None:
        """
        Clear all metadata.
        """
        pass


# ============================================================================
# LIFECYCLE INTERFACES
# ============================================================================


class ILifecycle(ABC):
    """
    Interface for objects with lifecycle management.

    Enforces consistent lifecycle behavior across XWSystem.
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the object."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Start the object."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the object."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the object."""
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """
        Check if object is initialized.

        Returns:
            True if initialized
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """
        Check if object is running.

        Returns:
            True if running
        """
        pass

    @abstractmethod
    def get_state(self) -> str:
        """
        Get current state.

        Returns:
            Current state string
        """
        pass


# ============================================================================
# FACTORY INTERFACES
# ============================================================================


class IFactory(ABC):
    """
    Interface for factory objects.

    Enforces consistent factory behavior across XWSystem.
    """

    @abstractmethod
    def create(self, *args, **kwargs) -> Any:
        """
        Create a new instance.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            New instance
        """
        pass

    @abstractmethod
    def create_from_config(self, config: dict[str, Any]) -> Any:
        """
        Create instance from configuration.

        Args:
            config: Configuration dictionary

        Returns:
            New instance
        """
        pass

    @abstractmethod
    def get_supported_types(self) -> list[str]:
        """
        Get list of supported types.

        Returns:
            List of supported type names
        """
        pass

    @abstractmethod
    def can_create(self, type_name: str) -> bool:
        """
        Check if factory can create type.

        Args:
            type_name: Type name to check

        Returns:
            True if can create
        """
        pass


# ============================================================================
# CORE INTERFACE
# ============================================================================


class ICore(ABC):
    """Interface for core functionality."""

    @property
    @abstractmethod
    def mode(self) -> CoreMode:
        """Get core mode."""
        pass

    @property
    @abstractmethod
    def state(self) -> CoreState:
        """Get core state."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize core functionality."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown core functionality."""
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
    def get_dependencies(self) -> list[str]:
        """Get all dependencies."""
        pass

    @abstractmethod
    def check_dependencies(self) -> bool:
        """Check if all dependencies are satisfied."""
        pass

