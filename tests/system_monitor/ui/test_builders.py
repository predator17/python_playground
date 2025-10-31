"""Unit tests for system_monitor.ui builder modules."""

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

# Mock system_monitor.widgets before importing UI modules
mock_time_series_chart = MagicMock()
mock_metric_card = MagicMock()
sys.modules['system_monitor.widgets'] = MagicMock()
sys.modules['system_monitor.widgets'].TimeSeriesChart = mock_time_series_chart
sys.modules['system_monitor.widgets'].MetricCard = mock_metric_card

from system_monitor.ui.toolbar_builder import ToolbarBuilder
from system_monitor.ui.dashboard_builder import DashboardBuilder
from system_monitor.ui.cpu_tab_builder import CPUTabBuilder


class TestToolbarBuilder(unittest.TestCase):
    """Test ToolbarBuilder methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MagicMock()
        self.monitor.interval_ms = 100
        self.monitor.addToolBar = MagicMock(return_value=MagicMock())

    def test_build_toolbar_creates_toolbar(self):
        """Test toolbar creation."""
        result = ToolbarBuilder.build_toolbar(self.monitor)
        
        self.monitor.addToolBar.assert_called_once_with("Controls")
        self.assertIsNotNone(result)

    def test_build_toolbar_creates_spinboxes(self):
        """Test toolbar creates interval spinboxes."""
        ToolbarBuilder.build_toolbar(self.monitor)
        
        self.assertIsNotNone(self.monitor.spin_interval)
        self.assertIsNotNone(self.monitor.spin_gpu_refresh)
        self.assertIsNotNone(self.monitor.spin_proc_refresh)

    def test_build_toolbar_creates_pause_button(self):
        """Test toolbar creates pause button."""
        ToolbarBuilder.build_toolbar(self.monitor)
        
        self.assertIsNotNone(self.monitor.btn_pause)


class TestDashboardBuilder(unittest.TestCase):
    """Test DashboardBuilder methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MagicMock()
        self.monitor.chart_cpu = MagicMock()
        self.monitor.chart_mem = MagicMock()
        self.monitor.chart_net = MagicMock()
        self.monitor.chart_disk = MagicMock()
        self.monitor.chart_gpu = MagicMock()
        self.monitor.gpu_provider = MagicMock()
        self.monitor.gpu_provider.gpu_names.return_value = []

    @patch('system_monitor.ui.dashboard_builder.MetricCard')
    @patch('system_monitor.ui.dashboard_builder.get_cpu_model_name')
    def test_build_dashboard_creates_cards(self, mock_cpu_model, mock_card):
        """Test dashboard creates all metric cards."""
        mock_cpu_model.return_value = "Test CPU"
        
        result = DashboardBuilder.build_dashboard(self.monitor)
        
        # Should create 7 cards (CPU, Mem, Net Up, Net Down, Disk Read, Disk Write, GPU)
        self.assertEqual(mock_card.call_count, 7)
        self.assertIsNotNone(result)

    @patch('system_monitor.ui.dashboard_builder.MetricCard')
    @patch('system_monitor.ui.dashboard_builder.get_cpu_model_name')
    def test_build_dashboard_sets_cpu_model(self, mock_cpu_model, mock_card):
        """Test dashboard sets CPU model name."""
        mock_cpu_model.return_value = "Intel Core i7"
        mock_card_instance = MagicMock()
        mock_card.return_value = mock_card_instance
        
        DashboardBuilder.build_dashboard(self.monitor)
        
        mock_cpu_model.assert_called_once()


class TestCPUTabBuilder(unittest.TestCase):
    """Test CPUTabBuilder methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MagicMock()
        self.monitor.chart_cpu = MagicMock()

    @patch('system_monitor.ui.cpu_tab_builder.psutil.cpu_count')
    @patch('system_monitor.ui.cpu_tab_builder.TimeSeriesChart')
    def test_build_cpu_tab_creates_per_core_charts(self, mock_chart, mock_cpu_count):
        """Test CPU tab creates per-core charts."""
        mock_cpu_count.return_value = 4
        
        result = CPUTabBuilder.build_cpu_tab(self.monitor)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(self.monitor.core_charts), 4)
        self.assertEqual(len(self.monitor.core_freq_labels), 4)

    @patch('system_monitor.ui.cpu_tab_builder.psutil.cpu_count')
    def test_build_cpu_tab_creates_summary_labels(self, mock_cpu_count):
        """Test CPU tab creates summary labels."""
        mock_cpu_count.return_value = 2
        
        CPUTabBuilder.build_cpu_tab(self.monitor)
        
        self.assertIsNotNone(self.monitor.lbl_proc_summary)
        self.assertIsNotNone(self.monitor.lbl_asyncio)


if __name__ == '__main__':
    unittest.main()
