"""Dashboard builder for SystemMonitor application."""

#      Copyright (c) 2025 predator. All rights reserved.

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget, QGridLayout

from system_monitor.widgets import MetricCard
from system_monitor.utils import get_cpu_model_name

if TYPE_CHECKING:
    from system_monitor.app import SystemMonitor


class DashboardBuilder:
    """Builds the dashboard tab with metric cards."""

    @staticmethod
    def build_dashboard(monitor: 'SystemMonitor') -> QWidget:
        """Create dashboard widget with all metric cards."""
        dashboard = QWidget()
        grid = QGridLayout(dashboard)
        grid.setSpacing(12)
        
        DashboardBuilder._create_cpu_card(monitor)
        DashboardBuilder._create_memory_card(monitor)
        DashboardBuilder._create_network_cards(monitor)
        DashboardBuilder._create_disk_cards(monitor)
        DashboardBuilder._create_gpu_card(monitor)
        
        grid.addWidget(monitor.card_cpu, 0, 0)
        grid.addWidget(monitor.card_mem, 0, 1)
        grid.addWidget(monitor.card_net_up, 1, 0)
        grid.addWidget(monitor.card_net_down, 1, 1)
        grid.addWidget(monitor.card_disk_read, 2, 0)
        grid.addWidget(monitor.card_disk_write, 2, 1)
        grid.addWidget(monitor.card_gpu, 3, 0, 1, 2)
        
        return dashboard
    
    @staticmethod
    def _create_cpu_card(monitor: 'SystemMonitor') -> None:
        """Create CPU metric card."""
        monitor.card_cpu = MetricCard("CPU", unit="%", is_percent=True, color="#00c853")
        monitor.card_cpu.set_tooltip("Overall CPU utilization across all cores")
        cpu_model = get_cpu_model_name()
        monitor.card_cpu.set_model(cpu_model)
    
    @staticmethod
    def _create_memory_card(monitor: 'SystemMonitor') -> None:
        """Create memory metric card."""
        monitor.card_mem = MetricCard("Memory", unit="%", is_percent=True, color="#ffd54f")
        monitor.card_mem.set_tooltip("Physical memory (RAM) usage")
    
    @staticmethod
    def _create_network_cards(monitor: 'SystemMonitor') -> None:
        """Create network metric cards."""
        monitor.card_net_up = MetricCard("Net Up", unit="MiB/s", is_percent=False, color="#2962ff")
        monitor.card_net_up.set_tooltip("Network upload throughput")
        monitor.card_net_down = MetricCard("Net Down", unit="MiB/s", is_percent=False, color="#ff5252")
        monitor.card_net_down.set_tooltip("Network download throughput")
    
    @staticmethod
    def _create_disk_cards(monitor: 'SystemMonitor') -> None:
        """Create disk metric cards."""
        monitor.card_disk_read = MetricCard("Disk Read", unit="MiB/s", is_percent=False, color="#00bcd4")
        monitor.card_disk_read.set_tooltip("Disk read throughput")
        monitor.card_disk_write = MetricCard("Disk Write", unit="MiB/s", is_percent=False, color="#ab47bc")
        monitor.card_disk_write.set_tooltip("Disk write throughput")
    
    @staticmethod
    def _create_gpu_card(monitor: 'SystemMonitor') -> None:
        """Create GPU metric card."""
        monitor.card_gpu = MetricCard("GPU", unit="%", is_percent=True, color="#7c4dff")
        gpu_names = monitor.gpu_provider.gpu_names()
        if not gpu_names:
            monitor.card_gpu.set_unavailable("N/A")
            monitor.card_gpu.set_tooltip("No NVIDIA GPU detected")
        else:
            monitor.card_gpu.set_model(gpu_names[0])
