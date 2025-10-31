"""
Real-time System Monitor (PySide6)

Dependencies:
- PySide6 (Qt 6)
- psutil
- Optional: nvidia-ml-py (for NVIDIA GPU metrics) or system nvidia-smi

Install:
  pip install PySide6 psutil nvidia-ml-py

Run:
  python app.py

Notes:
- Updates every 100 ms by default (configurable via toolbar).
- Uses QtCharts for efficient, built-in plotting (no extra plotting libs required).
- Keyboard shortcuts: P=Pause, R=Resume, Esc=Quit
"""
from __future__ import annotations

import sys
import platform
import asyncio
import math
from typing import List, Optional, Tuple

try:
    import psutil  # type: ignore
except Exception as e:
    print("psutil is required. Install with: pip install psutil")
    raise

from PySide6.QtCore import Qt, QTimer, QMargins, QElapsedTimer, Signal, QObject
from PySide6.QtGui import QColor, QKeySequence, QAction
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
from PySide6.QtCharts import QLineSeries

from providers import GPUProvider
from utils import (
    get_cpu_model_name,
    get_per_core_frequencies,
    get_memory_frequency,
    get_cpu_temperatures,
    get_gpu_temperatures,
    apply_dark_theme,
)
from widgets import TimeSeriesChart, MetricCard
from core.metrics_updater import MetricsUpdater
from core.process_manager import ProcessManager
from core.info_manager import InfoManager


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
        """Gather and display system information."""
        InfoManager.refresh_info(self)

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
        ProcessManager.on_proc_item_expanded(self, item)

    def refresh_processes(self) -> None:
        """Refresh the process tree with core affinity grouping."""
        ProcessManager.refresh_processes(self)

    # ----------------------- Timer update ----------------------
    def on_timer(self) -> None:
        """Main timer callback - updates all metrics."""
        if self._paused:
            self._elapsed.restart()
            return
        
        dt_ms = max(1, self._elapsed.restart())
        dt = dt_ms / 1000.0
        
        MetricsUpdater.update_all_metrics(self, dt)


def main() -> None:
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    win = SystemMonitor(interval_ms=100)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()