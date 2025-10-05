"""
Real-time System Monitor (PySide6)

Dependencies:
- PySide6 (Qt 6)
- psutil
- Optional: nvidia-ml-py (for NVIDIA GPU metrics) or system nvidia-smi

Install:
  pip install PySide6 psutil nvidia-ml-py

Run:
  python play.py

Notes:
- Updates every 1 ms by default.
- Uses QtCharts for efficient, built-in plotting (no extra plotting libs required).
"""
from __future__ import annotations

import sys
import platform
import time
import shutil
import subprocess
import threading
import asyncio
import math
from dataclasses import dataclass
from email.policy import default
from typing import List, Optional, Tuple

try:
    import psutil  # type: ignore
except Exception as e:
    print("psutil is required. Install with: pip install psutil")
    raise

# PySide6 imports
from PySide6.QtCore import Qt, QTimer, QPointF, QMargins, QElapsedTimer
from PySide6.QtGui import QFont, QPalette, QColor, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QTabWidget,
    QTextEdit,
    QSizePolicy,
    QFrame,
    QHBoxLayout,
    QProgressBar,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSpinBox,
    QToolBar,
    QScrollArea,
)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis


def apply_dark_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(18, 18, 18))
    palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
    palette.setColor(QPalette.Base, QColor(24, 24, 24))
    palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(224, 224, 224))
    palette.setColor(QPalette.Button, QColor(30, 30, 30))
    palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Highlight, QColor(53, 132, 228))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    app.setStyleSheet(
        """
        QWidget { background-color: #121212; color: #e0e0e0; }
        QFrame#Card { background-color: #1e1e1e; border: 1px solid #2a2a2a; border-radius: 10px; }
        QLabel#Title { font-weight: 600; font-size: 13pt; color: #cfcfcf; }
        QLabel#Value { font-weight: 700; font-size: 20pt; color: #ffffff; }
        QProgressBar { background-color: #2a2a2a; border: 1px solid #3a3a3a; border-radius: 6px; height: 14px; }
        QProgressBar::chunk { background-color: #00c853; border-radius: 6px; }
        QTabWidget::pane { border: 1px solid #2a2a2a; }
        QTabBar::tab { background: #1e1e1e; padding: 6px 12px; border: 1px solid #2a2a2a; border-bottom: none; }
        QTabBar::tab:selected { background: #2a2a2a; }
        """
    )

