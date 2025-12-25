#exonware/xwsystem/patterns/contracts.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Pattern contracts and interfaces for XWSystem design patterns.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Callable, Union
# Root cause: Migrating to Python 3.12 built-in generic syntax for consistency
# Priority #3: Maintainability - Modern type annotations improve code clarity

# Import enums from types module
from .defs import (
    PatternType,
    HandlerType,
    ContextType,
    FactoryType,
    PoolType,
    RegistryType,
    StrategyType,
    ObserverType,
    CommandType,
    StateType,
    BuilderType,
    PrototypeType,
    AdapterType,
    DecoratorType,
    ProxyType,
    FacadeType,
    ChainHandlerType,
    MediatorType,
    MementoType,
    VisitorType,
    IteratorType,
    ConcurrencyType,
    ArchitecturalType,
    SpecificationType,
    ValueObjectType,
    AggregateType
)


# ============================================================================
# CORE INTERFACES
# ============================================================================

class IHandler[T](ABC):
    """Interface for handlers in the chain of responsibility pattern."""
    
    @abstractmethod
    def handle(self, request: T) -> T:
        """Handle the request."""
        pass
    
    @abstractmethod
    def can_handle(self, request: T) -> bool:
        """Check if this handler can handle the request."""
        pass
    
    @abstractmethod
    def set_next(self, handler: 'IHandler[T]') -> 'IHandler[T]':
        """Set the next handler in the chain."""
        pass


class IHandlerFactory[T](ABC):
    """Interface for handler factories."""
    
    @abstractmethod
    def create_handler(self, handler_type: str, **kwargs) -> T:
        """Create a handler of the specified type."""
        pass
    
    @abstractmethod
    def register_handler(self, handler_type: str, handler_class: type[T]) -> None:
        """Register a handler class."""
        pass
    
    @abstractmethod
    def unregister_handler(self, handler_type: str) -> None:
        """Unregister a handler class."""
        pass
    
    @abstractmethod
    def list_handlers(self) -> list[str]:
        """List all registered handler types."""
        pass
    
    @abstractmethod
    def has_handler(self, handler_type: str) -> bool:
        """Check if a handler type is registered."""
        pass


class IContextManager(ABC):
    """Interface for context managers."""
    
    @abstractmethod
    def __enter__(self) -> 'IContextManager':
        """Enter the context."""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type: Optional[type[BaseException]], 
                exc_val: Optional[BaseException], 
                exc_tb: Optional[Any]) -> bool:
        """Exit the context."""
        pass
    
    @abstractmethod
    def is_active(self) -> bool:
        """Check if context is active."""
        pass
    
    @abstractmethod
    def get_context_data(self) -> dict[str, Any]:
        """Get context data."""
        pass


class IObjectPool[T](ABC):
    """Interface for object pools."""
    
    @abstractmethod
    def get(self, obj_type: type[T], *args, **kwargs) -> T:
        """Get an object from the pool."""
        pass
    
    @abstractmethod
    def release(self, obj: T) -> None:
        """Release an object back to the pool."""
        pass
    
    @abstractmethod
    def clear(self, obj_type: Optional[type[T]] = None) -> None:
        """Clear objects from the pool."""
        pass
    
    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get pool statistics."""
        pass
    
    @abstractmethod
    def is_empty(self, obj_type: type[T]) -> bool:
        """Check if pool is empty for a type."""
        pass


class IRegistry[K, V](ABC):
    """Interface for registries."""
    
    @abstractmethod
    def register(self, key: K, value: V) -> None:
        """Register a value with a key."""
        pass
    
    @abstractmethod
    def unregister(self, key: K) -> V:
        """Unregister a value by key."""
        pass
    
    @abstractmethod
    def get(self, key: K) -> Optional[V]:
        """Get a value by key."""
        pass
    
    @abstractmethod
    def has(self, key: K) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    def list_keys(self) -> list[K]:
        """List all keys."""
        pass
    
    @abstractmethod
    def list_values(self) -> list[V]:
        """List all values."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all entries."""
        pass


class IStrategy(ABC):
    """Interface for strategies."""
    
    @abstractmethod
    def execute(self, context: Any) -> Any:
        """Execute the strategy."""
        pass
    
    @abstractmethod
    def can_handle(self, context: Any) -> bool:
        """Check if strategy can handle context."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name."""
        pass


class IObserver(ABC):
    """Interface for observers."""
    
    @abstractmethod
    def update(self, subject: 'ISubject', event: Any) -> None:
        """Update the observer."""
        pass
    
    @abstractmethod
    def get_id(self) -> str:
        """Get observer ID."""
        pass


