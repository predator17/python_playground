"""System information manager for SystemMonitor."""

#      Copyright (c) 2025 predator. All rights reserved.

import sys
import platform
from typing import TYPE_CHECKING

try:
    import psutil
except ImportError:
    psutil = None

from system_monitor.utils import get_cpu_model_name

if TYPE_CHECKING:
    from system_monitor.app import SystemMonitor


class InfoManager:
    """Handles system information gathering and display."""

    @staticmethod
    def refresh_info(monitor: 'SystemMonitor') -> None:
        """Gather and display comprehensive system information."""
        lines = []
        
        # CPU Information
        lines.append("=== CPU Information ===")
        lines.append(f"Processor: {get_cpu_model_name()}")
        lines.append(f"Machine: {platform.machine()}")
        try:
            lines.append(f"Architecture: {platform.architecture()}")
        except Exception:
            pass
        lines.append(f"CPU Count (logical): {psutil.cpu_count(logical=True)}")
        lines.append(f"CPU Count (physical): {psutil.cpu_count(logical=False)}")
        try:
            freq = psutil.cpu_freq()
            if freq:
                lines.append(
                    f"CPU Frequency: current {freq.current/1000:.2f} GHz, "
                    f"max {freq.max/1000:.2f} GHz"
                )
        except Exception:
            pass

        # System Information
        lines.append("\n=== System Information ===")
        lines.append(f"System: {platform.system()}")
        lines.append(f"Node Name: {platform.node()}")
        lines.append(f"Release: {platform.release()}")
        lines.append(f"Version: {platform.version()}")
        lines.append(f"Platform: {platform.platform()}")

        # Memory Information
        lines.append("\n=== Memory Information ===")
        vm = psutil.virtual_memory()
        lines.append(
            f"Total: {vm.total/ (1024**3):.2f} GiB; "
            f"Available: {vm.available/(1024**3):.2f} GiB"
        )
        lines.append(f"Used: {vm.used/(1024**3):.2f} GiB ({vm.percent:.1f}%)")

        # Disk Information
        lines.append("\n=== Disk Information ===")
        for p in psutil.disk_partitions(all=False):
            try:
                du = psutil.disk_usage(p.mountpoint)
                lines.append(
                    f"{p.device} ({p.mountpoint}) - "
                    f"{du.used/(1024**3):.2f}/{du.total/(1024**3):.2f} GiB used "
                    f"({du.percent:.1f}%)"
                )
            except Exception:
                pass

        # GPU Information
        lines.append("\n=== GPU Information ===")
        names = monitor.gpu_provider.gpu_names()
        if names:
            for i, n in enumerate(names):
                lines.append(f"GPU {i}: {n}")
        else:
            lines.append("No NVIDIA GPUs detected or metrics unavailable.")

        # Python Information
        lines.append("\n=== Python Information ===")
        lines.append(f"Python Version: {sys.version}")
        lines.append(f"Python Executable: {sys.executable}")

        monitor.info_edit.setPlainText("\n".join(lines))
