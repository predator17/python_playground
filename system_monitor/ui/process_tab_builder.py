"""Process tab builder for SystemMonitor application."""

#      Copyright (c) 2025 predator. All rights reserved.

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTreeWidget, QHeaderView, QTextEdit
)

if TYPE_CHECKING:
    from system_monitor.app import SystemMonitor


class ProcessTabBuilder:
    """Builds the Processes and Info tabs."""

    @staticmethod
    def build_process_tab(monitor: 'SystemMonitor') -> QWidget:
        """Create Processes tab with hierarchical tree and search."""
        procs_tab = QWidget()
        procs_l = QVBoxLayout(procs_tab)
        
        ProcessTabBuilder._add_search_box(monitor, procs_l)
        ProcessTabBuilder._add_process_tree(monitor, procs_l)
        ProcessTabBuilder._init_process_state(monitor)
        
        return procs_tab
    
    @staticmethod
    def _add_search_box(monitor: 'SystemMonitor', layout: QVBoxLayout) -> None:
        """Add search box for filtering processes."""
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        
        monitor.proc_search = QLineEdit()
        monitor.proc_search.setPlaceholderText("Filter by process name or PID...")
        monitor.proc_search.textChanged.connect(monitor.on_proc_search_changed)
        search_row.addWidget(monitor.proc_search)
        
        layout.addLayout(search_row)
    
    @staticmethod
    def _add_process_tree(monitor: 'SystemMonitor', layout: QVBoxLayout) -> None:
        """Add hierarchical process tree widget."""
        monitor.proc_tree = QTreeWidget()
        monitor.proc_tree.setHeaderLabels(["Type/Name", "PID", "CPU %", "Mem %", "Threads", "Core"])
        monitor.proc_tree.setColumnCount(6)
        monitor.proc_tree.setSortingEnabled(False)
        
        hdr = monitor.proc_tree.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setSectionsClickable(True)
        monitor.proc_tree.setAlternatingRowColors(True)
        monitor.proc_tree.itemExpanded.connect(monitor.on_proc_item_expanded)
        
        layout.addWidget(monitor.proc_tree)
    
    @staticmethod
    def _init_process_state(monitor: 'SystemMonitor') -> None:
        """Initialize process filtering and refresh state."""
        monitor._proc_filter = ""
        monitor._proc_refresh_accum = 0.0
        monitor._procs_primed = False
        monitor._expanded_items = {}
    
    @staticmethod
    def build_info_tab(monitor: 'SystemMonitor') -> QWidget:
        """Create System Info tab."""
        monitor.info_edit = QTextEdit()
        monitor.info_edit.setReadOnly(True)
        
        info_tab = QWidget()
        info_l = QVBoxLayout(info_tab)
        info_l.addWidget(monitor.info_edit)
        
        return info_tab
