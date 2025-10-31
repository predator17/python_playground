"""Real-time System Monitor application."""

#      Copyright (c) 2025 predator. All rights reserved.

from __future__ import annotations

import sys

try:
    import psutil
except ImportError:
    print("psutil is required. Install with: pip install psutil")
    raise

from PySide6.QtCore import QTimer, QElapsedTimer
from PySide6.QtGui import QKeySequence, QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QTreeWidgetItem

from system_monitor.providers import GPUProvider
from system_monitor.utils import apply_dark_theme
from system_monitor.core.metrics_updater import MetricsUpdater
from system_monitor.core.process_manager import ProcessManager
from system_monitor.core.info_manager import InfoManager
from system_monitor.ui import (
    ToolbarBuilder, DashboardBuilder, ChartFactory,
    CPUTabBuilder, BasicTabsBuilder, GPUTabBuilder, ProcessTabBuilder, EventHandlers
)


class SystemMonitor(QMainWindow):
    """Main application window for system monitoring."""

    def __init__(self, interval_ms: int = 100) -> None:
        super().__init__()
        self.interval_ms = interval_ms
        self.gpu_provider = GPUProvider()
        self._paused = False
        self.setWindowTitle(f"System Monitor ({self.interval_ms} ms)")
        self.resize(1200, 800)
        
        self._setup_ui()
        self._init_metrics_state()
        self._setup_timer()
        self._setup_shortcuts()
    
    def _setup_ui(self) -> None:
        """Build all UI components using builder pattern."""
        ToolbarBuilder.build_toolbar(self)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create charts
        self.chart_cpu = ChartFactory.create_cpu_chart()
        self.chart_mem = ChartFactory.create_memory_chart()
        self.chart_net = ChartFactory.create_network_chart()
        self.chart_disk = ChartFactory.create_disk_chart()
        gpu_names = self.gpu_provider.gpu_names()
        self.chart_gpu = ChartFactory.create_gpu_chart(gpu_names)
        
        # Create tabs
        self.dashboard = DashboardBuilder.build_dashboard(self)
        self.tabs.addTab(self.dashboard, "Dashboard")
        self.tabs.addTab(CPUTabBuilder.build_cpu_tab(self), "CPU")
        self.tabs.addTab(BasicTabsBuilder.build_memory_tab(self), "Memory")
        self.tabs.addTab(BasicTabsBuilder.build_network_tab(self), "Network")
        self.tabs.addTab(BasicTabsBuilder.build_disk_tab(self), "Disk")
        
        gpu_tab = GPUTabBuilder.build_gpu_tab(self, gpu_names) if self.chart_gpu else GPUTabBuilder._build_no_gpu_tab()
        if not self.chart_gpu:
            GPUTabBuilder.setup_no_gpu_fallback(self)
        self.tabs.addTab(gpu_tab, "GPU")
        self.tabs.addTab(ProcessTabBuilder.build_process_tab(self), "Processes")
        self.tabs.addTab(ProcessTabBuilder.build_info_tab(self), "System Info")
        
        self.refresh_info()
        self._wire_unit_selectors()
    
    def _wire_unit_selectors(self) -> None:
        """Connect unit selector signals."""
        self.unit_combo_net.currentTextChanged.connect(lambda m: EventHandlers.on_unit_changed(self, m))
        self.unit_combo_disk.currentTextChanged.connect(lambda m: EventHandlers.on_unit_changed(self, m))
        self.unit_mode = "MiB/s"
        self._bytes_per_unit = 1024**2
        EventHandlers.on_unit_changed(self, self.unit_mode)
    
    def _init_metrics_state(self) -> None:
        """Initialize metric collection state."""
        self._last_net = psutil.net_io_counters()
        self._last_disk = psutil.disk_io_counters()
        self._elapsed = QElapsedTimer()
        self._elapsed.start()
        psutil.cpu_percent(interval=None)
        self._net_dyn_up = 1.0
        self._net_dyn_down = 1.0
        self._disk_dyn_read = 1.0
        self._disk_dyn_write = 1.0
        self._gpu_refresh_accum = 0.0
    
    def _setup_timer(self) -> None:
        """Setup main update timer and keyboard shortcuts."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(self.interval_ms)
    
    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        for key, handler in [("P", lambda: EventHandlers.toggle_pause(self)), ("Esc", self.close)]:
            action = QAction(self)
            action.setShortcut(QKeySequence(key))
            action.triggered.connect(handler)
            self.addAction(action)
    
    def refresh_info(self) -> None:
        InfoManager.refresh_info(self)
    
    def refresh_processes(self) -> None:
        ProcessManager.refresh_processes(self)
    
    def on_interval_changed(self, val: int) -> None:
        EventHandlers.on_interval_changed(self, val)
    
    def on_proc_search_changed(self, text: str) -> None:
        EventHandlers.on_proc_search_changed(self, text)
    
    def on_proc_item_expanded(self, item: QTreeWidgetItem) -> None:
        EventHandlers.on_proc_item_expanded(self, item)
    
    def on_timer(self) -> None:
        """Main timer callback."""
        if self._paused:
            self._elapsed.restart()
            return
        dt_ms = max(1, self._elapsed.restart())
        dt = dt_ms / 1000.0
        MetricsUpdater.update_all_metrics(self, dt)
    
    def closeEvent(self, event) -> None:
        """Handle application close event - cleanup background threads."""
        ProcessManager.shutdown_collector()
        super().closeEvent(event)


def main() -> None:
    """Application entry point."""
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    win = SystemMonitor(interval_ms=100)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
