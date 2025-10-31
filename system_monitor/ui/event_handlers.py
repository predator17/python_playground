"""Event handlers for SystemMonitor application."""

#      Copyright (c) 2025 predator. All rights reserved.

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QTreeWidgetItem

from system_monitor.core.process_manager import ProcessManager

if TYPE_CHECKING:
    from system_monitor.app import SystemMonitor


class EventHandlers:
    """Centralized event handlers for SystemMonitor."""

    @staticmethod
    def on_unit_changed(monitor: 'SystemMonitor', mode: str) -> None:
        """Handle unit selector change."""
        mapping = {"MB/s": 1_000_000, "MiB/s": 1024**2}
        if mode not in mapping:
            return
        monitor.unit_mode = mode
        monitor._bytes_per_unit = mapping[mode]
        
        if hasattr(monitor, "unit_combo_net") and monitor.unit_combo_net.currentText() != mode:
            monitor.unit_combo_net.blockSignals(True)
            monitor.unit_combo_net.setCurrentText(mode)
            monitor.unit_combo_net.blockSignals(False)
        if hasattr(monitor, "unit_combo_disk") and monitor.unit_combo_disk.currentText() != mode:
            monitor.unit_combo_disk.blockSignals(True)
            monitor.unit_combo_disk.setCurrentText(mode)
            monitor.unit_combo_disk.blockSignals(False)
        
        monitor.card_net_up.unit = mode
        monitor.card_net_down.unit = mode
        monitor.card_disk_read.unit = mode
        monitor.card_disk_write.unit = mode
        monitor.chart_net.chart.setTitle(f"Network Throughput ({mode})")
        monitor.chart_disk.chart.setTitle(f"Disk Throughput ({mode})")
        monitor._net_dyn_up = 1.0
        monitor._net_dyn_down = 1.0
        monitor._disk_dyn_read = 1.0
        monitor._disk_dyn_write = 1.0
    
    @staticmethod
    def on_interval_changed(monitor: 'SystemMonitor', val: int) -> None:
        """Handle update interval change."""
        ms = max(1, int(val))
        if ms != monitor.interval_ms:
            monitor.interval_ms = ms
            monitor.timer.setInterval(monitor.interval_ms)
            EventHandlers._update_window_title(monitor)
    
    @staticmethod
    def toggle_pause(monitor: 'SystemMonitor') -> None:
        """Toggle pause/resume state."""
        monitor._paused = not monitor._paused
        if monitor._paused:
            monitor.btn_pause.setText("▶ Resume")
            monitor.btn_pause.setToolTip("Resume monitoring (Shortcut: P)")
        else:
            monitor.btn_pause.setText("⏸ Pause")
            monitor.btn_pause.setToolTip("Pause monitoring (Shortcut: P)")
        EventHandlers._update_window_title(monitor)
    
    @staticmethod
    def _update_window_title(monitor: 'SystemMonitor') -> None:
        """Update window title with current state."""
        state = " [PAUSED]" if monitor._paused else ""
        monitor.setWindowTitle(f"System Monitor ({monitor.interval_ms} ms){state}")
    
    @staticmethod
    def on_proc_search_changed(monitor: 'SystemMonitor', text: str) -> None:
        """Handle process search filter change."""
        monitor._proc_filter = text.strip().lower()
        if not monitor._paused:
            ProcessManager.refresh_processes(monitor)
    
    @staticmethod
    def on_proc_item_expanded(monitor: 'SystemMonitor', item: QTreeWidgetItem) -> None:
        """Lazy load thread details when process item expanded."""
        ProcessManager.on_proc_item_expanded(monitor, item)
