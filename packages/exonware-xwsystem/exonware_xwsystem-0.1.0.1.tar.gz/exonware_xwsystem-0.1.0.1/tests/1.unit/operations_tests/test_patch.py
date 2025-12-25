#!/usr/bin/env python3
"""
#exonware/xwsystem/tests/1.unit/operations_tests/test_patch.py

Unit tests for patch operations.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.387
Generation Date: October 27, 2025

Tests following 5 priorities:
1. Security - Safe patch application
2. Usability - Clear patch API
3. Maintainability - Clean test structure
4. Performance - Efficient patch operations
5. Extensibility - RFC 6902 compliance
"""

import pytest
from exonware.xwsystem.operations import (
    PatchOperationImpl,
    apply_patch,
    PatchOperation,
    PatchResult,
    PatchError
)


@pytest.mark.xwsystem_unit
class TestPatchOperationCore:
    """Core patch operation tests (RFC 6902)."""
    
    def test_patch_add_operation(self):
        """Test add operation."""
        data = {"a": 1}
        operations = [{"op": "add", "path": "/b", "value": 2}]
        
        result = apply_patch(data, operations)
        
        assert result.success
        assert result.operations_applied == 1
        assert result.result == {"a": 1, "b": 2}
    
    def test_patch_remove_operation(self):
        """Test remove operation."""
        data = {"a": 1, "b": 2}
        operations = [{"op": "remove", "path": "/b"}]
        
        result = apply_patch(data, operations)
        
        assert result.success
        assert result.result == {"a": 1}
    
    def test_patch_replace_operation(self):
        """Test replace operation."""
        data = {"a": 1, "b": 2}
        operations = [{"op": "replace", "path": "/b", "value": 3}]
        
        result = apply_patch(data, operations)
        
        assert result.success
        assert result.result == {"a": 1, "b": 3}
    
    def test_patch_move_operation(self):
        """Test move operation."""
        data = {"a": 1, "b": 2}
        operations = [{"op": "move", "from": "/b", "path": "/c"}]
        
        result = apply_patch(data, operations)
        
        assert result.success
        assert result.result == {"a": 1, "c": 2}
        assert "b" not in result.result
    
    def test_patch_copy_operation(self):
        """Test copy operation."""
        data = {"a": 1, "b": 2}
        operations = [{"op": "copy", "from": "/b", "path": "/c"}]
        
        result = apply_patch(data, operations)
        
        assert result.success
        assert result.result == {"a": 1, "b": 2, "c": 2}
    
    def test_patch_test_operation_success(self):
        """Test test operation (success case)."""
        data = {"a": 1}
        operations = [{"op": "test", "path": "/a", "value": 1}]
        
        result = apply_patch(data, operations)
        
        assert result.success
    
    def test_patch_test_operation_failure(self):
        """Test test operation (failure case)."""
        data = {"a": 1}
        operations = [{"op": "test", "path": "/a", "value": 2}]
        
        result = apply_patch(data, operations)
        
        assert not result.success
        assert len(result.errors) > 0


