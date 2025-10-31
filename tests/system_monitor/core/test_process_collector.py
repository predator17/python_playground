"""Unit tests for system_monitor.core.process_collector module."""

#      Copyright (c) 2025 predator. All rights reserved.

import unittest
import time
import threading
from unittest.mock import MagicMock, patch, call
from queue import Queue, Empty

from system_monitor.core.process_collector import ProcessCollector


class TestProcessCollectorInit(unittest.TestCase):
    """Test ProcessCollector initialization."""

    def test_initialization_default(self):
        """Test initialization with default parameters."""
        collector = ProcessCollector()
        
        self.assertIsNotNone(collector._executor)
        self.assertIsInstance(collector._result_queue, Queue)
        self.assertEqual(collector._result_queue.maxsize, 1)
        self.assertFalse(collector._collecting)
        self.assertFalse(collector._shutdown)
        
        collector.shutdown()

    def test_initialization_custom_workers(self):
        """Test initialization with custom max_workers."""
        collector = ProcessCollector(max_workers=2)
        
        self.assertIsNotNone(collector._executor)
        collector.shutdown()


class TestProcessCollectorAsyncCollection(unittest.TestCase):
    """Test ProcessCollector async collection workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = ProcessCollector(max_workers=1)

    def tearDown(self):
        """Clean up after tests."""
        self.collector.shutdown()

    def test_collect_async_starts_collection(self):
        """Test collect_async initiates background collection."""
        with patch.object(self.collector._executor, 'submit') as mock_submit:
            mock_future = MagicMock()
            mock_submit.return_value = mock_future
            
            self.collector.collect_async(n_cores=4, proc_filter="")
            
            mock_submit.assert_called_once()
            self.assertTrue(self.collector._collecting)

    def test_collect_async_already_collecting(self):
        """Test collect_async doesn't start if already collecting."""
        self.collector._collecting = True
        
        with patch.object(self.collector._executor, 'submit') as mock_submit:
            self.collector.collect_async(n_cores=4, proc_filter="")
            
            mock_submit.assert_not_called()

    def test_collect_async_when_shutdown(self):
        """Test collect_async doesn't start if already shutdown."""
        self.collector._shutdown = True
        
        with patch.object(self.collector._executor, 'submit') as mock_submit:
            self.collector.collect_async(n_cores=4, proc_filter="")
            
            mock_submit.assert_not_called()

    def test_collect_async_with_filter(self):
        """Test collect_async passes filter parameter."""
        with patch.object(self.collector._executor, 'submit') as mock_submit:
            mock_future = MagicMock()
            mock_submit.return_value = mock_future
            
            self.collector.collect_async(n_cores=4, proc_filter="python")
            
            args, kwargs = mock_submit.call_args
            self.assertEqual(args[0], self.collector._collect_processes)
            self.assertEqual(args[1], 4)
            self.assertEqual(args[2], "python")


