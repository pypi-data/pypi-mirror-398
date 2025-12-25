#exonware/xwsystem/structures/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Structures module errors - exception classes for data structure functionality.
"""


class StructureError(Exception):
    """Base exception for structure errors."""
    pass


class TreeError(StructureError):
    """Raised when tree operation fails."""
    pass


class TreeNodeError(TreeError):
    """Raised when tree node operation fails."""
    pass


class TreeTraversalError(TreeError):
    """Raised when tree traversal fails."""
    pass


class TreeValidationError(TreeError):
    """Raised when tree validation fails."""
    pass


class GraphError(StructureError):
    """Raised when graph operation fails."""
    pass


class GraphNodeError(GraphError):
    """Raised when graph node operation fails."""
    pass


class GraphEdgeError(GraphError):
    """Raised when graph edge operation fails."""
    pass


class GraphTraversalError(GraphError):
    """Raised when graph traversal fails."""
    pass


class GraphValidationError(GraphError):
    """Raised when graph validation fails."""
    pass


class CircularReferenceError(StructureError):
    """Raised when circular reference is detected."""
    pass


class CircularDetectionError(CircularReferenceError):
    """Raised when circular reference detection fails."""
    pass


class CircularBreakError(CircularReferenceError):
    """Raised when circular reference breaking fails."""
    pass


class StructureValidationError(StructureError):
    """Raised when structure validation fails."""
    pass


class StructureTypeError(StructureError):
    """Raised when structure type is invalid."""
    pass


class StructureSizeError(StructureError):
    """Raised when structure size is invalid."""
    pass


class StructureOperationError(StructureError):
    """Raised when structure operation fails."""
    pass


class StructureIndexError(StructureError):
    """Raised when structure index is invalid."""
    pass


class StructureKeyError(StructureError):
    """Raised when structure key is invalid."""
    pass
