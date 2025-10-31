"""Unit tests for system_monitor.ui.event_handlers module."""

#      Copyright (c) 2025 predator. All rights reserved.

import unittest
from unittest.mock import MagicMock, patch

from system_monitor.ui.event_handlers import EventHandlers


class TestEventHandlers(unittest.TestCase):
    """Test EventHandlers static methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MagicMock()
        self.monitor.unit_combo_net = MagicMock()
        self.monitor.unit_combo_disk = MagicMock()
        self.monitor.card_net_up = MagicMock()
        self.monitor.card_net_down = MagicMock()
        self.monitor.card_disk_read = MagicMock()
        self.monitor.card_disk_write = MagicMock()
        self.monitor.chart_net = MagicMock()
        self.monitor.chart_disk = MagicMock()
        self.monitor.chart_net.chart = MagicMock()
        self.monitor.chart_disk.chart = MagicMock()

    def test_on_unit_changed_to_mb(self):
        """Test unit change to MB/s."""
        EventHandlers.on_unit_changed(self.monitor, "MB/s")
        
        self.assertEqual(self.monitor.unit_mode, "MB/s")
        self.assertEqual(self.monitor._bytes_per_unit, 1_000_000)
        self.assertEqual(self.monitor.card_net_up.unit, "MB/s")
        self.assertEqual(self.monitor.card_net_down.unit, "MB/s")

    def test_on_unit_changed_to_mib(self):
        """Test unit change to MiB/s."""
        EventHandlers.on_unit_changed(self.monitor, "MiB/s")
        
        self.assertEqual(self.monitor.unit_mode, "MiB/s")
        self.assertEqual(self.monitor._bytes_per_unit, 1024**2)

    def test_on_unit_changed_syncs_combos(self):
        """Test unit change syncs both combo boxes."""
        self.monitor.unit_combo_net.currentText.return_value = "MiB/s"
        self.monitor.unit_combo_disk.currentText.return_value = "MiB/s"
        
        EventHandlers.on_unit_changed(self.monitor, "MB/s")
        
        self.monitor.unit_combo_net.setCurrentText.assert_called_with("MB/s")
        self.monitor.unit_combo_disk.setCurrentText.assert_called_with("MB/s")

    def test_on_interval_changed(self):
        """Test interval change updates timer."""
        self.monitor.interval_ms = 100
        self.monitor.timer = MagicMock()
        
        EventHandlers.on_interval_changed(self.monitor, 200)
        
        self.assertEqual(self.monitor.interval_ms, 200)
        self.monitor.timer.setInterval.assert_called_once_with(200)

    def test_toggle_pause_to_paused(self):
        """Test toggle pause to paused state."""
        self.monitor._paused = False
        self.monitor.btn_pause = MagicMock()
        
        EventHandlers.toggle_pause(self.monitor)
        
        self.assertTrue(self.monitor._paused)
        self.monitor.btn_pause.setText.assert_called_with("▶ Resume")

    def test_toggle_pause_to_resumed(self):
        """Test toggle pause to resumed state."""
        self.monitor._paused = True
        self.monitor.btn_pause = MagicMock()
        
        EventHandlers.toggle_pause(self.monitor)
        
        self.assertFalse(self.monitor._paused)
        self.monitor.btn_pause.setText.assert_called_with("⏸ Pause")

    @patch.object(EventHandlers, '_update_window_title')
    def test_toggle_pause_updates_title(self, mock_update):
        """Test toggle pause updates window title."""
        self.monitor._paused = False
        self.monitor.btn_pause = MagicMock()
        
        EventHandlers.toggle_pause(self.monitor)
        
        mock_update.assert_called_once_with(self.monitor)

    @patch('system_monitor.ui.event_handlers.ProcessManager.refresh_processes')
    def test_on_proc_search_changed(self, mock_refresh):
        """Test process search filter change."""
        self.monitor._paused = False
        
        EventHandlers.on_proc_search_changed(self.monitor, "  Python  ")
        
        self.assertEqual(self.monitor._proc_filter, "python")
        mock_refresh.assert_called_once_with(self.monitor)

    @patch('system_monitor.ui.event_handlers.ProcessManager.on_proc_item_expanded')
    def test_on_proc_item_expanded(self, mock_expand):
        """Test process item expansion delegation."""
        mock_item = MagicMock()
        
        EventHandlers.on_proc_item_expanded(self.monitor, mock_item)
        
        mock_expand.assert_called_once_with(self.monitor, mock_item)


if __name__ == '__main__':
    unittest.main()
