#!/usr/bin/env python3
"""
#exonware/xwsystem/tests/1.unit/operations_tests/test_diff.py

Unit tests for diff operations.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.387
Generation Date: October 27, 2025

Tests following 5 priorities:
1. Security - Safe diff generation
2. Usability - Clear diff output
3. Maintainability - Clean test structure
4. Performance - Efficient diff generation
5. Extensibility - Multiple diff modes
"""

import pytest
import time
from exonware.xwsystem.operations import (
    DiffOperation,
    generate_diff,
    DiffMode,
    DiffResult,
    DiffError
)


@pytest.mark.xwsystem_unit
class TestDiffOperationCore:
    """Core diff operation tests."""
    
    def test_diff_identical_structures(self):
        """Test diff of identical structures."""
        data = {"a": 1, "b": 2}
        
        result = generate_diff(data, data)
        
        assert isinstance(result, DiffResult)
        assert result.total_changes == 0
        assert len(result.operations) == 0
    
    def test_diff_added_keys(self):
        """Test diff detects added keys."""
        original = {"a": 1}
        modified = {"a": 1, "b": 2}
        
        result = generate_diff(original, modified)
        
        assert result.total_changes > 0
        assert any(op["op"] == "add" and op["path"] == "/b" for op in result.operations)
    
    def test_diff_removed_keys(self):
        """Test diff detects removed keys."""
        original = {"a": 1, "b": 2}
        modified = {"a": 1}
        
        result = generate_diff(original, modified)
        
        assert result.total_changes > 0
        assert any(op["op"] == "remove" and op["path"] == "/b" for op in result.operations)
    
    def test_diff_changed_values(self):
        """Test diff detects changed values."""
        original = {"a": 1, "b": 2}
        modified = {"a": 1, "b": 3}
        
        result = generate_diff(original, modified)
        
        assert result.total_changes > 0
        assert any(op["op"] == "replace" and op["path"] == "/b" for op in result.operations)
    
    def test_diff_nested_structures(self):
        """Test diff of nested structures."""
        original = {"a": {"b": {"c": 1}}}
        modified = {"a": {"b": {"c": 2}}}
        
        result = generate_diff(original, modified)
        
        assert result.total_changes > 0
        assert "/a/b/c" in result.paths_changed


@pytest.mark.xwsystem_unit
class TestDiffModes:
    """Tests for different diff modes."""
    
    def test_structural_diff_mode(self):
        """Test structural diff (keys only)."""
        original = {"a": 1, "b": 2}
        modified = {"a": 1, "c": 3}
        
        result = generate_diff(original, modified, mode=DiffMode.STRUCTURAL)
        
        assert result.mode == DiffMode.STRUCTURAL
        assert result.total_changes > 0
    
    def test_content_diff_mode(self):
        """Test content diff (values only)."""
        original = {"a": 1, "b": 2}
        modified = {"a": 2, "b": 2}
        
        result = generate_diff(original, modified, mode=DiffMode.CONTENT)
        
        assert result.mode == DiffMode.CONTENT
        assert result.total_changes > 0
    
    def test_full_diff_mode(self):
        """Test full diff (structure + content)."""
        original = {"a": 1}
        modified = {"a": 2, "b": 3}
        
        result = generate_diff(original, modified, mode=DiffMode.FULL)
        
        assert result.mode == DiffMode.FULL
        assert result.total_changes > 0


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_security
class TestDiffSecurity:
    """Security tests for diff operations (Priority #1)."""
    
    def test_diff_does_not_mutate_originals(self):
        """Test that diff doesn't modify input data."""
        original = {"a": 1, "b": {"c": 2}}
        modified = {"a": 2, "b": {"d": 3}}
        original_copy = {"a": 1, "b": {"c": 2}}
        modified_copy = {"a": 2, "b": {"d": 3}}
        
        result = generate_diff(original, modified)
        
        # Inputs should not be modified
        assert original == original_copy
        assert modified == modified_copy
    
    def test_diff_handles_large_structures_safely(self):
        """Test diff with large structures doesn't crash."""
        original = {f"key{i}": i for i in range(10000)}
        modified = {f"key{i}": i * 2 for i in range(10000)}
        
        # Should not crash or hang
        result = generate_diff(original, modified)
        assert result is not None


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_usability
class TestDiffUsability:
    """Usability tests for diff operations (Priority #2)."""
    
    def test_diff_result_is_informative(self):
        """Test that diff result provides useful information."""
        original = {"a": 1}
        modified = {"a": 2, "b": 3}
        
        result = generate_diff(original, modified)
        
        # Should have clear attributes
        assert hasattr(result, 'operations')
        assert hasattr(result, 'total_changes')
        assert hasattr(result, 'paths_changed')
        assert hasattr(result, 'mode')
    
    def test_diff_error_messages_are_clear(self):
        """Test that error messages are helpful."""
        differ = DiffOperation()
        
        try:
            differ.execute({})  # Missing required argument
        except DiffError as e:
            assert "modified" in str(e).lower()
    
    def test_convenience_function_is_simple(self):
        """Test that convenience function is easy to use."""
        result = generate_diff({"a": 1}, {"a": 2})
        
        assert isinstance(result, DiffResult)
        assert result.total_changes > 0


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_performance
class TestDiffPerformance:
    """Performance tests for diff operations (Priority #4)."""
    
    def test_diff_large_structures_quickly(self):
        """Test diff performance with large structures."""
        original = {f"key{i}": {"nested": i} for i in range(1000)}
        modified = {f"key{i}": {"nested": i * 2} for i in range(1000)}
        
        start = time.time()
        result = generate_diff(original, modified)
        elapsed = time.time() - start
        
        # Should complete quickly
        assert elapsed < 2.0
        assert result.total_changes > 0


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_extensibility
class TestDiffExtensibility:
    """Extensibility tests for diff operations (Priority #5)."""
    
    def test_diff_supports_multiple_modes(self):
        """Test that diff is extensible with modes."""
        original = {"a": 1}
        modified = {"a": 2}
        
        for mode in DiffMode:
            result = generate_diff(original, modified, mode=mode)
            assert isinstance(result, DiffResult)
    
    def test_diff_operation_can_be_extended(self):
        """Test that DiffOperation can be extended."""
        class CustomDiffer(DiffOperation):
            def custom_diff(self, data1, data2):
                return {"custom": True}
        
        custom = CustomDiffer()
        result = custom.custom_diff({}, {})
        
        assert result == {"custom": True}


@pytest.mark.xwsystem_unit
class TestDiffEdgeCases:
    """Edge case tests for diff operations."""
    
    def test_diff_empty_structures(self):
        """Test diffing empty structures."""
        result = generate_diff({}, {})
        assert result.total_changes == 0
    
    def test_diff_null_values(self):
        """Test diff with None values."""
        original = {"a": None}
        modified = {"a": 1}
        
        result = generate_diff(original, modified)
        assert result.total_changes > 0
    
    def test_diff_type_changes(self):
        """Test diff with type changes."""
        original = {"a": 1}
        modified = {"a": "string"}
        
        result = generate_diff(original, modified)
        assert result.total_changes > 0

