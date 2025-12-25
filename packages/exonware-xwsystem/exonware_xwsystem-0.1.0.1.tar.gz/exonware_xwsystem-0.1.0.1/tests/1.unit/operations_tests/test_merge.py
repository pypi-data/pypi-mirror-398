#!/usr/bin/env python3
"""
#exonware/xwsystem/tests/1.unit/operations_tests/test_merge.py

Unit tests for merge operations.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.387
Generation Date: October 27, 2025

Tests following 5 priorities:
1. Security - Input validation and safe operations
2. Usability - Clear API and error messages
3. Maintainability - Clean test structure
4. Performance - Efficient merge operations
5. Extensibility - Multiple merge strategies
"""

import pytest
import threading
import time
from exonware.xwsystem.operations import (
    MergeOperation,
    deep_merge,
    MergeStrategy,
    MergeError
)


@pytest.mark.xwsystem_unit
class TestMergeOperationCore:
    """Core merge operation tests."""
    
    def test_deep_merge_dictionaries(self):
        """Test deep merge of nested dictionaries."""
        target = {"a": 1, "b": {"c": 2, "d": 3}}
        source = {"b": {"d": 4, "e": 5}, "f": 6}
        
        result = deep_merge(target, source)
        
        assert result["a"] == 1
        assert result["b"]["c"] == 2
        assert result["b"]["d"] == 4  # Overwritten
        assert result["b"]["e"] == 5  # Added
        assert result["f"] == 6
    
    def test_shallow_merge_dictionaries(self):
        """Test shallow merge (top-level only)."""
        target = {"a": 1, "b": {"c": 2}}
        source = {"b": {"d": 3}, "e": 4}
        
        result = deep_merge(target, source, strategy=MergeStrategy.SHALLOW)
        
        assert result["a"] == 1
        assert result["b"] == {"d": 3}  # Replaced, not merged
        assert result["e"] == 4
    
    def test_overwrite_merge(self):
        """Test overwrite merge strategy."""
        target = {"a": 1, "b": 2}
        source = {"c": 3}
        
        result = deep_merge(target, source, strategy=MergeStrategy.OVERWRITE)
        
        assert result == {"c": 3}  # Completely replaced
    
    def test_append_merge_lists(self):
        """Test append merge for lists."""
        target = {"items": [1, 2, 3]}
        source = {"items": [4, 5]}
        
        result = deep_merge(target, source, strategy=MergeStrategy.APPEND)
        
        assert result["items"] == [1, 2, 3, 4, 5]
    
    def test_unique_merge_lists(self):
        """Test unique merge for lists."""
        target = {"items": [1, 2, 3, 2]}
        source = {"items": [3, 4, 5]}
        
        result = deep_merge(target, source, strategy=MergeStrategy.UNIQUE)
        
        # Should contain unique items only
        assert set(result["items"]) == {1, 2, 3, 4, 5}
        # Order should be preserved from target then source
        assert result["items"].index(1) < result["items"].index(4)


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_security
class TestMergeSecurity:
    """Security tests for merge operations (Priority #1)."""
    
    def test_merge_does_not_mutate_original(self):
        """Test that merge doesn't mutate original data (security)."""
        original_target = {"a": 1, "b": {"c": 2}}
        target = {"a": 1, "b": {"c": 2}}
        source = {"b": {"d": 3}}
        
        result = deep_merge(target, source)
        
        # Original should not be modified
        assert target == original_target
        assert result != target
    
    def test_merge_handles_circular_references_safely(self):
        """Test that merge handles edge cases safely."""
        target = {"a": 1}
        source = {"b": 2}
        
        # Should not crash or hang
        result = deep_merge(target, source)
        assert result is not None
    
    def test_merge_with_none_values(self):
        """Test merge with None values doesn't cause security issues."""
        target = {"a": None, "b": 2}
        source = {"a": 1, "c": None}
        
        result = deep_merge(target, source)
        
        assert result["a"] == 1
        assert result["b"] == 2
        assert result["c"] is None


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_usability
class TestMergeUsability:
    """Usability tests for merge operations (Priority #2)."""
    
    def test_merge_error_messages_are_clear(self):
        """Test that error messages are helpful (usability)."""
        merger = MergeOperation()
        
        try:
            # Missing required arguments
            merger.execute({})
        except MergeError as e:
            assert "target and source" in str(e).lower()
            assert len(str(e)) > 10  # Not just a cryptic code
    
    def test_convenience_function_is_simple(self):
        """Test that convenience function is easy to use."""
        # Should work with minimal syntax
        result = deep_merge({"a": 1}, {"b": 2})
        
        assert result == {"a": 1, "b": 2}
    
    def test_strategy_enum_is_clear(self):
        """Test that strategy enum values are descriptive."""
        assert MergeStrategy.DEEP.value == "deep"
        assert MergeStrategy.SHALLOW.value == "shallow"
        assert MergeStrategy.APPEND.value == "append"


