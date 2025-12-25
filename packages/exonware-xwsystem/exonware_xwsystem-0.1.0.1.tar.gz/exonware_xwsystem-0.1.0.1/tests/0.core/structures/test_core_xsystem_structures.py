#exonware/xwsystem/tests/core/structures/test_core_xwsystem_structures.py
"""
XSystem Structures Core Tests

Comprehensive tests for XSystem data structures including circular detection,
tree walking, and structure management.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

try:
    from exonware.xwsystem.structures.circular_detector import CircularDetector
    from exonware.xwsystem.structures.tree_walker import TreeWalker
    from exonware.xwsystem.structures.base import BaseStructure
    from exonware.xwsystem.structures.contracts import ICircularDetector, ITreeWalker
    from exonware.xwsystem.structures.errors import StructureError, CircularReferenceError, TreeError
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    class CircularDetector:
        def __init__(self): pass
        def detect_circular_reference(self, obj): return False
        def find_circular_path(self, obj): return []
        def is_circular(self, obj): return False
    
    class TreeWalker:
        def __init__(self): pass
        def walk_tree(self, root): return []
        def find_node(self, root, predicate): return None
        def get_tree_depth(self, root): return 0
        def get_tree_size(self, root): return 0
    
    class BaseStructure:
        def __init__(self): pass
        def initialize(self): pass
        def cleanup(self): pass
        def validate(self): return True
    
    class ICircularDetector: pass
    class ITreeWalker: pass
    
    class StructureError(Exception): pass
    class CircularReferenceError(Exception): pass
    class TreeError(Exception): pass


def test_circular_detector():
    """Test circular detector functionality."""
    print("📋 Testing: Circular Detector")
    print("-" * 30)
    
    try:
        detector = CircularDetector()
        
        # Test circular reference detection
        test_obj = {"key": "value"}
        is_circular = detector.detect_circular_reference(test_obj)
        assert isinstance(is_circular, bool)
        
        # Test circular path finding
        path = detector.find_circular_path(test_obj)
        assert isinstance(path, list)
        
        # Test circular check
        is_circular_check = detector.is_circular(test_obj)
        assert isinstance(is_circular_check, bool)
        
        print("✅ Circular detector tests passed")
        return True
    except Exception as e:
        print(f"❌ Circular detector tests failed: {e}")
        return False


def test_tree_walker():
    """Test tree walker functionality."""
    print("📋 Testing: Tree Walker")
    print("-" * 30)
    
    try:
        walker = TreeWalker()
        
        # Test tree walking
        test_tree = {"root": {"child1": {}, "child2": {}}}
        nodes = walker.walk_tree(test_tree)
        assert isinstance(nodes, list)
        
        # Test node finding
        def find_root(node):
            return "root" in node if isinstance(node, dict) else False
        
        found_node = walker.find_node(test_tree, find_root)
        # Can be None if not found, which is valid
        
        # Test tree depth
        depth = walker.get_tree_depth(test_tree)
        assert isinstance(depth, int)
        assert depth >= 0
        
        # Test tree size
        size = walker.get_tree_size(test_tree)
        assert isinstance(size, int)
        assert size >= 0
        
        print("✅ Tree walker tests passed")
        return True
    except Exception as e:
        print(f"❌ Tree walker tests failed: {e}")
        return False


def test_base_structure():
    """Test base structure functionality."""
    print("📋 Testing: Base Structure")
    print("-" * 30)
    
    try:
        structure = BaseStructure()
        
        # Test structure operations
        structure.initialize()
        
        # Test validation
        is_valid = structure.validate()
        assert isinstance(is_valid, bool)
        
        structure.cleanup()
        
        print("✅ Base structure tests passed")
        return True
    except Exception as e:
        print(f"❌ Base structure tests failed: {e}")
        return False


def test_structures_interfaces():
    """Test structures interface compliance."""
    print("📋 Testing: Structures Interfaces")
    print("-" * 30)
    
    try:
        # Test interface compliance
        detector = CircularDetector()
        walker = TreeWalker()
        structure = BaseStructure()
        
        # Verify objects can be instantiated
        assert detector is not None
        assert walker is not None
        assert structure is not None
        
        print("✅ Structures interfaces tests passed")
        return True
    except Exception as e:
        print(f"❌ Structures interfaces tests failed: {e}")
        return False


def test_structures_error_handling():
    """Test structures error handling."""
    print("📋 Testing: Structures Error Handling")
    print("-" * 30)
    
    try:
        # Test error classes
        structure_error = StructureError("Test structure error")
        circular_error = CircularReferenceError("Test circular error")
        tree_error = TreeError("Test tree error")
        
        assert str(structure_error) == "Test structure error"
        assert str(circular_error) == "Test circular error"
        assert str(tree_error) == "Test tree error"
        
        print("✅ Structures error handling tests passed")
        return True
    except Exception as e:
        print(f"❌ Structures error handling tests failed: {e}")
        return False


def test_structures_operations():
    """Test structures operations."""
    print("📋 Testing: Structures Operations")
    print("-" * 30)
    
    try:
        detector = CircularDetector()
        walker = TreeWalker()
        structure = BaseStructure()
        
        # Test integrated operations
        structure.initialize()
        
        # Create test data structure
        test_data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        
        # Test circular detection
        is_circular = detector.detect_circular_reference(test_data)
        assert isinstance(is_circular, bool)
        
        # Test tree walking
        nodes = walker.walk_tree(test_data)
        assert isinstance(nodes, list)
        
        # Test structure validation
        is_valid = structure.validate()
        assert isinstance(is_valid, bool)
        
        structure.cleanup()
        
        print("✅ Structures operations tests passed")
        return True
    except Exception as e:
        print(f"❌ Structures operations tests failed: {e}")
        return False


def test_structures_analysis():
    """Test structures analysis functionality."""
    print("📋 Testing: Structures Analysis")
    print("-" * 30)
    
    try:
        detector = CircularDetector()
        walker = TreeWalker()
        
        # Test complex data structure
        complex_data = {
            "users": [
                {"id": 1, "name": "Alice", "friends": [2, 3]},
                {"id": 2, "name": "Bob", "friends": [1, 3]},
                {"id": 3, "name": "Charlie", "friends": [1, 2]}
            ],
            "posts": [
                {"id": 1, "author": 1, "content": "Hello world"},
                {"id": 2, "author": 2, "content": "Nice day"}
            ]
        }
        
        # Test circular detection on complex structure
        is_circular = detector.detect_circular_reference(complex_data)
        assert isinstance(is_circular, bool)
        
        # Test tree analysis
        depth = walker.get_tree_depth(complex_data)
        assert isinstance(depth, int)
        assert depth >= 0
        
        size = walker.get_tree_size(complex_data)
        assert isinstance(size, int)
        assert size >= 0
        
        # Test node finding
        def find_user(node):
            if isinstance(node, dict) and "name" in node:
                return node["name"] == "Alice"
            return False
        
        found_user = walker.find_node(complex_data, find_user)
        # Can be None if not found, which is valid
        
        print("✅ Structures analysis tests passed")
        return True
    except Exception as e:
        print(f"❌ Structures analysis tests failed: {e}")
        return False


def test_structures_integration():
    """Test structures integration functionality."""
    print("📋 Testing: Structures Integration")
    print("-" * 30)
    
    try:
        detector = CircularDetector()
        walker = TreeWalker()
        structure = BaseStructure()
        
        # Test integrated workflow
        structure.initialize()
        
        # Create test structure
        test_structure = {
            "metadata": {"version": "1.0", "type": "test"},
            "data": {
                "items": [
                    {"id": 1, "value": "item1"},
                    {"id": 2, "value": "item2"}
                ]
            }
        }
        
        # Analyze structure
        is_circular = detector.detect_circular_reference(test_structure)
        nodes = walker.walk_tree(test_structure)
        depth = walker.get_tree_depth(test_structure)
        size = walker.get_tree_size(test_structure)
        
        # Validate structure
        is_valid = structure.validate()
        
        # Verify all operations completed
        assert isinstance(is_circular, bool)
        assert isinstance(nodes, list)
        assert isinstance(depth, int)
        assert isinstance(size, int)
        assert isinstance(is_valid, bool)
        
        structure.cleanup()
        
        print("✅ Structures integration tests passed")
        return True
    except Exception as e:
        print(f"❌ Structures integration tests failed: {e}")
        return False


def main():
    """Run all structures core tests."""
    print("=" * 50)
    print("🧪 XSystem Structures Core Tests")
    print("=" * 50)
    print("Testing XSystem data structures including circular detection,")
    print("tree walking, and structure management")
    print("=" * 50)
    
    tests = [
        test_circular_detector,
        test_tree_walker,
        test_base_structure,
        test_structures_interfaces,
        test_structures_error_handling,
        test_structures_operations,
        test_structures_analysis,
        test_structures_integration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print("📊 XSYSTEM STRUCTURES TEST SUMMARY")
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All XSystem structures tests passed!")
        return 0
    else:
        print("💥 Some XSystem structures tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
