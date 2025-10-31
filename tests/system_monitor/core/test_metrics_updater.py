"""Unit tests for system_monitor.core.metrics_updater module."""

#      Copyright (c) 2025 predator. All rights reserved.

import unittest
from unittest.mock import MagicMock, patch

from system_monitor.core.metrics_updater import MetricsUpdater


class TestMetricsUpdaterUpdateCPU(unittest.TestCase):
    """Test MetricsUpdater CPU update methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MagicMock()
        self.monitor.card_cpu = MagicMock()
        self.monitor.tabs = MagicMock()
        self.monitor.chart_cpu = MagicMock()

    @patch('system_monitor.core.metrics_updater.psutil.cpu_percent')
    @patch('system_monitor.core.metrics_updater.psutil.cpu_freq')
    def test_update_cpu_basic(self, mock_freq, mock_cpu):
        """Test basic CPU update."""
        mock_cpu.return_value = 50.5
        mock_freq_obj = MagicMock()
        mock_freq_obj.current = 3600.0
        mock_freq.return_value = mock_freq_obj
        self.monitor.tabs.currentIndex.return_value = 0
        
        MetricsUpdater._update_cpu(self.monitor, 0.1)
        
        self.monitor.card_cpu.update_percent.assert_called_once_with(50.5)
        self.monitor.card_cpu.set_frequency.assert_called_once_with(3600.0)

    @patch('system_monitor.core.metrics_updater.psutil.cpu_percent')
    def test_update_cpu_on_cpu_tab(self, mock_cpu):
        """Test CPU update when on CPU tab."""
        mock_cpu.side_effect = [45.0, [25.0, 50.0, 75.0]]
        self.monitor.tabs.currentIndex.return_value = 1  # CPU tab
        self.monitor.core_charts = [MagicMock(), MagicMock(), MagicMock()]
        self.monitor.core_freq_labels = []
        
        MetricsUpdater._update_cpu(self.monitor, 0.1)
        
        self.monitor.chart_cpu.append.assert_called_once_with([45.0])
        for i, chart in enumerate(self.monitor.core_charts):
            chart.append.assert_called_once()

    @patch('system_monitor.core.metrics_updater.get_per_core_frequencies')
    @patch('system_monitor.core.metrics_updater.psutil.cpu_percent')
    def test_update_cpu_with_core_frequencies(self, mock_cpu, mock_freq):
        """Test CPU update with per-core frequencies."""
        mock_cpu.side_effect = [45.0, [25.0, 50.0]]
        mock_freq.return_value = [3200.0, 3400.0]
        self.monitor.tabs.currentIndex.return_value = 1
        self.monitor.core_charts = [MagicMock(), MagicMock()]
        self.monitor.core_freq_labels = [MagicMock(), MagicMock()]
        
        MetricsUpdater._update_cpu(self.monitor, 0.1)
        
        self.monitor.core_freq_labels[0].setText.assert_called_with("3200 MHz")
        self.monitor.core_freq_labels[1].setText.assert_called_with("3400 MHz")


class TestMetricsUpdaterUpdateMemory(unittest.TestCase):
    """Test MetricsUpdater memory update method."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MagicMock()
        self.monitor.card_mem = MagicMock()
        self.monitor.tabs = MagicMock()
        self.monitor.chart_mem = MagicMock()

    @patch('system_monitor.core.metrics_updater.psutil.virtual_memory')
    def test_update_memory_basic(self, mock_mem):
        """Test basic memory update."""
        mock_mem_obj = MagicMock()
        mock_mem_obj.percent = 65.5
        mock_mem.return_value = mock_mem_obj
        self.monitor.tabs.currentIndex.return_value = 0
        
        MetricsUpdater._update_memory(self.monitor)
        
        self.monitor.card_mem.update_percent.assert_called_once_with(65.5)

    @patch('system_monitor.core.metrics_updater.psutil.virtual_memory')
    def test_update_memory_on_memory_tab(self, mock_mem):
        """Test memory update when on memory tab."""
        mock_mem_obj = MagicMock()
        mock_mem_obj.percent = 70.0
        mock_mem.return_value = mock_mem_obj
        self.monitor.tabs.currentIndex.return_value = 2  # Memory tab
        
        MetricsUpdater._update_memory(self.monitor)
        
        self.monitor.chart_mem.append.assert_called_once_with([70.0])