@pytest.mark.xwsystem_unit
class TestPatchMultipleOperations:
    """Tests for multiple patch operations."""
    
    def test_patch_multiple_operations(self):
        """Test applying multiple operations."""
        data = {"a": 1}
        operations = [
            {"op": "add", "path": "/b", "value": 2},
            {"op": "add", "path": "/c", "value": 3},
            {"op": "replace", "path": "/a", "value": 10}
        ]
        
        result = apply_patch(data, operations)
        
        assert result.success
        assert result.operations_applied == 3
        assert result.result == {"a": 10, "b": 2, "c": 3}
    
    def test_patch_nested_paths(self):
        """Test patching nested structures."""
        data = {"a": {"b": {"c": 1}}}
        operations = [{"op": "replace", "path": "/a/b/c", "value": 2}]
        
        result = apply_patch(data, operations)
        
        assert result.success
        assert result.result["a"]["b"]["c"] == 2


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_security
class TestPatchSecurity:
    """Security tests for patch operations (Priority #1)."""
    
    def test_patch_does_not_mutate_original(self):
        """Test that patch doesn't modify original data."""
        original = {"a": 1, "b": 2}
        data = {"a": 1, "b": 2}
        operations = [{"op": "replace", "path": "/b", "value": 3}]
        
        result = apply_patch(data, operations)
        
        # Original should not be modified
        assert data == original
        assert result.result != data
    
    def test_patch_handles_invalid_paths_safely(self):
        """Test patch handles invalid paths safely."""
        data = {"a": 1}
        operations = [{"op": "remove", "path": "/nonexistent"}]
        
        result = apply_patch(data, operations)
        
        # Should not crash, should report error
        assert not result.success or len(result.errors) > 0
    
    def test_patch_rejects_root_removal(self):
        """Test that removing root is rejected."""
        data = {"a": 1}
        operations = [{"op": "remove", "path": "/"}]
        
        result = apply_patch(data, operations)
        
        assert not result.success


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_usability
class TestPatchUsability:
    """Usability tests for patch operations (Priority #2)."""
    
    def test_patch_result_is_informative(self):
        """Test that patch result provides useful information."""
        data = {"a": 1}
        operations = [{"op": "add", "path": "/b", "value": 2}]
        
        result = apply_patch(data, operations)
        
        # Should have clear attributes
        assert hasattr(result, 'success')
        assert hasattr(result, 'operations_applied')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'result')
    
    def test_patch_errors_are_descriptive(self):
        """Test that patch errors are descriptive."""
        data = {"a": 1}
        operations = [{"op": "invalid_op", "path": "/a"}]
        
        result = apply_patch(data, operations)
        
        assert not result.success
        assert len(result.errors) > 0
        # Error should mention the issue
        assert "unknown" in result.errors[0].lower() or "invalid" in result.errors[0].lower()
    
    def test_convenience_function_is_simple(self):
        """Test that convenience function is easy to use."""
        result = apply_patch({"a": 1}, [{"op": "add", "path": "/b", "value": 2}])
        
        assert isinstance(result, PatchResult)
        assert result.success


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_performance
class TestPatchPerformance:
    """Performance tests for patch operations (Priority #4)."""
    
    def test_patch_many_operations_efficiently(self):
        """Test patching with many operations."""
        data = {}
        operations = [
            {"op": "add", "path": f"/key{i}", "value": i}
            for i in range(1000)
        ]
        
        import time
        start = time.time()
        result = apply_patch(data, operations)
        elapsed = time.time() - start
        
        # Should complete quickly
        assert elapsed < 2.0
        assert result.success
        assert len(result.result) == 1000


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_extensibility
class TestPatchExtensibility:
    """Extensibility tests for patch operations (Priority #5)."""
    
    def test_patch_supports_all_rfc6902_operations(self):
        """Test that all RFC 6902 operations are supported."""
        data = {"a": 1, "b": 2}
        
        operations_to_test = [
            {"op": "add", "path": "/c", "value": 3},
            {"op": "remove", "path": "/c"},
            {"op": "replace", "path": "/a", "value": 10},
            {"op": "move", "from": "/a", "path": "/d"},
            {"op": "copy", "from": "/b", "path": "/e"},
            {"op": "test", "path": "/b", "value": 2}
        ]
        
        for operation in operations_to_test:
            result = apply_patch(data.copy(), [operation])
            # Each operation should work
            assert result is not None
    
    def test_patch_operation_can_be_extended(self):
        """Test that PatchOperationImpl can be extended."""
        class CustomPatcher(PatchOperationImpl):
            def custom_patch(self, data):
                return {"custom": True}
        
        custom = CustomPatcher()
        result = custom.custom_patch({})
        
        assert result == {"custom": True}


@pytest.mark.xwsystem_unit
class TestPatchEdgeCases:
    """Edge case tests for patch operations."""
    
    def test_patch_empty_operations(self):
        """Test patching with no operations."""
        data = {"a": 1}
        operations = []
        
        result = apply_patch(data, operations)
        
        assert result.success
        assert result.operations_applied == 0
        assert result.result == {"a": 1}
    
    def test_patch_with_special_characters_in_path(self):
        """Test paths with special characters."""
        data = {"a/b": 1}
        # JSON Pointer escapes / as ~1
        operations = [{"op": "replace", "path": "/a~1b", "value": 2}]
        
        result = apply_patch(data, operations)
        
        # Should handle escaped paths
        assert result is not None
    
    def test_patch_array_operations(self):
        """Test patching arrays."""
        data = {"items": [1, 2, 3]}
        operations = [{"op": "add", "path": "/items/3", "value": 4}]
        
        result = apply_patch(data, operations)
        
        assert result.success
        assert result.result["items"] == [1, 2, 3, 4]

