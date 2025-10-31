"""Tests for MetricsUpdater module."""

#      Copyright (c) 2025 predator. All rights reserved.

import pytest
from unittest.mock import MagicMock, patch, Mock
import math


class TestMetricsUpdater:
    """Test MetricsUpdater class methods."""

    def setup_method(self):
        """Setup mock monitor for each test."""
        self.monitor = MagicMock()
        self.monitor.tabs = MagicMock()
        self.monitor.card_cpu = MagicMock()
        self.monitor.card_mem = MagicMock()
        self.monitor.card_net_up = MagicMock()
        self.monitor.card_net_down = MagicMock()
        self.monitor.card_disk_read = MagicMock()
        self.monitor.card_disk_write = MagicMock()
        self.monitor.card_gpu = MagicMock()
        self.monitor.chart_cpu = MagicMock()
        self.monitor.chart_mem = MagicMock()
        self.monitor.chart_net = MagicMock()
        self.monitor.chart_disk = MagicMock()
        self.monitor.chart_gpu = MagicMock()
        self.monitor._bytes_per_unit = 1024 ** 2
        self.monitor._net_dyn_up = 1.0
        self.monitor._net_dyn_down = 1.0
        self.monitor._disk_dyn_read = 1.0
        self.monitor._disk_dyn_write = 1.0
        self.monitor._gpu_refresh_accum = 0.0
        self.monitor._proc_refresh_accum = 0.0
        self.monitor.gpu_provider = MagicMock()
        self.monitor.spin_gpu_refresh = MagicMock()
        self.monitor.spin_proc_refresh = MagicMock()
        self.monitor.lbl_gpu_info = MagicMock()

    @patch('system_monitor.core.metrics_updater.MetricsUpdater._update_processes')
    @patch('system_monitor.core.metrics_updater.MetricsUpdater._update_gpu')
    @patch('system_monitor.core.metrics_updater.MetricsUpdater._update_disk')
    @patch('system_monitor.core.metrics_updater.MetricsUpdater._update_network')
    @patch('system_monitor.core.metrics_updater.MetricsUpdater._update_memory')
    @patch('system_monitor.core.metrics_updater.MetricsUpdater._update_cpu')
    def test_update_all_metrics_calls_all_methods(self, mock_cpu, mock_mem, mock_net, 
                                                   mock_disk, mock_gpu, mock_proc):
        """Test update_all_metrics calls all update methods."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        dt = 0.1
        MetricsUpdater.update_all_metrics(self.monitor, dt)
        
        mock_cpu.assert_called_once_with(self.monitor, dt)
        mock_mem.assert_called_once_with(self.monitor)
        mock_net.assert_called_once_with(self.monitor, dt)
        mock_disk.assert_called_once_with(self.monitor, dt)
        mock_gpu.assert_called_once_with(self.monitor, dt)
        mock_proc.assert_called_once_with(self.monitor, dt)

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_cpu_basic(self, mock_psutil):
        """Test basic CPU update."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        mock_psutil.cpu_percent.return_value = 45.5
        mock_psutil.cpu_freq.return_value = MagicMock(current=2400.0)
        self.monitor.tabs.currentIndex.return_value = 0  # Not on CPU tab
        
        MetricsUpdater._update_cpu(self.monitor, 0.1)
        
        self.monitor.card_cpu.update_percent.assert_called_once_with(45.5)
        self.monitor.card_cpu.set_frequency.assert_called_once_with(2400.0)

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_cpu_no_frequency(self, mock_psutil):
        """Test CPU update when frequency is not available."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.cpu_freq.return_value = None
        self.monitor.tabs.currentIndex.return_value = 0
        
        MetricsUpdater._update_cpu(self.monitor, 0.1)
        
        self.monitor.card_cpu.update_percent.assert_called_once_with(50.0)
        self.monitor.card_cpu.set_frequency.assert_not_called()

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_cpu_frequency_exception(self, mock_psutil):
        """Test CPU update handles frequency exception."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.cpu_freq.side_effect = Exception("Freq error")
        self.monitor.tabs.currentIndex.return_value = 0
        
        MetricsUpdater._update_cpu(self.monitor, 0.1)
        
        self.monitor.card_cpu.update_percent.assert_called_once_with(50.0)

    @patch('system_monitor.core.metrics_updater.get_per_core_frequencies')
    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_cpu_on_cpu_tab(self, mock_psutil, mock_get_freqs):
        """Test CPU update when on CPU tab with per-core data."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        mock_psutil.cpu_percent.side_effect = [45.5, [10.0, 20.0, 30.0, 40.0]]
        self.monitor.tabs.currentIndex.return_value = 1  # CPU tab
        self.monitor.core_charts = [MagicMock(), MagicMock(), MagicMock()]
        self.monitor.core_freq_labels = [MagicMock(), MagicMock(), MagicMock()]
        mock_get_freqs.return_value = [2400.0, 2500.0, 2600.0]
        
        MetricsUpdater._update_cpu(self.monitor, 0.1)
        
        self.monitor.chart_cpu.append.assert_called_once_with([45.5])
        self.monitor.core_charts[0].append.assert_called_once_with([10.0])
        self.monitor.core_charts[1].append.assert_called_once_with([20.0])
        self.monitor.core_charts[2].append.assert_called_once_with([30.0])
        self.monitor.core_freq_labels[0].setText.assert_called_once_with("2400 MHz")
        self.monitor.core_freq_labels[1].setText.assert_called_once_with("2500 MHz")
        self.monitor.core_freq_labels[2].setText.assert_called_once_with("2600 MHz")

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_cpu_on_cpu_tab_no_cores(self, mock_psutil):
        """Test CPU update on CPU tab when per-core data is not available."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        mock_psutil.cpu_percent.side_effect = [45.5, []]
        self.monitor.tabs.currentIndex.return_value = 1
        
        MetricsUpdater._update_cpu(self.monitor, 0.1)
        
        self.monitor.chart_cpu.append.assert_called_once_with([45.5])

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_cpu_percpu_exception(self, mock_psutil):
        """Test CPU update handles per-core exception."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        mock_psutil.cpu_percent.side_effect = [45.5, Exception("Core error")]
        self.monitor.tabs.currentIndex.return_value = 1
        
        MetricsUpdater._update_cpu(self.monitor, 0.1)
        
        self.monitor.chart_cpu.append.assert_called_once_with([45.5])

    @patch('system_monitor.core.metrics_updater.get_per_core_frequencies')
    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_cpu_freq_labels_exception(self, mock_psutil, mock_get_freqs):
        """Test CPU update handles frequency label exception."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        mock_psutil.cpu_percent.side_effect = [45.5, [10.0, 20.0]]
        self.monitor.tabs.currentIndex.return_value = 1
        self.monitor.core_charts = [MagicMock(), MagicMock()]
        self.monitor.core_freq_labels = [MagicMock(), MagicMock()]
        mock_get_freqs.side_effect = Exception("Freq error")
        
        MetricsUpdater._update_cpu(self.monitor, 0.1)
        
        self.monitor.chart_cpu.append.assert_called_once()

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_memory_basic(self, mock_psutil):
        """Test basic memory update."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        mock_mem = MagicMock(percent=65.5)
        mock_psutil.virtual_memory.return_value = mock_mem
        self.monitor.tabs.currentIndex.return_value = 0  # Not on memory tab
        
        MetricsUpdater._update_memory(self.monitor)
        
        self.monitor.card_mem.update_percent.assert_called_once_with(65.5)
        self.monitor.chart_mem.append.assert_not_called()

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_memory_on_memory_tab(self, mock_psutil):
        """Test memory update when on memory tab."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        mock_mem = MagicMock(percent=70.0)
        mock_psutil.virtual_memory.return_value = mock_mem
        self.monitor.tabs.currentIndex.return_value = 2  # Memory tab
        
        MetricsUpdater._update_memory(self.monitor)
        
        self.monitor.card_mem.update_percent.assert_called_once_with(70.0)
        self.monitor.chart_mem.append.assert_called_once_with([70.0])

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_network_basic(self, mock_psutil):
        """Test basic network update."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        last_net = MagicMock(bytes_sent=1000, bytes_recv=2000)
        current_net = MagicMock(bytes_sent=2000, bytes_recv=4000)
        self.monitor._last_net = last_net
        mock_psutil.net_io_counters.return_value = current_net
        self.monitor.tabs.currentIndex.return_value = 0
        
        dt = 1.0
        MetricsUpdater._update_network(self.monitor, dt)
        
        # Calculate expected values: (delta_bytes / dt) / bytes_per_unit
        expected_up = (2000 - 1000) / 1.0 / (1024 ** 2)
        expected_down = (4000 - 2000) / 1.0 / (1024 ** 2)
        
        self.monitor.card_net_up.update_value.assert_called_once()
        self.monitor.card_net_down.update_value.assert_called_once()
        assert self.monitor._last_net == current_net

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_network_dynamic_scaling(self, mock_psutil):
        """Test network update with dynamic scaling."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        last_net = MagicMock(bytes_sent=1000, bytes_recv=2000)
        current_net = MagicMock(bytes_sent=1001000, bytes_recv=2001000)
        self.monitor._last_net = last_net
        mock_psutil.net_io_counters.return_value = current_net
        self.monitor.tabs.currentIndex.return_value = 0
        
        dt = 1.0
        
        MetricsUpdater._update_network(self.monitor, dt)
        
        # Dynamic maxes should be updated (current speed is much higher than initial 1.0)
        assert self.monitor._net_dyn_up > 0.5  # Should be significantly higher
        assert self.monitor._net_dyn_down > 0.5  # Should be significantly higher

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_network_on_network_tab(self, mock_psutil):
        """Test network update when on network tab."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        last_net = MagicMock(bytes_sent=1000, bytes_recv=2000)
        current_net = MagicMock(bytes_sent=2000, bytes_recv=4000)
        self.monitor._last_net = last_net
        mock_psutil.net_io_counters.return_value = current_net
        self.monitor.tabs.currentIndex.return_value = 3  # Network tab
        
        MetricsUpdater._update_network(self.monitor, 1.0)
        
        self.monitor.chart_net.append.assert_called_once()

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_disk_basic(self, mock_psutil):
        """Test basic disk update."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        last_disk = MagicMock(read_bytes=1000, write_bytes=2000)
        current_disk = MagicMock(read_bytes=2000, write_bytes=4000)
        self.monitor._last_disk = last_disk
        mock_psutil.disk_io_counters.return_value = current_disk
        self.monitor.tabs.currentIndex.return_value = 0
        
        dt = 1.0
        MetricsUpdater._update_disk(self.monitor, dt)
        
        self.monitor.card_disk_read.update_value.assert_called_once()
        self.monitor.card_disk_write.update_value.assert_called_once()
        assert self.monitor._last_disk == current_disk

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_disk_no_last_disk(self, mock_psutil):
        """Test disk update when _last_disk is None."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        current_disk = MagicMock(read_bytes=2000, write_bytes=4000)
        self.monitor._last_disk = None
        mock_psutil.disk_io_counters.return_value = current_disk
        self.monitor.tabs.currentIndex.return_value = 0
        
        MetricsUpdater._update_disk(self.monitor, 1.0)
        
        # Should set to 0.0 when no last_disk
        call_args_read = self.monitor.card_disk_read.update_value.call_args
        call_args_write = self.monitor.card_disk_write.update_value.call_args
        assert call_args_read[0][0] == 0.0
        assert call_args_write[0][0] == 0.0

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_disk_exception(self, mock_psutil):
        """Test disk update when disk_io_counters raises exception."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        mock_psutil.disk_io_counters.side_effect = Exception("Disk error")
        self.monitor._last_disk = MagicMock()
        self.monitor.tabs.currentIndex.return_value = 0
        
        MetricsUpdater._update_disk(self.monitor, 1.0)
        
        # Should handle None disk and set values to 0
        assert self.monitor._last_disk is None

    @patch('system_monitor.core.metrics_updater.psutil')
    def test_update_disk_on_disk_tab(self, mock_psutil):
        """Test disk update when on disk tab."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        last_disk = MagicMock(read_bytes=1000, write_bytes=2000)
        current_disk = MagicMock(read_bytes=2000, write_bytes=4000)
        self.monitor._last_disk = last_disk
        mock_psutil.disk_io_counters.return_value = current_disk
        self.monitor.tabs.currentIndex.return_value = 4  # Disk tab
        
        MetricsUpdater._update_disk(self.monitor, 1.0)
        
        self.monitor.chart_disk.append.assert_called_once()

    def test_update_gpu_no_refresh_yet(self):
        """Test GPU update when refresh interval not reached."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        self.monitor._gpu_refresh_accum = 0.0
        self.monitor.spin_gpu_refresh.value.return_value = 1000  # 1 second
        
        MetricsUpdater._update_gpu(self.monitor, 0.1)
        
        # Should accumulate but not refresh
        assert self.monitor._gpu_refresh_accum == 0.1
        self.monitor.gpu_provider.gpu_utils.assert_not_called()

    def test_update_gpu_refresh_with_data(self):
        """Test GPU update when refresh interval reached with data."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        self.monitor._gpu_refresh_accum = 1.0
        self.monitor.spin_gpu_refresh.value.return_value = 1000  # 1 second
        self.monitor.gpu_provider.gpu_utils.return_value = [50.0, 60.0]
        self.monitor.gpu_provider.gpu_frequencies.return_value = [1500.0, 1600.0]
        self.monitor.gpu_provider.gpu_vram_info.return_value = [(2000, 4000), (3000, 6000)]
        self.monitor.tabs.currentIndex.return_value = 0  # Not on GPU tab
        
        MetricsUpdater._update_gpu(self.monitor, 0.1)
        
        # Should reset accumulator
        assert self.monitor._gpu_refresh_accum == 0.0
        # Should update card with average
        self.monitor.card_gpu.update_percent.assert_called_once_with(55.0)
        self.monitor.card_gpu.set_frequency.assert_called_once_with(1500.0)

    def test_update_gpu_no_data(self):
        """Test GPU update when no GPU data available."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        self.monitor._gpu_refresh_accum = 1.0
        self.monitor.spin_gpu_refresh.value.return_value = 1000
        self.monitor.gpu_provider.gpu_utils.return_value = []
        
        MetricsUpdater._update_gpu(self.monitor, 0.1)
        
        self.monitor.card_gpu.set_unavailable.assert_called_once_with("N/A")
        self.monitor.lbl_gpu_info.setText.assert_called_once_with("No GPU data available")

    @patch('system_monitor.core.metrics_updater.get_gpu_temperatures')
    def test_update_gpu_on_gpu_tab(self, mock_get_temps):
        """Test GPU update when on GPU tab with charts."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        self.monitor._gpu_refresh_accum = 1.0
        self.monitor.spin_gpu_refresh.value.return_value = 1000
        self.monitor.gpu_provider.gpu_utils.return_value = [50.0, 60.0]
        self.monitor.gpu_provider.gpu_frequencies.return_value = [1500.0, 1600.0]
        self.monitor.gpu_provider.gpu_vram_info.return_value = [(2000, 4000), (3000, 6000)]
        self.monitor.tabs.currentIndex.return_value = 5  # GPU tab
        self.monitor.chart_gpu_vram = MagicMock()
        self.monitor.chart_gpu_temp = MagicMock()
        mock_get_temps.return_value = [65.0, 70.0]
        
        MetricsUpdater._update_gpu(self.monitor, 0.1)
        
        self.monitor.chart_gpu.append.assert_called_once_with([50.0, 60.0])
        self.monitor.chart_gpu_vram.append.assert_called_once_with([2000, 3000])
        self.monitor.chart_gpu_temp.append.assert_called_once_with([65.0, 70.0])

    def test_update_gpu_on_gpu_tab_no_vram_chart(self):
        """Test GPU update on GPU tab without VRAM chart."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        self.monitor._gpu_refresh_accum = 1.0
        self.monitor.spin_gpu_refresh.value.return_value = 1000
        self.monitor.gpu_provider.gpu_utils.return_value = [50.0]
        self.monitor.gpu_provider.gpu_frequencies.return_value = [1500.0]
        self.monitor.gpu_provider.gpu_vram_info.return_value = [(2000, 4000)]
        self.monitor.tabs.currentIndex.return_value = 5
        # No chart_gpu_vram attribute
        
        MetricsUpdater._update_gpu(self.monitor, 0.1)
        
        self.monitor.chart_gpu.append.assert_called_once_with([50.0])

    @patch('system_monitor.core.metrics_updater.MetricsUpdater._update_gpu_tooltips')
    @patch('system_monitor.core.metrics_updater.get_gpu_temperatures')
    def test_update_gpu_temp_exception(self, mock_get_temps, mock_tooltips):
        """Test GPU update handles temperature exception."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        self.monitor._gpu_refresh_accum = 1.0
        self.monitor.spin_gpu_refresh.value.return_value = 1000
        self.monitor.gpu_provider.gpu_utils.return_value = [50.0]
        self.monitor.gpu_provider.gpu_frequencies.return_value = [1500.0]
        self.monitor.gpu_provider.gpu_vram_info.return_value = [(2000, 4000)]
        self.monitor.tabs.currentIndex.return_value = 5
        self.monitor.chart_gpu_temp = MagicMock()
        mock_get_temps.side_effect = Exception("Temp error")
        
        MetricsUpdater._update_gpu(self.monitor, 0.1)
        
        # Should continue without crashing
        self.monitor.chart_gpu.append.assert_called_once()
        # Temperature chart should not be updated due to exception
        self.monitor.chart_gpu_temp.append.assert_not_called()

    def test_update_gpu_accum_exception(self):
        """Test GPU update handles accumulator exception."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        # No _gpu_refresh_accum attribute
        delattr(self.monitor, '_gpu_refresh_accum')
        self.monitor.spin_gpu_refresh.value.return_value = 1000
        
        MetricsUpdater._update_gpu(self.monitor, 0.1)
        
        # Should initialize to 0.0
        assert self.monitor._gpu_refresh_accum == 0.0

    @patch('system_monitor.core.metrics_updater.get_gpu_temperatures')
    def test_update_gpu_tooltips_complete(self, mock_get_temps):
        """Test GPU tooltips with complete information."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        self.monitor.gpu_provider.gpu_names.return_value = ["GPU 0 Name", "GPU 1 Name"]
        mock_get_temps.return_value = [65.0, 70.0]
        utils = [50.0, 60.0]
        vram_info = [(2000, 4000), (3000, 6000)]
        freqs = [1500.0, 1600.0]
        
        MetricsUpdater._update_gpu_tooltips(self.monitor, utils, vram_info, freqs)
        
        self.monitor.card_gpu.set_tooltip.assert_called_once()
        self.monitor.lbl_gpu_info.setText.assert_called_once()
        
        # Check tooltip contains expected information
        tooltip = self.monitor.card_gpu.set_tooltip.call_args[0][0]
        assert "GPU 0 Name" in tooltip
        assert "50%" in tooltip
        assert "2000" in tooltip
        assert "1500" in tooltip
        assert "65°C" in tooltip

    @patch('system_monitor.core.metrics_updater.get_gpu_temperatures')
    def test_update_gpu_tooltips_minimal(self, mock_get_temps):
        """Test GPU tooltips with minimal information."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        self.monitor.gpu_provider.gpu_names.return_value = []
        mock_get_temps.return_value = []
        utils = [50.0]
        vram_info = []
        freqs = []
        
        MetricsUpdater._update_gpu_tooltips(self.monitor, utils, vram_info, freqs)
        
        # Should still set tooltip with basic info
        tooltip = self.monitor.card_gpu.set_tooltip.call_args[0][0]
        assert "GPU 0" in tooltip
        assert "50%" in tooltip

    @patch('system_monitor.core.metrics_updater.get_gpu_temperatures')
    def test_update_gpu_tooltips_zero_vram(self, mock_get_temps):
        """Test GPU tooltips with zero total VRAM."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        self.monitor.gpu_provider.gpu_names.return_value = ["GPU 0"]
        mock_get_temps.return_value = [65.0]
        utils = [50.0]
        vram_info = [(0, 0)]  # Zero total VRAM
        freqs = [1500.0]
        
        MetricsUpdater._update_gpu_tooltips(self.monitor, utils, vram_info, freqs)
        
        tooltip = self.monitor.card_gpu.set_tooltip.call_args[0][0]
        # Should not include VRAM info when total is 0
        assert "VRAM" not in tooltip

    def test_update_processes_no_refresh_yet(self):
        """Test process update when refresh interval not reached."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        self.monitor._proc_refresh_accum = 0.0
        self.monitor.spin_proc_refresh.value.return_value = 1000
        self.monitor.refresh_processes = MagicMock()
        
        MetricsUpdater._update_processes(self.monitor, 0.1)
        
        # Should accumulate but not refresh
        assert self.monitor._proc_refresh_accum == 0.1
        self.monitor.refresh_processes.assert_not_called()

    def test_update_processes_refresh(self):
        """Test process update when refresh interval reached."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        self.monitor._proc_refresh_accum = 1.0
        self.monitor.spin_proc_refresh.value.return_value = 1000
        self.monitor.refresh_processes = MagicMock()
        
        MetricsUpdater._update_processes(self.monitor, 0.1)
        
        # Should reset and refresh
        assert self.monitor._proc_refresh_accum == 0.0
        self.monitor.refresh_processes.assert_called_once()

    def test_update_processes_accum_exception(self):
        """Test process update handles accumulator exception."""
        from system_monitor.core.metrics_updater import MetricsUpdater
        
        delattr(self.monitor, '_proc_refresh_accum')
        self.monitor.spin_proc_refresh.value.return_value = 1000
        self.monitor.refresh_processes = MagicMock()
        
        MetricsUpdater._update_processes(self.monitor, 0.1)
        
        # Should initialize to 0.0
        assert self.monitor._proc_refresh_accum == 0.0