# ----------------------------- GPU Provider -----------------------------
class GPUProvider:
    """Provides GPU names and utilization percentages.
    Tries nvidia-ml-py first; falls back to calling nvidia-smi if available.
    """

    def __init__(self) -> None:
        self.method: str = "none"
        self._gpu_names: List[str] = []
        self._nvml = None
        self._nvml_handles = []
        self._last_smi_time: float = 0.0
        self._last_smi_utils: List[float] = []
        self._smi_min_interval = 1.0  # seconds; avoid hammering nvidia-smi; polled in background thread

        # Try NVML (pynvml)
        try:
            import pynvml as nvml  # type: ignore
            nvml.nvmlInit()
            count = nvml.nvmlDeviceGetCount()
            self._nvml = nvml
            for i in range(count):
                h = nvml.nvmlDeviceGetHandleByIndex(i)
                self._nvml_handles.append(h)
                name = nvml.nvmlDeviceGetName(h)
                if isinstance(name, bytes):
                    name = name.decode("utf-8", errors="ignore")
                self._gpu_names.append(str(name))
            if self._gpu_names:
                self.method = "nvml"
        except Exception:
            self._nvml = None
            self._nvml_handles = []

        # Fallback to nvidia-smi
        if self.method == "none" and shutil.which("nvidia-smi"):
            try:
                names = self._query_nvidia_smi_names()
                if names:
                    self._gpu_names = names
                    self._last_smi_utils = [0.0 for _ in names]
                    self.method = "nvidia-smi"
                    # Start background polling thread to avoid UI blocking
                    self._smi_stop = False
                    self._smi_thread = threading.Thread(target=self._smi_poll_loop, daemon=True)
                    self._smi_thread.start()
            except Exception:
                pass

    def _query_nvidia_smi_names(self) -> List[str]:
        cmd = [
            "nvidia-smi",
            "--query-gpu=name",
            "--format=csv,noheader",
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
        names = [line.strip() for line in out.stdout.strip().splitlines() if line.strip()]
        return names

    def _query_nvidia_smi_utils(self) -> List[float]:
        cmd = [
            "nvidia-smi",
            "--query-gpu=utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
        utils: List[float] = []
        for line in out.stdout.strip().splitlines():
            try:
                utils.append(float(line.strip()))
            except Exception:
                utils.append(0.0)
        return utils

    def gpu_names(self) -> List[str]:
        return list(self._gpu_names)

    def gpu_utils(self) -> List[float]:
        if self.method == "nvml" and self._nvml is not None:
            vals: List[float] = []
            for h in self._nvml_handles:
                try:
                    util = self._nvml.nvmlDeviceGetUtilizationRates(h)
                    vals.append(float(util.gpu))
                except Exception:
                    vals.append(0.0)
            return vals
        elif self.method == "nvidia-smi":
            # Values are refreshed by a background thread to avoid blocking the UI
            return list(self._last_smi_utils)
        else:
            return []

    def _smi_poll_loop(self) -> None:
        # Background polling loop for nvidia-smi to avoid blocking the UI thread
        while True:
            try:
                utils = self._query_nvidia_smi_utils()
                if utils:
                    self._last_smi_utils = utils
            except Exception:
                # swallow exceptions; next iteration will retry
                pass
            time.sleep(self._smi_min_interval)


# --------------------------- Chart Widget -------------------------------
class TimeSeriesChart(QWidget):
    def __init__(
        self,
        title: str,
        series_names: List[str],
        max_points: int = 400,  # ~20s at 50 ms
        y_range: Optional[Tuple[float, float]] = (0.0, 100.0),
        auto_scale: bool = False,
    ) -> None:
        super().__init__()
        self.max_points = max_points
        self.auto_scale = auto_scale
        self._x: int = 0

        layout = QVBoxLayout(self)
        self.chart = QChart()
        self.chart.setTheme(QChart.ChartThemeDark)
        self.chart.setTitle(title)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)
        self.chart.setAnimationOptions(QChart.NoAnimation)
        self.chart.setBackgroundVisible(False)
        self.chart.setMargins(QMargins(8, 8, 8, 8))

        self.series: List[QLineSeries] = []
        for name in series_names:
            s = QLineSeries()
            s.setName(name)
            self.chart.addSeries(s)
            self.series.append(s)

        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Samples")
        self.axis_x.setRange(0, max_points)
        self.axis_x.setTickCount(6)
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        for s in self.series:
            s.attachAxis(self.axis_x)

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Value")
        if y_range is not None:
            self.axis_y.setRange(y_range[0], y_range[1])
        else:
            self.axis_y.setRange(0, 100)
        self.axis_y.setTickCount(6)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        for s in self.series:
            s.attachAxis(self.axis_y)

        self.view = QChartView(self.chart)
        self.view.setRenderHint(QPainter.Antialiasing, True)
        self.view.setRubberBand(QChartView.RectangleRubberBand)
        self.view.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.view)

        # pre-allocate point buffers
        self._buffers: List[List[QPointF]] = [[] for _ in self.series]

        # Size policy to stretch
        sp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(sp)

    def append(self, values: List[float]) -> None:
        # ensure length matches
        n = min(len(values), len(self.series))
        self._x += 1
        x0 = max(0, self._x - self.max_points)
        # Append new points and trim buffers
        for i in range(n):
            buf = self._buffers[i]
            buf.append(QPointF(float(self._x), float(values[i])))
            if len(buf) > self.max_points:
                # keep only the last max_points
                del buf[: len(buf) - self.max_points]
            # update series efficiently
            self.series[i].replace(buf)

        # Update axes ranges
        self.axis_x.setRange(x0, x0 + self.max_points)

        if self.auto_scale:
            # Determine max among all series buffers
            current_max = 1.0
            for buf in self._buffers:
                if buf:
                    m = max(p.y() for p in buf)
                    if m > current_max:
                        current_max = m
            # add headroom
            self.axis_y.setRange(0, current_max * 1.2)


