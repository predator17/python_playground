"""Metrics updater for SystemMonitor - handles periodic metric updates."""

#      Copyright (c) 2025 predator. All rights reserved.

import math
from typing import TYPE_CHECKING

try:
    import psutil
except ImportError:
    psutil = None

from system_monitor.utils import get_per_core_frequencies, get_gpu_temperatures

if TYPE_CHECKING:
    from system_monitor.app import SystemMonitor


class MetricsUpdater:
    """Handles periodic updates of system metrics."""

    @staticmethod
    def update_all_metrics(monitor: 'SystemMonitor', dt: float) -> None:
        """
        Update all system metrics.
        
        Args:
            monitor: SystemMonitor instance with UI components
            dt: Time delta in seconds since last update
        """
        MetricsUpdater._update_cpu(monitor, dt)
        MetricsUpdater._update_memory(monitor)
        MetricsUpdater._update_network(monitor, dt)
        MetricsUpdater._update_disk(monitor, dt)
        MetricsUpdater._update_gpu(monitor, dt)
        MetricsUpdater._update_processes(monitor, dt)

    @staticmethod
    def _update_cpu(monitor: 'SystemMonitor', dt: float) -> None:
        """Update CPU metrics."""
        cpu = float(psutil.cpu_percent(interval=None))
        monitor.card_cpu.update_percent(cpu)
        
        # Update CPU frequency
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq and cpu_freq.current:
                monitor.card_cpu.set_frequency(cpu_freq.current)
        except Exception:
            pass
        
        # Update chart if on CPU tab
        if monitor.tabs.currentIndex() == 1:
            monitor.chart_cpu.append([cpu])
            
            # Per-core CPU update
            try:
                cores = psutil.cpu_percent(interval=None, percpu=True)
                if isinstance(cores, list) and cores and hasattr(monitor, "core_charts"):
                    for i, val in enumerate(cores[: len(monitor.core_charts)]):
                        monitor.core_charts[i].append([float(val)])
            except Exception:
                pass
            
            # Update per-core frequency labels
            if hasattr(monitor, "core_freq_labels") and monitor.core_freq_labels:
                try:
                    core_freqs = get_per_core_frequencies()
                    if core_freqs:
                        for i, freq in enumerate(core_freqs[: len(monitor.core_freq_labels)]):
                            monitor.core_freq_labels[i].setText(f"{freq:.0f} MHz")
                except Exception:
                    pass

    @staticmethod
    def _update_memory(monitor: 'SystemMonitor') -> None:
        """Update memory metrics."""
        mem = psutil.virtual_memory()
        mem_pct = float(mem.percent)
        monitor.card_mem.update_percent(mem_pct)
        
        if monitor.tabs.currentIndex() == 2:
            monitor.chart_mem.append([mem_pct])

    @staticmethod
    def _update_network(monitor: 'SystemMonitor', dt: float) -> None:
        """Update network metrics."""
        net = psutil.net_io_counters()
        up_mbs = max(0.0, (net.bytes_sent - monitor._last_net.bytes_sent) / dt) / monitor._bytes_per_unit
        down_mbs = max(0.0, (net.bytes_recv - monitor._last_net.bytes_recv) / dt) / monitor._bytes_per_unit
        monitor._last_net = net
        
        # Update dynamic reference maxes using time-constant decay
        tau = 10.0
        alpha = math.exp(-dt / tau)
        monitor._net_dyn_up = max(up_mbs, monitor._net_dyn_up * alpha)
        monitor._net_dyn_down = max(down_mbs, monitor._net_dyn_down * alpha)
        
        monitor.card_net_up.update_value(up_mbs, ref_max=monitor._net_dyn_up)
        monitor.card_net_down.update_value(down_mbs, ref_max=monitor._net_dyn_down)
        
        if monitor.tabs.currentIndex() == 3:
            monitor.chart_net.append([up_mbs, down_mbs])

    @staticmethod
    def _update_disk(monitor: 'SystemMonitor', dt: float) -> None:
        """Update disk I/O metrics."""
        try:
            dio = psutil.disk_io_counters()
        except Exception:
            dio = None
        
        if dio and getattr(monitor, "_last_disk", None):
            read_mbs = max(0.0, (dio.read_bytes - monitor._last_disk.read_bytes) / dt) / monitor._bytes_per_unit
            write_mbs = max(0.0, (dio.write_bytes - monitor._last_disk.write_bytes) / dt) / monitor._bytes_per_unit
        else:
            read_mbs = 0.0
            write_mbs = 0.0
        monitor._last_disk = dio
        
        # Update dynamic reference maxes
        tau = 10.0
        alpha = math.exp(-dt / tau)
        monitor._disk_dyn_read = max(read_mbs, monitor._disk_dyn_read * alpha)
        monitor._disk_dyn_write = max(write_mbs, monitor._disk_dyn_write * alpha)
        
        monitor.card_disk_read.update_value(read_mbs, ref_max=monitor._disk_dyn_read)
        monitor.card_disk_write.update_value(write_mbs, ref_max=monitor._disk_dyn_write)
        
        if monitor.tabs.currentIndex() == 4:
            monitor.chart_disk.append([read_mbs, write_mbs])

    @staticmethod
    def _update_gpu(monitor: 'SystemMonitor', dt: float) -> None:
        """Update GPU metrics with configurable refresh rate."""
        try:
            monitor._gpu_refresh_accum += dt
        except Exception:
            monitor._gpu_refresh_accum = 0.0
        
        gpu_refresh_interval = monitor.spin_gpu_refresh.value() / 1000.0
        if monitor._gpu_refresh_accum >= gpu_refresh_interval:
            monitor._gpu_refresh_accum = 0.0
            
            utils = monitor.gpu_provider.gpu_utils()
            if utils:
                avg = sum(utils) / len(utils)
                monitor.card_gpu.update_percent(avg)
                
                # Update GPU frequency
                freqs = monitor.gpu_provider.gpu_frequencies()
                if freqs and freqs[0] > 0:
                    monitor.card_gpu.set_frequency(freqs[0])
                
                # Get VRAM info
                vram_info = monitor.gpu_provider.gpu_vram_info()
                
                # Update GPU charts if on GPU tab
                if monitor.chart_gpu is not None and monitor.tabs.currentIndex() == 5:
                    monitor.chart_gpu.append(utils)
                    
                    # Update VRAM chart
                    if hasattr(monitor, "chart_gpu_vram") and monitor.chart_gpu_vram is not None:
                        vram_values = [used_mb for used_mb, _ in vram_info] if vram_info else []
                        if vram_values:
                            monitor.chart_gpu_vram.append(vram_values)
                    
                    # Update temperature chart
                    if hasattr(monitor, "chart_gpu_temp") and monitor.chart_gpu_temp is not None:
                        try:
                            gpu_temps = get_gpu_temperatures(monitor.gpu_provider)
                            if gpu_temps and any(t > 0 for t in gpu_temps):
                                monitor.chart_gpu_temp.append(gpu_temps)
                        except Exception:
                            pass
                
                # Update tooltips with per-GPU details
                MetricsUpdater._update_gpu_tooltips(monitor, utils, vram_info, freqs)
            else:
                monitor.card_gpu.set_unavailable("N/A")
                if monitor.lbl_gpu_info is not None:
                    monitor.lbl_gpu_info.setText("No GPU data available")

    @staticmethod
    def _update_gpu_tooltips(monitor: 'SystemMonitor', utils, vram_info, freqs) -> None:
        """Update GPU tooltips with detailed information."""
        names = monitor.gpu_provider.gpu_names()
        tip_parts = []
        info_parts = []
        gpu_temps = get_gpu_temperatures(monitor.gpu_provider)
        
        for i, u in enumerate(utils):
            name = names[i] if i < len(names) else f"GPU {i}"
            detail = f"{name}: {u:.0f}%"
            info_detail = f"GPU {i} ({name}): Utilization {u:.0f}%"
            
            # Add VRAM info
            if i < len(vram_info):
                used_mb, total_mb = vram_info[i]
                if total_mb > 0:
                    detail += f" | VRAM: {used_mb:.0f}/{total_mb:.0f} MB ({used_mb/total_mb*100:.1f}%)"
                    info_detail += f", VRAM: {used_mb:.0f}/{total_mb:.0f} MB ({used_mb/total_mb*100:.1f}%)"
            
            # Add frequency
            if i < len(freqs) and freqs[i] > 0:
                detail += f" | {freqs[i]:.0f} MHz"
                info_detail += f", Clock: {freqs[i]:.0f} MHz"
            
            # Add temperature
            if i < len(gpu_temps) and gpu_temps[i] > 0:
                detail += f" | {gpu_temps[i]:.0f}°C"
                info_detail += f", Temp: {gpu_temps[i]:.0f}°C"
            
            tip_parts.append(detail)
            info_parts.append(info_detail)
        
        monitor.card_gpu.set_tooltip("\n".join(tip_parts))
        if monitor.lbl_gpu_info is not None:
            monitor.lbl_gpu_info.setText("\n".join(info_parts))

    @staticmethod
    def _update_processes(monitor: 'SystemMonitor', dt: float) -> None:
        """Update process table with configurable refresh rate."""
        try:
            monitor._proc_refresh_accum += dt
        except Exception:
            monitor._proc_refresh_accum = 0.0
        
        proc_refresh_interval = monitor.spin_proc_refresh.value() / 1000.0
        if monitor._proc_refresh_accum >= proc_refresh_interval:
            monitor._proc_refresh_accum = 0.0
            monitor.refresh_processes()
