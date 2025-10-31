"""Basic tabs builder for Memory, Network, and Disk tabs."""

#      Copyright (c) 2025 predator. All rights reserved.

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox

from system_monitor.utils import get_memory_frequency

if TYPE_CHECKING:
    from system_monitor.app import SystemMonitor


class BasicTabsBuilder:
    """Builds Memory, Network, and Disk tabs."""

    @staticmethod
    def build_memory_tab(monitor: 'SystemMonitor') -> QWidget:
        """Create Memory tab with frequency display."""
        mem_tab = QWidget()
        mem_l = QVBoxLayout(mem_tab)
        mem_l.addWidget(monitor.chart_mem)
        
        mem_freq = get_memory_frequency()
        if mem_freq > 0:
            small_style = "QLabel { color: #b0b0b0; font-size: 9pt; }"
            monitor.lbl_mem_freq = QLabel(f"RAM Frequency: {mem_freq:.0f} MHz")
            monitor.lbl_mem_freq.setStyleSheet(small_style)
            mem_l.addWidget(monitor.lbl_mem_freq)
        else:
            monitor.lbl_mem_freq = None
        
        return mem_tab
    
    @staticmethod
    def build_network_tab(monitor: 'SystemMonitor') -> QWidget:
        """Create Network tab with unit selector."""
        net_tab = QWidget()
        net_l = QVBoxLayout(net_tab)
        
        unit_row = QHBoxLayout()
        unit_row.addWidget(QLabel("Units:"))
        monitor.unit_combo_net = QComboBox()
        monitor.unit_combo_net.addItems(["MB/s", "MiB/s"])
        monitor.unit_combo_net.setCurrentText("MiB/s")
        unit_row.addWidget(monitor.unit_combo_net)
        
        monitor.net_formula_lbl = QLabel("1 MiB/s ≈ 1.048576 MB/s | 1 MB/s ≈ 0.9537 MiB/s")
        monitor.net_formula_lbl.setStyleSheet("QLabel { color: #b0b0b0; font-size: 9pt; }")
        unit_row.addWidget(monitor.net_formula_lbl)
        
        net_l.addLayout(unit_row)
        net_l.addWidget(monitor.chart_net)
        
        return net_tab
    
    @staticmethod
    def build_disk_tab(monitor: 'SystemMonitor') -> QWidget:
        """Create Disk tab with unit selector."""
        disk_tab = QWidget()
        disk_l = QVBoxLayout(disk_tab)
        
        unit_row = QHBoxLayout()
        unit_row.addWidget(QLabel("Units:"))
        monitor.unit_combo_disk = QComboBox()
        monitor.unit_combo_disk.addItems(["MB/s", "MiB/s"])
        monitor.unit_combo_disk.setCurrentText("MiB/s")
        unit_row.addWidget(monitor.unit_combo_disk)
        
        monitor.disk_formula_lbl = QLabel("1 MiB/s ≈ 1.048576 MB/s | 1 MB/s ≈ 0.9537 MiB/s")
        monitor.disk_formula_lbl.setStyleSheet("QLabel { color: #b0b0b0; font-size: 9pt; }")
        unit_row.addWidget(monitor.disk_formula_lbl)
        
        disk_l.addLayout(unit_row)
        disk_l.addWidget(monitor.chart_disk)
        
        return disk_tab