class TestMetricsUpdaterUpdateNetwork(unittest.TestCase):
    """Test MetricsUpdater network update method."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MagicMock()
        self.monitor.card_net_up = MagicMock()
        self.monitor.card_net_down = MagicMock()
        self.monitor.tabs = MagicMock()
        self.monitor.chart_net = MagicMock()
        self.monitor._bytes_per_unit = 1024**2  # MiB
        self.monitor._net_dyn_up = 1.0
        self.monitor._net_dyn_down = 1.0

    @patch('system_monitor.core.metrics_updater.psutil.net_io_counters')
    def test_update_network(self, mock_net):
        """Test network update."""
        last_net = MagicMock()
        last_net.bytes_sent = 1000000
        last_net.bytes_recv = 2000000
        self.monitor._last_net = last_net
        
        current_net = MagicMock()
        current_net.bytes_sent = 2000000
        current_net.bytes_recv = 4000000
        mock_net.return_value = current_net
        
        self.monitor.tabs.currentIndex.return_value = 0
        
        MetricsUpdater._update_network(self.monitor, 1.0)  # 1 second
        
        self.monitor.card_net_up.update_value.assert_called_once()
        self.monitor.card_net_down.update_value.assert_called_once()


class TestMetricsUpdaterUpdateDisk(unittest.TestCase):
    """Test MetricsUpdater disk update method."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MagicMock()
        self.monitor.card_disk_read = MagicMock()
        self.monitor.card_disk_write = MagicMock()
        self.monitor.tabs = MagicMock()
        self.monitor.chart_disk = MagicMock()
        self.monitor._bytes_per_unit = 1024**2
        self.monitor._disk_dyn_read = 1.0
        self.monitor._disk_dyn_write = 1.0

    @patch('system_monitor.core.metrics_updater.psutil.disk_io_counters')
    def test_update_disk_with_data(self, mock_disk):
        """Test disk update with valid data."""
        last_disk = MagicMock()
        last_disk.read_bytes = 1000000
        last_disk.write_bytes = 2000000
        self.monitor._last_disk = last_disk
        
        current_disk = MagicMock()
        current_disk.read_bytes = 2000000
        current_disk.write_bytes = 4000000
        mock_disk.return_value = current_disk
        
        self.monitor.tabs.currentIndex.return_value = 0
        
        MetricsUpdater._update_disk(self.monitor, 1.0)
        
        self.monitor.card_disk_read.update_value.assert_called_once()
        self.monitor.card_disk_write.update_value.assert_called_once()

    @patch('system_monitor.core.metrics_updater.psutil.disk_io_counters')
    def test_update_disk_exception(self, mock_disk):
        """Test disk update handles exceptions."""
        mock_disk.side_effect = Exception("Test error")
        self.monitor._last_disk = None
        self.monitor.tabs.currentIndex.return_value = 0
        
        # Should not raise
        MetricsUpdater._update_disk(self.monitor, 1.0)
        
        self.monitor.card_disk_read.update_value.assert_called_once()
        self.monitor.card_disk_write.update_value.assert_called_once()