class ISubject(ABC):
    """Interface for subjects."""
    
    @abstractmethod
    def attach(self, observer: IObserver) -> None:
        """Attach an observer."""
        pass
    
    @abstractmethod
    def detach(self, observer: IObserver) -> None:
        """Detach an observer."""
        pass
    
    @abstractmethod
    def notify(self, event: Any) -> None:
        """Notify all observers."""
        pass


class ICommand(ABC):
    """Interface for commands."""
    
    @abstractmethod
    def execute(self) -> Any:
        """Execute the command."""
        pass
    
    @abstractmethod
    def undo(self) -> Any:
        """Undo the command."""
        pass
    
    @abstractmethod
    def can_undo(self) -> bool:
        """Check if command can be undone."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get command description."""
        pass


class IState(ABC):
    """Interface for states."""
    
    @abstractmethod
    def enter(self, context: Any) -> None:
        """Enter the state."""
        pass
    
    @abstractmethod
    def exit(self, context: Any) -> None:
        """Exit the state."""
        pass
    
    @abstractmethod
    def handle(self, context: Any, event: Any) -> None:
        """Handle an event in this state."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get state name."""
        pass


class IBuilder[T](ABC):
    """Interface for builders."""
    
    @abstractmethod
    def build(self) -> T:
        """Build the object."""
        pass
    
    @abstractmethod
    def reset(self) -> 'IBuilder[T]':
        """Reset the builder."""
        pass
    
    @abstractmethod
    def is_valid(self) -> bool:
        """Check if builder is in valid state."""
        pass


class IPrototype[T](ABC):
    """Interface for prototypes."""
    
    @abstractmethod
    def clone(self) -> T:
        """Clone the object."""
        pass
    
    @abstractmethod
    def deep_clone(self) -> T:
        """Create a deep clone."""
        pass
    
    @abstractmethod
    def shallow_clone(self) -> T:
        """Create a shallow clone."""
        pass


class IAdapter(ABC):
    """Interface for adapters."""
    
    @abstractmethod
    def adapt(self, source: Any) -> Any:
        """Adapt source to target."""
        pass
    
    @abstractmethod
    def can_adapt(self, source: Any) -> bool:
        """Check if source can be adapted."""
        pass
    
    @abstractmethod
    def get_source_type(self) -> type:
        """Get source type."""
        pass
    
    @abstractmethod
    def get_target_type(self) -> type:
        """Get target type."""
        pass


class IDecorator[T](ABC):
    """Interface for decorators."""
    
    @abstractmethod
    def decorate(self, target: T) -> T:
        """Decorate the target."""
        pass
    
    @abstractmethod
    def undecorate(self, target: T) -> T:
        """Remove decoration from target."""
        pass
    
    @abstractmethod
    def is_decorated(self, target: T) -> bool:
        """Check if target is decorated."""
        pass


class IProxy[T](ABC):
    """Interface for proxies."""
    
    @abstractmethod
    def get_real_object(self) -> T:
        """Get the real object."""
        pass
    
    @abstractmethod
    def is_accessible(self) -> bool:
        """Check if real object is accessible."""
        pass
    
    @abstractmethod
    def get_proxy_type(self) -> str:
        """Get proxy type."""
        pass


class IFacade(ABC):
    """Interface for facades."""
    
    @abstractmethod
    def execute(self, operation: str, *args, **kwargs) -> Any:
        """Execute an operation through the facade."""
        pass
    
    @abstractmethod
    def get_available_operations(self) -> list[str]:
        """Get list of available operations."""
        pass
    
    @abstractmethod
    def is_operation_supported(self, operation: str) -> bool:
        """Check if operation is supported."""
        pass


class IDynamicFacade(ABC):
    """Interface for dynamic facades."""
    
    @abstractmethod
    def get_available_formats(self) -> list[str]:
        """Get list of available formats."""
        pass
    
    @abstractmethod
    def has_format(self, format_name: str) -> bool:
        """Check if format is available."""
        pass
    
    @abstractmethod
    def load(self, source: Any, format_name: str, **kwargs) -> Any:
        """Load data using specified format."""
        pass
    
    @abstractmethod
    def save(self, data: Any, target: Any, format_name: str, **kwargs) -> None:
        """Save data using specified format."""
        pass


class IChainHandler(ABC):
    """Interface for chain handlers."""
    
    @abstractmethod
    def handle(self, request: Any) -> Any:
        """Handle the request."""
        pass
    
    @abstractmethod
    def set_next(self, handler: 'IChainHandler') -> 'IChainHandler':
        """Set the next handler."""
        pass
    
    @abstractmethod
    def can_handle(self, request: Any) -> bool:
        """Check if can handle request."""
        pass


