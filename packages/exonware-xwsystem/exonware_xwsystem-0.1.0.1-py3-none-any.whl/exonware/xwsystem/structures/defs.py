#!/usr/bin/env python3
#exonware/xwsystem/structures/types.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 07-Sep-2025

Structures types and enums for XWSystem.
"""

from enum import Enum
from ..shared.defs import ValidationLevel


# ============================================================================
# STRUCTURES ENUMS
# ============================================================================

class StructureType(Enum):
    """Data structure types."""
    TREE = "tree"
    GRAPH = "graph"
    LIST = "list"
    DICT = "dict"
    SET = "set"
    QUEUE = "queue"
    STACK = "stack"
    HEAP = "heap"
    GENERIC = "generic"
    CUSTOM = "custom"


class TraversalOrder(Enum):
    """Tree traversal orders."""
    PREORDER = "preorder"
    INORDER = "inorder"
    POSTORDER = "postorder"
    LEVEL_ORDER = "level_order"


class TraversalType(Enum):
    """Traversal types for data structures."""
    DEPTH_FIRST = "depth_first"
    BREADTH_FIRST = "breadth_first"
    ITERATIVE = "iterative"
    RECURSIVE = "recursive"
    INORDER = "inorder"
    PREORDER = "preorder"
    POSTORDER = "postorder"
    LEVEL_ORDER = "level_order"


class GraphType(Enum):
    """Graph types."""
    DIRECTED = "directed"
    UNDIRECTED = "undirected"
    WEIGHTED = "weighted"
    UNWEIGHTED = "unweighted"


class CircularDetectionMethod(Enum):
    """Circular detection methods."""
    DFS = "dfs"
    BFS = "bfs"
    TARJAN = "tarjan"
    KAHN = "kahn"
