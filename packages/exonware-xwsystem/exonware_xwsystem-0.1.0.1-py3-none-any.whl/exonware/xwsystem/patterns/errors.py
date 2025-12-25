#exonware/xwsystem/patterns/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Pattern-specific error classes for XSystem design patterns.
"""

from typing import Any, Optional


class PatternError(Exception):
    """Base exception for all pattern-related errors."""
    
    def __init__(self, message: str, pattern_type: Optional[str] = None, 
                 context: Optional[dict[str, Any]] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.pattern_type = pattern_type
        self.context = context or {}
        self.original_error = original_error
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.pattern_type:
            base_msg = f"[{self.pattern_type}] {base_msg}"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg = f"{base_msg} (Context: {context_str})"
        return base_msg


class HandlerError(PatternError):
    """Error related to handler operations."""
    
    def __init__(self, message: str, handler_type: Optional[str] = None, 
                 handler_id: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Handler", **kwargs)
        self.handler_type = handler_type
        self.handler_id = handler_id


class HandlerNotFoundError(HandlerError):
    """Error when a requested handler is not found."""
    
    def __init__(self, handler_type: str, available_handlers: Optional[list[str]] = None, **kwargs):
        message = f"Handler of type '{handler_type}' not found"
        if available_handlers:
            message += f". Available handlers: {', '.join(available_handlers)}"
        super().__init__(message, handler_type=handler_type, **kwargs)
        self.available_handlers = available_handlers or []


class HandlerRegistrationError(HandlerError):
    """Error when handler registration fails."""
    
    def __init__(self, message: str, handler_type: str, handler_class: Optional[type] = None, **kwargs):
        super().__init__(message, handler_type=handler_type, **kwargs)
        self.handler_class = handler_class


class HandlerExecutionError(HandlerError):
    """Error when handler execution fails."""
    
    def __init__(self, message: str, handler_type: str, input_data: Optional[Any] = None, **kwargs):
        super().__init__(message, handler_type=handler_type, **kwargs)
        self.input_data = input_data


class FactoryError(PatternError):
    """Error related to factory operations."""
    
    def __init__(self, message: str, factory_type: Optional[str] = None, 
                 product_type: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Factory", **kwargs)
        self.factory_type = factory_type
        self.product_type = product_type


class FactoryCreationError(FactoryError):
    """Error when factory creation fails."""
    
    def __init__(self, message: str, factory_type: str, product_type: str, **kwargs):
        super().__init__(message, factory_type=factory_type, product_type=product_type, **kwargs)


class FactoryRegistrationError(FactoryError):
    """Error when factory registration fails."""
    
    def __init__(self, message: str, factory_type: str, product_class: Optional[type] = None, **kwargs):
        super().__init__(message, factory_type=factory_type, **kwargs)
        self.product_class = product_class


class ContextError(PatternError):
    """Error related to context manager operations."""
    
    def __init__(self, message: str, context_type: Optional[str] = None, 
                 context_id: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Context", **kwargs)
        self.context_type = context_type
        self.context_id = context_id


class ContextEnterError(ContextError):
    """Error when entering a context fails."""
    
    def __init__(self, message: str, context_type: str, **kwargs):
        super().__init__(message, context_type=context_type, **kwargs)


class ContextExitError(ContextError):
    """Error when exiting a context fails."""
    
    def __init__(self, message: str, context_type: str, exit_code: Optional[int] = None, **kwargs):
        super().__init__(message, context_type=context_type, **kwargs)
        self.exit_code = exit_code


class ObjectPoolError(PatternError):
    """Error related to object pool operations."""
    
    def __init__(self, message: str, pool_type: Optional[str] = None, 
                 pool_size: Optional[int] = None, **kwargs):
        super().__init__(message, pattern_type="ObjectPool", **kwargs)
        self.pool_type = pool_type
        self.pool_size = pool_size


class PoolExhaustedError(ObjectPoolError):
    """Error when object pool is exhausted."""
    
    def __init__(self, message: str, pool_type: str, max_size: int, current_size: int, **kwargs):
        super().__init__(message, pool_type=pool_type, pool_size=current_size, **kwargs)
        self.max_size = max_size
        self.current_size = current_size


class PoolObjectError(ObjectPoolError):
    """Error related to pool object operations."""
    
    def __init__(self, message: str, pool_type: str, object_type: Optional[str] = None, **kwargs):
        super().__init__(message, pool_type=pool_type, **kwargs)
        self.object_type = object_type


class RegistryError(PatternError):
    """Error related to registry operations."""
    
    def __init__(self, message: str, registry_type: Optional[str] = None, 
                 key: Optional[Any] = None, **kwargs):
        super().__init__(message, pattern_type="Registry", **kwargs)
        self.registry_type = registry_type
        self.key = key


class RegistryKeyError(RegistryError):
    """Error when registry key operations fail."""
    
    def __init__(self, message: str, registry_type: str, key: Any, **kwargs):
        super().__init__(message, registry_type=registry_type, key=key, **kwargs)


class RegistryValueError(RegistryError):
    """Error when registry value operations fail."""
    
    def __init__(self, message: str, registry_type: str, key: Any, value: Optional[Any] = None, **kwargs):
        super().__init__(message, registry_type=registry_type, key=key, **kwargs)
        self.value = value


class StrategyError(PatternError):
    """Error related to strategy pattern operations."""
    
    def __init__(self, message: str, strategy_type: Optional[str] = None, 
                 strategy_name: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Strategy", **kwargs)
        self.strategy_type = strategy_type
        self.strategy_name = strategy_name


class StrategyNotFoundError(StrategyError):
    """Error when a requested strategy is not found."""
    
    def __init__(self, strategy_name: str, available_strategies: Optional[list[str]] = None, **kwargs):
        message = f"Strategy '{strategy_name}' not found"
        if available_strategies:
            message += f". Available strategies: {', '.join(available_strategies)}"
        super().__init__(message, strategy_name=strategy_name, **kwargs)
        self.available_strategies = available_strategies or []


class StrategyExecutionError(StrategyError):
    """Error when strategy execution fails."""
    
    def __init__(self, message: str, strategy_name: str, input_data: Optional[Any] = None, **kwargs):
        super().__init__(message, strategy_name=strategy_name, **kwargs)
        self.input_data = input_data


class ObserverError(PatternError):
    """Error related to observer pattern operations."""
    
    def __init__(self, message: str, observer_id: Optional[str] = None, 
                 subject_id: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Observer", **kwargs)
        self.observer_id = observer_id
        self.subject_id = subject_id


class ObserverRegistrationError(ObserverError):
    """Error when observer registration fails."""
    
    def __init__(self, message: str, observer_id: str, subject_id: str, **kwargs):
        super().__init__(message, observer_id=observer_id, subject_id=subject_id, **kwargs)


class ObserverNotificationError(ObserverError):
    """Error when observer notification fails."""
    
    def __init__(self, message: str, observer_id: str, subject_id: str, event: Optional[str] = None, **kwargs):
        super().__init__(message, observer_id=observer_id, subject_id=subject_id, **kwargs)
        self.event = event


class CommandError(PatternError):
    """Error related to command pattern operations."""
    
    def __init__(self, message: str, command_type: Optional[str] = None, 
                 command_id: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Command", **kwargs)
        self.command_type = command_type
        self.command_id = command_id


class CommandExecutionError(CommandError):
    """Error when command execution fails."""
    
    def __init__(self, message: str, command_type: str, command_id: Optional[str] = None, **kwargs):
        super().__init__(message, command_type=command_type, command_id=command_id, **kwargs)


class CommandUndoError(CommandError):
    """Error when command undo fails."""
    
    def __init__(self, message: str, command_type: str, command_id: Optional[str] = None, **kwargs):
        super().__init__(message, command_type=command_type, command_id=command_id, **kwargs)


class StateError(PatternError):
    """Error related to state pattern operations."""
    
    def __init__(self, message: str, state_name: Optional[str] = None, 
                 context_id: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="State", **kwargs)
        self.state_name = state_name
        self.context_id = context_id


class StateTransitionError(StateError):
    """Error when state transition fails."""
    
    def __init__(self, message: str, from_state: str, to_state: str, context_id: Optional[str] = None, **kwargs):
        super().__init__(message, state_name=to_state, context_id=context_id, **kwargs)
        self.from_state = from_state
        self.to_state = to_state


class StateNotFoundError(StateError):
    """Error when a requested state is not found."""
    
    def __init__(self, state_name: str, available_states: Optional[list[str]] = None, **kwargs):
        message = f"State '{state_name}' not found"
        if available_states:
            message += f". Available states: {', '.join(available_states)}"
        super().__init__(message, state_name=state_name, **kwargs)
        self.available_states = available_states or []


class BuilderError(PatternError):
    """Error related to builder pattern operations."""
    
    def __init__(self, message: str, builder_type: Optional[str] = None, 
                 build_step: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Builder", **kwargs)
        self.builder_type = builder_type
        self.build_step = build_step


class BuildError(BuilderError):
    """Error when build process fails."""
    
    def __init__(self, message: str, builder_type: str, build_step: str, **kwargs):
        super().__init__(message, builder_type=builder_type, build_step=build_step, **kwargs)


class BuildValidationError(BuilderError):
    """Error when build validation fails."""
    
    def __init__(self, message: str, builder_type: str, validation_errors: Optional[list[str]] = None, **kwargs):
        super().__init__(message, builder_type=builder_type, **kwargs)
        self.validation_errors = validation_errors or []


class PrototypeError(PatternError):
    """Error related to prototype pattern operations."""
    
    def __init__(self, message: str, prototype_type: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Prototype", **kwargs)
        self.prototype_type = prototype_type


class CloneError(PrototypeError):
    """Error when cloning fails."""
    
    def __init__(self, message: str, prototype_type: str, **kwargs):
        super().__init__(message, prototype_type=prototype_type, **kwargs)


class AdapterError(PatternError):
    """Error related to adapter pattern operations."""
    
    def __init__(self, message: str, adapter_type: Optional[str] = None, 
                 source_type: Optional[str] = None, target_type: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Adapter", **kwargs)
        self.adapter_type = adapter_type
        self.source_type = source_type
        self.target_type = target_type


class AdaptationError(AdapterError):
    """Error when adaptation fails."""
    
    def __init__(self, message: str, adapter_type: str, source_type: str, target_type: str, **kwargs):
        super().__init__(message, adapter_type=adapter_type, source_type=source_type, target_type=target_type, **kwargs)


class CompatibilityError(AdapterError):
    """Error when compatibility check fails."""
    
    def __init__(self, message: str, adapter_type: str, source_type: str, **kwargs):
        super().__init__(message, adapter_type=adapter_type, source_type=source_type, **kwargs)


class DecoratorError(PatternError):
    """Error related to decorator pattern operations."""
    
    def __init__(self, message: str, decorator_type: Optional[str] = None, 
                 decorator_name: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Decorator", **kwargs)
        self.decorator_type = decorator_type
        self.decorator_name = decorator_name


class DecorationError(DecoratorError):
    """Error when decoration fails."""
    
    def __init__(self, message: str, decorator_name: str, target_type: Optional[str] = None, **kwargs):
        super().__init__(message, decorator_name=decorator_name, **kwargs)
        self.target_type = target_type


class ProxyError(PatternError):
    """Error related to proxy pattern operations."""
    
    def __init__(self, message: str, proxy_type: Optional[str] = None, 
                 real_object_type: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Proxy", **kwargs)
        self.proxy_type = proxy_type
        self.real_object_type = real_object_type


class ProxyAccessError(ProxyError):
    """Error when proxy access fails."""
    
    def __init__(self, message: str, proxy_type: str, real_object_type: str, **kwargs):
        super().__init__(message, proxy_type=proxy_type, real_object_type=real_object_type, **kwargs)


class FacadeError(PatternError):
    """Error related to facade pattern operations."""
    
    def __init__(self, message: str, facade_type: Optional[str] = None, 
                 operation: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Facade", **kwargs)
        self.facade_type = facade_type
        self.operation = operation


class FacadeOperationError(FacadeError):
    """Error when facade operation fails."""
    
    def __init__(self, message: str, facade_type: str, operation: str, **kwargs):
        super().__init__(message, facade_type=facade_type, operation=operation, **kwargs)


class ChainHandlerError(PatternError):
    """Error related to chain of responsibility pattern operations."""
    
    def __init__(self, message: str, handler_type: Optional[str] = None, 
                 chain_position: Optional[int] = None, **kwargs):
        super().__init__(message, pattern_type="ChainHandler", **kwargs)
        self.handler_type = handler_type
        self.chain_position = chain_position


class ChainSetupError(ChainHandlerError):
    """Error when chain setup fails."""
    
    def __init__(self, message: str, handler_type: str, **kwargs):
        super().__init__(message, handler_type=handler_type, **kwargs)


class ChainExecutionError(ChainHandlerError):
    """Error when chain execution fails."""
    
    def __init__(self, message: str, handler_type: str, chain_position: int, **kwargs):
        super().__init__(message, handler_type=handler_type, chain_position=chain_position, **kwargs)


class MediatorError(PatternError):
    """Error related to mediator pattern operations."""
    
    def __init__(self, message: str, mediator_type: Optional[str] = None, 
                 colleague_id: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Mediator", **kwargs)
        self.mediator_type = mediator_type
        self.colleague_id = colleague_id


class MediatorRegistrationError(MediatorError):
    """Error when mediator registration fails."""
    
    def __init__(self, message: str, mediator_type: str, colleague_id: str, **kwargs):
        super().__init__(message, mediator_type=mediator_type, colleague_id=colleague_id, **kwargs)


class MediatorCommunicationError(MediatorError):
    """Error when mediator communication fails."""
    
    def __init__(self, message: str, mediator_type: str, sender_id: str, receiver_id: Optional[str] = None, **kwargs):
        super().__init__(message, mediator_type=mediator_type, colleague_id=sender_id, **kwargs)
        self.sender_id = sender_id
        self.receiver_id = receiver_id


class MementoError(PatternError):
    """Error related to memento pattern operations."""
    
    def __init__(self, message: str, memento_type: Optional[str] = None, 
                 originator_id: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Memento", **kwargs)
        self.memento_type = memento_type
        self.originator_id = originator_id


class MementoCreationError(MementoError):
    """Error when memento creation fails."""
    
    def __init__(self, message: str, memento_type: str, originator_id: str, **kwargs):
        super().__init__(message, memento_type=memento_type, originator_id=originator_id, **kwargs)


class MementoRestoreError(MementoError):
    """Error when memento restore fails."""
    
    def __init__(self, message: str, memento_type: str, originator_id: str, **kwargs):
        super().__init__(message, memento_type=memento_type, originator_id=originator_id, **kwargs)


class VisitorError(PatternError):
    """Error related to visitor pattern operations."""
    
    def __init__(self, message: str, visitor_type: Optional[str] = None, 
                 element_type: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Visitor", **kwargs)
        self.visitor_type = visitor_type
        self.element_type = element_type


class VisitorAcceptError(VisitorError):
    """Error when visitor acceptance fails."""
    
    def __init__(self, message: str, visitor_type: str, element_type: str, **kwargs):
        super().__init__(message, visitor_type=visitor_type, element_type=element_type, **kwargs)


class IteratorError(PatternError):
    """Error related to iterator pattern operations."""
    
    def __init__(self, message: str, iterator_type: Optional[str] = None, 
                 collection_type: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Iterator", **kwargs)
        self.iterator_type = iterator_type
        self.collection_type = collection_type


class IteratorExhaustedError(IteratorError):
    """Error when iterator is exhausted."""
    
    def __init__(self, message: str, iterator_type: str, collection_type: str, **kwargs):
        super().__init__(message, iterator_type=iterator_type, collection_type=collection_type, **kwargs)


class ConcurrencyError(PatternError):
    """Error related to concurrency pattern operations."""
    
    def __init__(self, message: str, concurrency_type: Optional[str] = None, 
                 thread_id: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Concurrency", **kwargs)
        self.concurrency_type = concurrency_type
        self.thread_id = thread_id


class LockError(ConcurrencyError):
    """Error related to lock operations."""
    
    def __init__(self, message: str, lock_type: str, thread_id: Optional[str] = None, **kwargs):
        super().__init__(message, concurrency_type="Lock", thread_id=thread_id, **kwargs)
        self.lock_type = lock_type


class DeadlockError(LockError):
    """Error when deadlock is detected."""
    
    def __init__(self, message: str, lock_type: str, thread_id: str, **kwargs):
        super().__init__(message, lock_type=lock_type, thread_id=thread_id, **kwargs)


class TimeoutError(ConcurrencyError):
    """Error when operation times out."""
    
    def __init__(self, message: str, concurrency_type: str, timeout_duration: float, **kwargs):
        super().__init__(message, concurrency_type=concurrency_type, **kwargs)
        self.timeout_duration = timeout_duration


class ArchitecturalError(PatternError):
    """Error related to architectural pattern operations."""
    
    def __init__(self, message: str, architecture_type: Optional[str] = None, 
                 component_id: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Architectural", **kwargs)
        self.architecture_type = architecture_type
        self.component_id = component_id


class MVCError(ArchitecturalError):
    """Error related to MVC pattern operations."""
    
    def __init__(self, message: str, component: str, component_id: Optional[str] = None, **kwargs):
        super().__init__(message, architecture_type="MVC", component_id=component_id, **kwargs)
        self.component = component


class RepositoryError(ArchitecturalError):
    """Error related to repository pattern operations."""
    
    def __init__(self, message: str, repository_type: str, entity_type: Optional[str] = None, **kwargs):
        super().__init__(message, architecture_type="Repository", **kwargs)
        self.repository_type = repository_type
        self.entity_type = entity_type


class TransactionError(ArchitecturalError):
    """Error related to transaction operations."""
    
    def __init__(self, message: str, transaction_id: Optional[str] = None, **kwargs):
        super().__init__(message, architecture_type="Transaction", component_id=transaction_id, **kwargs)
        self.transaction_id = transaction_id


class CQRSError(ArchitecturalError):
    """Error related to CQRS pattern operations."""
    
    def __init__(self, message: str, operation_type: str, **kwargs):
        super().__init__(message, architecture_type="CQRS", **kwargs)
        self.operation_type = operation_type


class EventSourcingError(ArchitecturalError):
    """Error related to event sourcing operations."""
    
    def __init__(self, message: str, event_type: Optional[str] = None, 
                 aggregate_id: Optional[str] = None, **kwargs):
        super().__init__(message, architecture_type="EventSourcing", **kwargs)
        self.event_type = event_type
        self.aggregate_id = aggregate_id


class CircuitBreakerError(ArchitecturalError):
    """Error related to circuit breaker operations."""
    
    def __init__(self, message: str, circuit_state: str, **kwargs):
        super().__init__(message, architecture_type="CircuitBreaker", **kwargs)
        self.circuit_state = circuit_state


class SpecificationError(PatternError):
    """Error related to specification pattern operations."""
    
    def __init__(self, message: str, specification_type: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Specification", **kwargs)
        self.specification_type = specification_type


class SpecificationEvaluationError(SpecificationError):
    """Error when specification evaluation fails."""
    
    def __init__(self, message: str, specification_type: str, candidate_type: Optional[str] = None, **kwargs):
        super().__init__(message, specification_type=specification_type, **kwargs)
        self.candidate_type = candidate_type


class ValueObjectError(PatternError):
    """Error related to value object operations."""
    
    def __init__(self, message: str, value_object_type: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="ValueObject", **kwargs)
        self.value_object_type = value_object_type


class AggregateError(PatternError):
    """Error related to aggregate operations."""
    
    def __init__(self, message: str, aggregate_type: Optional[str] = None, 
                 aggregate_id: Optional[str] = None, **kwargs):
        super().__init__(message, pattern_type="Aggregate", **kwargs)
        self.aggregate_type = aggregate_type
        self.aggregate_id = aggregate_id


class AggregateInvariantError(AggregateError):
    """Error when aggregate invariant is violated."""
    
    def __init__(self, message: str, aggregate_type: str, aggregate_id: str, **kwargs):
        super().__init__(message, aggregate_type=aggregate_type, aggregate_id=aggregate_id, **kwargs)


# Aliases for backward compatibility
PoolError = ObjectPoolError