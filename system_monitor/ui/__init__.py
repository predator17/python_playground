"""UI builders and factories for SystemMonitor application."""

#      Copyright (c) 2025 predator. All rights reserved.

from .toolbar_builder import ToolbarBuilder
from .dashboard_builder import DashboardBuilder
from .cpu_tab_builder import CPUTabBuilder
from .basic_tabs_builder import BasicTabsBuilder
from .gpu_tab_builder import GPUTabBuilder
from .process_tab_builder import ProcessTabBuilder
from .chart_factory import ChartFactory
from .event_handlers import EventHandlers

__all__ = [
    "ToolbarBuilder",
    "DashboardBuilder",
    "CPUTabBuilder",
    "BasicTabsBuilder",
    "GPUTabBuilder",
    "ProcessTabBuilder",
    "ChartFactory",
    "EventHandlers",
]
