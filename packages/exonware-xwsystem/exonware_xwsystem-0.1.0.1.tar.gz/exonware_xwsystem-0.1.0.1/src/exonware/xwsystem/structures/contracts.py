"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Structures module contracts - interfaces and enums for data structure functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, Iterator, Callable

# Import enums from types module
from .defs import (
    StructureType,
    TraversalOrder,
    TraversalType,
    GraphType,
    CircularDetectionMethod,
    ValidationLevel
)


class ITreeNode(ABC):
    """Interface for tree node operations."""
    
    @property
    @abstractmethod
    def value(self) -> Any:
        """Node value."""
        pass
    
    @property
    @abstractmethod
    def children(self) -> list['ITreeNode']:
        """Node children."""
        pass
    
    @property
    @abstractmethod
    def parent(self) -> Optional['ITreeNode']:
        """Node parent."""
        pass
    
    @abstractmethod
    def add_child(self, child: 'ITreeNode') -> None:
        """Add child node."""
        pass
    
    @abstractmethod
    def remove_child(self, child: 'ITreeNode') -> None:
        """Remove child node."""
        pass
    
    @abstractmethod
    def is_leaf(self) -> bool:
        """Check if node is leaf."""
        pass
    
    @abstractmethod
    def get_depth(self) -> int:
        """Get node depth."""
        pass


class ITreeWalker(ABC):
    """Interface for tree walking operations."""
    
    @abstractmethod
    def walk_preorder(self, root: ITreeNode) -> Iterator[ITreeNode]:
        """Walk tree in preorder."""
        pass
    
    @abstractmethod
    def walk_inorder(self, root: ITreeNode) -> Iterator[ITreeNode]:
        """Walk tree in inorder."""
        pass
    
    @abstractmethod
    def walk_postorder(self, root: ITreeNode) -> Iterator[ITreeNode]:
        """Walk tree in postorder."""
        pass
    
    @abstractmethod
    def walk_level_order(self, root: ITreeNode) -> Iterator[ITreeNode]:
        """Walk tree in level order."""
        pass
    
    @abstractmethod
    def find_nodes(self, root: ITreeNode, predicate: Callable[[ITreeNode], bool]) -> list[ITreeNode]:
        """Find nodes matching predicate."""
        pass


class ICircularDetector(ABC):
    """Interface for circular reference detection."""
    
    @abstractmethod
    def detect_circular_reference(self, obj: Any) -> bool:
        """Detect circular reference in object."""
        pass
    
    @abstractmethod
    def find_circular_paths(self, obj: Any) -> list[list[Any]]:
        """Find all circular paths."""
        pass
    
    @abstractmethod
    def get_circular_objects(self, obj: Any) -> list[Any]:
        """Get objects involved in circular references."""
        pass
    
    @abstractmethod
    def break_circular_references(self, obj: Any) -> Any:
        """Break circular references."""
        pass


class IGraphNode(ABC):
    """Interface for graph node operations."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Node ID."""
        pass
    
    @property
    @abstractmethod
    def data(self) -> Any:
        """Node data."""
        pass
    
    @property
    @abstractmethod
    def neighbors(self) -> list['IGraphNode']:
        """Node neighbors."""
        pass
    
    @abstractmethod
    def add_neighbor(self, neighbor: 'IGraphNode', weight: Optional[float] = None) -> None:
        """Add neighbor node."""
        pass
    
    @abstractmethod
    def remove_neighbor(self, neighbor: 'IGraphNode') -> None:
        """Remove neighbor node."""
        pass
    
    @abstractmethod
    def get_edge_weight(self, neighbor: 'IGraphNode') -> Optional[float]:
        """Get edge weight to neighbor."""
        pass


class IGraph(ABC):
    """Interface for graph operations."""
    
    @abstractmethod
    def add_node(self, node: IGraphNode) -> None:
        """Add node to graph."""
        pass
    
    @abstractmethod
    def remove_node(self, node_id: str) -> None:
        """Remove node from graph."""
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[IGraphNode]:
        """Get node by ID."""
        pass
    
    @abstractmethod
    def add_edge(self, from_node: str, to_node: str, weight: Optional[float] = None) -> None:
        """Add edge between nodes."""
        pass
    
    @abstractmethod
    def remove_edge(self, from_node: str, to_node: str) -> None:
        """Remove edge between nodes."""
        pass
    
    @abstractmethod
    def get_all_nodes(self) -> list[IGraphNode]:
        """Get all nodes."""
        pass
    
    @abstractmethod
    def get_all_edges(self) -> list[tuple]:
        """Get all edges."""
        pass
    
    @abstractmethod
    def is_connected(self, from_node: str, to_node: str) -> bool:
        """Check if nodes are connected."""
        pass
