#exonware/xwsystem/structures/base.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Structures module base classes - abstract classes for data structure functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Iterator
from .contracts import StructureType, TraversalType, ValidationLevel


class AStructureBase(ABC):
    """Abstract base class for data structures."""
    
    def __init__(self, structure_type: StructureType = StructureType.GENERIC):
        """
        Initialize structure base.
        
        Args:
            structure_type: Type of data structure
        """
        self.structure_type = structure_type
        self._size = 0
        self._elements: list[Any] = []
    
    @abstractmethod
    def add(self, element: Any) -> bool:
        """Add element to structure."""
        pass
    
    @abstractmethod
    def remove(self, element: Any) -> bool:
        """Remove element from structure."""
        pass
    
    @abstractmethod
    def contains(self, element: Any) -> bool:
        """Check if structure contains element."""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get structure size."""
        pass
    
    @abstractmethod
    def is_empty(self) -> bool:
        """Check if structure is empty."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all elements from structure."""
        pass
    
    @abstractmethod
    def to_list(self) -> list[Any]:
        """Convert structure to list."""
        pass
    
    @abstractmethod
    def from_list(self, elements: list[Any]) -> None:
        """Initialize structure from list."""
        pass
    
    @abstractmethod
    def validate(self, validation_level: ValidationLevel = ValidationLevel.BASIC) -> bool:
        """Validate structure."""
        pass


class ATreeBase(ABC):
    """Abstract base class for tree structures."""
    
    def __init__(self):
        """Initialize tree base."""
        self._root: Optional[Any] = None
        self._size = 0
    
    @abstractmethod
    def insert(self, value: Any) -> bool:
        """Insert value into tree."""
        pass
    
    @abstractmethod
    def delete(self, value: Any) -> bool:
        """Delete value from tree."""
        pass
    
    @abstractmethod
    def search(self, value: Any) -> Optional[Any]:
        """Search for value in tree."""
        pass
    
    @abstractmethod
    def get_root(self) -> Optional[Any]:
        """Get tree root."""
        pass
    
    @abstractmethod
    def get_height(self) -> int:
        """Get tree height."""
        pass
    
    @abstractmethod
    def get_size(self) -> int:
        """Get tree size."""
        pass
    
    @abstractmethod
    def is_empty(self) -> bool:
        """Check if tree is empty."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear tree."""
        pass
    
    @abstractmethod
    def traverse(self, traversal_type: TraversalType = TraversalType.INORDER) -> Iterator[Any]:
        """Traverse tree."""
        pass
    
    @abstractmethod
    def get_leaves(self) -> list[Any]:
        """Get tree leaves."""
        pass
    
    @abstractmethod
    def get_internal_nodes(self) -> list[Any]:
        """Get internal nodes."""
        pass


class AGraphBase(ABC):
    """Abstract base class for graph structures."""
    
    def __init__(self, directed: bool = False):
        """
        Initialize graph base.
        
        Args:
            directed: Whether graph is directed
        """
        self.directed = directed
        self._vertices: dict[Any, list[Any]] = {}
        self._edges: list[tuple[Any, Any]] = []
        self._vertex_count = 0
        self._edge_count = 0
    
    @abstractmethod
    def add_vertex(self, vertex: Any) -> bool:
        """Add vertex to graph."""
        pass
    
    @abstractmethod
    def remove_vertex(self, vertex: Any) -> bool:
        """Remove vertex from graph."""
        pass
    
    @abstractmethod
    def add_edge(self, vertex1: Any, vertex2: Any, weight: Optional[float] = None) -> bool:
        """Add edge to graph."""
        pass
    
    @abstractmethod
    def remove_edge(self, vertex1: Any, vertex2: Any) -> bool:
        """Remove edge from graph."""
        pass
    
    @abstractmethod
    def has_vertex(self, vertex: Any) -> bool:
        """Check if graph has vertex."""
        pass
    
    @abstractmethod
    def has_edge(self, vertex1: Any, vertex2: Any) -> bool:
        """Check if graph has edge."""
        pass
    
    @abstractmethod
    def get_vertices(self) -> list[Any]:
        """Get all vertices."""
        pass
    
    @abstractmethod
    def get_edges(self) -> list[tuple[Any, Any]]:
        """Get all edges."""
        pass
    
    @abstractmethod
    def get_neighbors(self, vertex: Any) -> list[Any]:
        """Get vertex neighbors."""
        pass
    
    @abstractmethod
    def get_degree(self, vertex: Any) -> int:
        """Get vertex degree."""
        pass
    
    @abstractmethod
    def get_vertex_count(self) -> int:
        """Get vertex count."""
        pass
    
    @abstractmethod
    def get_edge_count(self) -> int:
        """Get edge count."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if graph is connected."""
        pass
    
    @abstractmethod
    def is_cyclic(self) -> bool:
        """Check if graph is cyclic."""
        pass


class ACircularDetectorBase(ABC):
    """Abstract base class for circular reference detection."""
    
    def __init__(self):
        """Initialize circular detector."""
        self._visited: set = set()
        self._recursion_stack: set = set()
        self._circular_refs: list[list[Any]] = []
    
    @abstractmethod
    def detect_circular_references(self, obj: Any, max_depth: int = 100) -> list[list[Any]]:
        """Detect circular references in object."""
        pass
    
    @abstractmethod
    def has_circular_reference(self, obj: Any, max_depth: int = 100) -> bool:
        """Check if object has circular references."""
        pass
    
    @abstractmethod
    def get_circular_paths(self) -> list[list[Any]]:
        """Get detected circular paths."""
        pass
    
    @abstractmethod
    def clear_detection_cache(self) -> None:
        """Clear detection cache."""
        pass
    
    @abstractmethod
    def break_circular_references(self, obj: Any) -> Any:
        """Break circular references in object."""
        pass
    
    @abstractmethod
    def get_reference_count(self, obj: Any) -> int:
        """Get reference count for object."""
        pass
    
    @abstractmethod
    def get_object_size(self, obj: Any) -> int:
        """Get object size in bytes."""
        pass
    
    @abstractmethod
    def get_memory_usage(self, obj: Any) -> dict[str, int]:
        """Get memory usage statistics."""
        pass


