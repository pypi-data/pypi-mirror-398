"""
#exonware/xwsystem/tests/1.unit/caching_unit/conftest.py

Unit test fixtures for caching tests.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.388
Generation Date: 01-Nov-2025
"""

import pytest


@pytest.fixture
def mock_logger(monkeypatch):
    """Mock logger for testing."""
    logs = []
    
    class MockLogger:
        def debug(self, msg):
            logs.append(('debug', msg))
        def info(self, msg):
            logs.append(('info', msg))
        def warning(self, msg):
            logs.append(('warning', msg))
        def error(self, msg):
            logs.append(('error', msg))
    
    return MockLogger(), logs