class TestProcessCollectorCollectProcesses(unittest.TestCase):
    """Test ProcessCollector _collect_processes method."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = ProcessCollector(max_workers=1)

    def tearDown(self):
        """Clean up after tests."""
        self.collector.shutdown()

    @patch('system_monitor.core.process_collector.psutil.process_iter')
    def test_collect_processes_basic(self, mock_iter):
        """Test basic process collection."""
        mock_proc = MagicMock()
        mock_proc.cpu_percent.return_value = 25.0
        mock_proc.info = {
            'pid': 1234,
            'name': 'test_process',
            'memory_percent': 10.5,
            'num_threads': 2
        }
        mock_proc.cpu_affinity.return_value = [0, 1, 2, 3]
        mock_iter.return_value = [mock_proc]
        
        result = self.collector._collect_processes(n_cores=4, proc_filter="")
        
        self.assertIsInstance(result, dict)
        self.assertIn('core_processes', result)
        self.assertIn('proc_count', result)
        self.assertIn('total_threads', result)
        self.assertEqual(result['proc_count'], 1)
        self.assertEqual(result['total_threads'], 2)

    @patch('system_monitor.core.process_collector.psutil.process_iter')
    def test_collect_processes_with_filter(self, mock_iter):
        """Test process collection with filter."""
        mock_proc1 = MagicMock()
        mock_proc1.cpu_percent.return_value = 25.0
        mock_proc1.info = {
            'pid': 1234,
            'name': 'python',
            'memory_percent': 10.5,
            'num_threads': 2
        }
        mock_proc1.cpu_affinity.return_value = [0, 1, 2, 3]
        
        mock_proc2 = MagicMock()
        mock_proc2.cpu_percent.return_value = 15.0
        mock_proc2.info = {
            'pid': 5678,
            'name': 'chrome',
            'memory_percent': 5.0,
            'num_threads': 4
        }
        mock_proc2.cpu_affinity.return_value = [0, 1, 2, 3]
        
        mock_iter.return_value = [mock_proc1, mock_proc2]
        
        result = self.collector._collect_processes(n_cores=4, proc_filter="python")
        
        # Should only include python process
        self.assertEqual(result['proc_count'], 2)  # Both counted before filter
        # Check if filtered correctly by looking at all_cores_processes
        self.assertEqual(len(result['all_cores_processes']), 1)

    @patch('system_monitor.core.process_collector.psutil.process_iter')
    def test_collect_processes_pinned_to_core(self, mock_iter):
        """Test process pinned to specific core."""
        mock_proc = MagicMock()
        mock_proc.cpu_percent.return_value = 50.0
        mock_proc.info = {
            'pid': 1234,
            'name': 'pinned_proc',
            'memory_percent': 15.0,
            'num_threads': 1
        }
        mock_proc.cpu_affinity.return_value = [2]  # Pinned to core 2
        mock_iter.return_value = [mock_proc]
        
        result = self.collector._collect_processes(n_cores=4, proc_filter="")
        
        # Should be in core_processes[2]
        self.assertEqual(len(result['core_processes'][2]), 1)
        self.assertEqual(result['core_processes'][2][0][1], 1234)  # PID

    @patch('system_monitor.core.process_collector.psutil.process_iter')
    def test_collect_processes_cpu_exception(self, mock_iter):
        """Test handling CPU percent exception."""
        mock_proc = MagicMock()
        mock_proc.cpu_percent.side_effect = Exception("Test error")
        mock_proc.info = {
            'pid': 1234,
            'name': 'test',
            'memory_percent': 10.0,
            'num_threads': 1
        }
        mock_proc.cpu_affinity.return_value = [0, 1, 2, 3]
        mock_iter.return_value = [mock_proc]
        
        result = self.collector._collect_processes(n_cores=4, proc_filter="")
        
        # Should handle exception and set CPU to 0.0
        self.assertEqual(result['proc_count'], 1)
        cpu_val = result['all_cores_processes'][0][0]
        self.assertEqual(cpu_val, 0.0)

    @patch('system_monitor.core.process_collector.psutil.process_iter')
    def test_collect_processes_affinity_exception(self, mock_iter):
        """Test handling affinity exception."""
        mock_proc = MagicMock()
        mock_proc.cpu_percent.return_value = 25.0
        mock_proc.info = {
            'pid': 1234,
            'name': 'test',
            'memory_percent': 10.0,
            'num_threads': 1
        }
        mock_proc.cpu_affinity.side_effect = Exception("Test error")
        mock_iter.return_value = [mock_proc]
        
        result = self.collector._collect_processes(n_cores=4, proc_filter="")
        
        # Should handle exception and add to all_cores_processes
        self.assertEqual(len(result['all_cores_processes']), 1)

    @patch('system_monitor.core.process_collector.psutil.process_iter')
    def test_collect_processes_shutdown_flag(self, mock_iter):
        """Test collection respects shutdown flag."""
        self.collector._shutdown = True
        
        result = self.collector._collect_processes(n_cores=4, proc_filter="")
        
        # Should return early
        self.assertIsInstance(result, dict)
        self.assertEqual(result['proc_count'], 0)

    @patch('system_monitor.core.process_collector.psutil.process_iter')
    def test_collect_processes_general_exception(self, mock_iter):
        """Test handling general exception during collection."""
        mock_iter.side_effect = Exception("Test error")
        
        result = self.collector._collect_processes(n_cores=4, proc_filter="")
        
        # Should return error result
        self.assertIn('error', result)
        self.assertEqual(result['proc_count'], 0)


class TestProcessCollectorCallbacks(unittest.TestCase):
    """Test ProcessCollector callback mechanisms."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = ProcessCollector(max_workers=1)

    def tearDown(self):
        """Clean up after tests."""
        self.collector.shutdown()

    def test_on_collection_complete_resets_flag(self):
        """Test callback resets collecting flag."""
        self.collector._collecting = True
        
        mock_future = MagicMock()
        mock_future.result.return_value = {
            'core_processes': {},
            'proc_count': 0,
            'total_threads': 0
        }
        
        self.collector._on_collection_complete(mock_future)
        
        self.assertFalse(self.collector._collecting)

    def test_on_collection_complete_puts_result(self):
        """Test callback puts result in queue."""
        mock_future = MagicMock()
        test_result = {
            'core_processes': {},
            'proc_count': 5,
            'total_threads': 10
        }
        mock_future.result.return_value = test_result
        
        self.collector._on_collection_complete(mock_future)
        
        # Should be in queue
        result = self.collector.get_result()
        self.assertEqual(result, test_result)

    def test_on_collection_complete_replaces_old_result(self):
        """Test callback replaces old result in queue."""
        # Put an old result
        old_result = {'proc_count': 1}
        self.collector._result_queue.put(old_result)
        
        mock_future = MagicMock()
        new_result = {'proc_count': 2}
        mock_future.result.return_value = new_result
        
        self.collector._on_collection_complete(mock_future)
        
        # Should get new result
        result = self.collector.get_result()
        self.assertEqual(result['proc_count'], 2)

    def test_on_collection_complete_handles_exception(self):
        """Test callback handles future exception."""
        self.collector._collecting = True
        
        mock_future = MagicMock()
        mock_future.result.side_effect = Exception("Test error")
        
        # Should not raise
        self.collector._on_collection_complete(mock_future)
        
        # Flag should still be reset
        self.assertFalse(self.collector._collecting)


