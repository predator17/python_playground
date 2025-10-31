"""Unit tests for system_monitor.widgets modules."""

#      Copyright (c) 2025 predator. All rights reserved.

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import sys

# Mock PySide6 before importing widgets
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCharts'] = MagicMock()

from system_monitor.widgets.time_series_chart import TimeSeriesChart
from system_monitor.widgets.metric_card import MetricCard


class TestTimeSeriesChart(unittest.TestCase):
    """Test TimeSeriesChart widget."""

    @patch('system_monitor.widgets.time_series_chart.QWidget.__init__')
    @patch('system_monitor.widgets.time_series_chart.QVBoxLayout')
    @patch('system_monitor.widgets.time_series_chart.QChart')
    @patch('system_monitor.widgets.time_series_chart.QLineSeries')
    @patch('system_monitor.widgets.time_series_chart.QValueAxis')
    @patch('system_monitor.widgets.time_series_chart.QChartView')
    def test_initialization(self, mock_chart_view, mock_axis, mock_series, 
                          mock_chart, mock_layout, mock_init):
        """Test TimeSeriesChart initialization."""
        mock_init.return_value = None
        
        chart = TimeSeriesChart("Test Chart", ["Series1", "Series2"], max_points=100)
        
        self.assertEqual(chart.max_points, 100)
        self.assertFalse(chart.auto_scale)
        self.assertEqual(chart._x, 0)

    @patch('system_monitor.widgets.time_series_chart.QWidget.__init__')
    @patch('system_monitor.widgets.time_series_chart.QVBoxLayout')
    @patch('system_monitor.widgets.time_series_chart.QChart')
    @patch('system_monitor.widgets.time_series_chart.QLineSeries')
    @patch('system_monitor.widgets.time_series_chart.QValueAxis')
    @patch('system_monitor.widgets.time_series_chart.QChartView')
    def test_append_values(self, mock_chart_view, mock_axis, mock_series, 
                          mock_chart, mock_layout, mock_init):
        """Test appending values to chart."""
        mock_init.return_value = None
        
        chart = TimeSeriesChart("Test", ["S1"], max_points=50)
        chart.series = [MagicMock()]
        chart._buffers = [[]]
        chart.axis_x = MagicMock()
        chart.axis_y = MagicMock()
        
        chart.append([75.0])
        
        self.assertEqual(chart._x, 1)
        self.assertEqual(len(chart._buffers[0]), 1)

    @patch('system_monitor.widgets.time_series_chart.QWidget.__init__')
    @patch('system_monitor.widgets.time_series_chart.QVBoxLayout')
    @patch('system_monitor.widgets.time_series_chart.QChart')
    @patch('system_monitor.widgets.time_series_chart.QLineSeries')
    @patch('system_monitor.widgets.time_series_chart.QValueAxis')
    @patch('system_monitor.widgets.time_series_chart.QChartView')
    def test_auto_scaling(self, mock_chart_view, mock_axis, mock_series,
                         mock_chart, mock_layout, mock_init):
        """Test auto-scaling functionality."""
        mock_init.return_value = None
        
        chart = TimeSeriesChart("Test", ["S1"], auto_scale=True)
        chart.series = [MagicMock()]
        chart._buffers = [[]]
        chart.axis_x = MagicMock()
        chart.axis_y = MagicMock()
        
        self.assertTrue(chart.auto_scale)


