"""
Real-time System Monitor (PySide6)

A comprehensive system monitoring application built with PySide6.

Dependencies:
- PySide6 (Qt 6)
- psutil
- Optional: nvidia-ml-py (for NVIDIA GPU metrics) or system nvidia-smi

Install:
  pip install PySide6 psutil nvidia-ml-py

Run:
  python -m system_monitor

Notes:
- Updates every 100 ms by default (configurable via toolbar).
- Uses QtCharts for efficient, built-in plotting (no extra plotting libs required).
- Keyboard shortcuts: P=Pause, R=Resume, Esc=Quit
"""

#      Copyright (c) 2025 predator. All rights reserved.

__version__ = "1.0.0"