# --------------------------- Main Window --------------------------------
class MetricCard(QWidget):
    def __init__(self, title: str, unit: str = "", is_percent: bool = False, color: str = "#00c853", sparkline: bool = True, max_points: int = 120) -> None:
        super().__init__()
        self.is_percent = is_percent
        self.unit = unit
        self._dyn_max: float = 10.0 if not is_percent else 100.0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame()
        self.frame.setObjectName("Card")
        outer.addWidget(self.frame)

        v = QVBoxLayout(self.frame)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("Title")
        self.lbl_value = QLabel(("-- " + unit).strip())
        self.lbl_value.setObjectName("Value")
        v.addWidget(self.lbl_title)
        v.addWidget(self.lbl_value)

        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setStyleSheet(f"QProgressBar::chunk{{background-color:{color}; border-radius:6px;}}")
        v.addWidget(self.bar)

        self.sparkline: Optional[TimeSeriesChart] = None
        if sparkline:
            # For sparkline, hide decorations
            self.sparkline = TimeSeriesChart("", [title], max_points=max_points, y_range=(0, 100 if is_percent else 1), auto_scale=(not is_percent))
            self.sparkline.chart.legend().setVisible(False)
            self.sparkline.chart.setTitle("")
            self.sparkline.axis_x.setVisible(False)
            self.sparkline.axis_y.setVisible(False)
            self.sparkline.chart.setMargins(QMargins(0, 0, 0, 0))
            v.addWidget(self.sparkline)

        sp = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setSizePolicy(sp)

    def set_tooltip(self, text: str) -> None:
        self.setToolTip(text)
        self.frame.setToolTip(text)
        self.lbl_value.setToolTip(text)
        self.lbl_title.setToolTip(text)

    def set_unavailable(self, message: str = "N/A") -> None:
        self.lbl_value.setText(message)
        self.bar.setValue(0)

    def update_percent(self, pct: float) -> None:
        try:
            pct_f = max(0.0, min(100.0, float(pct)))
        except Exception:
            pct_f = 0.0
        self.lbl_value.setText(f"{pct_f:.1f} %")
        self.bar.setValue(int(round(pct_f)))
        if self.sparkline is not None:
            self.sparkline.append([pct_f])

    def update_value(self, value: float, ref_max: Optional[float] = None) -> None:
        try:
            v = float(value)
        except Exception:
            v = 0.0
        self.lbl_value.setText(f"{v:.2f} {self.unit}".strip())
        if self.is_percent:
            m = 100.0
        else:
            if ref_max is None:
                self._dyn_max = max(v, self._dyn_max * 0.98)
                m = max(self._dyn_max, 1e-6)
            else:
                m = max(ref_max, 1e-6)
        pct = int(round(max(0.0, min(100.0, (v / m) * 100.0)))) if m > 0 else 0
        self.bar.setValue(pct)
        if self.sparkline is not None:
            self.sparkline.append([v])


