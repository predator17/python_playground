"""Chart factory for creating time-series charts."""

#      Copyright (c) 2025 predator. All rights reserved.

from typing import Optional

from system_monitor.widgets import TimeSeriesChart


class ChartFactory:
    """Factory for creating various metric charts."""

    @staticmethod
    def create_cpu_chart() -> TimeSeriesChart:
        """Create main CPU utilization chart."""
        return TimeSeriesChart("CPU Utilization", ["CPU %"], y_range=(0, 100))
    
    @staticmethod
    def create_memory_chart() -> TimeSeriesChart:
        """Create memory utilization chart."""
        return TimeSeriesChart("Memory Utilization", ["Mem %"], y_range=(0, 100))
    
    @staticmethod
    def create_network_chart() -> TimeSeriesChart:
        """Create network throughput chart."""
        return TimeSeriesChart(
            "Network Throughput (MiB/s)",
            ["Up", "Down"],
            y_range=(0, 10),
            auto_scale=True
        )
    
    @staticmethod
    def create_disk_chart() -> TimeSeriesChart:
        """Create disk throughput chart."""
        return TimeSeriesChart(
            "Disk Throughput (MiB/s)",
            ["Read", "Write"],
            y_range=(0, 10),
            auto_scale=True
        )
    
    @staticmethod
    def create_gpu_chart(gpu_names: list) -> Optional[TimeSeriesChart]:
        """Create GPU utilization chart if GPUs are available."""
        if not gpu_names:
            return None
        return TimeSeriesChart(
            "GPU Utilization",
            [f"{name}" for name in gpu_names],
            y_range=(0, 100)
        )
