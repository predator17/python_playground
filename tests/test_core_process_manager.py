"""Tests for ProcessManager module."""

#      Copyright (c) 2025 predator. All rights reserved.

import pytest
from unittest.mock import MagicMock, patch, Mock
from PySide6.QtWidgets import QTreeWidgetItem


class TestProcessManager:
    """Test ProcessManager class methods."""

    def setup_method(self):
        """Setup mock monitor for each test."""
        # Reset class-level collector before each test
        from system_monitor.core.process_manager import ProcessManager
        ProcessManager._collector = None
        
        self.monitor = MagicMock()
        self.monitor.proc_tree = MagicMock()
        self.monitor.lbl_proc_summary = MagicMock()
        self.monitor.lbl_asyncio = MagicMock()
        self.monitor._proc_filter = ""

    def test_initialize_collector_creates_collector(self):
        """Test initialize_collector creates ProcessCollector."""
        from system_monitor.core.process_manager import ProcessManager
        
        with patch('system_monitor.core.process_manager.ProcessCollector') as mock_collector_cls:
            mock_collector = MagicMock()
            mock_collector_cls.return_value = mock_collector
            
            ProcessManager.initialize_collector()
            
            mock_collector_cls.assert_called_once_with(max_workers=1)
            assert ProcessManager._collector == mock_collector

    def test_initialize_collector_only_once(self):
        """Test initialize_collector only creates collector once."""
        from system_monitor.core.process_manager import ProcessManager
        
        with patch('system_monitor.core.process_manager.ProcessCollector') as mock_collector_cls:
            mock_collector = MagicMock()
            mock_collector_cls.return_value = mock_collector
            
            ProcessManager.initialize_collector()
            ProcessManager.initialize_collector()
            
            # Should only be called once
            mock_collector_cls.assert_called_once()

    def test_shutdown_collector_shuts_down(self):
        """Test shutdown_collector properly shuts down collector."""
        from system_monitor.core.process_manager import ProcessManager
        
        mock_collector = MagicMock()
        ProcessManager._collector = mock_collector
        
        ProcessManager.shutdown_collector()
        
        mock_collector.shutdown.assert_called_once()
        assert ProcessManager._collector is None

    def test_shutdown_collector_when_none(self):
        """Test shutdown_collector handles None collector."""
        from system_monitor.core.process_manager import ProcessManager
        
        ProcessManager._collector = None
        
        # Should not raise exception
        ProcessManager.shutdown_collector()
        
        assert ProcessManager._collector is None

    @patch('system_monitor.core.process_manager.psutil')
    def test_on_proc_item_expanded_loads_threads(self, mock_psutil):
        """Test on_proc_item_expanded loads threads for process."""
        from system_monitor.core.process_manager import ProcessManager
        
        item = MagicMock(spec=QTreeWidgetItem)
        item.childCount.return_value = 0
        item.text.return_value = "1234"
        
        mock_proc = MagicMock()
        mock_thread_info = MagicMock()
        mock_thread_info.id = 5678
        mock_proc.threads.return_value = [mock_thread_info]
        mock_psutil.Process.return_value = mock_proc
        
        ProcessManager.on_proc_item_expanded(self.monitor, item)
        
        mock_psutil.Process.assert_called_once_with(1234)
        mock_proc.threads.assert_called_once()

    def test_on_proc_item_expanded_already_has_children(self):
        """Test on_proc_item_expanded skips if already has children."""
        from system_monitor.core.process_manager import ProcessManager
        
        item = MagicMock(spec=QTreeWidgetItem)
        item.childCount.return_value = 5
        
        ProcessManager.on_proc_item_expanded(self.monitor, item)
        
        # Should return early without accessing text
        item.text.assert_not_called()

    def test_on_proc_item_expanded_invalid_pid(self):
        """Test on_proc_item_expanded handles invalid PID."""
        from system_monitor.core.process_manager import ProcessManager
        
        item = MagicMock(spec=QTreeWidgetItem)
        item.childCount.return_value = 0
        item.text.return_value = "not_a_number"
        
        # Should not raise exception
        ProcessManager.on_proc_item_expanded(self.monitor, item)

    def test_on_proc_item_expanded_empty_pid(self):
        """Test on_proc_item_expanded handles empty PID."""
        from system_monitor.core.process_manager import ProcessManager
        
        item = MagicMock(spec=QTreeWidgetItem)
        item.childCount.return_value = 0
        item.text.return_value = ""
        
        # Should not raise exception
        ProcessManager.on_proc_item_expanded(self.monitor, item)

    @patch('system_monitor.core.process_manager.psutil')
    def test_on_proc_item_expanded_exception(self, mock_psutil):
        """Test on_proc_item_expanded handles exceptions."""
        from system_monitor.core.process_manager import ProcessManager
        
        item = MagicMock(spec=QTreeWidgetItem)
        item.childCount.return_value = 0
        item.text.return_value = "1234"
        mock_psutil.Process.side_effect = Exception("Process error")
        
        # Should not raise exception
        ProcessManager.on_proc_item_expanded(self.monitor, item)

    @patch('system_monitor.core.process_manager.psutil')
    def test_refresh_processes_priming_pass(self, mock_psutil):
        """Test refresh_processes first pass primes CPU percentages."""
        from system_monitor.core.process_manager import ProcessManager
        
        self.monitor._procs_primed = False
        mock_proc = MagicMock()
        mock_psutil.process_iter.return_value = [mock_proc]
        
        ProcessManager.refresh_processes(self.monitor)
        
        mock_proc.cpu_percent.assert_called_once_with(None)
        assert self.monitor._procs_primed is True

    @patch('system_monitor.core.process_manager.psutil')
    def test_refresh_processes_priming_exception(self, mock_psutil):
        """Test refresh_processes handles exceptions during priming."""
        from system_monitor.core.process_manager import ProcessManager
        
        self.monitor._procs_primed = False
        mock_proc = MagicMock()
        mock_proc.cpu_percent.side_effect = Exception("CPU error")
        mock_psutil.process_iter.return_value = [mock_proc]
        
        ProcessManager.refresh_processes(self.monitor)
        
        assert self.monitor._procs_primed is True

    @patch('system_monitor.core.process_manager.ProcessManager._update_ui_with_result')
    @patch('system_monitor.core.process_manager.psutil')
    def test_refresh_processes_with_result(self, mock_psutil, mock_update_ui):
        """Test refresh_processes updates UI when result available."""
        from system_monitor.core.process_manager import ProcessManager
        
        self.monitor._procs_primed = True
        mock_collector = MagicMock()
        mock_result = {'core_processes': {}, 'proc_count': 10, 'total_threads': 50}
        mock_collector.get_result.return_value = mock_result
        mock_collector.is_collecting.return_value = False
        ProcessManager._collector = mock_collector
        mock_psutil.cpu_count.return_value = 4
        
        ProcessManager.refresh_processes(self.monitor)
        
        mock_update_ui.assert_called_once_with(self.monitor, mock_result)
        mock_collector.collect_async.assert_called_once_with(4, "")

    @patch('system_monitor.core.process_manager.ProcessManager.initialize_collector')
    @patch('system_monitor.core.process_manager.psutil')
    def test_refresh_processes_initializes_collector(self, mock_psutil, mock_init):
        """Test refresh_processes initializes collector if needed."""
        from system_monitor.core.process_manager import ProcessManager
        
        self.monitor._procs_primed = True
        ProcessManager._collector = None
        
        ProcessManager.refresh_processes(self.monitor)
        
        mock_init.assert_called_once()

    @patch('system_monitor.core.process_manager.psutil')
    def test_refresh_processes_skips_collect_if_collecting(self, mock_psutil):
        """Test refresh_processes skips new collection if already collecting."""
        from system_monitor.core.process_manager import ProcessManager
        
        self.monitor._procs_primed = True
        mock_collector = MagicMock()
        mock_collector.get_result.return_value = None
        mock_collector.is_collecting.return_value = True
        ProcessManager._collector = mock_collector
        
        ProcessManager.refresh_processes(self.monitor)
        
        mock_collector.collect_async.assert_not_called()

    def test_refresh_processes_exception_handling(self):
        """Test refresh_processes handles exceptions gracefully."""
        from system_monitor.core.process_manager import ProcessManager
        
        # Cause exception by not setting _procs_primed and mocking process_iter to raise
        with patch('system_monitor.core.process_manager.psutil') as mock_psutil:
            mock_psutil.process_iter.side_effect = Exception("Fatal error")
            
            # Should not raise
            ProcessManager.refresh_processes(self.monitor)

    @patch('system_monitor.core.process_manager.ProcessManager._update_summary_labels')
    @patch('system_monitor.core.process_manager.ProcessManager._build_process_tree')
    @patch('system_monitor.core.process_manager.ProcessManager._save_expansion_state')
    def test_update_ui_with_result_success(self, mock_save_state, mock_build_tree, mock_update_labels):
        """Test _update_ui_with_result successfully updates UI."""
        from system_monitor.core.process_manager import ProcessManager
        
        result = {
            'core_processes': {0: [], 1: []},
            'proc_count': 10,
            'total_threads': 50
        }
        mock_save_state.return_value = (set(), {})
        
        ProcessManager._update_ui_with_result(self.monitor, result)
        
        self.monitor.proc_tree.clear.assert_called_once()
        mock_save_state.assert_called_once_with(self.monitor, 2)
        mock_build_tree.assert_called_once()
        mock_update_labels.assert_called_once_with(self.monitor, 10, 50)

    @patch('system_monitor.core.process_manager.ProcessManager._update_summary_labels')
    @patch('system_monitor.core.process_manager.ProcessManager._build_process_tree')
    @patch('system_monitor.core.process_manager.ProcessManager._save_expansion_state')
    def test_update_ui_with_result_first_build(self, mock_save_state, mock_build_tree, mock_update_labels):
        """Test _update_ui_with_result handles first build."""
        from system_monitor.core.process_manager import ProcessManager
        
        result = {'core_processes': {0: []}, 'proc_count': 5, 'total_threads': 25}
        mock_save_state.return_value = (set(), {})
        
        # First build - no _proc_tree_built attribute
        if hasattr(self.monitor, '_proc_tree_built'):
            delattr(self.monitor, '_proc_tree_built')
        
        ProcessManager._update_ui_with_result(self.monitor, result)
        
        assert self.monitor._proc_tree_built is True
        # Verify first_build=True is passed
        call_args = mock_build_tree.call_args[0]
        assert call_args[3] is True  # first_build parameter

    def test_update_ui_with_result_exception_handling(self):
        """Test _update_ui_with_result handles exceptions."""
        from system_monitor.core.process_manager import ProcessManager
        
        result = {'core_processes': {}}
        self.monitor.proc_tree.clear.side_effect = Exception("Clear error")
        
        # Should not raise
        ProcessManager._update_ui_with_result(self.monitor, result)

    def test_save_expansion_state_no_items(self):
        """Test _save_expansion_state with no items."""
        from system_monitor.core.process_manager import ProcessManager
        
        self.monitor.proc_tree.topLevelItemCount.return_value = 0
        
        expanded_cores, expanded_processes = ProcessManager._save_expansion_state(self.monitor, 4)
        
        assert expanded_cores == set()
        assert expanded_processes == {}

    def test_save_expansion_state_with_expanded_cores(self):
        """Test _save_expansion_state with expanded core items."""
        from system_monitor.core.process_manager import ProcessManager
        
        # Create mock core item
        core_item = MagicMock(spec=QTreeWidgetItem)
        core_item.isExpanded.return_value = True
        core_item.text.return_value = "CPU Core 0"
        core_item.childCount.return_value = 0
        
        self.monitor.proc_tree.topLevelItemCount.return_value = 1
        self.monitor.proc_tree.topLevelItem.return_value = core_item
        
        expanded_cores, expanded_processes = ProcessManager._save_expansion_state(self.monitor, 4)
        
        assert 0 in expanded_cores

    def test_save_expansion_state_with_expanded_processes(self):
        """Test _save_expansion_state with expanded process items."""
        from system_monitor.core.process_manager import ProcessManager
        
        # Create mock process item
        proc_item = MagicMock(spec=QTreeWidgetItem)
        proc_item.isExpanded.return_value = True
        proc_item.text.return_value = "1234"
        
        # Create mock core item
        core_item = MagicMock(spec=QTreeWidgetItem)
        core_item.isExpanded.return_value = True
        core_item.text.return_value = "CPU Core 0"
        core_item.childCount.return_value = 1
        core_item.child.return_value = proc_item
        
        self.monitor.proc_tree.topLevelItemCount.return_value = 1
        self.monitor.proc_tree.topLevelItem.return_value = core_item
        
        expanded_cores, expanded_processes = ProcessManager._save_expansion_state(self.monitor, 4)
        
        assert 0 in expanded_cores
        assert 0 in expanded_processes
        assert 1234 in expanded_processes[0]

    def test_save_expansion_state_exception_handling(self):
        """Test _save_expansion_state handles exceptions."""
        from system_monitor.core.process_manager import ProcessManager
        
        core_item = MagicMock(spec=QTreeWidgetItem)
        core_item.isExpanded.return_value = True
        core_item.text.side_effect = Exception("Text error")
        
        self.monitor.proc_tree.topLevelItemCount.return_value = 1
        self.monitor.proc_tree.topLevelItem.return_value = core_item
        
        # Should not raise
        expanded_cores, expanded_processes = ProcessManager._save_expansion_state(self.monitor, 4)
        
        assert isinstance(expanded_cores, set)
        assert isinstance(expanded_processes, dict)

    @patch('system_monitor.core.process_manager.QTreeWidgetItem')
    def test_build_process_tree_basic(self, mock_tree_item_cls):
        """Test _build_process_tree builds tree structure."""
        from system_monitor.core.process_manager import ProcessManager
        
        mock_proc_obj = MagicMock()
        core_processes = {
            0: [(25.5, 1234, "process1", 100.0, 5, mock_proc_obj)]
        }
        
        ProcessManager._build_process_tree(
            self.monitor, 1, core_processes, False, set(), {}
        )
        
        # Should create core item and process item
        assert mock_tree_item_cls.call_count >= 2

    @patch('system_monitor.core.process_manager.QTreeWidgetItem')
    def test_build_process_tree_first_build_expands(self, mock_tree_item_cls):
        """Test _build_process_tree expands on first build."""
        from system_monitor.core.process_manager import ProcessManager
        
        mock_core_item = MagicMock()
        mock_tree_item_cls.return_value = mock_core_item
        core_processes = {0: []}
        
        ProcessManager._build_process_tree(
            self.monitor, 1, core_processes, True, set(), {}
        )
        
        mock_core_item.setExpanded.assert_called_with(True)

    @patch('system_monitor.core.process_manager.QTreeWidgetItem')
    def test_build_process_tree_restores_expansion(self, mock_tree_item_cls):
        """Test _build_process_tree restores expansion state."""
        from system_monitor.core.process_manager import ProcessManager
        
        mock_items = [MagicMock(), MagicMock()]
        mock_tree_item_cls.side_effect = mock_items
        
        mock_proc_obj = MagicMock()
        core_processes = {0: [(25.5, 1234, "proc", 100.0, 5, mock_proc_obj)]}
        expanded_cores = {0}
        expanded_processes = {0: {1234}}
        
        ProcessManager._build_process_tree(
            self.monitor, 1, core_processes, False, expanded_cores, expanded_processes
        )
        
        # Core should be expanded
        mock_items[0].setExpanded.assert_called_with(True)

    @patch('system_monitor.core.process_manager.QTreeWidgetItem')
    def test_build_process_tree_lazy_load_threads(self, mock_tree_item_cls):
        """Test _build_process_tree sets lazy load indicator for threads."""
        from system_monitor.core.process_manager import ProcessManager
        
        mock_core_item = MagicMock()
        mock_proc_item = MagicMock()
        mock_tree_item_cls.side_effect = [mock_core_item, mock_proc_item]
        
        mock_proc_obj = MagicMock()
        core_processes = {0: [(25.5, 1234, "proc", 100.0, 5, mock_proc_obj)]}
        
        ProcessManager._build_process_tree(
            self.monitor, 1, core_processes, False, set(), {}
        )
        
        # Should set child indicator for multi-threaded process
        mock_proc_item.setChildIndicatorPolicy.assert_called()

    @patch('system_monitor.core.process_manager.asyncio')
    def test_update_summary_labels_basic(self, mock_asyncio):
        """Test _update_summary_labels updates labels."""
        from system_monitor.core.process_manager import ProcessManager
        
        mock_asyncio.get_running_loop.side_effect = Exception("No loop")
        
        ProcessManager._update_summary_labels(self.monitor, 100, 500)
        
        self.monitor.lbl_proc_summary.setText.assert_called_once_with("Processes: 100   Threads: 500")
        self.monitor.lbl_asyncio.setText.assert_called_once_with("Python coroutines (asyncio tasks): 0")

    @patch('system_monitor.core.process_manager.asyncio')
    def test_update_summary_labels_with_asyncio(self, mock_asyncio):
        """Test _update_summary_labels includes asyncio task count."""
        from system_monitor.core.process_manager import ProcessManager
        
        mock_loop = MagicMock()
        mock_asyncio.get_running_loop.return_value = mock_loop
        mock_asyncio.all_tasks.return_value = [1, 2, 3]  # 3 tasks
        
        ProcessManager._update_summary_labels(self.monitor, 100, 500)
        
        self.monitor.lbl_asyncio.setText.assert_called_once_with("Python coroutines (asyncio tasks): 3")
