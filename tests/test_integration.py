"""Integration tests for system_monitor application."""

#      Copyright (c) 2025 predator. All rights reserved.

import unittest
from unittest.mock import MagicMock, patch


class TestSystemMonitorIntegration(unittest.TestCase):
    """Integration tests for SystemMonitor application."""

    def _setup_mocks(self, mock_psutil, mock_gpu):
        """Setup common mocks for SystemMonitor tests."""
        # Mock psutil methods
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=0, bytes_recv=0)
        mock_psutil.disk_io_counters.return_value = MagicMock(read_bytes=0, write_bytes=0)
        mock_psutil.cpu_percent.return_value = 0.0
        mock_psutil.cpu_count.return_value = 4  # Mock CPU count for per-core charts
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.disk_partitions.return_value = []
        
        # Mock GPU provider
        mock_gpu_instance = MagicMock()
        mock_gpu_instance.gpu_names.return_value = []
        mock_gpu_instance.gpu_utils.return_value = []
        mock_gpu_instance.gpu_vram_info.return_value = []
        mock_gpu_instance.gpu_frequencies.return_value = []
        mock_gpu.return_value = mock_gpu_instance
        
        return mock_gpu_instance

    @patch('system_monitor.app.apply_dark_theme')
    @patch('system_monitor.app.GPUProvider')
    @patch('system_monitor.app.psutil')
    def test_system_monitor_initialization(self, mock_psutil, mock_gpu, mock_theme):
        """Test SystemMonitor initialization creates all components."""
        from system_monitor.app import SystemMonitor
        
        self._setup_mocks(mock_psutil, mock_gpu)
        
        monitor = SystemMonitor(interval_ms=100)
        
        self.assertEqual(monitor.interval_ms, 100)
        self.assertIsNotNone(monitor.gpu_provider)
        self.assertFalse(monitor._paused)

    @patch('system_monitor.app.apply_dark_theme')
    @patch('system_monitor.app.GPUProvider')
    @patch('system_monitor.app.psutil')
    def test_system_monitor_timer_setup(self, mock_psutil, mock_gpu, mock_theme):
        """Test SystemMonitor timer is properly configured."""
        from system_monitor.app import SystemMonitor
        
        self._setup_mocks(mock_psutil, mock_gpu)
        
        monitor = SystemMonitor(interval_ms=200)
        
        self.assertIsNotNone(monitor.timer)
        # Timer should be started with correct interval
        self.assertTrue(hasattr(monitor, 'timer'))

    @patch('system_monitor.app.apply_dark_theme')
    @patch('system_monitor.app.GPUProvider')
    @patch('system_monitor.app.psutil')
    @patch('system_monitor.app.MetricsUpdater.update_all_metrics')
    def test_system_monitor_on_timer_not_paused(self, mock_update, mock_psutil, mock_gpu, mock_theme):
        """Test on_timer updates metrics when not paused."""
        from system_monitor.app import SystemMonitor
        
        self._setup_mocks(mock_psutil, mock_gpu)
        
        monitor = SystemMonitor(interval_ms=100)
        monitor._paused = False
        
        monitor.on_timer()
        
        mock_update.assert_called_once()

    @patch('system_monitor.app.apply_dark_theme')
    @patch('system_monitor.app.GPUProvider')
    @patch('system_monitor.app.psutil')
    @patch('system_monitor.app.MetricsUpdater.update_all_metrics')
    def test_system_monitor_on_timer_paused(self, mock_update, mock_psutil, mock_gpu, mock_theme):
        """Test on_timer skips updates when paused."""
        from system_monitor.app import SystemMonitor
        
        self._setup_mocks(mock_psutil, mock_gpu)
        
        monitor = SystemMonitor(interval_ms=100)
        monitor._paused = True
        
        monitor.on_timer()
        
        mock_update.assert_not_called()

    @patch('system_monitor.app.apply_dark_theme')
    @patch('system_monitor.app.GPUProvider')
    @patch('system_monitor.app.psutil')
    @patch('system_monitor.app.ProcessManager.shutdown_collector')
    def test_system_monitor_close_event_cleanup(self, mock_shutdown, mock_psutil, mock_gpu, mock_theme):
        """Test closeEvent properly cleans up resources."""
        from system_monitor.app import SystemMonitor
        
        self._setup_mocks(mock_psutil, mock_gpu)
        
        monitor = SystemMonitor(interval_ms=100)
        mock_event = MagicMock()
        
        monitor.closeEvent(mock_event)
        
        mock_shutdown.assert_called_once()


class TestMainFunction(unittest.TestCase):
    """Test main application entry point."""

    @patch('system_monitor.app.sys.exit')
    @patch('system_monitor.app.SystemMonitor')
    @patch('system_monitor.app.apply_dark_theme')
    @patch('system_monitor.app.QApplication')
    def test_main_creates_application(self, mock_qapp, mock_theme, mock_monitor, mock_exit):
        """Test main() creates QApplication and SystemMonitor."""
        from system_monitor.app import main
        
        mock_app_instance = MagicMock()
        mock_qapp.return_value = mock_app_instance
        mock_monitor_instance = MagicMock()
        mock_monitor.return_value = mock_monitor_instance
        mock_app_instance.exec.return_value = 0
        
        main()
        
        mock_qapp.assert_called_once()
        mock_theme.assert_called_once_with(mock_app_instance)
        mock_monitor.assert_called_once_with(interval_ms=100)
        mock_monitor_instance.show.assert_called_once()


if __name__ == '__main__':
    unittest.main()
