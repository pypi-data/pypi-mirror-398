#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for shared base classes.

Following GUIDE_TEST.md standards.
"""

import sys

import pytest

from exonware.xwsystem.shared import (
    ACoreBase,
    AResourceManagerBase,
    AConfigurationBase,
    BaseCore,
)


@pytest.mark.xwsystem_unit
class TestACoreBase:
    """Test ACoreBase abstract class."""
    
    def test_acore_base_is_abstract(self):
        """Test that ACoreBase is abstract."""
        # Cannot instantiate abstract class
        with pytest.raises(TypeError):
            ACoreBase()


@pytest.mark.xwsystem_unit
class TestAResourceManagerBase:
    """Test AResourceManagerBase abstract class."""
    
    def test_aresource_manager_base_is_abstract(self):
        """Test that AResourceManagerBase is abstract."""
        # Cannot instantiate abstract class
        with pytest.raises(TypeError):
            AResourceManagerBase()


@pytest.mark.xwsystem_unit
class TestAConfigurationBase:
    """Test AConfigurationBase abstract class."""
    
    def test_aconfiguration_base_is_abstract(self):
        """Test that AConfigurationBase is abstract."""
        # Cannot instantiate abstract class
        with pytest.raises(TypeError):
            AConfigurationBase()


@pytest.mark.xwsystem_unit
class TestBaseCore:
    """Test BaseCore class."""
    
    def test_base_core_exists(self):
        """Test BaseCore class exists."""
        assert BaseCore is not None