class TestProcessCollectorGetResult(unittest.TestCase):
    """Test ProcessCollector get_result method."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = ProcessCollector(max_workers=1)

    def tearDown(self):
        """Clean up after tests."""
        self.collector.shutdown()

    def test_get_result_empty_queue(self):
        """Test get_result returns None when queue is empty."""
        result = self.collector.get_result()
        
        self.assertIsNone(result)

    def test_get_result_returns_data(self):
        """Test get_result returns data from queue."""
        test_data = {'proc_count': 10}
        self.collector._result_queue.put(test_data)
        
        result = self.collector.get_result()
        
        self.assertEqual(result, test_data)

    def test_get_result_consumes_queue(self):
        """Test get_result removes item from queue."""
        test_data = {'proc_count': 10}
        self.collector._result_queue.put(test_data)
        
        result1 = self.collector.get_result()
        result2 = self.collector.get_result()
        
        self.assertEqual(result1, test_data)
        self.assertIsNone(result2)


class TestProcessCollectorIsCollecting(unittest.TestCase):
    """Test ProcessCollector is_collecting method."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = ProcessCollector(max_workers=1)

    def tearDown(self):
        """Clean up after tests."""
        self.collector.shutdown()

    def test_is_collecting_false_initially(self):
        """Test is_collecting returns False initially."""
        self.assertFalse(self.collector.is_collecting())

    def test_is_collecting_true_during_collection(self):
        """Test is_collecting returns True during collection."""
        self.collector._collecting = True
        
        self.assertTrue(self.collector.is_collecting())

    def test_is_collecting_thread_safe(self):
        """Test is_collecting is thread-safe."""
        results = []
        
        def check_collecting():
            result = self.collector.is_collecting()
            results.append(result)
        
        threads = [threading.Thread(target=check_collecting) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 10 results, all False
        self.assertEqual(len(results), 10)
        for r in results:
            self.assertFalse(r)


class TestProcessCollectorShutdown(unittest.TestCase):
    """Test ProcessCollector shutdown functionality."""

    def test_shutdown_sets_flag(self):
        """Test shutdown sets shutdown flag."""
        collector = ProcessCollector()
        
        collector.shutdown()
        
        self.assertTrue(collector._shutdown)

    def test_shutdown_stops_executor(self):
        """Test shutdown stops executor."""
        collector = ProcessCollector()
        
        collector.shutdown()
        
        self.assertTrue(collector._executor._shutdown)

    def test_shutdown_idempotent(self):
        """Test shutdown can be called multiple times."""
        collector = ProcessCollector()
        
        collector.shutdown()
        collector.shutdown()  # Should not raise
        
        self.assertTrue(collector._shutdown)

    def test_del_calls_shutdown(self):
        """Test __del__ calls shutdown."""
        collector = ProcessCollector()
        collector.shutdown = MagicMock()
        
        collector.__del__()
        
        collector.shutdown.assert_called_once()

    def test_del_handles_exceptions(self):
        """Test __del__ handles shutdown exceptions."""
        collector = ProcessCollector()
        collector.shutdown = MagicMock(side_effect=Exception("Test error"))
        
        # Should not raise
        collector.__del__()


class TestProcessCollectorIntegration(unittest.TestCase):
    """Integration tests for ProcessCollector."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = ProcessCollector(max_workers=1)

    def tearDown(self):
        """Clean up after tests."""
        self.collector.shutdown()

    @patch('system_monitor.core.process_collector.psutil.process_iter')
    def test_full_async_workflow(self, mock_iter):
        """Test complete async collection workflow."""
        # Mock processes
        mock_proc = MagicMock()
        mock_proc.cpu_percent.return_value = 50.0
        mock_proc.info = {
            'pid': 1234,
            'name': 'test_process',
            'memory_percent': 20.0,
            'num_threads': 3
        }
        mock_proc.cpu_affinity.return_value = [0, 1]
        mock_iter.return_value = [mock_proc]
        
        # Start async collection
        self.collector.collect_async(n_cores=2, proc_filter="")
        
        # Wait for collection to complete
        time.sleep(0.1)
        
        # Get result
        result = self.collector.get_result()
        
        self.assertIsNotNone(result)
        self.assertEqual(result['proc_count'], 1)
        self.assertEqual(result['total_threads'], 3)


if __name__ == '__main__':
    unittest.main()