class IMediator(ABC):
    """Interface for mediators."""
    
    @abstractmethod
    def register_colleague(self, colleague_id: str, colleague: Any) -> None:
        """Register a colleague."""
        pass
    
    @abstractmethod
    def unregister_colleague(self, colleague_id: str) -> None:
        """Unregister a colleague."""
        pass
    
    @abstractmethod
    def send_message(self, sender_id: str, receiver_id: str, message: Any) -> None:
        """Send a message between colleagues."""
        pass
    
    @abstractmethod
    def broadcast_message(self, sender_id: str, message: Any) -> None:
        """Broadcast a message to all colleagues."""
        pass


class IMemento(ABC):
    """Interface for mementos."""
    
    @abstractmethod
    def get_state(self) -> Any:
        """Get the saved state."""
        pass
    
    @abstractmethod
    def get_timestamp(self) -> float:
        """Get creation timestamp."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get memento description."""
        pass


class IOriginator(ABC):
    """Interface for originators."""
    
    @abstractmethod
    def create_memento(self) -> IMemento:
        """Create a memento."""
        pass
    
    @abstractmethod
    def restore_from_memento(self, memento: IMemento) -> None:
        """Restore from memento."""
        pass


class IVisitor(ABC):
    """Interface for visitors."""
    
    @abstractmethod
    def visit(self, element: Any) -> Any:
        """Visit an element."""
        pass
    
    @abstractmethod
    def can_visit(self, element: Any) -> bool:
        """Check if can visit element."""
        pass


class IElement(ABC):
    """Interface for elements that accept visitors."""
    
    @abstractmethod
    def accept(self, visitor: IVisitor) -> Any:
        """Accept a visitor."""
        pass


class IIterator[T](ABC):
    """Interface for iterators."""
    
    @abstractmethod
    def __next__(self) -> T:
        """Get next item."""
        pass
    
    @abstractmethod
    def __iter__(self) -> 'IIterator[T]':
        """Get iterator."""
        pass
    
    @abstractmethod
    def has_next(self) -> bool:
        """Check if has next item."""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset iterator."""
        pass


class IConcurrencyControl(ABC):
    """Interface for concurrency control."""
    
    @abstractmethod
    def acquire(self) -> None:
        """Acquire the lock."""
        pass
    
    @abstractmethod
    def release(self) -> None:
        """Release the lock."""
        pass
    
    @abstractmethod
    def is_locked(self) -> bool:
        """Check if locked."""
        pass
    
    @abstractmethod
    def try_acquire(self, timeout: Optional[float] = None) -> bool:
        """Try to acquire with timeout."""
        pass


class IArchitecturalPattern(ABC):
    """Interface for architectural patterns."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the pattern."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the pattern."""
        pass
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if initialized."""
        pass
    
    @abstractmethod
    def get_components(self) -> list[str]:
        """Get list of components."""
        pass


class ISpecification(ABC):
    """Interface for specifications."""
    
    @abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool:
        """Check if candidate satisfies specification."""
        pass
    
    @abstractmethod
    def and_specification(self, other: 'ISpecification') -> 'ISpecification':
        """Create AND specification."""
        pass
    
    @abstractmethod
    def or_specification(self, other: 'ISpecification') -> 'ISpecification':
        """Create OR specification."""
        pass
    
    @abstractmethod
    def not_specification(self) -> 'ISpecification':
        """Create NOT specification."""
        pass


class IValueObject(ABC):
    """Interface for value objects."""
    
    @abstractmethod
    def equals(self, other: Any) -> bool:
        """Check if equal to other."""
        pass
    
    @abstractmethod
    def get_hash(self) -> int:
        """Get hash code."""
        pass
    
    @abstractmethod
    def to_string(self) -> str:
        """Convert to string."""
        pass


class IAggregate(ABC):
    """Interface for aggregates in domain-driven design."""
    
    @abstractmethod
    def get_id(self) -> str:
        """Get the aggregate ID."""
        pass
    
    @abstractmethod
    def get_version(self) -> int:
        """Get the aggregate version."""
        pass
    
    @abstractmethod
    def get_uncommitted_events(self) -> list[Any]:
        """Get uncommitted events."""
        pass
    
    @abstractmethod
    def mark_events_as_committed(self) -> None:
        """Mark events as committed."""
        pass


class IPattern(ABC):
    """Interface for design patterns."""
    
    @abstractmethod
    def get_pattern_type(self) -> PatternType:
        """Get pattern type."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get pattern name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get pattern description."""
        pass
    
    @abstractmethod
    def is_applicable(self, context: Any) -> bool:
        """Check if pattern is applicable to context."""
        pass
    
    @abstractmethod
    def apply(self, context: Any) -> Any:
        """Apply the pattern to context."""
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate data for pattern application."""
        pass