class ATreeWalkerBase(ABC):
    """Abstract base class for tree traversal."""
    
    def __init__(self):
        """Initialize tree walker."""
        self._current_node: Optional[Any] = None
        self._visited_nodes: set = set()
        self._path: list[Any] = []
    
    @abstractmethod
    def walk(self, root: Any, traversal_type: TraversalType = TraversalType.INORDER) -> Iterator[Any]:
        """Walk tree with specified traversal type."""
        pass
    
    @abstractmethod
    def walk_preorder(self, root: Any) -> Iterator[Any]:
        """Walk tree in preorder."""
        pass
    
    @abstractmethod
    def walk_inorder(self, root: Any) -> Iterator[Any]:
        """Walk tree in inorder."""
        pass
    
    @abstractmethod
    def walk_postorder(self, root: Any) -> Iterator[Any]:
        """Walk tree in postorder."""
        pass
    
    @abstractmethod
    def walk_level_order(self, root: Any) -> Iterator[Any]:
        """Walk tree in level order."""
        pass
    
    @abstractmethod
    def find_path(self, root: Any, target: Any) -> Optional[list[Any]]:
        """Find path to target node."""
        pass
    
    @abstractmethod
    def get_depth(self, root: Any, target: Any) -> int:
        """Get depth of target node."""
        pass
    
    @abstractmethod
    def get_ancestors(self, root: Any, target: Any) -> list[Any]:
        """Get ancestors of target node."""
        pass
    
    @abstractmethod
    def get_descendants(self, root: Any, target: Any) -> list[Any]:
        """Get descendants of target node."""
        pass
    
    @abstractmethod
    def get_siblings(self, root: Any, target: Any) -> list[Any]:
        """Get siblings of target node."""
        pass
    
    @abstractmethod
    def get_leaf_nodes(self, root: Any) -> list[Any]:
        """Get all leaf nodes."""
        pass
    
    @abstractmethod
    def get_internal_nodes(self, root: Any) -> list[Any]:
        """Get all internal nodes."""
        pass


class AStructureValidatorBase(ABC):
    """Abstract base class for structure validation."""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.BASIC):
        """
        Initialize structure validator.
        
        Args:
            validation_level: Validation level
        """
        self.validation_level = validation_level
        self._validation_errors: list[str] = []
    
    @abstractmethod
    def validate_structure(self, structure: Any) -> bool:
        """Validate data structure."""
        pass
    
    @abstractmethod
    def validate_tree(self, tree: Any) -> bool:
        """Validate tree structure."""
        pass
    
    @abstractmethod
    def validate_graph(self, graph: Any) -> bool:
        """Validate graph structure."""
        pass
    
    @abstractmethod
    def validate_circular_references(self, obj: Any) -> bool:
        """Validate for circular references."""
        pass
    
    @abstractmethod
    def get_validation_errors(self) -> list[str]:
        """Get validation errors."""
        pass
    
    @abstractmethod
    def clear_validation_errors(self) -> None:
        """Clear validation errors."""
        pass
    
    @abstractmethod
    def add_validation_rule(self, rule_name: str, rule_func: callable) -> None:
        """Add validation rule."""
        pass
    
    @abstractmethod
    def remove_validation_rule(self, rule_name: str) -> None:
        """Remove validation rule."""
        pass
    
    @abstractmethod
    def get_validation_score(self) -> float:
        """Get validation score."""
        pass


class BaseStructure(AStructureBase):
    """Base implementation of data structure."""
    
    def __init__(self, structure_type: StructureType = StructureType.GENERIC):
        """Initialize base structure."""
        super().__init__(structure_type)
        self._elements: list[Any] = []
    
    def add(self, element: Any) -> bool:
        """Add element to structure."""
        try:
            self._elements.append(element)
            self._size += 1
            return True
        except Exception:
            return False
    
    def remove(self, element: Any) -> bool:
        """Remove element from structure."""
        try:
            if element in self._elements:
                self._elements.remove(element)
                self._size -= 1
                return True
            return False
        except Exception:
            return False
    
    def contains(self, element: Any) -> bool:
        """Check if structure contains element."""
        return element in self._elements
    
    def size(self) -> int:
        """Get structure size."""
        return self._size
    
    def is_empty(self) -> bool:
        """Check if structure is empty."""
        return self._size == 0
    
    def clear(self) -> None:
        """Clear all elements from structure."""
        self._elements.clear()
        self._size = 0
    
    def to_list(self) -> list[Any]:
        """Convert structure to list."""
        return self._elements.copy()
    
    def from_list(self, elements: list[Any]) -> None:
        """Initialize structure from list."""
        self._elements = elements.copy()
        self._size = len(elements)
    
    def validate(self, validation_level: ValidationLevel = ValidationLevel.BASIC) -> bool:
        """Validate structure."""
        if validation_level == ValidationLevel.NONE:
            return True
        
        # Basic validation
        if self._size != len(self._elements):
            return False
        
        if validation_level in [ValidationLevel.STRICT, ValidationLevel.COMPREHENSIVE]:
            # Check for None elements
            if None in self._elements:
                return False
        
        return True