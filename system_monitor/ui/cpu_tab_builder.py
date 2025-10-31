"""CPU tab builder for SystemMonitor application."""

#      Copyright (c) 2025 predator. All rights reserved.

import math
from typing import TYPE_CHECKING, List

try:
    import psutil
except ImportError:
    psutil = None

from PySide6.QtCore import Qt, QMargins
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QScrollArea, QFrame
)

from system_monitor.widgets import TimeSeriesChart

if TYPE_CHECKING:
    from system_monitor.app import SystemMonitor


class CPUTabBuilder:
    """Builds the CPU tab with per-core charts and summary labels."""

    CORE_COLORS = [
        QColor("#e53935"), QColor("#8e24aa"), QColor("#3949ab"), QColor("#1e88e5"),
        QColor("#00897b"), QColor("#43a047"), QColor("#fdd835"), QColor("#fb8c00"),
        QColor("#6d4c41"), QColor("#546e7a"), QColor("#d81b60"), QColor("#00acc1"),
    ]

    @staticmethod
    def build_cpu_tab(monitor: 'SystemMonitor') -> QWidget:
        """Create CPU tab with main chart, per-core charts, and summary."""
        cpu_tab = QWidget()
        cpu_l = QVBoxLayout(cpu_tab)
        cpu_l.addWidget(monitor.chart_cpu)
        
        CPUTabBuilder._build_per_core_charts(monitor, cpu_l)
        CPUTabBuilder._build_summary_labels(monitor, cpu_l)
        
        return cpu_tab
    
    @staticmethod
    def _build_per_core_charts(monitor: 'SystemMonitor', layout: QVBoxLayout) -> None:
        """Build per-core CPU charts with frequency labels."""
        n_cores = psutil.cpu_count(logical=True) or 1
        monitor.core_charts: List[TimeSeriesChart] = []
        monitor.core_freq_labels: List[QLabel] = []
        
        cores_container = QWidget()
        cores_grid = QGridLayout(cores_container)
        cores_grid.setSpacing(8)
        cols = min(4, max(1, int(math.sqrt(n_cores)) + 1))
        
        small_style = "QLabel { color: #b0b0b0; font-size: 8pt; }"
        
        for i in range(n_cores):
            core_container = QWidget()
            core_layout = QVBoxLayout(core_container)
            core_layout.setContentsMargins(0, 0, 0, 0)
            core_layout.setSpacing(2)
            
            chart = TimeSeriesChart(f"CPU{i}", ["%"], max_points=200, y_range=(0, 100))
            if chart.series:
                chart.series[0].setColor(CPUTabBuilder.CORE_COLORS[i % len(CPUTabBuilder.CORE_COLORS)])
            chart.chart.legend().setVisible(False)
            chart.axis_x.setVisible(False)
            chart.axis_y.setVisible(False)
            chart.chart.setMargins(QMargins(4, 4, 4, 4))
            monitor.core_charts.append(chart)
            core_layout.addWidget(chart)
            
            freq_label = QLabel("-- MHz")
            freq_label.setStyleSheet(small_style)
            freq_label.setAlignment(Qt.AlignCenter)
            monitor.core_freq_labels.append(freq_label)
            core_layout.addWidget(freq_label)
            
            r, c = divmod(i, cols)
            cores_grid.addWidget(core_container, r, c)
        
        scroll = QScrollArea()
        scroll.setWidget(cores_container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(scroll)
    
    @staticmethod
    def _build_summary_labels(monitor: 'SystemMonitor', layout: QVBoxLayout) -> None:
        """Build summary labels for processes/threads/asyncio."""
        small_style = "QLabel { color: #b0b0b0; font-size: 9pt; }"
        
        monitor.lbl_proc_summary = QLabel("")
        monitor.lbl_asyncio = QLabel("")
        monitor.lbl_proc_summary.setStyleSheet(small_style)
        monitor.lbl_asyncio.setStyleSheet(small_style)
        
        summary_row = QHBoxLayout()
        summary_row.addWidget(monitor.lbl_proc_summary)
        summary_row.addWidget(monitor.lbl_asyncio)
        layout.addLayout(summary_row)