class TestMetricsUpdaterUpdateGPU(unittest.TestCase):
    """Test MetricsUpdater GPU update method."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MagicMock()
        self.monitor.card_gpu = MagicMock()
        self.monitor.gpu_provider = MagicMock()
        self.monitor.tabs = MagicMock()
        self.monitor.chart_gpu = MagicMock()
        self.monitor.spin_gpu_refresh = MagicMock()
        self.monitor.spin_gpu_refresh.value.return_value = 100
        self.monitor._gpu_refresh_accum = 0.0
        self.monitor.lbl_gpu_info = MagicMock()

    def test_update_gpu_with_data(self):
        """Test GPU update with valid data."""
        self.monitor.gpu_provider.gpu_utils.return_value = [75.0, 80.0]
        self.monitor.gpu_provider.gpu_frequencies.return_value = [1800.0, 1900.0]
        self.monitor.gpu_provider.gpu_vram_info.return_value = [(4000.0, 8000.0), (6000.0, 12000.0)]
        self.monitor.gpu_provider.gpu_names.return_value = ["GPU 0", "GPU 1"]
        self.monitor._gpu_refresh_accum = 0.15  # Enough to trigger refresh
        self.monitor.tabs.currentIndex.return_value = 0
        
        MetricsUpdater._update_gpu(self.monitor, 0.1)
        
        self.monitor.card_gpu.update_percent.assert_called_once()
        self.monitor.card_gpu.set_frequency.assert_called_once_with(1800.0)

    def test_update_gpu_no_data(self):
        """Test GPU update with no GPU data."""
        self.monitor.gpu_provider.gpu_utils.return_value = []
        self.monitor._gpu_refresh_accum = 0.15
        
        MetricsUpdater._update_gpu(self.monitor, 0.1)
        
        self.monitor.card_gpu.set_unavailable.assert_called_once_with("N/A")

    def test_update_gpu_accumulation(self):
        """Test GPU refresh accumulation."""
        self.monitor.gpu_provider.gpu_utils.return_value = []
        self.monitor._gpu_refresh_accum = 0.05
        
        MetricsUpdater._update_gpu(self.monitor, 0.03)
        
        # Should not refresh yet (0.08 < 0.1)
        self.assertEqual(self.monitor._gpu_refresh_accum, 0.08)


class TestMetricsUpdaterUpdateProcesses(unittest.TestCase):
    """Test MetricsUpdater process update method."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MagicMock()
        self.monitor.spin_proc_refresh = MagicMock()
        self.monitor.spin_proc_refresh.value.return_value = 100
        self.monitor._proc_refresh_accum = 0.0

    def test_update_processes_accumulation(self):
        """Test process refresh accumulation."""
        self.monitor._proc_refresh_accum = 0.05
        
        MetricsUpdater._update_processes(self.monitor, 0.03)
        
        # Should not refresh yet
        self.assertEqual(self.monitor._proc_refresh_accum, 0.08)
        self.monitor.refresh_processes.assert_not_called()

    def test_update_processes_triggers_refresh(self):
        """Test process refresh triggers when accumulated."""
        self.monitor._proc_refresh_accum = 0.15
        
        MetricsUpdater._update_processes(self.monitor, 0.1)
        
        # Should trigger refresh and reset
        self.monitor.refresh_processes.assert_called_once()


class TestMetricsUpdaterUpdateAll(unittest.TestCase):
    """Test MetricsUpdater update_all_metrics method."""

    @patch.object(MetricsUpdater, '_update_processes')
    @patch.object(MetricsUpdater, '_update_gpu')
    @patch.object(MetricsUpdater, '_update_disk')
    @patch.object(MetricsUpdater, '_update_network')
    @patch.object(MetricsUpdater, '_update_memory')
    @patch.object(MetricsUpdater, '_update_cpu')
    def test_update_all_metrics(self, mock_cpu, mock_mem, mock_net, mock_disk, mock_gpu, mock_proc):
        """Test update_all_metrics calls all update methods."""
        monitor = MagicMock()
        
        MetricsUpdater.update_all_metrics(monitor, 0.1)
        
        mock_cpu.assert_called_once_with(monitor, 0.1)
        mock_mem.assert_called_once_with(monitor)
        mock_net.assert_called_once_with(monitor, 0.1)
        mock_disk.assert_called_once_with(monitor, 0.1)
        mock_gpu.assert_called_once_with(monitor, 0.1)
        mock_proc.assert_called_once_with(monitor, 0.1)


if __name__ == '__main__':
    unittest.main()
