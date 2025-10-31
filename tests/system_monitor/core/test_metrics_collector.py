"""Unit tests for system_monitor.core.metrics_collector module."""

#      Copyright (c) 2025 predator. All rights reserved.

import unittest
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor

from system_monitor.core.metrics_collector import MetricsCollector


class TestMetricsCollectorInit(unittest.TestCase):
    """Test MetricsCollector initialization."""

    def test_initialization_default_workers(self):
        """Test initialization with default max_workers."""
        collector = MetricsCollector()
        
        self.assertIsNotNone(collector._executor)
        self.assertIsInstance(collector._executor, ThreadPoolExecutor)
        collector.shutdown()

    def test_initialization_custom_workers(self):
        """Test initialization with custom max_workers."""
        collector = MetricsCollector(max_workers=2)
        
        self.assertIsNotNone(collector._executor)
        collector.shutdown()


class TestMetricsCollectorCollection(unittest.TestCase):
    """Test MetricsCollector data collection methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = MetricsCollector(max_workers=2)

    def tearDown(self):
        """Clean up after tests."""
        self.collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil.cpu_percent')
    def test_collect_cpu_percent(self, mock_cpu):
        """Test CPU percent collection."""
        mock_cpu.return_value = 45.5
        
        result = self.collector._collect_cpu_percent()
        
        self.assertEqual(result, 45.5)
        mock_cpu.assert_called_once_with(interval=None)

    @patch('system_monitor.core.metrics_collector.psutil.cpu_percent')
    def test_collect_cpu_percent_exception(self, mock_cpu):
        """Test CPU percent collection handles exceptions."""
        mock_cpu.side_effect = Exception("Test error")
        
        result = self.collector._collect_cpu_percent()
        
        self.assertEqual(result, 0.0)

    @patch('system_monitor.core.metrics_collector.psutil.cpu_percent')
    def test_collect_cpu_percpu(self, mock_cpu):
        """Test per-core CPU percent collection."""
        mock_cpu.return_value = [25.0, 50.0, 75.0, 100.0]
        
        result = self.collector._collect_cpu_percpu()
        
        self.assertEqual(result, [25.0, 50.0, 75.0, 100.0])
        mock_cpu.assert_called_once_with(interval=None, percpu=True)

    @patch('system_monitor.core.metrics_collector.psutil.cpu_percent')
    def test_collect_cpu_percpu_empty(self, mock_cpu):
        """Test per-core CPU collection with None result."""
        mock_cpu.return_value = None
        
        result = self.collector._collect_cpu_percpu()
        
        self.assertEqual(result, [])

    @patch('system_monitor.core.metrics_collector.psutil.cpu_percent')
    def test_collect_cpu_percpu_exception(self, mock_cpu):
        """Test per-core CPU collection handles exceptions."""
        mock_cpu.side_effect = Exception("Test error")
        
        result = self.collector._collect_cpu_percpu()
        
        self.assertEqual(result, [])

    @patch('system_monitor.core.metrics_collector.psutil.cpu_freq')
    def test_collect_cpu_freq(self, mock_freq):
        """Test CPU frequency collection."""
        mock_freq_obj = MagicMock()
        mock_freq_obj.current = 3600.0
        mock_freq.return_value = mock_freq_obj
        
        result = self.collector._collect_cpu_freq()
        
        self.assertEqual(result, mock_freq_obj)
        mock_freq.assert_called_once()

    @patch('system_monitor.core.metrics_collector.psutil.cpu_freq')
    def test_collect_cpu_freq_exception(self, mock_freq):
        """Test CPU frequency collection handles exceptions."""
        mock_freq.side_effect = Exception("Test error")
        
        result = self.collector._collect_cpu_freq()
        
        self.assertIsNone(result)

    @patch('system_monitor.core.metrics_collector.psutil.virtual_memory')
    def test_collect_memory(self, mock_mem):
        """Test memory collection."""
        mock_mem_obj = MagicMock()
        mock_mem_obj.percent = 65.5
        mock_mem.return_value = mock_mem_obj
        
        result = self.collector._collect_memory()
        
        self.assertEqual(result, mock_mem_obj)
        mock_mem.assert_called_once()

    @patch('system_monitor.core.metrics_collector.psutil.virtual_memory')
    def test_collect_memory_exception(self, mock_mem):
        """Test memory collection handles exceptions."""
        mock_mem.side_effect = Exception("Test error")
        
        result = self.collector._collect_memory()
        
        self.assertIsNone(result)

    @patch('system_monitor.core.metrics_collector.psutil.net_io_counters')
    def test_collect_network(self, mock_net):
        """Test network collection."""
        mock_net_obj = MagicMock()
        mock_net_obj.bytes_sent = 1000
        mock_net.return_value = mock_net_obj
        
        result = self.collector._collect_network()
        
        self.assertEqual(result, mock_net_obj)
        mock_net.assert_called_once()

    @patch('system_monitor.core.metrics_collector.psutil.net_io_counters')
    def test_collect_network_exception(self, mock_net):
        """Test network collection handles exceptions."""
        mock_net.side_effect = Exception("Test error")
        
        result = self.collector._collect_network()
        
        self.assertIsNone(result)

    @patch('system_monitor.core.metrics_collector.psutil.disk_io_counters')
    def test_collect_disk(self, mock_disk):
        """Test disk collection."""
        mock_disk_obj = MagicMock()
        mock_disk_obj.read_bytes = 5000
        mock_disk.return_value = mock_disk_obj
        
        result = self.collector._collect_disk()
        
        self.assertEqual(result, mock_disk_obj)
        mock_disk.assert_called_once()

    @patch('system_monitor.core.metrics_collector.psutil.disk_io_counters')
    def test_collect_disk_exception(self, mock_disk):
        """Test disk collection handles exceptions."""
        mock_disk.side_effect = Exception("Test error")
        
        result = self.collector._collect_disk()
        
        self.assertIsNone(result)


class TestMetricsCollectorCollectAll(unittest.TestCase):
    """Test MetricsCollector parallel collection."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = MetricsCollector(max_workers=4)

    def tearDown(self):
        """Clean up after tests."""
        self.collector.shutdown()

    @patch('system_monitor.core.metrics_collector.psutil.disk_io_counters')
    @patch('system_monitor.core.metrics_collector.psutil.net_io_counters')
    @patch('system_monitor.core.metrics_collector.psutil.virtual_memory')
    @patch('system_monitor.core.metrics_collector.psutil.cpu_freq')
    @patch('system_monitor.core.metrics_collector.psutil.cpu_percent')
    def test_collect_all_success(self, mock_cpu, mock_freq, mock_mem, mock_net, mock_disk):
        """Test collect_all returns all metrics."""
        mock_cpu.return_value = 50.0
        mock_freq.return_value = MagicMock(current=3600.0)
        mock_mem.return_value = MagicMock(percent=60.0)
        mock_net.return_value = MagicMock(bytes_sent=1000)
        mock_disk.return_value = MagicMock(read_bytes=5000)
        
        result = self.collector.collect_all()
        
        self.assertIsInstance(result, dict)
        self.assertIn('cpu', result)
        self.assertIn('cpu_percpu', result)
        self.assertIn('cpu_freq', result)
        self.assertIn('memory', result)
        self.assertIn('network', result)
        self.assertIn('disk', result)

    @patch('system_monitor.core.metrics_collector.psutil.disk_io_counters')
    @patch('system_monitor.core.metrics_collector.psutil.net_io_counters')
    @patch('system_monitor.core.metrics_collector.psutil.virtual_memory')
    @patch('system_monitor.core.metrics_collector.psutil.cpu_freq')
    @patch('system_monitor.core.metrics_collector.psutil.cpu_percent')
    def test_collect_all_with_values(self, mock_cpu, mock_freq, mock_mem, mock_net, mock_disk):
        """Test collect_all returns correct values."""
        mock_cpu.side_effect = [75.5, [25.0, 50.0]]  # First for cpu, second for cpu_percpu
        mock_freq_obj = MagicMock()
        mock_freq_obj.current = 3600.0
        mock_freq.return_value = mock_freq_obj
        mock_mem_obj = MagicMock()
        mock_mem_obj.percent = 65.0
        mock_mem.return_value = mock_mem_obj
        mock_net.return_value = MagicMock()
        mock_disk.return_value = MagicMock()
        
        result = self.collector.collect_all()
        
        self.assertEqual(result['cpu'], 75.5)
        self.assertEqual(result['cpu_percpu'], [25.0, 50.0])
        self.assertEqual(result['cpu_freq'], mock_freq_obj)
        self.assertEqual(result['memory'], mock_mem_obj)

    @patch('system_monitor.core.metrics_collector.psutil.disk_io_counters')
    @patch('system_monitor.core.metrics_collector.psutil.net_io_counters')
    @patch('system_monitor.core.metrics_collector.psutil.virtual_memory')
    @patch('system_monitor.core.metrics_collector.psutil.cpu_freq')
    @patch('system_monitor.core.metrics_collector.psutil.cpu_percent')
    def test_collect_all_partial_failure(self, mock_cpu, mock_freq, mock_mem, mock_net, mock_disk):
        """Test collect_all handles partial failures."""
        mock_cpu.return_value = 50.0
        mock_freq.side_effect = Exception("Test error")
        mock_mem.return_value = MagicMock()
        mock_net.return_value = MagicMock()
        mock_disk.return_value = MagicMock()
        
        result = self.collector.collect_all()
        
        self.assertIsNotNone(result['cpu'])
        self.assertIsNone(result['cpu_freq'])  # Failed
        self.assertIsNotNone(result['memory'])

    def test_collect_all_returns_dict(self):
        """Test collect_all always returns a dictionary."""
        result = self.collector.collect_all()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 6)


class TestMetricsCollectorShutdown(unittest.TestCase):
    """Test MetricsCollector shutdown functionality."""

    def test_shutdown(self):
        """Test shutdown stops executor."""
        collector = MetricsCollector()
        
        collector.shutdown()
        
        # Executor should be shutdown (accessing _shutdown should be True)
        self.assertTrue(collector._executor._shutdown)

    def test_shutdown_idempotent(self):
        """Test shutdown can be called multiple times safely."""
        collector = MetricsCollector()
        
        collector.shutdown()
        collector.shutdown()  # Should not raise
        
        self.assertTrue(collector._executor._shutdown)

    def test_del_calls_shutdown(self):
        """Test __del__ calls shutdown."""
        collector = MetricsCollector()
        
        # Mock shutdown to verify it's called
        collector.shutdown = MagicMock()
        
        collector.__del__()
        
        collector.shutdown.assert_called_once()

    def test_del_handles_exceptions(self):
        """Test __del__ handles shutdown exceptions gracefully."""
        collector = MetricsCollector()
        
        # Make shutdown raise an exception
        collector.shutdown = MagicMock(side_effect=Exception("Test error"))
        
        # Should not raise
        collector.__del__()


if __name__ == '__main__':
    unittest.main()
