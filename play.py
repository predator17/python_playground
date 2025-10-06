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
- Updates every 100 ms by default (configurable via toolbar).
- Uses QtCharts for efficient, built-in plotting (no extra plotting libs required).
- Keyboard shortcuts: P=Pause, R=Resume, Esc=Quit
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
from typing import List, Optional, Tuple

try:
    import psutil  # type: ignore
except Exception as e:
    print("psutil is required. Install with: pip install psutil")
    raise

# PySide6 imports
from PySide6.QtCore import Qt, QTimer, QPointF, QMargins, QElapsedTimer, Signal, QObject
from PySide6.QtGui import QPalette, QColor, QPainter, QKeySequence, QAction
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
    QTreeWidget,
    QTreeWidgetItem,
    QLineEdit,
    QPushButton,
)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis


# ----------------------------- Helper Functions -----------------------------
def get_cpu_model_name() -> str:
    """Get CPU model/brand name."""
    try:
        # Try platform-specific methods first (more reliable than platform.processor())
        
        # Linux: read from /proc/cpuinfo
        if platform.system() == "Linux":
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line.lower():
                            model = line.split(":", 1)[1].strip()
                            if model and not model.startswith("x86"):  # Avoid architecture strings
                                return model
            except Exception:
                pass
        
        # macOS: use sysctl
        if platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                    timeout=1.0
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except Exception:
                pass
        
        # Windows: use wmic
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name"],
                    capture_output=True,
                    text=True,
                    timeout=1.5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1 and lines[1].strip():
                        return lines[1].strip()
            except Exception:
                pass
        
        # Fallback: try platform.processor() (may return architecture on some systems)
        proc = platform.processor()
        if proc and proc.strip() and not proc.strip().lower() in ["x86_64", "i386", "i686", "amd64", "arm64", "aarch64"]:
            return proc.strip()
        
        # Final fallback
        return f"{platform.machine()} CPU"
    except Exception:
        return "Unknown CPU"


def get_per_core_frequencies() -> List[float]:
    """Get per-core CPU frequencies in MHz. Returns empty list if not available."""
    try:
        # Try psutil per-core frequencies (supported on some systems)
        if hasattr(psutil, 'cpu_freq') and callable(psutil.cpu_freq):
            freq = psutil.cpu_freq(percpu=True)
            if freq and isinstance(freq, list):
                return [f.current for f in freq if hasattr(f, 'current')]
        return []
    except Exception:
        return []


def get_memory_frequency() -> float:
    """Get RAM frequency in MHz. Returns 0 if not available."""
    try:
        # Linux: try reading from dmidecode (requires root)
        if platform.system() == "Linux":
            try:
                result = subprocess.run(
                    ["dmidecode", "-t", "memory"],
                    capture_output=True,
                    text=True,
                    timeout=2.0
                )
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if "Speed:" in line and "MHz" in line:
                            # Extract first speed value found
                            parts = line.split(":")
                            if len(parts) > 1:
                                speed_str = parts[1].strip().split()[0]
                                return float(speed_str)
            except Exception:
                pass
        
        # Windows: use wmic
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "memorychip", "get", "speed"],
                    capture_output=True,
                    text=True,
                    timeout=2.0
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:
                        speed_str = lines[1].strip()
                        if speed_str.isdigit():
                            return float(speed_str)
            except Exception:
                pass
        
        return 0.0
    except Exception:
        return 0.0


def get_cpu_temperatures() -> List[Tuple[str, float]]:
    """Get CPU temperature sensors. Returns list of (label, temp_celsius) tuples."""
    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                cpu_temps = []
                # Look for common CPU temperature sensor names
                for name in ["coretemp", "k10temp", "cpu_thermal", "cpu-thermal"]:
                    if name in temps:
                        for entry in temps[name]:
                            if entry.current > 0:
                                cpu_temps.append((entry.label or name, entry.current))
                return cpu_temps
        return []
    except Exception:
        return []


