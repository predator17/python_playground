"""Process manager for SystemMonitor - handles process tree and filtering."""

#      Copyright (c) 2025 predator. All rights reserved.

import asyncio
from typing import TYPE_CHECKING, Optional

try:
    import psutil
except ImportError:
    psutil = None

from PySide6.QtWidgets import QTreeWidgetItem
from .process_collector import ProcessCollector

if TYPE_CHECKING:
    from system_monitor.app import SystemMonitor


class ProcessManager:
    """Handles process tree building and management.
    
    Uses ProcessCollector for background process enumeration to avoid blocking UI.
    """
    
    _collector: Optional[ProcessCollector] = None
    
    @classmethod
    def initialize_collector(cls) -> None:
        """Initialize the process collector (call once at app startup)."""
        if cls._collector is None:
            cls._collector = ProcessCollector(max_workers=1)
    
    @classmethod
    def shutdown_collector(cls) -> None:
        """Shutdown the process collector (call at app shutdown)."""
        if cls._collector is not None:
            cls._collector.shutdown()
            cls._collector = None

    @staticmethod
    def on_proc_item_expanded(monitor: 'SystemMonitor', item: QTreeWidgetItem) -> None:
        """Load threads when a process item is expanded."""
        if item.childCount() > 0:
            return
        
        pid_text = item.text(1)
        if not pid_text or not pid_text.isdigit():
            return
        
        try:
            pid = int(pid_text)
            proc = psutil.Process(pid)
            thread_ids = proc.threads()
            for thread_info in thread_ids[:10]:
                thread_item = QTreeWidgetItem(item)
                thread_item.setText(0, f"Thread {thread_info.id}")
                thread_item.setText(1, str(thread_info.id))
        except Exception:
            pass

    @staticmethod
    def refresh_processes(monitor: 'SystemMonitor') -> None:
        """Refresh the process tree with core affinity grouping (async version).
        
        Uses ProcessCollector to gather data in background thread, then consumes
        results from queue to update UI without blocking.
        """
        try:
            # First pass: prime per-process CPU percentages (still synchronous, but fast)
            if not getattr(monitor, "_procs_primed", False):
                for p in psutil.process_iter():
                    try:
                        p.cpu_percent(None)
                    except Exception:
                        pass
                monitor._procs_primed = True
                return
            
            # Initialize collector if needed
            if ProcessManager._collector is None:
                ProcessManager.initialize_collector()
            
            # Check if we have a result ready from previous collection
            result = ProcessManager._collector.get_result()
            if result is not None:
                # We have data ready, update the UI
                ProcessManager._update_ui_with_result(monitor, result)
            
            # Start new async collection if not already collecting
            if not ProcessManager._collector.is_collecting():
                n_cores = psutil.cpu_count(logical=True) or 1
                ProcessManager._collector.collect_async(n_cores, monitor._proc_filter)
            
        except Exception:
            pass
    
    @staticmethod
    def _update_ui_with_result(monitor: 'SystemMonitor', result: dict) -> None:
        """Update UI with collected process data (called in main thread).
        
        Args:
            monitor: SystemMonitor instance
            result: Dictionary with process data from collector
        """
        try:
            core_processes = result.get('core_processes', {})
            proc_count = result.get('proc_count', 0)
            total_threads = result.get('total_threads', 0)
            
            n_cores = len(core_processes)
            
            # Save current expansion state before clearing
            expanded_cores, expanded_processes = ProcessManager._save_expansion_state(monitor, n_cores)
            
            # Clear tree and rebuild
            monitor.proc_tree.clear()
            
            # Track if this is the first time building the tree
            first_build = not hasattr(monitor, "_proc_tree_built")
            if first_build:
                monitor._proc_tree_built = True
            
            # Build process tree
            ProcessManager._build_process_tree(
                monitor, n_cores, core_processes, first_build, 
                expanded_cores, expanded_processes
            )
            
            # Update summary labels
            ProcessManager._update_summary_labels(monitor, proc_count, total_threads)
            
        except Exception:
            pass

    @staticmethod
    def _save_expansion_state(monitor: 'SystemMonitor', n_cores: int) -> tuple:
        """Save the current expansion state of the process tree."""
        expanded_cores = set()
        expanded_processes = {}
        
        for i in range(monitor.proc_tree.topLevelItemCount()):
            core_item = monitor.proc_tree.topLevelItem(i)
            if core_item and core_item.isExpanded():
                try:
                    core_text = core_item.text(0)
                    core_id = int(core_text.split()[-1])
                    expanded_cores.add(core_id)
                    
                    # Track expanded processes under this core
                    expanded_pids = set()
                    for j in range(core_item.childCount()):
                        proc_item = core_item.child(j)
                        if proc_item and proc_item.isExpanded():
                            pid_text = proc_item.text(1)
                            if pid_text.isdigit():
                                expanded_pids.add(int(pid_text))
                    if expanded_pids:
                        expanded_processes[core_id] = expanded_pids
                except Exception:
                    pass
        
        return expanded_cores, expanded_processes

    @staticmethod
    def _build_process_tree(monitor: 'SystemMonitor', n_cores: int, core_processes: dict,
                           first_build: bool, expanded_cores: set, expanded_processes: dict) -> None:
        """Build the process tree with core nodes."""
        for core_id in range(n_cores):
            core_procs = core_processes[core_id]
            core_procs.sort(key=lambda x: x[0], reverse=True)
            
            # Create core node
            core_item = QTreeWidgetItem(monitor.proc_tree)
            core_item.setText(0, f"CPU Core {core_id}")
            core_item.setText(2, f"{sum(x[0] for x in core_procs[:10]):.1f}")
            
            # Expand based on state
            should_expand = first_build or (core_id in expanded_cores)
            core_item.setExpanded(should_expand)
            
            # Add top processes to this core
            for cpu, pid, name, mem, thr, proc_obj in core_procs[:10]:
                proc_item = QTreeWidgetItem(core_item)
                proc_item.setText(0, name)
                proc_item.setText(1, str(pid))
                proc_item.setText(2, f"{cpu:.1f}")
                proc_item.setText(3, f"{mem:.1f}")
                proc_item.setText(4, str(thr))
                proc_item.setText(5, str(core_id))
                
                # Restore process expansion state
                if core_id in expanded_processes and pid in expanded_processes[core_id]:
                    proc_item.setExpanded(True)
                    if thr > 1:
                        try:
                            thread_ids = proc_obj.threads()
                            for thread_info in thread_ids[:10]:
                                thread_item = QTreeWidgetItem(proc_item)
                                thread_item.setText(0, f"Thread {thread_info.id}")
                                thread_item.setText(1, str(thread_info.id))
                        except Exception:
                            pass
                else:
                    # Lazy load threads
                    if thr > 1:
                        proc_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)

    @staticmethod
    def _update_summary_labels(monitor: 'SystemMonitor', proc_count: int, total_threads: int) -> None:
        """Update process and thread summary labels."""
        monitor.lbl_proc_summary.setText(f"Processes: {proc_count:,}   Threads: {total_threads:,}")
        
        # asyncio coroutines count
        coro_count = 0
        try:
            loop = asyncio.get_running_loop()
            coro_count = len(asyncio.all_tasks(loop))
        except Exception:
            coro_count = 0
        monitor.lbl_asyncio.setText(f"Python coroutines (asyncio tasks): {coro_count}")
