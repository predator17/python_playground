"""System information utility functions."""

#      Copyright (c) 2025 predator. All rights reserved.

from __future__ import annotations

import platform
import subprocess
from typing import List, Tuple

try:
    import psutil  # type: ignore
except Exception as e:
    print("psutil is required. Install with: pip install psutil")
    raise

from .cache import cached_static_property


@cached_static_property('cpu_model_name')
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
                    if len(lines) > 1 and lines[2].strip():
                        return lines[2].strip()
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


@cached_static_property('memory_frequency')
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
