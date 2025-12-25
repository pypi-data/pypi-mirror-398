#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for PagingStrategyRegistry.

Following GUIDE_TEST.md standards.
"""

import sys

import pytest


from exonware.xwsystem.io.file import (
    PagingStrategyRegistry,
    get_global_paging_registry,
    BytePagingStrategy,
    LinePagingStrategy,
    RecordPagingStrategy,
)


@pytest.mark.xwsystem_unit
@pytest.mark.xwsystem_io
class TestPagingStrategyRegistry:
    """Test PagingStrategyRegistry."""
    
    def test_paging_registry_initialization(self):
        """Test registry initialization."""
        registry = PagingStrategyRegistry()
        assert registry is not None
    
    def test_paging_registry_register(self):
        """Test registering a strategy."""
        registry = PagingStrategyRegistry()
        registry.register(BytePagingStrategy)
        
        strategy = registry.get("byte")
        assert strategy is not None
        assert isinstance(strategy, BytePagingStrategy)
    
    def test_paging_registry_get(self):
        """Test getting a strategy by ID."""
        registry = get_global_paging_registry()
        
        # Get byte strategy
        strategy = registry.get("byte")
        assert strategy is not None
        
        # Get line strategy
        strategy = registry.get("line")
        assert strategy is not None
    
    def test_paging_registry_list_strategies(self):
        """Test listing all strategies."""
        registry = get_global_paging_registry()
        strategies = registry.list_strategies()
        
        assert "byte" in strategies
        assert "line" in strategies
        assert "record" in strategies
    
    def test_paging_registry_auto_detect(self):
        """Test auto-detection of strategy."""
        registry = get_global_paging_registry()
        
        # Auto-detect for binary mode
        strategy = registry.auto_detect(mode='rb')
        assert strategy is not None
        assert strategy.strategy_id == "byte"
        
        # Auto-detect for text mode
        strategy = registry.auto_detect(mode='r')
        assert strategy is not None
        assert strategy.strategy_id == "line"