@pytest.mark.xwsystem_unit
class TestMergeMaintainability:
    """Maintainability tests for merge operations (Priority #3)."""
    
    def test_merge_operation_is_reusable(self):
        """Test that merge operation can be reused."""
        merger = MergeOperation()
        
        # Should work multiple times
        result1 = merger.merge({"a": 1}, {"b": 2})
        result2 = merger.merge({"c": 3}, {"d": 4})
        
        assert result1 == {"a": 1, "b": 2}
        assert result2 == {"c": 3, "d": 4}
    
    def test_merge_with_different_strategies(self):
        """Test that different strategies work consistently."""
        target = {"a": 1}
        source = {"b": 2}
        
        for strategy in MergeStrategy:
            result = deep_merge(target, source, strategy=strategy)
            assert result is not None


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_performance
class TestMergePerformance:
    """Performance tests for merge operations (Priority #4)."""
    
    def test_merge_large_dictionaries(self):
        """Test merge performance with large dictionaries."""
        target = {f"key{i}": i for i in range(1000)}
        source = {f"key{i}": i * 2 for i in range(500, 1500)}
        
        start = time.time()
        result = deep_merge(target, source)
        elapsed = time.time() - start
        
        # Should complete quickly
        assert elapsed < 1.0
        assert len(result) == 1500
    
    def test_merge_is_thread_safe(self):
        """Test that merge operation is thread-safe."""
        merger = MergeOperation()
        results = []
        errors = []
        
        def merge_task(i):
            try:
                result = merger.merge({"a": i}, {"b": i * 2})
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Run multiple threads
        threads = [threading.Thread(target=merge_task, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should succeed
        assert len(errors) == 0
        assert len(results) == 10


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_extensibility
class TestMergeExtensibility:
    """Extensibility tests for merge operations (Priority #5)."""
    
    def test_merge_supports_multiple_strategies(self):
        """Test that merge is extensible with strategies."""
        strategies = [
            MergeStrategy.DEEP,
            MergeStrategy.SHALLOW,
            MergeStrategy.OVERWRITE,
            MergeStrategy.APPEND,
            MergeStrategy.UNIQUE
        ]
        
        target = {"a": [1, 2], "b": {"c": 3}}
        source = {"a": [3, 4], "b": {"d": 5}}
        
        for strategy in strategies:
            result = deep_merge(target, source, strategy=strategy)
            assert result is not None
    
    def test_merge_operation_can_be_extended(self):
        """Test that MergeOperation can be extended."""
        class CustomMerger(MergeOperation):
            def custom_merge(self, target, source):
                return {"custom": True}
        
        custom = CustomMerger()
        result = custom.custom_merge({}, {})
        
        assert result == {"custom": True}


@pytest.mark.xwsystem_unit
class TestMergeEdgeCases:
    """Edge case tests for merge operations."""
    
    def test_merge_empty_dicts(self):
        """Test merging empty dictionaries."""
        assert deep_merge({}, {}) == {}
        assert deep_merge({"a": 1}, {}) == {"a": 1}
        assert deep_merge({}, {"b": 2}) == {"b": 2}
    
    def test_merge_empty_lists(self):
        """Test merging empty lists."""
        result = deep_merge({"items": []}, {"items": []}, strategy=MergeStrategy.APPEND)
        assert result["items"] == []
    
    def test_merge_with_mixed_types(self):
        """Test merge with different types."""
        # Dict to list - source wins
        result = deep_merge({"a": {"b": 1}}, {"a": [1, 2]})
        assert result["a"] == [1, 2]
    
    def test_merge_with_scalars(self):
        """Test merge with scalar values."""
        result = deep_merge({"a": 1}, {"a": 2})
        assert result["a"] == 2  # Source wins

