#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for shared contracts/interfaces.

Following GUIDE_TEST.md standards.
"""

import sys

import pytest

from exonware.xwsystem.shared import (
    ICloneable,
    IComparable,
    IContainer,
    ICore,
    IID,
    IStringable,
)


@pytest.mark.xwsystem_unit
class TestICloneable:
    """Test ICloneable interface."""
    
    def test_icloneable_exists(self):
        """Test ICloneable interface exists."""
        assert ICloneable is not None


@pytest.mark.xwsystem_unit
class TestIComparable:
    """Test IComparable interface."""
    
    def test_icomparable_exists(self):
        """Test IComparable interface exists."""
        assert IComparable is not None


@pytest.mark.xwsystem_unit
class TestIContainer:
    """Test IContainer interface."""
    
    def test_icontainer_exists(self):
        """Test IContainer interface exists."""
        assert IContainer is not None


@pytest.mark.xwsystem_unit
class TestICore:
    """Test ICore interface."""
    
    def test_icore_exists(self):
        """Test ICore interface exists."""
        assert ICore is not None


@pytest.mark.xwsystem_unit
class TestIID:
    """Test IID interface."""
    
    def test_iid_exists(self):
        """Test IID interface exists."""
        assert IID is not None


@pytest.mark.xwsystem_unit
class TestIStringable:
    """Test IStringable interface."""
    
    def test_istringable_exists(self):
        """Test IStringable interface exists."""
        assert IStringable is not None

