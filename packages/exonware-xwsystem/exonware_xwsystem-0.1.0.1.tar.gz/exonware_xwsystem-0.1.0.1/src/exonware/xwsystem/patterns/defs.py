#!/usr/bin/env python3
#exonware/xwsystem/patterns/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

Pattern types and enums for XWSystem design patterns.
"""

from enum import Enum


# ============================================================================
# PATTERN ENUMS
# ============================================================================

class PatternType(Enum):
    """Types of design patterns supported."""
    CREATIONAL = "creational"
    STRUCTURAL = "structural"
    BEHAVIORAL = "behavioral"
    CONCURRENCY = "concurrency"
    ARCHITECTURAL = "architectural"


class HandlerType(Enum):
    """Types of handlers supported."""
    SERIALIZATION = "serialization"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    CACHING = "caching"
    MONITORING = "monitoring"
    SECURITY = "security"


class ContextType(Enum):
    """Types of context managers supported."""
    RESOURCE = "resource"
    TRANSACTION = "transaction"
    PERFORMANCE = "performance"
    SECURITY = "security"
    LOGGING = "logging"


class FactoryType(Enum):
    """Types of factories supported."""
    OBJECT = "object"
    HANDLER = "handler"
    STRATEGY = "strategy"
    BUILDER = "builder"
    PROTOTYPE = "prototype"


class PoolType(Enum):
    """Types of object pools supported."""
    THREAD = "thread"
    CONNECTION = "connection"
    MEMORY = "memory"
    CACHE = "cache"
    RESOURCE = "resource"


class RegistryType(Enum):
    """Types of registries supported."""
    HANDLER = "handler"
    STRATEGY = "strategy"
    FACTORY = "factory"
    SERVICE = "service"
    COMPONENT = "component"


class StrategyType(Enum):
    """Types of strategies supported."""
    ALGORITHM = "algorithm"
    BEHAVIOR = "behavior"
    POLICY = "policy"
    RULE = "rule"
    HEURISTIC = "heuristic"


class ObserverType(Enum):
    """Types of observers supported."""
    EVENT = "event"
    STATE = "state"
    DATA = "data"
    PERFORMANCE = "performance"
    SECURITY = "security"


class CommandType(Enum):
    """Types of commands supported."""
    ACTION = "action"
    QUERY = "query"
    TRANSACTION = "transaction"
    BATCH = "batch"
    ASYNC = "async"


class StateType(Enum):
    """Types of states supported."""
    SIMPLE = "simple"
    COMPOSITE = "composite"
    HIERARCHICAL = "hierarchical"
    CONCURRENT = "concurrent"
    PERSISTENT = "persistent"


class BuilderType(Enum):
    """Types of builders supported."""
    OBJECT = "object"
    CONFIGURATION = "configuration"
    QUERY = "query"
    PIPELINE = "pipeline"
    WORKFLOW = "workflow"


class PrototypeType(Enum):
    """Types of prototypes supported."""
    SHALLOW = "shallow"
    DEEP = "deep"
    CUSTOM = "custom"
    REGISTRY = "registry"
    FACTORY = "factory"


class AdapterType(Enum):
    """Types of adapters supported."""
    OBJECT = "object"
    CLASS = "class"
    INTERFACE = "interface"
    FUNCTIONAL = "functional"
    DATA = "data"


class DecoratorType(Enum):
    """Types of decorators supported."""
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    PROPERTY = "property"
    BEHAVIOR = "behavior"


class ProxyType(Enum):
    """Types of proxies supported."""
    VIRTUAL = "virtual"
    REMOTE = "remote"
    PROTECTION = "protection"
    CACHING = "caching"
    SYNCHRONIZATION = "synchronization"


class FacadeType(Enum):
    """Types of facades supported."""
    SIMPLE = "simple"
    COMPLEX = "complex"
    DYNAMIC = "dynamic"
    STATIC = "static"
    HIERARCHICAL = "hierarchical"


class ChainHandlerType(Enum):
    """Types of chain handlers supported."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    PRIORITY = "priority"
    FALLBACK = "fallback"


class MediatorType(Enum):
    """Types of mediators supported."""
    SIMPLE = "simple"
    COMPLEX = "complex"
    HIERARCHICAL = "hierarchical"
    DISTRIBUTED = "distributed"
    EVENT_DRIVEN = "event_driven"


class MementoType(Enum):
    """Types of mementos supported."""
    SIMPLE = "simple"
    COMPLEX = "complex"
    INCREMENTAL = "incremental"
    COMPRESSED = "compressed"
    ENCRYPTED = "encrypted"


class VisitorType(Enum):
    """Types of visitors supported."""
    SIMPLE = "simple"
    COMPLEX = "complex"
    HIERARCHICAL = "hierarchical"
    MULTI_DISPATCH = "multi_dispatch"
    FUNCTIONAL = "functional"


class IteratorType(Enum):
    """Types of iterators supported."""
    SEQUENTIAL = "sequential"
    RANDOM_ACCESS = "random_access"
    BIDIRECTIONAL = "bidirectional"
    FILTERED = "filtered"
    TRANSFORMED = "transformed"


class ConcurrencyType(Enum):
    """Types of concurrency patterns supported."""
    LOCK = "lock"
    SEMAPHORE = "semaphore"
    MUTEX = "mutex"
    CONDITION = "condition"
    BARRIER = "barrier"


class ArchitecturalType(Enum):
    """Types of architectural patterns supported."""
    MVC = "mvc"
    MVP = "mvp"
    MVVM = "mvvm"
    LAYERED = "layered"
    MICROSERVICE = "microservice"


class SpecificationType(Enum):
    """Types of specifications supported."""
    SIMPLE = "simple"
    COMPOSITE = "composite"
    NEGATION = "negation"
    CONJUNCTION = "conjunction"
    DISJUNCTION = "disjunction"


class ValueObjectType(Enum):
    """Types of value objects supported."""
    IMMUTABLE = "immutable"
    MUTABLE = "mutable"
    COMPOSITE = "composite"
    PRIMITIVE = "primitive"
    CUSTOM = "custom"


class AggregateType(Enum):
    """Types of aggregates supported."""
    SIMPLE = "simple"
    COMPLEX = "complex"
    HIERARCHICAL = "hierarchical"
    DISTRIBUTED = "distributed"
    EVENT_SOURCED = "event_sourced"
