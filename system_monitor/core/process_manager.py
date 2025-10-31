"""Process manager for SystemMonitor - handles process tree and filtering."""

import asyncio
from typing import TYPE_CHECKING

try:
    import psutil
except ImportError:
    psutil = None

from PySide6.QtWidgets import QTreeWidgetItem

if TYPE_CHECKING:
    from system_monitor.app import SystemMonitor


class ProcessManager:
    """Handles process tree building and management."""

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
        """Refresh the process tree with core affinity grouping."""
        try:
            # First pass: prime per-process CPU percentages
            if not getattr(monitor, "_procs_primed", False):
                for p in psutil.process_iter():
                    try:
                        p.cpu_percent(None)
                    except Exception:
                        pass
                monitor._procs_primed = True
                return

            # Collect process data
            n_cores = psutil.cpu_count(logical=True) or 1
            core_processes = {i: [] for i in range(n_cores)}
            all_cores_processes = []
            
            total_threads = 0
            proc_count = 0
            
            for p in psutil.process_iter(['pid', 'name', 'memory_percent', 'num_threads']):
                proc_count += 1
                try:
                    cpu = float(p.cpu_percent(None))
                except Exception:
                    cpu = 0.0
                mem = float(p.info.get('memory_percent') or 0.0)
                threads = int(p.info.get('num_threads') or 0)
                total_threads += threads
                pid = p.info.get('pid')
                name = p.info.get('name') or ""
                
                # Apply search filter if active
                if monitor._proc_filter:
                    if monitor._proc_filter not in name.lower() and monitor._proc_filter not in str(pid):
                        continue
                
                # Get CPU affinity and thread details
                try:
                    affinity = p.cpu_affinity()
                    if affinity and len(affinity) < n_cores:
                        # Process is pinned to specific cores
                        for core_id in affinity:
                            if core_id < n_cores:
                                core_processes[core_id].append((cpu, pid, name, mem, threads, p))
                    else:
                        # Process can run on all cores
                        all_cores_processes.append((cpu, pid, name, mem, threads, p))
                except Exception:
                    all_cores_processes.append((cpu, pid, name, mem, threads, p))
            
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
