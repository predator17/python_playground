"""Utility functions for system information retrieval."""

#      Copyright (c) 2025 predator. All rights reserved.

from .system_info import (
    get_cpu_model_name,
    get_per_core_frequencies,
    get_memory_frequency,
    get_cpu_temperatures,
    get_gpu_temperatures,
)
from .theme import apply_dark_theme
from .cache import SystemInfoCache, cached_static_property

__all__ = [
    "get_cpu_model_name",
    "get_per_core_frequencies",
    "get_memory_frequency",
    "get_cpu_temperatures",
    "get_gpu_temperatures",
    "apply_dark_theme",
    "SystemInfoCache",
    "cached_static_property",
]
