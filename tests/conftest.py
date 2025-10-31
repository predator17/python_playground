"""Pytest configuration and shared fixtures."""

#      Copyright (c) 2025 predator. All rights reserved.

import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest


@pytest.fixture(scope='session')
def qapp():
    """Create QApplication instance for the test session."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Don't quit - let pytest handle cleanup


@pytest.fixture
def mock_psutil():
    """Mock psutil module with common return values."""
    mock = MagicMock()
    mock.net_io_counters.return_value = MagicMock(
        bytes_sent=1000000,
        bytes_recv=2000000,
        packets_sent=100,
        packets_recv=200
    )
    mock.disk_io_counters.return_value = MagicMock(
        read_bytes=5000000,
        write_bytes=3000000
    )
    mock.cpu_percent.return_value = 45.5
    mock.cpu_count.return_value = 8
    mock.virtual_memory.return_value = MagicMock(
        total=16000000000,
        available=8000000000,
        percent=50.0,
        used=8000000000,
        free=8000000000
    )
    mock.disk_partitions.return_value = [
        MagicMock(device='/dev/sda1', mountpoint='/', fstype='ext4')
    ]
    mock.disk_usage.return_value = MagicMock(
        total=500000000000,
        used=250000000000,
        free=250000000000,
        percent=50.0
    )
    return mock


@pytest.fixture
def mock_gpu_provider():
    """Mock GPUProvider with common return values."""
    mock = MagicMock()
    mock.gpu_names.return_value = ['NVIDIA GeForce RTX 3080']
    mock.gpu_utils.return_value = [75.5]
    mock.gpu_vram_info.return_value = [(8000, 10000)]  # (used, total)
    mock.gpu_frequencies.return_value = [(1500, 1800)]  # (current, max)
    mock.gpu_temps.return_value = [65.0]
    mock.gpu_power.return_value = [220.0]
    return mock


@pytest.fixture
def mock_process():
    """Mock psutil.Process with common attributes."""
    mock = MagicMock()
    mock.pid = 1234
    mock.name.return_value = 'python'
    mock.username.return_value = 'user'
    mock.cpu_percent.return_value = 5.5
    mock.memory_percent.return_value = 2.5
    mock.status.return_value = 'running'
    mock.children.return_value = []
    return mock
