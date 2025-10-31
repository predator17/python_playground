"""GPU data provider supporting NVML and nvidia-smi."""

#      Copyright (c) 2025 predator. All rights reserved.

from __future__ import annotations

import shutil
import subprocess
import threading
import time
from typing import List, Tuple


class GPUProvider:
    """Provides GPU names, utilization, VRAM, and frequency.
    Tries nvidia-ml-py first; falls back to calling nvidia-smi if available.
    """

    def __init__(self) -> None:
        self.method: str = "none"
        self._gpu_names: List[str] = []
        self._nvml = None
        self._nvml_handles = []
        self._last_smi_time: float = 0.0
        self._last_smi_utils: List[float] = []
        self._last_smi_vram: List[Tuple[float, float]] = []  # (used_mb, total_mb) per GPU
        self._last_smi_freq: List[float] = []  # current freq in MHz per GPU
        self._smi_min_interval = 1.0  # seconds; avoid hammering nvidia-smi; polled in background thread

        # Try NVML (pynvml)
        try:
            import pynvml as nvml  # type: ignore
            nvml.nvmlInit()
            count = nvml.nvmlDeviceGetCount()
            self._nvml = nvml
            for i in range(count):
                h = nvml.nvmlDeviceGetHandleByIndex(i)
                self._nvml_handles.append(h)
                name = nvml.nvmlDeviceGetName(h)
                if isinstance(name, bytes):
                    name = name.decode("utf-8", errors="ignore")
                self._gpu_names.append(str(name))
            if self._gpu_names:
                self.method = "nvml"
        except Exception:
            self._nvml = None
            self._nvml_handles = []

        # Fallback to nvidia-smi
        if self.method == "none" and shutil.which("nvidia-smi"):
            try:
                names = self._query_nvidia_smi_names()
                if names:
                    self._gpu_names = names
                    self._last_smi_utils = [0.0 for _ in names]
                    self._last_smi_vram = [(0.0, 0.0) for _ in names]
                    self._last_smi_freq = [0.0 for _ in names]
                    self.method = "nvidia-smi"
                    # Start background polling thread to avoid UI blocking
                    self._smi_stop = False
                    self._smi_thread = threading.Thread(target=self._smi_poll_loop, daemon=True)
                    self._smi_thread.start()
            except Exception:
                pass

    def _query_nvidia_smi_names(self) -> List[str]:
        cmd = [
            "nvidia-smi",
            "--query-gpu=name",
            "--format=csv,noheader",
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
        names = [line.strip() for line in out.stdout.strip().splitlines() if line.strip()]
        return names

    def _query_nvidia_smi_utils(self) -> List[float]:
        cmd = [
            "nvidia-smi",
            "--query-gpu=utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
        utils: List[float] = []
        for line in out.stdout.strip().splitlines():
            try:
                utils.append(float(line.strip()))
            except Exception:
                utils.append(0.0)
        return utils

    def _query_nvidia_smi_vram(self) -> List[Tuple[float, float]]:
        """Query VRAM usage (used, total) in MB via nvidia-smi."""
        cmd = [
            "nvidia-smi",
            "--query-gpu=memory.used,memory.total",
            "--format=csv,noheader,nounits",
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
        vram: List[Tuple[float, float]] = []
        for line in out.stdout.strip().splitlines():
            try:
                parts = line.strip().split(",")
                used = float(parts[0].strip())
                total = float(parts[1].strip())
                vram.append((used, total))
            except Exception:
                vram.append((0.0, 0.0))
        return vram

    def _query_nvidia_smi_freq(self) -> List[float]:
        """Query GPU clock frequency in MHz via nvidia-smi."""
        cmd = [
            "nvidia-smi",
            "--query-gpu=clocks.current.graphics",
            "--format=csv,noheader,nounits",
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
        freqs: List[float] = []
        for line in out.stdout.strip().splitlines():
            try:
                freqs.append(float(line.strip()))
            except Exception:
                freqs.append(0.0)
        return freqs

    def gpu_names(self) -> List[str]:
        return list(self._gpu_names)

    def gpu_utils(self) -> List[float]:
        if self.method == "nvml" and self._nvml is not None:
            vals: List[float] = []
            for h in self._nvml_handles:
                try:
                    util = self._nvml.nvmlDeviceGetUtilizationRates(h)
                    vals.append(float(util.gpu))
                except Exception:
                    vals.append(0.0)
            return vals
        elif self.method == "nvidia-smi":
            # Values are refreshed by a background thread to avoid blocking the UI
            return list(self._last_smi_utils)
        else:
            return []

    def gpu_vram_info(self) -> List[Tuple[float, float]]:
        """Returns list of (used_mb, total_mb) tuples for each GPU."""
        if self.method == "nvml" and self._nvml is not None:
            vram_list: List[Tuple[float, float]] = []
            for h in self._nvml_handles:
                try:
                    mem_info = self._nvml.nvmlDeviceGetMemoryInfo(h)
                    used_mb = mem_info.used / (1024 * 1024)
                    total_mb = mem_info.total / (1024 * 1024)
                    vram_list.append((used_mb, total_mb))
                except Exception:
                    vram_list.append((0.0, 0.0))
            return vram_list
        elif self.method == "nvidia-smi":
            return list(self._last_smi_vram)
        else:
            return []

    def gpu_frequencies(self) -> List[float]:
        """Returns list of current GPU clock frequencies in MHz."""
        if self.method == "nvml" and self._nvml is not None:
            freqs: List[float] = []
            for h in self._nvml_handles:
                try:
                    freq_mhz = self._nvml.nvmlDeviceGetClockInfo(h, self._nvml.NVML_CLOCK_GRAPHICS)
                    freqs.append(float(freq_mhz))
                except Exception:
                    freqs.append(0.0)
            return freqs
        elif self.method == "nvidia-smi":
            return list(self._last_smi_freq)
        else:
            return []

    def _smi_poll_loop(self) -> None:
        # Background polling loop for nvidia-smi to avoid blocking the UI thread
        while True:
            try:
                utils = self._query_nvidia_smi_utils()
                if utils:
                    self._last_smi_utils = utils
                vram = self._query_nvidia_smi_vram()
                if vram:
                    self._last_smi_vram = vram
                freq = self._query_nvidia_smi_freq()
                if freq:
                    self._last_smi_freq = freq
            except Exception:
                # swallow exceptions; next iteration will retry
                pass
            time.sleep(self._smi_min_interval)