class SystemMonitor(QMainWindow):
    def __init__(self, interval_ms: int = 1) -> None:
        super().__init__()
        self.interval_ms = interval_ms
        self.setWindowTitle(f"System Monitor ({self.interval_ms} ms)")
        self.resize(1200, 800)
        self.gpu_provider = GPUProvider()

        # Toolbar for global controls
        toolbar = self.addToolBar("Controls")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar_lbl = QLabel("Update interval (ms):")
        toolbar_lbl.setStyleSheet("QLabel { color: #b0b0b0; }")
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(1, 5000)
        self.spin_interval.setValue(self.interval_ms)
        self.spin_interval.setSingleStep(1)
        self.spin_interval.setToolTip("Global data update interval in milliseconds")
        toolbar.addWidget(toolbar_lbl)
        toolbar.addWidget(self.spin_interval)
        self.spin_interval.valueChanged.connect(self.on_interval_changed)

        # Tabs
        tabs = QTabWidget()
        self.setCentralWidget(tabs)
        self.tabs = tabs

        # Dashboard (cards)
        self.dashboard = QWidget()
        grid = QGridLayout(self.dashboard)
        grid.setSpacing(12)

        self.card_cpu = MetricCard("CPU", unit="%", is_percent=True, color="#00c853")
        self.card_mem = MetricCard("Memory", unit="%", is_percent=True, color="#ffd54f")
        self.card_net_up = MetricCard("Net Up", unit="MiB/s", is_percent=False, color="#2962ff")
        self.card_net_down = MetricCard("Net Down", unit="MiB/s", is_percent=False, color="#ff5252")
        self.card_disk_read = MetricCard("Disk Read", unit="MiB/s", is_percent=False, color="#00bcd4")
        self.card_disk_write = MetricCard("Disk Write", unit="MiB/s", is_percent=False, color="#ab47bc")
        gpu_names_dash = self.gpu_provider.gpu_names()
        self.card_gpu = MetricCard("GPU", unit="%", is_percent=True, color="#7c4dff")
        if not gpu_names_dash:
            self.card_gpu.set_unavailable("N/A")

        grid.addWidget(self.card_cpu, 0, 0)
        grid.addWidget(self.card_mem, 0, 1)
        grid.addWidget(self.card_net_up, 1, 0)
        grid.addWidget(self.card_net_down, 1, 1)
        grid.addWidget(self.card_disk_read, 2, 0)
        grid.addWidget(self.card_disk_write, 2, 1)
        grid.addWidget(self.card_gpu, 3, 0, 1, 2)

        tabs.addTab(self.dashboard, "Dashboard")

        # Charts
        self.chart_cpu = TimeSeriesChart("CPU Utilization", ["CPU %"], y_range=(0, 100))
        self.chart_mem = TimeSeriesChart("Memory Utilization", ["Mem %"], y_range=(0, 100))
        self.chart_net = TimeSeriesChart(
            "Network Throughput (MiB/s)", ["Up", "Down"], y_range=(0, 10), auto_scale=True
        )
        self.chart_disk = TimeSeriesChart(
            "Disk Throughput (MiB/s)", ["Read", "Write"], y_range=(0, 10), auto_scale=True
        )
        gpu_names = self.gpu_provider.gpu_names()
        if gpu_names:
            self.chart_gpu: Optional[TimeSeriesChart] = TimeSeriesChart(
                "GPU Utilization", [f"{name}" for name in gpu_names], y_range=(0, 100)
            )
        else:
            self.chart_gpu = None

        # Layout charts into tabs
        cpu_tab = QWidget()
        cpu_l = QVBoxLayout(cpu_tab)
        cpu_l.addWidget(self.chart_cpu)
        # Per-core CPU charts (separate small multiples)
        n_cores = psutil.cpu_count(logical=True) or 1
        self.core_charts: List[TimeSeriesChart] = []
        cores_container = QWidget()
        cores_grid = QGridLayout(cores_container)
        cores_grid.setSpacing(8)
        cols = min(4, max(1, int(math.sqrt(n_cores)) + 1))
        # Qualitative color palette for per-core charts
        core_colors = [
            QColor("#e53935"), QColor("#8e24aa"), QColor("#3949ab"), QColor("#1e88e5"),
            QColor("#00897b"), QColor("#43a047"), QColor("#fdd835"), QColor("#fb8c00"),
            QColor("#6d4c41"), QColor("#546e7a"), QColor("#d81b60"), QColor("#00acc1"),
        ]
        for i in range(n_cores):
            chart = TimeSeriesChart(f"CPU{i}", ["%"], max_points=200, y_range=(0, 100))
            # Apply distinct color to this core's series
            if chart.series:
                chart.series[0].setColor(core_colors[i % len(core_colors)])
            chart.chart.legend().setVisible(False)
            chart.axis_x.setVisible(False)
            chart.axis_y.setVisible(False)
            chart.chart.setMargins(QMargins(4, 4, 4, 4))
            self.core_charts.append(chart)
            r, c = divmod(i, cols)
            cores_grid.addWidget(chart, r, c)
        # Wrap core charts in a scroll area for many-core systems
        scroll = QScrollArea()
        scroll.setWidget(cores_container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        cpu_l.addWidget(scroll)
        # Summary labels for processes/threads/coroutines
        self.lbl_proc_summary = QLabel("")
        self.lbl_asyncio = QLabel("")
        small_style = "QLabel { color: #b0b0b0; font-size: 9pt; }"
        self.lbl_proc_summary.setStyleSheet(small_style)
        self.lbl_asyncio.setStyleSheet(small_style)
        summary_row = QHBoxLayout()
        summary_row.addWidget(self.lbl_proc_summary)
        summary_row.addWidget(self.lbl_asyncio)
        cpu_l.addLayout(summary_row)
        mem_tab = QWidget(); mem_l = QVBoxLayout(mem_tab); mem_l.addWidget(self.chart_mem)
        net_tab = QWidget()
        net_l = QVBoxLayout(net_tab)
        # Unit selector row for Network
        unit_row_net = QHBoxLayout()
        unit_row_net.addWidget(QLabel("Units:"))
        self.unit_combo_net = QComboBox()
        self.unit_combo_net.addItems(["MB/s", "MiB/s"])
        self.unit_combo_net.setCurrentText("MiB/s")
        unit_row_net.addWidget(self.unit_combo_net)
        self.net_formula_lbl = QLabel("1 MiB/s ≈ 1.048576 MB/s | 1 MB/s ≈ 0.9537 MiB/s")
        self.net_formula_lbl.setStyleSheet("QLabel { color: #b0b0b0; font-size: 9pt; }")
        unit_row_net.addWidget(self.net_formula_lbl)
        net_l.addLayout(unit_row_net)
        net_l.addWidget(self.chart_net)
        disk_tab = QWidget()
        disk_l = QVBoxLayout(disk_tab)
        # Unit selector row for Disk
        unit_row_disk = QHBoxLayout()
        unit_row_disk.addWidget(QLabel("Units:"))
        self.unit_combo_disk = QComboBox()
        self.unit_combo_disk.addItems(["MB/s", "MiB/s"])
        self.unit_combo_disk.setCurrentText("MiB/s")
        unit_row_disk.addWidget(self.unit_combo_disk)
        self.disk_formula_lbl = QLabel("1 MiB/s ≈ 1.048576 MB/s | 1 MB/s ≈ 0.9537 MiB/s")
        self.disk_formula_lbl.setStyleSheet("QLabel { color: #b0b0b0; font-size: 9pt; }")
        unit_row_disk.addWidget(self.disk_formula_lbl)
        disk_l.addLayout(unit_row_disk)
        disk_l.addWidget(self.chart_disk)
        tabs.addTab(cpu_tab, "CPU")
        tabs.addTab(mem_tab, "Memory")
        tabs.addTab(net_tab, "Network")
        tabs.addTab(disk_tab, "Disk")
        if self.chart_gpu is not None:
            gpu_tab = QWidget(); gpu_l = QVBoxLayout(gpu_tab); gpu_l.addWidget(self.chart_gpu)
            tabs.addTab(gpu_tab, "GPU")
        else:
            gpu_tab = QWidget(); gpu_l = QVBoxLayout(gpu_tab);
            gpu_l.addWidget(QLabel("No NVIDIA GPU metrics available (pynvml/nvidia-smi not found)."))
            tabs.addTab(gpu_tab, "GPU")

        # Wire unit selectors and init unit mode
        self.unit_combo_net.currentTextChanged.connect(self.on_unit_changed)
        self.unit_combo_disk.currentTextChanged.connect(self.on_unit_changed)
        self.unit_mode = "MiB/s"
        self._bytes_per_unit = 1024**2
        self.on_unit_changed(self.unit_mode)

        # Processes tab
        self.proc_table = QTableWidget(0, 5)
        self.proc_table.setHorizontalHeaderLabels(["PID", "Name", "CPU %", "Mem %", "Threads"])
        hdr = self.proc_table.horizontalHeader()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        procs_tab = QWidget(); procs_l = QVBoxLayout(procs_tab); procs_l.addWidget(self.proc_table)
        self.tabs.addTab(procs_tab, "Processes")
        self._proc_refresh_accum = 0.0
        self._procs_primed = False

        # Info tab
        self.info_edit = QTextEdit()
        self.info_edit.setReadOnly(True)
        info_tab = QWidget(); info_l = QVBoxLayout(info_tab); info_l.addWidget(self.info_edit)
        tabs.addTab(info_tab, "System Info")

        # Initialize metrics state
        self._last_net = psutil.net_io_counters()
        self._elapsed = QElapsedTimer()
        self._elapsed.start()
        # Warm-up CPU percent calculation
        psutil.cpu_percent(interval=None)
        # Dynamic network scale baselines
        self._net_dyn_up = 1.0
        self._net_dyn_down = 1.0
        # Disk IO state and dynamic scale baselines
        self._last_disk = psutil.disk_io_counters()
        self._disk_dyn_read = 1.0
        self._disk_dyn_write = 1.0

        self.refresh_info()

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(self.interval_ms)

    # ---------------------- Info builders ----------------------
    def refresh_info(self) -> None:
        lines = []
        # CPU
        lines.append("=== CPU Information ===")
        lines.append(f"Processor: {platform.processor()}")
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
                lines.append(f"CPU Frequency: current {freq.current/1000:.2f} GHz, max {freq.max/1000:.2f} GHz")
        except Exception:
            pass

        # System
        lines.append("\n=== System Information ===")
        lines.append(f"System: {platform.system()}")
        lines.append(f"Node Name: {platform.node()}")
        lines.append(f"Release: {platform.release()}")
        lines.append(f"Version: {platform.version()}")
        lines.append(f"Platform: {platform.platform()}")

        # Memory
        lines.append("\n=== Memory Information ===")
        vm = psutil.virtual_memory()
        lines.append(f"Total: {vm.total/ (1024**3):.2f} GiB; Available: {vm.available/(1024**3):.2f} GiB")
        lines.append(f"Used: {vm.used/(1024**3):.2f} GiB ({vm.percent:.1f}%)")

        # Disk
        lines.append("\n=== Disk Information ===")
        for p in psutil.disk_partitions(all=False):
            try:
                du = psutil.disk_usage(p.mountpoint)
                lines.append(
                    f"{p.device} ({p.mountpoint}) - {du.used/(1024**3):.2f}/{du.total/(1024**3):.2f} GiB used ({du.percent:.1f}%)"
                )
            except Exception:
                pass

        # GPU
        lines.append("\n=== GPU Information ===")
        names = self.gpu_provider.gpu_names()
        if names:
            for i, n in enumerate(names):
                lines.append(f"GPU {i}: {n}")
        else:
            lines.append("No NVIDIA GPUs detected or metrics unavailable.")

        # Python
        lines.append("\n=== Python Information ===")
        lines.append(f"Python Version: {sys.version}")
        lines.append(f"Python Executable: {sys.executable}")

        self.info_edit.setPlainText("\n".join(lines))

    def on_unit_changed(self, mode: str) -> None:
        mapping = {"MB/s": 1_000_000, "MiB/s": 1024**2}
        if mode not in mapping:
            return
        self.unit_mode = mode
        self._bytes_per_unit = mapping[mode]
        # Sync combos without recursion
        if hasattr(self, "unit_combo_net"):
            if self.unit_combo_net.currentText() != mode:
                self.unit_combo_net.blockSignals(True)
                self.unit_combo_net.setCurrentText(mode)
                self.unit_combo_net.blockSignals(False)
        if hasattr(self, "unit_combo_disk"):
            if self.unit_combo_disk.currentText() != mode:
                self.unit_combo_disk.blockSignals(True)
                self.unit_combo_disk.setCurrentText(mode)
                self.unit_combo_disk.blockSignals(False)
        # Update card unit labels
        self.card_net_up.unit = mode
        self.card_net_down.unit = mode
        self.card_disk_read.unit = mode
        self.card_disk_write.unit = mode
        # Update chart titles
        self.chart_net.chart.setTitle(f"Network Throughput ({mode})")
        self.chart_disk.chart.setTitle(f"Disk Throughput ({mode})")
        # Reset dynamic baselines to adapt quickly after unit change
        self._net_dyn_up = 1.0
        self._net_dyn_down = 1.0
        self._disk_dyn_read = 1.0
        self._disk_dyn_write = 1.0

    def on_interval_changed(self, val: int) -> None:
        try:
            ms = int(val)
        except Exception:
            return
        ms = max(1, ms)
        if ms != self.interval_ms:
            self.interval_ms = ms
            try:
                self.timer.setInterval(self.interval_ms)
            except Exception:
                # Fallback in case timer not yet started
                self.timer.start(self.interval_ms)
            self.setWindowTitle(f"System Monitor ({self.interval_ms} ms)")

    def refresh_processes(self) -> None:
        try:
            # First pass: prime per-process CPU percentages
            if not getattr(self, "_procs_primed", False):
                for p in psutil.process_iter():
                    try:
                        p.cpu_percent(None)
                    except Exception:
                        pass
                self._procs_primed = True
                return

            rows = []
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
                rows.append((cpu, p.info.get('pid'), p.info.get('name') or "", mem, threads))

            rows.sort(key=lambda x: x[0], reverse=True)
            rows = rows[:20]
            self.proc_table.setRowCount(len(rows))
            for r, (cpu, pid, name, mem, thr) in enumerate(rows):
                self.proc_table.setItem(r, 0, QTableWidgetItem(str(pid)))
                self.proc_table.setItem(r, 1, QTableWidgetItem(name))
                self.proc_table.setItem(r, 2, QTableWidgetItem(f"{cpu:.1f}"))
                self.proc_table.setItem(r, 3, QTableWidgetItem(f"{mem:.1f}"))
                self.proc_table.setItem(r, 4, QTableWidgetItem(str(thr)))

            # Update summary labels under CPU tab
            self.lbl_proc_summary.setText(f"Processes: {proc_count:,}   Threads: {total_threads:,}")
            # asyncio coroutines count (tasks)
            coro_count = 0
            try:
                loop = asyncio.get_running_loop()
                coro_count = len(asyncio.all_tasks(loop))
            except Exception:
                coro_count = 0
            self.lbl_asyncio.setText(f"Python coroutines (asyncio tasks): {coro_count}")
        except Exception:
            # ignore transient access errors
            pass

    # ----------------------- Timer update ----------------------
    def on_timer(self) -> None:
        # Use a monotonic Qt timer for consistent dt
        dt_ms = max(1, self._elapsed.restart())
        dt = dt_ms / 1000.0

        # CPU
        cpu = float(psutil.cpu_percent(interval=None))
        self.card_cpu.update_percent(cpu)
        if self.tabs.currentIndex() == 1:
            self.chart_cpu.append([cpu])
            # Per-core CPU update into separate charts
            try:
                cores = psutil.cpu_percent(interval=None, percpu=True)
                if isinstance(cores, list) and cores and hasattr(self, "core_charts"):
                    for i, val in enumerate(cores[: len(self.core_charts)]):
                        self.core_charts[i].append([float(val)])
            except Exception:
                pass

        # Memory
        mem = psutil.virtual_memory()
        mem_pct = float(mem.percent)
        self.card_mem.update_percent(mem_pct)
        if self.tabs.currentIndex() == 2:
            self.chart_mem.append([mem_pct])

        # Network (MB/s)
        net = psutil.net_io_counters()
        up_mbs = max(0.0, (net.bytes_sent - self._last_net.bytes_sent) / dt) / self._bytes_per_unit
        down_mbs = max(0.0, (net.bytes_recv - self._last_net.bytes_recv) / dt) / self._bytes_per_unit
        self._last_net = net
        # Update dynamic reference maxes using time-constant decay (independent of frame rate)
        tau = 10.0  # seconds
        alpha = math.exp(-dt / tau)
        self._net_dyn_up = max(up_mbs, self._net_dyn_up * alpha)
        self._net_dyn_down = max(down_mbs, self._net_dyn_down * alpha)
        self.card_net_up.update_value(up_mbs, ref_max=self._net_dyn_up)
        self.card_net_down.update_value(down_mbs, ref_max=self._net_dyn_down)
        if self.tabs.currentIndex() == 3:
            self.chart_net.append([up_mbs, down_mbs])

        # Disk (MB/s)
        try:
            dio = psutil.disk_io_counters()
        except Exception:
            dio = None
        if dio and getattr(self, "_last_disk", None):
            read_mbs = max(0.0, (dio.read_bytes - self._last_disk.read_bytes) / dt) / self._bytes_per_unit
            write_mbs = max(0.0, (dio.write_bytes - self._last_disk.write_bytes) / dt) / self._bytes_per_unit
        else:
            read_mbs = 0.0
            write_mbs = 0.0
        self._last_disk = dio
        # Update dynamic reference maxes using time-constant decay
        self._disk_dyn_read = max(read_mbs, self._disk_dyn_read * alpha)
        self._disk_dyn_write = max(write_mbs, self._disk_dyn_write * alpha)
        self.card_disk_read.update_value(read_mbs, ref_max=self._disk_dyn_read)
        self.card_disk_write.update_value(write_mbs, ref_max=self._disk_dyn_write)
        if self.tabs.currentIndex() == 4:
            self.chart_disk.append([read_mbs, write_mbs])

        # GPU
        utils = self.gpu_provider.gpu_utils()
        if utils:
            avg = sum(utils) / len(utils)
            self.card_gpu.update_percent(avg)
            if self.chart_gpu is not None and self.tabs.currentIndex() == 5:
                self.chart_gpu.append(utils)
            # Tooltip with per-GPU details
            names = self.gpu_provider.gpu_names()
            tip_parts = []
            for i, u in enumerate(utils):
                name = names[i] if i < len(names) else f"GPU {i}"
                tip_parts.append(f"{name}: {u:.0f}%")
            self.card_gpu.set_tooltip(", ".join(tip_parts))
        else:
            self.card_gpu.set_unavailable("N/A")

        # Periodically refresh process table and summaries
        try:
            self._proc_refresh_accum += dt
        except Exception:
            self._proc_refresh_accum = 0.0
        if self._proc_refresh_accum >= 0.5:
            self._proc_refresh_accum = 0.0
            self.refresh_processes()


def main() -> None:
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    win = SystemMonitor(interval_ms=1)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()