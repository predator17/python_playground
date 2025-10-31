"""Unit tests for system_monitor.ui.chart_factory module."""

#      Copyright (c) 2025 predator. All rights reserved.

import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock PySide6 completely before any imports
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCharts'] = MagicMock()

# Mock system_monitor.widgets before importing chart_factory
mock_time_series_chart = MagicMock()
sys.modules['system_monitor.widgets'] = MagicMock()
sys.modules['system_monitor.widgets'].TimeSeriesChart = mock_time_series_chart

from system_monitor.ui.chart_factory import ChartFactory


class TestChartFactory(unittest.TestCase):
    """Test ChartFactory chart creation methods."""

    @patch('system_monitor.ui.chart_factory.TimeSeriesChart')
    def test_create_cpu_chart(self, mock_chart):
        """Test CPU chart creation."""
        ChartFactory.create_cpu_chart()
        
        mock_chart.assert_called_once_with("CPU Utilization", ["CPU %"], y_range=(0, 100))

    @patch('system_monitor.ui.chart_factory.TimeSeriesChart')
    def test_create_memory_chart(self, mock_chart):
        """Test memory chart creation."""
        ChartFactory.create_memory_chart()
        
        mock_chart.assert_called_once_with("Memory Utilization", ["Mem %"], y_range=(0, 100))

    @patch('system_monitor.ui.chart_factory.TimeSeriesChart')
    def test_create_network_chart(self, mock_chart):
        """Test network chart creation with auto-scale."""
        ChartFactory.create_network_chart()
        
        mock_chart.assert_called_once()
        call_args = mock_chart.call_args
        self.assertEqual(call_args[0][0], "Network Throughput (MiB/s)")
        self.assertEqual(call_args[0][1], ["Up", "Down"])
        self.assertTrue(call_args[1]['auto_scale'])

    @patch('system_monitor.ui.chart_factory.TimeSeriesChart')
    def test_create_disk_chart(self, mock_chart):
        """Test disk chart creation with auto-scale."""
        ChartFactory.create_disk_chart()
        
        mock_chart.assert_called_once()
        call_args = mock_chart.call_args
        self.assertEqual(call_args[0][0], "Disk Throughput (MiB/s)")
        self.assertEqual(call_args[0][1], ["Read", "Write"])
        self.assertTrue(call_args[1]['auto_scale'])

    @patch('system_monitor.ui.chart_factory.TimeSeriesChart')
    def test_create_gpu_chart_with_gpus(self, mock_chart):
        """Test GPU chart creation with GPU names."""
        gpu_names = ["NVIDIA RTX 3080", "NVIDIA RTX 3090"]
        
        result = ChartFactory.create_gpu_chart(gpu_names)
        
        mock_chart.assert_called_once_with(
            "GPU Utilization",
            ["NVIDIA RTX 3080", "NVIDIA RTX 3090"],
            y_range=(0, 100)
        )
        self.assertIsNotNone(result)

    @patch('system_monitor.ui.chart_factory.TimeSeriesChart')
    def test_create_gpu_chart_without_gpus(self, mock_chart):
        """Test GPU chart creation returns None without GPUs."""
        result = ChartFactory.create_gpu_chart([])
        
        mock_chart.assert_not_called()
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
