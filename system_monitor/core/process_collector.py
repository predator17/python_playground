"""Background process data collector using ThreadPoolExecutor."""

#      Copyright (c) 2025 predator. All rights reserved.

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue
from typing import Dict, List, Tuple, Optional, Any

try:
    import psutil
except ImportError:
    psutil = None


class ProcessCollector:
    """Collects process data in background thread to avoid blocking UI.
    
    Uses ThreadPoolExecutor for background collection and Queue for thread-safe
    communication with the main Qt thread. Implements producer-consumer pattern.
    """
    
    def __init__(self, max_workers: int = 1) -> None:
        """Initialize process collector.
        
        Args:
            max_workers: Number of worker threads (default 1 is sufficient)
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ProcessCollector")
        self._result_queue: Queue = Queue(maxsize=1)  # Only keep latest result
        self._collecting = False
        self._lock = threading.Lock()
        self._shutdown = False
    
    def collect_async(self, n_cores: int, proc_filter: str = "") -> None:
        """Start asynchronous process collection.
        
        Args:
            n_cores: Number of CPU cores for affinity grouping
            proc_filter: Optional filter string for process names/PIDs
        """
        with self._lock:
            if self._collecting or self._shutdown:
                return
            self._collecting = True
        
        # Submit collection task to executor
        future: Future = self._executor.submit(self._collect_processes, n_cores, proc_filter)
        future.add_done_callback(self._on_collection_complete)
    
    def _collect_processes(self, n_cores: int, proc_filter: str) -> Dict[str, Any]:
        """Collect process data in background thread (worker thread).
        
        Args:
            n_cores: Number of CPU cores
            proc_filter: Filter string for process names/PIDs
            
        Returns:
            Dictionary with collected process data
        """
        try:
            core_processes: Dict[int, List] = {i: [] for i in range(n_cores)}
            all_cores_processes: List = []
            total_threads = 0
            proc_count = 0
            
            # Iterate all processes (expensive operation done in background)
            for p in psutil.process_iter(['pid', 'name', 'memory_percent', 'num_threads']):
                if self._shutdown:
                    break
                
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
                
                # Apply search filter
                if proc_filter:
                    if proc_filter not in name.lower() and proc_filter not in str(pid):
                        continue
                
                # Get CPU affinity (expensive operation)
                try:
                    affinity = p.cpu_affinity()
                    if affinity and len(affinity) < n_cores:
                        # Process pinned to specific cores
                        for core_id in affinity:
                            if core_id < n_cores:
                                core_processes[core_id].append((cpu, pid, name, mem, threads, p))
                    else:
                        # Process can run on all cores
                        all_cores_processes.append((cpu, pid, name, mem, threads, p))
                except Exception:
                    all_cores_processes.append((cpu, pid, name, mem, threads, p))
            
            return {
                'core_processes': core_processes,
                'all_cores_processes': all_cores_processes,
                'total_threads': total_threads,
                'proc_count': proc_count,
            }
        except Exception as e:
            # Return empty result on error
            return {
                'core_processes': {i: [] for i in range(n_cores)},
                'all_cores_processes': [],
                'total_threads': 0,
                'proc_count': 0,
                'error': str(e),
            }
    
    def _on_collection_complete(self, future: Future) -> None:
        """Callback when collection completes (runs in worker thread).
        
        Args:
            future: Completed future with collection result
        """
        with self._lock:
            self._collecting = False
        
        try:
            result = future.result()
            # Put result in queue (non-blocking, drop old if full)
            if not self._result_queue.full():
                self._result_queue.put(result)
            else:
                # Drop old result and put new one
                try:
                    self._result_queue.get_nowait()
                except Exception:
                    pass
                self._result_queue.put(result)
        except Exception:
            pass
    
    def get_result(self) -> Optional[Dict[str, Any]]:
        """Get collected result if available (non-blocking, thread-safe).
        
        Returns:
            Process data dictionary or None if no result available
        """
        try:
            return self._result_queue.get_nowait()
        except Exception:
            return None
    
    def is_collecting(self) -> bool:
        """Check if collection is in progress (thread-safe)."""
        with self._lock:
            return self._collecting
    
    def shutdown(self) -> None:
        """Shutdown collector and wait for pending tasks (thread-safe)."""
        with self._lock:
            self._shutdown = True
        
        self._executor.shutdown(wait=True)
    
    def __del__(self) -> None:
        """Cleanup on destruction."""
        try:
            self.shutdown()
        except Exception:
            pass
