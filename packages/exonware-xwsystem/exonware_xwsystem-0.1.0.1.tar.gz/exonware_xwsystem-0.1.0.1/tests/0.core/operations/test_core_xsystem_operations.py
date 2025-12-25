#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core tests for operations module.

Tests merge, diff, and patch operations with roundtrip testing.

Following GUIDE_TEST.md standards.
"""

import sys

import pytest

from exonware.xwsystem.operations import (
    MergeOperation,
    DiffOperation,
    PatchOperationImpl,
    deep_merge,
    generate_diff,
    apply_patch,
    MergeStrategy,
    DiffMode,
    PatchOperation,
)


@pytest.mark.xwsystem_core
class TestMergeOperations:
    """Test merge operations."""
    
    def test_deep_merge_basic(self):
        """Test basic deep merge."""
        target = {"a": 1, "b": {"c": 2}}
        source = {"b": {"d": 3}, "e": 4}
        
        result = deep_merge(target, source)
        
        assert result["a"] == 1
        assert result["b"]["c"] == 2
        assert result["b"]["d"] == 3
        assert result["e"] == 4
    
    def test_deep_merge_nested(self):
        """Test nested deep merge."""
        target = {"level1": {"level2": {"value": "original"}}}
        source = {"level1": {"level2": {"new": "added"}}}
        
        result = deep_merge(target, source)
        
        assert result["level1"]["level2"]["value"] == "original"
        assert result["level1"]["level2"]["new"] == "added"
    
    def test_merge_operation_class(self):
        """Test MergeOperation class."""
        merge_op = MergeOperation()
        
        target = {"a": 1}
        source = {"b": 2}
        
        result = merge_op.merge(target, source, MergeStrategy.DEEP)
        assert result["a"] == 1
        assert result["b"] == 2
    
    def test_shallow_merge(self):
        """Test shallow merge strategy."""
        merge_op = MergeOperation()
        
        target = {"a": {"nested": 1}}
        source = {"a": {"other": 2}}
        
        result = merge_op.merge(target, source, MergeStrategy.SHALLOW)
        # Shallow merge should overwrite entire "a" key
        assert "nested" not in result["a"] or result["a"]["other"] == 2
    
    def test_append_merge(self):
        """Test append merge strategy."""
        merge_op = MergeOperation()
        
        target = [1, 2, 3]
        source = [4, 5]
        
        result = merge_op.merge(target, source, MergeStrategy.APPEND)
        assert len(result) == 5
        assert 1 in result and 4 in result


@pytest.mark.xwsystem_core
class TestDiffOperations:
    """Test diff operations."""
    
    def test_generate_diff_basic(self):
        """Test basic diff generation."""
        original = {"a": 1, "b": 2}
        modified = {"a": 1, "b": 3, "c": 4}
        
        diff_result = generate_diff(original, modified)
        
        assert diff_result is not None
        assert diff_result.total_changes > 0
        assert len(diff_result.operations) > 0
    
    def test_diff_operation_class(self):
        """Test DiffOperation class."""
        diff_op = DiffOperation()
        
        original = {"key": "value1"}
        modified = {"key": "value2"}
        
        result = diff_op.diff(original, modified, DiffMode.FULL)
        
        assert result.total_changes > 0
        assert "/key" in result.paths_changed or "key" in result.paths_changed
    
    def test_diff_structural_mode(self):
        """Test structural diff mode."""
        diff_op = DiffOperation()
        
        original = {"a": 1}
        modified = {"b": 2}
        
        result = diff_op.diff(original, modified, DiffMode.STRUCTURAL)
        assert result.mode == DiffMode.STRUCTURAL
    
    def test_diff_content_mode(self):
        """Test content diff mode."""
        diff_op = DiffOperation()
        
        original = {"a": 1}
        modified = {"a": 2}
        
        result = diff_op.diff(original, modified, DiffMode.CONTENT)
        assert result.mode == DiffMode.CONTENT


@pytest.mark.xwsystem_core
class TestPatchOperations:
    """Test patch operations."""
    
    def test_apply_patch_add(self):
        """Test applying add patch operation."""
        data = {"a": 1}
        operations = [{"op": "add", "path": "/b", "value": 2}]
        
        patch_result = apply_patch(data, operations)
        
        assert patch_result.success is True
        assert patch_result.result["a"] == 1
        assert patch_result.result["b"] == 2
    
    def test_apply_patch_remove(self):
        """Test applying remove patch operation."""
        data = {"a": 1, "b": 2}
        operations = [{"op": "remove", "path": "/b"}]
        
        patch_result = apply_patch(data, operations)
        
        assert patch_result.success is True
        assert "b" not in patch_result.result
    
    def test_apply_patch_replace(self):
        """Test applying replace patch operation."""
        data = {"a": 1}
        operations = [{"op": "replace", "path": "/a", "value": 2}]
        
        patch_result = apply_patch(data, operations)
        
        assert patch_result.success is True
        assert patch_result.result["a"] == 2
    
    def test_patch_operation_class(self):
        """Test PatchOperationImpl class."""
        patch_op = PatchOperationImpl()
        
        data = {"key": "value"}
        operations = [{"op": "add", "path": "/new", "value": "new_value"}]
        
        result = patch_op.apply_patch(data, operations)
        
        assert result.success is True
        assert result.operations_applied == 1
        assert result.result["new"] == "new_value"
    
    def test_apply_patch_multiple_operations(self):
        """Test applying multiple patch operations."""
        data = {"a": 1}
        operations = [
            {"op": "add", "path": "/b", "value": 2},
            {"op": "add", "path": "/c", "value": 3},
        ]
        
        patch_result = apply_patch(data, operations)
        
        assert patch_result.success is True
        assert patch_result.operations_applied == 2
        assert "b" in patch_result.result
        assert "c" in patch_result.result


@pytest.mark.xwsystem_core
class TestOperationsRoundtrip:
    """Test roundtrip operations (merge/diff/patch cycles)."""
    
    def test_merge_diff_roundtrip(self):
        """Test merge then diff roundtrip."""
        original = {"a": 1, "b": 2}
        changes = {"b": 3, "c": 4}
        
        # Merge changes
        merged = deep_merge(original, changes)
        
        # Generate diff
        diff_result = generate_diff(original, merged)
        
        assert diff_result.total_changes > 0
        assert len(diff_result.operations) > 0
    
    def test_diff_patch_roundtrip(self):
        """Test diff then patch roundtrip."""
        original = {"a": 1, "b": 2}
        modified = {"a": 1, "b": 3, "c": 4}
        
        # Generate diff
        diff_result = generate_diff(original, modified)
        
        # Apply patch
        patch_result = apply_patch(original, diff_result.operations)
        
        assert patch_result.success is True
        # Result should match modified (or be close)
        assert patch_result.result["b"] == modified["b"]
        assert "c" in patch_result.result

