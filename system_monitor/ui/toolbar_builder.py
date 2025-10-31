"""Toolbar builder for SystemMonitor application."""

#      Copyright (c) 2025 predator. All rights reserved.

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QLabel, QSpinBox, QPushButton, QToolBar

if TYPE_CHECKING:
    from system_monitor.app import SystemMonitor

from system_monitor.ui.event_handlers import EventHandlers


class ToolbarBuilder:
    """Builds and configures the application toolbar."""

    @staticmethod
    def build_toolbar(monitor: 'SystemMonitor') -> QToolBar:
        """Create and configure the main toolbar with all controls."""
        toolbar = monitor.addToolBar("Controls")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        
        ToolbarBuilder._add_interval_controls(monitor, toolbar)
        toolbar.addSeparator()
        ToolbarBuilder._add_gpu_refresh_control(monitor, toolbar)
        ToolbarBuilder._add_process_refresh_control(monitor, toolbar)
        toolbar.addSeparator()
        ToolbarBuilder._add_pause_button(monitor, toolbar)
        
        return toolbar
    
    @staticmethod
    def _add_interval_controls(monitor: 'SystemMonitor', toolbar: QToolBar) -> None:
        """Add global update interval controls."""
        lbl = QLabel("Update interval (ms):")
        lbl.setStyleSheet("QLabel { color: #b0b0b0; }")
        
        monitor.spin_interval = QSpinBox()
        monitor.spin_interval.setRange(1, 5000)
        monitor.spin_interval.setValue(monitor.interval_ms)
        monitor.spin_interval.setSingleStep(1)
        monitor.spin_interval.setToolTip("Global data update interval in milliseconds")
        monitor.spin_interval.valueChanged.connect(monitor.on_interval_changed)
        
        toolbar.addWidget(lbl)
        toolbar.addWidget(monitor.spin_interval)
    
    @staticmethod
    def _add_gpu_refresh_control(monitor: 'SystemMonitor', toolbar: QToolBar) -> None:
        """Add GPU refresh interval control."""
        toolbar.addWidget(QLabel("GPU refresh (ms):"))
        monitor.spin_gpu_refresh = QSpinBox()
        monitor.spin_gpu_refresh.setRange(100, 5000)
        monitor.spin_gpu_refresh.setValue(100)
        monitor.spin_gpu_refresh.setToolTip("GPU metrics update interval in milliseconds")
        toolbar.addWidget(monitor.spin_gpu_refresh)
    
    @staticmethod
    def _add_process_refresh_control(monitor: 'SystemMonitor', toolbar: QToolBar) -> None:
        """Add process refresh interval control."""
        toolbar.addWidget(QLabel("Process refresh (ms):"))
        monitor.spin_proc_refresh = QSpinBox()
        monitor.spin_proc_refresh.setRange(100, 5000)
        monitor.spin_proc_refresh.setValue(100)
        monitor.spin_proc_refresh.setToolTip("Process table update interval in milliseconds")
        toolbar.addWidget(monitor.spin_proc_refresh)
    
    @staticmethod
    def _add_pause_button(monitor: 'SystemMonitor', toolbar: QToolBar) -> None:
        """Add pause/resume button."""
        monitor.btn_pause = QPushButton("⏸ Pause")
        monitor.btn_pause.setObjectName("PauseButton")
        monitor.btn_pause.setToolTip("Pause/Resume monitoring (Shortcut: P)")
        monitor.btn_pause.clicked.connect(lambda: EventHandlers.toggle_pause(monitor))
        toolbar.addWidget(monitor.btn_pause)
