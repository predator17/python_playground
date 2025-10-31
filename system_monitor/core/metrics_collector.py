"""Parallel metrics collector using ThreadPoolExecutor."""

#      Copyright (c) 2025 predator. All rights reserved.

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Callable

try:
    import psutil
except ImportError:
    psutil = None


class MetricsCollector:
    """Collects system metrics in parallel to reduce latency.
    
    Uses ThreadPoolExecutor to run multiple psutil queries concurrently,
    which is beneficial when metrics collection involves I/O or system calls.
    """
    
    def __init__(self, max_workers: int = 4) -> None:
        """Initialize metrics collector.
        
        Args:
            max_workers: Number of worker threads (default 4 for CPU/Mem/Net/Disk)
        """
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="MetricsCollector"
        )
    
    def collect_all(self) -> Dict[str, Any]:
        """Collect all basic metrics in parallel.
        
        Returns:
            Dictionary with collected metrics: {
                'cpu': float,
                'cpu_percpu': list,
                'cpu_freq': object,
                'memory': object,
                'network': object,
                'disk': object,
            }
        """
        # Define collection tasks
        tasks = {
            'cpu': self._collect_cpu_percent,
            'cpu_percpu': self._collect_cpu_percpu,
            'cpu_freq': self._collect_cpu_freq,
            'memory': self._collect_memory,
            'network': self._collect_network,
            'disk': self._collect_disk,
        }
        
        # Submit all tasks
        futures = {self._executor.submit(func): key for key, func in tasks.items()}
        
        # Collect results as they complete
        results = {}
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception:
                results[key] = None
        
        return results
    
    def _collect_cpu_percent(self) -> float:
        """Collect overall CPU percentage."""
        try:
            return float(psutil.cpu_percent(interval=None))
        except Exception:
            return 0.0
    
    def _collect_cpu_percpu(self) -> list:
        """Collect per-core CPU percentages."""
        try:
            cores = psutil.cpu_percent(interval=None, percpu=True)
            if isinstance(cores, list) and cores:
                return [float(c) for c in cores]
            return []
        except Exception:
            return []
    
    def _collect_cpu_freq(self) -> Any:
        """Collect CPU frequency information."""
        try:
            return psutil.cpu_freq()
        except Exception:
            return None
    
    def _collect_memory(self) -> Any:
        """Collect memory information."""
        try:
            return psutil.virtual_memory()
        except Exception:
            return None
    
    def _collect_network(self) -> Any:
        """Collect network I/O counters."""
        try:
            return psutil.net_io_counters()
        except Exception:
            return None
    
    def _collect_disk(self) -> Any:
        """Collect disk I/O counters."""
        try:
            return psutil.disk_io_counters()
        except Exception:
            return None
    
    def shutdown(self) -> None:
        """Shutdown the executor and wait for pending tasks."""
        self._executor.shutdown(wait=True)
    
    def __del__(self) -> None:
        """Cleanup on destruction."""
        try:
            self.shutdown()
        except Exception:
            pass