class TestMetricCard(unittest.TestCase):
    """Test MetricCard widget."""

    @patch('system_monitor.widgets.metric_card.QWidget.__init__')
    @patch('system_monitor.widgets.metric_card.QVBoxLayout')
    @patch('system_monitor.widgets.metric_card.QFrame')
    @patch('system_monitor.widgets.metric_card.QLabel')
    @patch('system_monitor.widgets.metric_card.QProgressBar')
    @patch('system_monitor.widgets.metric_card.TimeSeriesChart')
    def test_initialization(self, mock_chart, mock_bar, mock_label, 
                          mock_frame, mock_layout, mock_init):
        """Test MetricCard initialization."""
        mock_init.return_value = None
        
        card = MetricCard("CPU Usage", "%", is_percent=True, color="#00c853")
        
        self.assertTrue(card.is_percent)
        self.assertEqual(card.unit, "%")
        self.assertEqual(card.color, "#00c853")

    @patch('system_monitor.widgets.metric_card.QWidget.__init__')
    @patch('system_monitor.widgets.metric_card.QVBoxLayout')
    @patch('system_monitor.widgets.metric_card.QFrame')
    @patch('system_monitor.widgets.metric_card.QLabel')
    @patch('system_monitor.widgets.metric_card.QProgressBar')
    @patch('system_monitor.widgets.metric_card.TimeSeriesChart')
    def test_update_percent(self, mock_chart, mock_bar, mock_label,
                          mock_frame, mock_layout, mock_init):
        """Test updating percentage value."""
        mock_init.return_value = None
        
        card = MetricCard("Test", is_percent=True)
        card.lbl_value = MagicMock()
        card.bar = MagicMock()
        card.sparkline = None
        
        card.update_percent(75.5)
        
        card.lbl_value.setText.assert_called_once()
        card.bar.setValue.assert_called_once_with(76)

    @patch('system_monitor.widgets.metric_card.QWidget.__init__')
    @patch('system_monitor.widgets.metric_card.QVBoxLayout')
    @patch('system_monitor.widgets.metric_card.QFrame')
    @patch('system_monitor.widgets.metric_card.QLabel')
    @patch('system_monitor.widgets.metric_card.QProgressBar')
    @patch('system_monitor.widgets.metric_card.TimeSeriesChart')
    def test_warning_colors(self, mock_chart, mock_bar, mock_label,
                          mock_frame, mock_layout, mock_init):
        """Test warning color application for high usage."""
        mock_init.return_value = None
        
        card = MetricCard("Test", is_percent=True, color="#00c853")
        card.lbl_value = MagicMock()
        card.bar = MagicMock()
        card.sparkline = None
        
        # Test critical level (>=90%)
        card.update_percent(95.0)
        card.bar.setStyleSheet.assert_called()
        
        # Test warning level (>=80%)
        card.update_percent(85.0)
        card.bar.setStyleSheet.assert_called()
        
        # Test normal level (<80%)
        card.update_percent(50.0)
        card.bar.setStyleSheet.assert_called()

    @patch('system_monitor.widgets.metric_card.QWidget.__init__')
    @patch('system_monitor.widgets.metric_card.QVBoxLayout')
    @patch('system_monitor.widgets.metric_card.QFrame')
    @patch('system_monitor.widgets.metric_card.QLabel')
    @patch('system_monitor.widgets.metric_card.QProgressBar')
    @patch('system_monitor.widgets.metric_card.TimeSeriesChart')
    def test_set_frequency(self, mock_chart, mock_bar, mock_label,
                          mock_frame, mock_layout, mock_init):
        """Test setting frequency display."""
        mock_init.return_value = None
        
        card = MetricCard("Test")
        card.lbl_frequency = MagicMock()
        
        card.set_frequency(3600.0)
        
        card.lbl_frequency.setText.assert_called_once()
        card.lbl_frequency.setVisible.assert_called_with(True)

    @patch('system_monitor.widgets.metric_card.QWidget.__init__')
    @patch('system_monitor.widgets.metric_card.QVBoxLayout')
    @patch('system_monitor.widgets.metric_card.QFrame')
    @patch('system_monitor.widgets.metric_card.QLabel')
    @patch('system_monitor.widgets.metric_card.QProgressBar')
    @patch('system_monitor.widgets.metric_card.TimeSeriesChart')
    def test_set_model(self, mock_chart, mock_bar, mock_label,
                      mock_frame, mock_layout, mock_init):
        """Test setting model/brand name."""
        mock_init.return_value = None
        
        card = MetricCard("Test")
        card.lbl_model = MagicMock()
        
        card.set_model("Intel Core i7-9700K")
        
        card.lbl_model.setText.assert_called_once()
        card.lbl_model.setVisible.assert_called_with(True)

    @patch('system_monitor.widgets.metric_card.QWidget.__init__')
    @patch('system_monitor.widgets.metric_card.QVBoxLayout')
    @patch('system_monitor.widgets.metric_card.QFrame')
    @patch('system_monitor.widgets.metric_card.QLabel')
    @patch('system_monitor.widgets.metric_card.QProgressBar')
    @patch('system_monitor.widgets.metric_card.TimeSeriesChart')
    def test_set_unavailable(self, mock_chart, mock_bar, mock_label,
                           mock_frame, mock_layout, mock_init):
        """Test setting unavailable state."""
        mock_init.return_value = None
        
        card = MetricCard("Test")
        card.lbl_value = MagicMock()
        card.bar = MagicMock()
        
        card.set_unavailable("N/A")
        
        card.lbl_value.setText.assert_called_once_with("N/A")
        card.bar.setValue.assert_called_once_with(0)

    @patch('system_monitor.widgets.metric_card.QWidget.__init__')
    @patch('system_monitor.widgets.metric_card.QVBoxLayout')
    @patch('system_monitor.widgets.metric_card.QFrame')
    @patch('system_monitor.widgets.metric_card.QLabel')
    @patch('system_monitor.widgets.metric_card.QProgressBar')
    @patch('system_monitor.widgets.metric_card.TimeSeriesChart')
    def test_update_value(self, mock_chart, mock_bar, mock_label,
                        mock_frame, mock_layout, mock_init):
        """Test updating non-percentage value."""
        mock_init.return_value = None
        
        card = MetricCard("Test", "GB", is_percent=False)
        card.lbl_value = MagicMock()
        card.bar = MagicMock()
        card.sparkline = None
        
        card.update_value(8.5)
        
        card.lbl_value.setText.assert_called_once()
        card.bar.setValue.assert_called_once()


if __name__ == '__main__':
    unittest.main()
