"""pytest configuration for system_monitor tests.

This module sets up global fixtures and mocking for PySide6 to allow
testing Qt-based components without requiring a display server.
"""

#      Copyright (c) 2025 predator. All rights reserved.

import sys
from unittest.mock import MagicMock
import pytest


# Mock PySide6 modules before any imports
def _setup_pyside6_mocks():
    """Setup PySide6 mocks globally for all tests."""
    if 'PySide6' not in sys.modules:
        sys.modules['PySide6'] = MagicMock()
        sys.modules['PySide6.QtCore'] = MagicMock()
        sys.modules['PySide6.QtGui'] = MagicMock()
        sys.modules['PySide6.QtWidgets'] = MagicMock()
        sys.modules['PySide6.QtCharts'] = MagicMock()


# Setup mocks before any tests run
_setup_pyside6_mocks()


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset SystemInfoCache before each test to prevent cache pollution."""
    from system_monitor.utils.cache import SystemInfoCache
    SystemInfoCache.reset()
    yield
    # Cleanup after test
    SystemInfoCache.reset()


@pytest.fixture
def mock_qapplication():
    """Provide a mocked QApplication for tests that need it."""
    mock_app = MagicMock()
    mock_app.exec.return_value = 0
    return mock_app
