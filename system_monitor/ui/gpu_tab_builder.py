"""GPU tab builder for SystemMonitor application."""

#      Copyright (c) 2025 predator. All rights reserved.

from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from system_monitor.widgets import TimeSeriesChart
from system_monitor.utils import get_gpu_temperatures

if TYPE_CHECKING:
    from system_monitor.app import SystemMonitor


class GPUTabBuilder:
    """Builds the GPU tab with utilization, VRAM, and temperature charts."""

    @staticmethod
    def build_gpu_tab(monitor: 'SystemMonitor', gpu_names: list) -> QWidget:
        """Create GPU tab with all charts and info."""
        if not gpu_names or monitor.chart_gpu is None:
            return GPUTabBuilder._build_no_gpu_tab()
        
        gpu_tab = QWidget()
        gpu_l = QVBoxLayout(gpu_tab)
        gpu_l.addWidget(monitor.chart_gpu)
        
        GPUTabBuilder._add_vram_chart(monitor, gpu_l, gpu_names)
        GPUTabBuilder._add_temperature_chart(monitor, gpu_l, gpu_names)
        GPUTabBuilder._add_info_label(monitor, gpu_l)
        
        return gpu_tab
    
    @staticmethod
    def _build_no_gpu_tab() -> QWidget:
        """Create placeholder tab when no GPU is available."""
        gpu_tab = QWidget()
        gpu_l = QVBoxLayout(gpu_tab)
        gpu_l.addWidget(QLabel("No NVIDIA GPU metrics available (pynvml/nvidia-smi not found)."))
        return gpu_tab
    
    @staticmethod
    def _add_vram_chart(monitor: 'SystemMonitor', layout: QVBoxLayout, gpu_names: list) -> None:
        """Add GPU VRAM usage chart with fixed y-axis."""
        vram_info = monitor.gpu_provider.gpu_vram_info()
        max_vram = 1000.0
        if vram_info:
            max_vram = max((total_mb for _, total_mb in vram_info if total_mb > 0), default=1000.0)
        
        monitor.chart_gpu_vram = TimeSeriesChart(
            "GPU VRAM Usage (MB)",
            [f"{name} VRAM" for name in gpu_names],
            max_points=400,
            y_range=(0, max_vram),
            auto_scale=False
        )
        layout.addWidget(monitor.chart_gpu_vram)
    
    @staticmethod
    def _add_temperature_chart(monitor: 'SystemMonitor', layout: QVBoxLayout, gpu_names: list) -> None:
        """Add GPU temperature chart if temperatures are available."""
        gpu_temps = get_gpu_temperatures(monitor.gpu_provider)
        if gpu_temps and any(t > 0 for t in gpu_temps):
            monitor.chart_gpu_temp = TimeSeriesChart(
                "GPU Temperature (°C)",
                [f"{name} Temp" for name in gpu_names],
                max_points=400,
                y_range=(0, 100),
                auto_scale=False
            )
            layout.addWidget(monitor.chart_gpu_temp)
        else:
            monitor.chart_gpu_temp = None
    
    @staticmethod
    def _add_info_label(monitor: 'SystemMonitor', layout: QVBoxLayout) -> None:
        """Add GPU info label for additional metrics."""
        monitor.lbl_gpu_info = QLabel("")
        monitor.lbl_gpu_info.setStyleSheet("QLabel { color: #b0b0b0; font-size: 9pt; padding: 8px; }")
        layout.addWidget(monitor.lbl_gpu_info)
    
    @staticmethod
    def setup_no_gpu_fallback(monitor: 'SystemMonitor') -> None:
        """Set None values when GPU is not available."""
        monitor.lbl_gpu_info = None
        monitor.chart_gpu_vram = None
        monitor.chart_gpu_temp = None