def get_gpu_temperatures(gpu_provider) -> List[float]:
    """Get GPU temperatures in Celsius. Returns list of temperatures for each GPU."""
    try:
        if gpu_provider.method == "nvml" and gpu_provider._nvml is not None:
            temps = []
            for h in gpu_provider._nvml_handles:
                try:
                    temp = gpu_provider._nvml.nvmlDeviceGetTemperature(h, gpu_provider._nvml.NVML_TEMPERATURE_GPU)
                    temps.append(float(temp))
                except Exception:
                    temps.append(0.0)
            return temps
        elif gpu_provider.method == "nvidia-smi":
            # Query via nvidia-smi
            cmd = [
                "nvidia-smi",
                "--query-gpu=temperature.gpu",
                "--format=csv,noheader,nounits",
            ]
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
            temps = []
            for line in out.stdout.strip().splitlines():
                try:
                    temps.append(float(line.strip()))
                except Exception:
                    temps.append(0.0)
            return temps
        return []
    except Exception:
        return []


def apply_dark_theme(app: QApplication) -> None:
    """Apply modern dark theme with enhanced aesthetics."""
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
        QMainWindow { background-color: #0d0d0d; }
        
        /* Enhanced card design with depth */
        QFrame#Card { 
            background-color: #1e1e1e; 
            border: 1px solid #333333; 
            border-radius: 12px;
            padding: 4px;
        }
        QFrame#Card:hover {
            border: 1px solid #404040;
            background-color: #232323;
        }
        
        /* Typography improvements */
        QLabel#Title { 
            font-weight: 600; 
            font-size: 12pt; 
            color: #b0b0b0;
            letter-spacing: 0.5px;
        }
        QLabel#Value { 
            font-weight: 700; 
            font-size: 22pt; 
            color: #ffffff;
            letter-spacing: 0.3px;
        }
        
        /* Enhanced progress bars */
        QProgressBar { 
            background-color: #1a1a1a; 
            border: 1px solid #2a2a2a; 
            border-radius: 7px; 
            height: 16px;
            text-align: center;
        }
        QProgressBar::chunk { 
            background-color: #00c853; 
            border-radius: 6px;
        }
        
        /* Toolbar styling */
        QToolBar {
            background-color: #1a1a1a;
            border-bottom: 2px solid #2a2a2a;
            spacing: 8px;
            padding: 8px;
        }
        QToolBar QLabel {
            color: #b0b0b0;
            font-size: 10pt;
            padding: 0 4px;
        }
        QToolBar QSpinBox {
            background-color: #252525;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            padding: 4px 8px;
            color: #e0e0e0;
            min-width: 80px;
        }
        QToolBar QPushButton {
            background-color: #2a2a2a;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            padding: 6px 12px;
            color: #e0e0e0;
            font-weight: 500;
        }
        QToolBar QPushButton:hover {
            background-color: #333333;
            border: 1px solid #4a4a4a;
        }
        QToolBar QPushButton:pressed {
            background-color: #202020;
        }
        QToolBar QPushButton#PauseButton {
            background-color: #1976d2;
            border: 1px solid #2196f3;
        }
        QToolBar QPushButton#PauseButton:hover {
            background-color: #2196f3;
        }
        
        /* Tab improvements */
        QTabWidget::pane { 
            border: 1px solid #2a2a2a;
            background-color: #141414;
            top: -1px;
        }
        QTabBar::tab { 
            background: #1a1a1a; 
            padding: 8px 16px; 
            border: 1px solid #2a2a2a; 
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            margin-right: 2px;
        }
        QTabBar::tab:selected { 
            background: #2a2a2a;
            border-bottom: 2px solid #3584e4;
        }
        QTabBar::tab:hover:!selected {
            background: #222222;
        }
        
        /* Table styling */
        QTableWidget {
            background-color: #1a1a1a;
            alternate-background-color: #1e1e1e;
            gridline-color: #2a2a2a;
            selection-background-color: #3584e4;
        }
        QHeaderView::section {
            background-color: #252525;
            color: #b0b0b0;
            padding: 6px;
            border: 1px solid #2a2a2a;
            font-weight: 600;
        }
        """
    )

# ----------------------------- GPU Provider -----------------------------
class GPUProvider:
    """Provides GPU names, utilization, VRAM, and frequency.
    Tries nvidia-ml-py first; falls back to calling nvidia-smi if available.
    """

    def __init__(self) -> None:
        self.method: str = "none"
        self._gpu_names: List[str] = []
        self._nvml = None
        self._nvml_handles = []
        self._last_smi_time: float = 0.0
        self._last_smi_utils: List[float] = []
        self._last_smi_vram: List[Tuple[float, float]] = []  # (used_mb, total_mb) per GPU
        self._last_smi_freq: List[float] = []  # current freq in MHz per GPU
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
                    self._last_smi_vram = [(0.0, 0.0) for _ in names]
                    self._last_smi_freq = [0.0 for _ in names]
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

    def _query_nvidia_smi_vram(self) -> List[Tuple[float, float]]:
        """Query VRAM usage (used, total) in MB via nvidia-smi."""
        cmd = [
            "nvidia-smi",
            "--query-gpu=memory.used,memory.total",
            "--format=csv,noheader,nounits",
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
        vram: List[Tuple[float, float]] = []
        for line in out.stdout.strip().splitlines():
            try:
                parts = line.strip().split(",")
                used = float(parts[0].strip())
                total = float(parts[1].strip())
                vram.append((used, total))
            except Exception:
                vram.append((0.0, 0.0))
        return vram

    def _query_nvidia_smi_freq(self) -> List[float]:
        """Query GPU clock frequency in MHz via nvidia-smi."""
        cmd = [
            "nvidia-smi",
            "--query-gpu=clocks.current.graphics",
            "--format=csv,noheader,nounits",
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
        freqs: List[float] = []
        for line in out.stdout.strip().splitlines():
            try:
                freqs.append(float(line.strip()))
            except Exception:
                freqs.append(0.0)
        return freqs

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

    def gpu_vram_info(self) -> List[Tuple[float, float]]:
        """Returns list of (used_mb, total_mb) tuples for each GPU."""
        if self.method == "nvml" and self._nvml is not None:
            vram_list: List[Tuple[float, float]] = []
            for h in self._nvml_handles:
                try:
                    mem_info = self._nvml.nvmlDeviceGetMemoryInfo(h)
                    used_mb = mem_info.used / (1024 * 1024)
                    total_mb = mem_info.total / (1024 * 1024)
                    vram_list.append((used_mb, total_mb))
                except Exception:
                    vram_list.append((0.0, 0.0))
            return vram_list
        elif self.method == "nvidia-smi":
            return list(self._last_smi_vram)
        else:
            return []

    def gpu_frequencies(self) -> List[float]:
        """Returns list of current GPU clock frequencies in MHz."""
        if self.method == "nvml" and self._nvml is not None:
            freqs: List[float] = []
            for h in self._nvml_handles:
                try:
                    freq_mhz = self._nvml.nvmlDeviceGetClockInfo(h, self._nvml.NVML_CLOCK_GRAPHICS)
                    freqs.append(float(freq_mhz))
                except Exception:
                    freqs.append(0.0)
            return freqs
        elif self.method == "nvidia-smi":
            return list(self._last_smi_freq)
        else:
            return []

    def _smi_poll_loop(self) -> None:
        # Background polling loop for nvidia-smi to avoid blocking the UI thread
        while True:
            try:
                utils = self._query_nvidia_smi_utils()
                if utils:
                    self._last_smi_utils = utils
                vram = self._query_nvidia_smi_vram()
                if vram:
                    self._last_smi_vram = vram
                freq = self._query_nvidia_smi_freq()
                if freq:
                    self._last_smi_freq = freq
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
    def __init__(self, title: str, unit: str = "", is_percent: bool = False, color: str = "#00c853", sparkline: bool = True, max_points: int = 60) -> None:
        super().__init__()
        self.is_percent = is_percent
        self.unit = unit
        self.color = color  # Store original color for reset
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

        # Optional labels for frequency and model name
        self.lbl_frequency = QLabel("")
        self.lbl_frequency.setStyleSheet("QLabel { color: #909090; font-size: 9pt; }")
        self.lbl_frequency.setVisible(False)
        v.addWidget(self.lbl_frequency)
        
        self.lbl_model = QLabel("")
        self.lbl_model.setStyleSheet("QLabel { color: #808080; font-size: 8pt; font-style: italic; }")
        self.lbl_model.setWordWrap(True)
        self.lbl_model.setVisible(False)
        v.addWidget(self.lbl_model)

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

    def set_frequency(self, freq_mhz: float) -> None:
        """Set frequency display in MHz."""
        if freq_mhz > 0:
            self.lbl_frequency.setText(f"⚡ {freq_mhz:.0f} MHz")
            self.lbl_frequency.setVisible(True)
        else:
            self.lbl_frequency.setVisible(False)

    def set_model(self, model_name: str) -> None:
        """Set model/brand name display."""
        if model_name and model_name.strip():
            self.lbl_model.setText(f"🔹 {model_name.strip()}")
            self.lbl_model.setVisible(True)
        else:
            self.lbl_model.setVisible(False)

    def update_percent(self, pct: float) -> None:
        """Update percentage value with warning colors for high usage."""
        try:
            pct_f = max(0.0, min(100.0, float(pct)))
        except Exception:
            pct_f = 0.0
        self.lbl_value.setText(f"{pct_f:.1f} %")
        self.bar.setValue(int(round(pct_f)))
        
        # Apply warning colors for high resource usage
        if pct_f >= 90.0:
            # Critical: red
            self.bar.setStyleSheet(f"QProgressBar::chunk{{background-color:#f44336; border-radius:6px;}}")
        elif pct_f >= 80.0:
            # Warning: orange
            self.bar.setStyleSheet(f"QProgressBar::chunk{{background-color:#ff9800; border-radius:6px;}}")
        else:
            # Normal: original color
            self.bar.setStyleSheet(f"QProgressBar::chunk{{background-color:{self.color}; border-radius:6px;}}")
        
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
    def __init__(self, interval_ms: int = 100) -> None:
        super().__init__()
        self.interval_ms = interval_ms
        self.setWindowTitle(f"System Monitor ({self.interval_ms} ms)")
        self.resize(1200, 800)
        self.gpu_provider = GPUProvider()
        self._paused = False  # Track pause state

        # Toolbar for global controls
        toolbar = self.addToolBar("Controls")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        
        # Update interval control
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
        
        # Add separator
        toolbar.addSeparator()
        
        # GPU refresh interval control
        toolbar.addWidget(QLabel("GPU refresh (ms):"))
        self.spin_gpu_refresh = QSpinBox()
        self.spin_gpu_refresh.setRange(100, 5000)
        self.spin_gpu_refresh.setValue(100)
        self.spin_gpu_refresh.setToolTip("GPU metrics update interval in milliseconds")
        toolbar.addWidget(self.spin_gpu_refresh)
        
        # Process refresh interval control
        toolbar.addWidget(QLabel("Process refresh (ms):"))
        self.spin_proc_refresh = QSpinBox()
        self.spin_proc_refresh.setRange(100, 5000)
        self.spin_proc_refresh.setValue(100)
        self.spin_proc_refresh.setToolTip("Process table update interval in milliseconds")
        toolbar.addWidget(self.spin_proc_refresh)
        
        toolbar.addSeparator()
        
        # Pause/Resume button
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setObjectName("PauseButton")
        self.btn_pause.setToolTip("Pause/Resume monitoring (Shortcut: P)")
        self.btn_pause.clicked.connect(self.toggle_pause)
        toolbar.addWidget(self.btn_pause)

        # Tabs
        tabs = QTabWidget()
        self.setCentralWidget(tabs)
        self.tabs = tabs

        # Dashboard (cards)
        self.dashboard = QWidget()
        grid = QGridLayout(self.dashboard)
        grid.setSpacing(12)

        self.card_cpu = MetricCard("CPU", unit="%", is_percent=True, color="#00c853")
        self.card_cpu.set_tooltip("Overall CPU utilization across all cores")
        # Set CPU model name (once during initialization)
        cpu_model = get_cpu_model_name()
        self.card_cpu.set_model(cpu_model)
        self.card_mem = MetricCard("Memory", unit="%", is_percent=True, color="#ffd54f")
        self.card_mem.set_tooltip("Physical memory (RAM) usage")
        self.card_net_up = MetricCard("Net Up", unit="MiB/s", is_percent=False, color="#2962ff")
        self.card_net_up.set_tooltip("Network upload throughput")
        self.card_net_down = MetricCard("Net Down", unit="MiB/s", is_percent=False, color="#ff5252")
        self.card_net_down.set_tooltip("Network download throughput")
        self.card_disk_read = MetricCard("Disk Read", unit="MiB/s", is_percent=False, color="#00bcd4")
        self.card_disk_read.set_tooltip("Disk read throughput")
        self.card_disk_write = MetricCard("Disk Write", unit="MiB/s", is_percent=False, color="#ab47bc")
        self.card_disk_write.set_tooltip("Disk write throughput")
        gpu_names_dash = self.gpu_provider.gpu_names()
        self.card_gpu = MetricCard("GPU", unit="%", is_percent=True, color="#7c4dff")
        if not gpu_names_dash:
            self.card_gpu.set_unavailable("N/A")
            self.card_gpu.set_tooltip("No NVIDIA GPU detected")
        else:
            # Set GPU model name (first GPU if multiple)
            self.card_gpu.set_model(gpu_names_dash[0])

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
        # Per-core CPU charts (separate small multiples with frequency labels)
        n_cores = psutil.cpu_count(logical=True) or 1
        self.core_charts: List[TimeSeriesChart] = []
        self.core_freq_labels: List[QLabel] = []  # Store frequency labels for updates
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
        small_style = "QLabel { color: #b0b0b0; font-size: 8pt; }"
        
        for i in range(n_cores):
            # Create a container for each core (chart + frequency label)
            core_container = QWidget()
            core_layout = QVBoxLayout(core_container)
            core_layout.setContentsMargins(0, 0, 0, 0)
            core_layout.setSpacing(2)
            
            # Create the chart
            chart = TimeSeriesChart(f"CPU{i}", ["%"], max_points=200, y_range=(0, 100))
            # Apply distinct color to this core's series
            if chart.series:
                chart.series[0].setColor(core_colors[i % len(core_colors)])
            chart.chart.legend().setVisible(False)
            chart.axis_x.setVisible(False)
            chart.axis_y.setVisible(False)
            chart.chart.setMargins(QMargins(4, 4, 4, 4))
            self.core_charts.append(chart)
            core_layout.addWidget(chart)
            
            # Create frequency label
            freq_label = QLabel("-- MHz")
            freq_label.setStyleSheet(small_style)
            freq_label.setAlignment(Qt.AlignCenter)
            self.core_freq_labels.append(freq_label)
            core_layout.addWidget(freq_label)
            
            r, c = divmod(i, cols)
            cores_grid.addWidget(core_container, r, c)
        
        # Wrap core charts in a scroll area for many-core systems
        scroll = QScrollArea()
        scroll.setWidget(cores_container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        cpu_l.addWidget(scroll)
        
        # Define small style for labels
        small_style = "QLabel { color: #b0b0b0; font-size: 9pt; }"
        
        # Summary labels for processes/threads/coroutines
        self.lbl_proc_summary = QLabel("")
        self.lbl_asyncio = QLabel("")
        self.lbl_proc_summary.setStyleSheet(small_style)
        self.lbl_asyncio.setStyleSheet(small_style)
        summary_row = QHBoxLayout()
        summary_row.addWidget(self.lbl_proc_summary)
        summary_row.addWidget(self.lbl_asyncio)
        cpu_l.addLayout(summary_row)
        
        # Memory tab with frequency display
        mem_tab = QWidget()
        mem_l = QVBoxLayout(mem_tab)
        mem_l.addWidget(self.chart_mem)
        # Add memory frequency info if available
        mem_freq = get_memory_frequency()
        if mem_freq > 0:
            self.lbl_mem_freq = QLabel(f"RAM Frequency: {mem_freq:.0f} MHz")
            self.lbl_mem_freq.setStyleSheet(small_style)
            mem_l.addWidget(self.lbl_mem_freq)
        else:
            self.lbl_mem_freq = None
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
            gpu_tab = QWidget()
            gpu_l = QVBoxLayout(gpu_tab)
            gpu_l.addWidget(self.chart_gpu)
            
            # GPU VRAM chart with fixed y-axis based on max total VRAM
            vram_info = self.gpu_provider.gpu_vram_info()
            max_vram = 1000.0  # Default fallback
            if vram_info:
                # Find the maximum total VRAM across all GPUs
                max_vram = max((total_mb for _, total_mb in vram_info if total_mb > 0), default=1000.0)
            self.chart_gpu_vram = TimeSeriesChart(
                "GPU VRAM Usage (MB)",
                [f"{name} VRAM" for name in gpu_names],
                max_points=400,
                y_range=(0, max_vram),
                auto_scale=False  # Fixed y-axis
            )
            gpu_l.addWidget(self.chart_gpu_vram)
            
            # GPU Temperature chart with fixed y-axis (0-100°C)
            gpu_temps = get_gpu_temperatures(self.gpu_provider)
            if gpu_temps and any(t > 0 for t in gpu_temps):
                self.chart_gpu_temp = TimeSeriesChart(
                    "GPU Temperature (°C)",
                    [f"{name} Temp" for name in gpu_names],
                    max_points=400,
                    y_range=(0, 100),
                    auto_scale=False  # Fixed y-axis at 100°C max
                )
                gpu_l.addWidget(self.chart_gpu_temp)
            else:
                self.chart_gpu_temp = None
            
            # GPU info labels
            self.lbl_gpu_info = QLabel("")
            self.lbl_gpu_info.setStyleSheet("QLabel { color: #b0b0b0; font-size: 9pt; padding: 8px; }")
            gpu_l.addWidget(self.lbl_gpu_info)
            tabs.addTab(gpu_tab, "GPU")
        else:
            gpu_tab = QWidget(); gpu_l = QVBoxLayout(gpu_tab);
            gpu_l.addWidget(QLabel("No NVIDIA GPU metrics available (pynvml/nvidia-smi not found)."))
            tabs.addTab(gpu_tab, "GPU")
            self.lbl_gpu_info = None
            self.chart_gpu_vram = None
            self.chart_gpu_temp = None

        # Wire unit selectors and init unit mode
        self.unit_combo_net.currentTextChanged.connect(self.on_unit_changed)
        self.unit_combo_disk.currentTextChanged.connect(self.on_unit_changed)
        self.unit_mode = "MiB/s"
        self._bytes_per_unit = 1024**2
        self.on_unit_changed(self.unit_mode)

        # Processes tab with hierarchical tree (Core → Process → Threads)
        procs_tab = QWidget()
        procs_l = QVBoxLayout(procs_tab)
        
        # Search box for filtering processes
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        self.proc_search = QLineEdit()
        self.proc_search.setPlaceholderText("Filter by process name or PID...")
        self.proc_search.textChanged.connect(self.on_proc_search_changed)
        search_row.addWidget(self.proc_search)
        procs_l.addLayout(search_row)
        
        # Process tree with hierarchical view (sorting disabled to allow manual expansion)
        self.proc_tree = QTreeWidget()
        self.proc_tree.setHeaderLabels(["Type/Name", "PID", "CPU %", "Mem %", "Threads", "Core"])
        self.proc_tree.setColumnCount(6)
        self.proc_tree.setSortingEnabled(False)  # Disable sorting to prevent auto-collapse on refresh
        hdr = self.proc_tree.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setSectionsClickable(True)  # Keep clickable for potential future use
        self.proc_tree.setAlternatingRowColors(True)
        
        # Connect itemExpanded for lazy thread loading
        self.proc_tree.itemExpanded.connect(self.on_proc_item_expanded)
        
        procs_l.addWidget(self.proc_tree)
        self.tabs.addTab(procs_tab, "Processes")
        
        # Process filter and refresh state
        self._proc_filter = ""
        self._proc_refresh_accum = 0.0
        self._procs_primed = False
        self._expanded_items = {}  # Track which items have been expanded

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
        # GPU refresh accumulator
        self._gpu_refresh_accum = 0.0

        self.refresh_info()

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(self.interval_ms)
        
        # Keyboard shortcuts
        self._setup_shortcuts()

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts for quick actions."""
        # Pause/Resume: P key
        pause_action = QAction("Pause/Resume", self)
        pause_action.setShortcut(QKeySequence("P"))
        pause_action.triggered.connect(self.toggle_pause)
        self.addAction(pause_action)
        
        # Quit: Esc key
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Esc"))
        quit_action.triggered.connect(self.close)
        self.addAction(quit_action)

    # ---------------------- Info builders ----------------------
    def refresh_info(self) -> None:
        lines = []
        # CPU
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
        """Handle update interval change from spinbox."""
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
            self._update_window_title()
    
    def toggle_pause(self) -> None:
        """Toggle pause/resume state for monitoring."""
        self._paused = not self._paused
        if self._paused:
            self.btn_pause.setText("▶ Resume")
            self.btn_pause.setToolTip("Resume monitoring (Shortcut: P)")
        else:
            self.btn_pause.setText("⏸ Pause")
            self.btn_pause.setToolTip("Pause monitoring (Shortcut: P)")
        self._update_window_title()
    
    def _update_window_title(self) -> None:
        """Update window title with current state."""
        state = " [PAUSED]" if self._paused else ""
        self.setWindowTitle(f"System Monitor ({self.interval_ms} ms){state}")
    
    def on_proc_search_changed(self, text: str) -> None:
        """Handle process search filter change."""
        self._proc_filter = text.strip().lower()
        # Force immediate refresh if not paused
        if not self._paused:
            self.refresh_processes()
    
    def on_proc_item_expanded(self, item: QTreeWidgetItem) -> None:
        """Lazy load thread details when a process item is expanded."""
        # Check if this item represents a process (has PID in column 1)
        pid_text = item.text(1)
        if not pid_text or not pid_text.isdigit():
            return
        
        # Check if already loaded
        item_id = id(item)
        if item_id in self._expanded_items:
            return
        
        self._expanded_items[item_id] = True
        
        # If item already has children, they were pre-loaded
        if item.childCount() > 0:
            return
        
        # Load thread details for this process
        try:
            pid = int(pid_text)
            proc = psutil.Process(pid)
            thread_ids = proc.threads()
            for i, thread_info in enumerate(thread_ids[:10]):  # Limit to 10 threads
                thread_item = QTreeWidgetItem(item)
                thread_item.setText(0, f"Thread {thread_info.id}")
                thread_item.setText(1, str(thread_info.id))
        except Exception:
            pass

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
                if self._proc_filter:
                    if self._proc_filter not in name.lower() and self._proc_filter not in str(pid):
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
            expanded_cores = set()
            expanded_processes = {}  # {core_id: set(pid)}
            
            for i in range(self.proc_tree.topLevelItemCount()):
                core_item = self.proc_tree.topLevelItem(i)
                if core_item and core_item.isExpanded():
                    # Extract core_id from text "CPU Core N"
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
            
            # Clear tree and rebuild
            self.proc_tree.clear()
            
            # Track if this is the first time building the tree
            first_build = not hasattr(self, "_proc_tree_built")
            if first_build:
                self._proc_tree_built = True
            
            # Add core nodes with their processes (including unpinned processes distributed to all cores)
            for core_id in range(n_cores):
                core_procs = core_processes[core_id]
                
                # Sort by CPU usage
                core_procs.sort(key=lambda x: x[0], reverse=True)
                
                # Create core node
                core_item = QTreeWidgetItem(self.proc_tree)
                core_item.setText(0, f"CPU Core {core_id}")
                core_item.setText(2, f"{sum(x[0] for x in core_procs[:10]):.1f}")
                
                # Determine if this core should be expanded
                # First build: expand all deeply by default
                # Subsequent builds: restore previous expansion state
                should_expand = first_build or (core_id in expanded_cores)
                core_item.setExpanded(should_expand)
                
                # Add top processes to this core (limit to 10 per core)
                for cpu, pid, name, mem, thr, proc_obj in core_procs[:10]:
                    proc_item = QTreeWidgetItem(core_item)
                    proc_item.setText(0, name)
                    proc_item.setText(1, str(pid))
                    proc_item.setText(2, f"{cpu:.1f}")
                    proc_item.setText(3, f"{mem:.1f}")
                    proc_item.setText(4, str(thr))
                    proc_item.setText(5, str(core_id))
                    
                    # Restore process expansion state if it was expanded before
                    if core_id in expanded_processes and pid in expanded_processes[core_id]:
                        proc_item.setExpanded(True)
                        # If process was expanded, load threads immediately
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
                        # Threads will be loaded lazily when user expands this item
                        if thr > 1:
                            proc_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
            
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
        # Skip updates if paused
        if self._paused:
            self._elapsed.restart()  # Keep timer in sync
            return
        
        # Use a monotonic Qt timer for consistent dt
        dt_ms = max(1, self._elapsed.restart())
        dt = dt_ms / 1000.0

        # CPU
        cpu = float(psutil.cpu_percent(interval=None))
        self.card_cpu.update_percent(cpu)
        # Update CPU frequency
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq and cpu_freq.current:
                self.card_cpu.set_frequency(cpu_freq.current)
        except Exception:
            pass
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
            
            # Update per-core frequency labels
            if hasattr(self, "core_freq_labels") and self.core_freq_labels:
                try:
                    core_freqs = get_per_core_frequencies()
                    if core_freqs:
                        for i, freq in enumerate(core_freqs[: len(self.core_freq_labels)]):
                            self.core_freq_labels[i].setText(f"{freq:.0f} MHz")
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

        # GPU (with configurable refresh rate)
        try:
            self._gpu_refresh_accum += dt
        except Exception:
            self._gpu_refresh_accum = 0.0
        
        gpu_refresh_interval = self.spin_gpu_refresh.value() / 1000.0  # Convert ms to seconds
        if self._gpu_refresh_accum >= gpu_refresh_interval:
            self._gpu_refresh_accum = 0.0
            
            utils = self.gpu_provider.gpu_utils()
            if utils:
                avg = sum(utils) / len(utils)
                self.card_gpu.update_percent(avg)
                # Update GPU frequency (first GPU if multiple)
                freqs = self.gpu_provider.gpu_frequencies()
                if freqs and freqs[0] > 0:
                    self.card_gpu.set_frequency(freqs[0])
                # Get VRAM info
                vram_info = self.gpu_provider.gpu_vram_info()
                
                # Update GPU charts if on GPU tab
                if self.chart_gpu is not None and self.tabs.currentIndex() == 5:
                    self.chart_gpu.append(utils)
                    
                    # Update VRAM chart
                    if hasattr(self, "chart_gpu_vram") and self.chart_gpu_vram is not None:
                        vram_values = [used_mb for used_mb, _ in vram_info] if vram_info else []
                        if vram_values:
                            self.chart_gpu_vram.append(vram_values)
                    
                    # Update temperature chart
                    if hasattr(self, "chart_gpu_temp") and self.chart_gpu_temp is not None:
                        try:
                            gpu_temps = get_gpu_temperatures(self.gpu_provider)
                            if gpu_temps and any(t > 0 for t in gpu_temps):
                                self.chart_gpu_temp.append(gpu_temps)
                        except Exception:
                            pass
                
                # Tooltip with per-GPU details including VRAM and temperature
                names = self.gpu_provider.gpu_names()
                tip_parts = []
                info_parts = []
                gpu_temps = get_gpu_temperatures(self.gpu_provider)
                
                for i, u in enumerate(utils):
                    name = names[i] if i < len(names) else f"GPU {i}"
                    detail = f"{name}: {u:.0f}%"
                    info_detail = f"GPU {i} ({name}): Utilization {u:.0f}%"
                    # Add VRAM info if available
                    if i < len(vram_info):
                        used_mb, total_mb = vram_info[i]
                        if total_mb > 0:
                            detail += f" | VRAM: {used_mb:.0f}/{total_mb:.0f} MB ({used_mb/total_mb*100:.1f}%)"
                            info_detail += f", VRAM: {used_mb:.0f}/{total_mb:.0f} MB ({used_mb/total_mb*100:.1f}%)"
                    # Add frequency if available
                    if i < len(freqs) and freqs[i] > 0:
                        detail += f" | {freqs[i]:.0f} MHz"
                        info_detail += f", Clock: {freqs[i]:.0f} MHz"
                    # Add temperature if available
                    if i < len(gpu_temps) and gpu_temps[i] > 0:
                        detail += f" | {gpu_temps[i]:.0f}°C"
                        info_detail += f", Temp: {gpu_temps[i]:.0f}°C"
                    tip_parts.append(detail)
                    info_parts.append(info_detail)
                self.card_gpu.set_tooltip("\n".join(tip_parts))
                # Update GPU tab info label
                if self.lbl_gpu_info is not None:
                    self.lbl_gpu_info.setText("\n".join(info_parts))
            else:
                self.card_gpu.set_unavailable("N/A")
                if self.lbl_gpu_info is not None:
                    self.lbl_gpu_info.setText("No GPU data available")

        # Periodically refresh process table and summaries (with configurable refresh rate)
        try:
            self._proc_refresh_accum += dt
        except Exception:
            self._proc_refresh_accum = 0.0
        
        proc_refresh_interval = self.spin_proc_refresh.value() / 1000.0  # Convert ms to seconds
        if self._proc_refresh_accum >= proc_refresh_interval:
            self._proc_refresh_accum = 0.0
            self.refresh_processes()


def main() -> None:
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    win = SystemMonitor(interval_ms=100)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()