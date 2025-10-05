"""
Real-time System Monitor (PySide6)

Dependencies:
- PySide6 (Qt 6)
- psutil
- Optional: pynvml (for NVIDIA GPU metrics) or system nvidia-smi

Install:
  pip install PySide6 psutil pynvml

Run:
  python play.py

Notes:
- Updates every 50 ms by default.
- Uses QtCharts for efficient, built-in plotting (no extra plotting libs required).
"""
from __future__ import annotations

import sys
import platform
import time
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple

try:
    import psutil  # type: ignore
except Exception as e:
    print("psutil is required. Install with: pip install psutil")
    raise

# PySide6 imports
from PySide6.QtCore import Qt, QTimer, QPointF, QMargins
from PySide6.QtGui import QFont, QPalette, QColor
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
    Tries pynvml first; falls back to calling nvidia-smi if available.
    """

    def __init__(self) -> None:
        self.method: str = "none"
        self._gpu_names: List[str] = []
        self._nvml = None
        self._nvml_handles = []
        self._last_smi_time: float = 0.0
        self._last_smi_utils: List[float] = []
        self._smi_min_interval = 0.02  # seconds; avoid hammering nvidia-smi every 5ms

        # Try NVML
        try:
            import pynvml  # type: ignore

            pynvml.nvmlInit()
            count = pynvml.nvmlDeviceGetCount()
            self._nvml = pynvml
            for i in range(count):
                h = pynvml.nvmlDeviceGetHandleByIndex(i)
                self._nvml_handles.append(h)
                name = pynvml.nvmlDeviceGetName(h)
                # bytes to str if needed
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
            now = time.time()
            # throttle calls
            if now - self._last_smi_time >= self._smi_min_interval:
                try:
                    self._last_smi_utils = self._query_nvidia_smi_utils()
                except Exception:
                    pass
                self._last_smi_time = now
            return list(self._last_smi_utils)
        else:
            return []


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
        self.view.setRenderHint(self.view.renderHints() | self.view.renderHints())
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
    def __init__(self, interval_ms: int = 5) -> None:
        super().__init__()
        self.setWindowTitle("System Monitor (5ms)")
        self.resize(1200, 800)

        self.interval_ms = interval_ms
        self.gpu_provider = GPUProvider()

        # Tabs
        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        # Dashboard (cards)
        self.dashboard = QWidget()
        grid = QGridLayout(self.dashboard)
        grid.setSpacing(12)

        self.card_cpu = MetricCard("CPU", unit="%", is_percent=True, color="#00c853")
        self.card_mem = MetricCard("Memory", unit="%", is_percent=True, color="#ffd54f")
        self.card_net_up = MetricCard("Net Up", unit="MB/s", is_percent=False, color="#2962ff")
        self.card_net_down = MetricCard("Net Down", unit="MB/s", is_percent=False, color="#ff5252")
        self.card_disk_read = MetricCard("Disk Read", unit="MB/s", is_percent=False, color="#00bcd4")
        self.card_disk_write = MetricCard("Disk Write", unit="MB/s", is_percent=False, color="#ab47bc")
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
            "Network Throughput (MB/s)", ["Up", "Down"], y_range=(0, 10), auto_scale=True
        )
        self.chart_disk = TimeSeriesChart(
            "Disk Throughput (MB/s)", ["Read", "Write"], y_range=(0, 10), auto_scale=True
        )
        gpu_names = self.gpu_provider.gpu_names()
        if gpu_names:
            self.chart_gpu: Optional[TimeSeriesChart] = TimeSeriesChart(
                "GPU Utilization", [f"{name}" for name in gpu_names], y_range=(0, 100)
            )
        else:
            self.chart_gpu = None

        # Layout charts into tabs
        cpu_tab = QWidget(); cpu_l = QVBoxLayout(cpu_tab); cpu_l.addWidget(self.chart_cpu)
        mem_tab = QWidget(); mem_l = QVBoxLayout(mem_tab); mem_l.addWidget(self.chart_mem)
        net_tab = QWidget(); net_l = QVBoxLayout(net_tab); net_l.addWidget(self.chart_net)
        disk_tab = QWidget(); disk_l = QVBoxLayout(disk_tab); disk_l.addWidget(self.chart_disk)
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

        # Info tab
        self.info_edit = QTextEdit()
        self.info_edit.setReadOnly(True)
        info_tab = QWidget(); info_l = QVBoxLayout(info_tab); info_l.addWidget(self.info_edit)
        tabs.addTab(info_tab, "System Info")

        # Initialize metrics state
        self._last_net = psutil.net_io_counters()
        self._last_time = time.time()
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
        lines.append(f"Total: {vm.total/ (1024**3):.2f} GB; Available: {vm.available/(1024**3):.2f} GB")
        lines.append(f"Used: {vm.used/(1024**3):.2f} GB ({vm.percent:.1f}%)")

        # Disk
        lines.append("\n=== Disk Information ===")
        for p in psutil.disk_partitions(all=False):
            try:
                du = psutil.disk_usage(p.mountpoint)
                lines.append(
                    f"{p.device} ({p.mountpoint}) - {du.used/(1024**3):.2f}/{du.total/(1024**3):.2f} GB used ({du.percent:.1f}%)"
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

    # ----------------------- Timer update ----------------------
    def on_timer(self) -> None:
        now = time.time()
        dt = max(1e-6, now - self._last_time)
        self._last_time = now

        # CPU
        cpu = float(psutil.cpu_percent(interval=None))
        self.card_cpu.update_percent(cpu)
        self.chart_cpu.append([cpu])

        # Memory
        mem = psutil.virtual_memory()
        mem_pct = float(mem.percent)
        self.card_mem.update_percent(mem_pct)
        self.chart_mem.append([mem_pct])

        # Network (MB/s)
        net = psutil.net_io_counters()
        up_mbs = max(0.0, (net.bytes_sent - self._last_net.bytes_sent) / dt) / (1024 * 1024)
        down_mbs = max(0.0, (net.bytes_recv - self._last_net.bytes_recv) / dt) / (1024 * 1024)
        self._last_net = net
        # Update dynamic reference maxes (decay slowly)
        self._net_dyn_up = max(up_mbs, self._net_dyn_up * 0.98)
        self._net_dyn_down = max(down_mbs, self._net_dyn_down * 0.98)
        self.card_net_up.update_value(up_mbs, ref_max=self._net_dyn_up)
        self.card_net_down.update_value(down_mbs, ref_max=self._net_dyn_down)
        self.chart_net.append([up_mbs, down_mbs])

        # Disk (MB/s)
        try:
            dio = psutil.disk_io_counters()
        except Exception:
            dio = None
        if dio and getattr(self, "_last_disk", None):
            read_mbs = max(0.0, (dio.read_bytes - self._last_disk.read_bytes) / dt) / (1024 * 1024)
            write_mbs = max(0.0, (dio.write_bytes - self._last_disk.write_bytes) / dt) / (1024 * 1024)
        else:
            read_mbs = 0.0
            write_mbs = 0.0
        self._last_disk = dio
        # Update dynamic reference maxes (decay slowly)
        self._disk_dyn_read = max(read_mbs, self._disk_dyn_read * 0.98)
        self._disk_dyn_write = max(write_mbs, self._disk_dyn_write * 0.98)
        self.card_disk_read.update_value(read_mbs, ref_max=self._disk_dyn_read)
        self.card_disk_write.update_value(write_mbs, ref_max=self._disk_dyn_write)
        self.chart_disk.append([read_mbs, write_mbs])

        # GPU
        utils = self.gpu_provider.gpu_utils()
        if utils:
            avg = sum(utils) / len(utils)
            self.card_gpu.update_percent(avg)
            if self.chart_gpu is not None:
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


def main() -> None:
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    win = SystemMonitor(interval_ms=50)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()