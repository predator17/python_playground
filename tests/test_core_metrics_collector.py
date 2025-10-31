"""Tests for MetricsCollector class."""

#      Copyright (c) 2025 predator. All rights reserved.

from unittest.mock import patch, MagicMock
import pytest


@pytest.fixture
def mock_psutil_module():
    """Mock psutil module for metrics_collector."""
    mock = MagicMock()
    mock.cpu_percent.return_value = 45.5
    mock.cpu_freq.return_value = MagicMock(current=2400, min=800, max=3600)
    mock.virtual_memory.return_value = MagicMock(
        total=16000000000,
        percent=50.0
    )
    mock.net_io_counters.return_value = MagicMock(
        bytes_sent=1000000,
        bytes_recv=2000000
    )
    mock.disk_io_counters.return_value = MagicMock(
        read_bytes=5000000,
        write_bytes=3000000
    )
    return mock


class TestMetricsCollector:
    """Test MetricsCollector class."""

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_init(self, mock_psutil):
        """Test MetricsCollector initialization."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        collector = MetricsCollector(max_workers=4)
        
        assert collector._executor is not None
        assert collector._executor._max_workers == 4

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_all_success(self, mock_psutil):
        """Test collect_all returns all metrics successfully."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        # Setup mock returns
        mock_psutil.cpu_percent.return_value = 45.5
        mock_psutil.cpu_freq.return_value = MagicMock(current=2400)
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.net_io_counters.return_value = MagicMock(bytes_sent=1000)
        mock_psutil.disk_io_counters.return_value = MagicMock(read_bytes=5000)
        
        collector = MetricsCollector()
        results = collector.collect_all()
        
        assert 'cpu' in results
        assert 'cpu_percpu' in results
        assert 'cpu_freq' in results
        assert 'memory' in results
        assert 'network' in results
        assert 'disk' in results
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_cpu_percent(self, mock_psutil):
        """Test _collect_cpu_percent."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        mock_psutil.cpu_percent.return_value = 67.8
        
        collector = MetricsCollector()
        result = collector._collect_cpu_percent()
        
        assert result == 67.8
        mock_psutil.cpu_percent.assert_called_with(interval=None)
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_cpu_percent_error(self, mock_psutil):
        """Test _collect_cpu_percent handles errors."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        mock_psutil.cpu_percent.side_effect = Exception("Test error")
        
        collector = MetricsCollector()
        result = collector._collect_cpu_percent()
        
        assert result == 0.0
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_cpu_percpu(self, mock_psutil):
        """Test _collect_cpu_percpu."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        mock_psutil.cpu_percent.return_value = [10.5, 20.3, 30.1, 40.9]
        
        collector = MetricsCollector()
        result = collector._collect_cpu_percpu()
        
        assert result == [10.5, 20.3, 30.1, 40.9]
        mock_psutil.cpu_percent.assert_called_with(interval=None, percpu=True)
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_cpu_percpu_empty(self, mock_psutil):
        """Test _collect_cpu_percpu with empty result."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        mock_psutil.cpu_percent.return_value = []
        
        collector = MetricsCollector()
        result = collector._collect_cpu_percpu()
        
        assert result == []
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_cpu_percpu_error(self, mock_psutil):
        """Test _collect_cpu_percpu handles errors."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        mock_psutil.cpu_percent.side_effect = Exception("Test error")
        
        collector = MetricsCollector()
        result = collector._collect_cpu_percpu()
        
        assert result == []
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_cpu_freq(self, mock_psutil):
        """Test _collect_cpu_freq."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        freq_obj = MagicMock(current=2400, min=800, max=3600)
        mock_psutil.cpu_freq.return_value = freq_obj
        
        collector = MetricsCollector()
        result = collector._collect_cpu_freq()
        
        assert result == freq_obj
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_cpu_freq_error(self, mock_psutil):
        """Test _collect_cpu_freq handles errors."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        mock_psutil.cpu_freq.side_effect = Exception("Test error")
        
        collector = MetricsCollector()
        result = collector._collect_cpu_freq()
        
        assert result is None
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_memory(self, mock_psutil):
        """Test _collect_memory."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        mem_obj = MagicMock(total=16000000000, percent=50.0)
        mock_psutil.virtual_memory.return_value = mem_obj
        
        collector = MetricsCollector()
        result = collector._collect_memory()
        
        assert result == mem_obj
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_memory_error(self, mock_psutil):
        """Test _collect_memory handles errors."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        mock_psutil.virtual_memory.side_effect = Exception("Test error")
        
        collector = MetricsCollector()
        result = collector._collect_memory()
        
        assert result is None
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_network(self, mock_psutil):
        """Test _collect_network."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        net_obj = MagicMock(bytes_sent=1000000, bytes_recv=2000000)
        mock_psutil.net_io_counters.return_value = net_obj
        
        collector = MetricsCollector()
        result = collector._collect_network()
        
        assert result == net_obj
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_network_error(self, mock_psutil):
        """Test _collect_network handles errors."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        mock_psutil.net_io_counters.side_effect = Exception("Test error")
        
        collector = MetricsCollector()
        result = collector._collect_network()
        
        assert result is None
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_disk(self, mock_psutil):
        """Test _collect_disk."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        disk_obj = MagicMock(read_bytes=5000000, write_bytes=3000000)
        mock_psutil.disk_io_counters.return_value = disk_obj
        
        collector = MetricsCollector()
        result = collector._collect_disk()
        
        assert result == disk_obj
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_disk_error(self, mock_psutil):
        """Test _collect_disk handles errors."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        mock_psutil.disk_io_counters.side_effect = Exception("Test error")
        
        collector = MetricsCollector()
        result = collector._collect_disk()
        
        assert result is None
        
        collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_shutdown(self, mock_psutil):
        """Test shutdown method."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        collector = MetricsCollector()
        collector.shutdown()
        
        # After shutdown, executor should be shutdown
        assert collector._executor._shutdown

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_del(self, mock_psutil):
        """Test __del__ method."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        collector = MetricsCollector()
        # Call __del__ explicitly
        collector.__del__()
        
        # Should not raise exception
        assert collector._executor._shutdown

    @patch('system_monitor.core.metrics_collector.psutil')
    def test_collect_all_with_errors(self, mock_psutil):
        """Test collect_all handles partial failures."""
        from system_monitor.core.metrics_collector import MetricsCollector
        
        # Some succeed, some fail
        mock_psutil.cpu_percent.return_value = 45.5
        mock_psutil.cpu_freq.side_effect = Exception("Freq error")
        mock_psutil.virtual_memory.return_value = MagicMock(percent=50.0)
        mock_psutil.net_io_counters.side_effect = Exception("Net error")
        mock_psutil.disk_io_counters.return_value = MagicMock(read_bytes=5000)
        
        collector = MetricsCollector()
        results = collector.collect_all()
        
        # Should still have all keys, but some may be None
        assert 'cpu' in results
        assert 'cpu_freq' in results
        assert 'memory' in results
        assert 'network' in results
        assert 'disk' in results
        
        collector.shutdown()
