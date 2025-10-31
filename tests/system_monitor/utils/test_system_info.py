"""Unit tests for system_monitor.utils.system_info module."""

#      Copyright (c) 2025 predator. All rights reserved.

import unittest
from unittest.mock import patch, MagicMock, mock_open
import subprocess

from system_monitor.utils.system_info import (
    get_cpu_model_name,
    get_per_core_frequencies,
    get_memory_frequency,
    get_cpu_temperatures,
    get_gpu_temperatures,
)


class TestGetCpuModelName(unittest.TestCase):
    """Test get_cpu_model_name function."""

    @patch('system_monitor.utils.system_info.platform.system')
    @patch('builtins.open', new_callable=mock_open, read_data='model name\t: Intel Core i7-9700K\n')
    def test_linux_cpu_model(self, mock_file, mock_system):
        """Test getting CPU model on Linux."""
        mock_system.return_value = 'Linux'
        result = get_cpu_model_name()
        self.assertEqual(result, 'Intel Core i7-9700K')

    @patch('system_monitor.utils.system_info.platform.system')
    @patch('system_monitor.utils.system_info.subprocess.run')
    def test_darwin_cpu_model(self, mock_run, mock_system):
        """Test getting CPU model on macOS."""
        mock_system.return_value = 'Darwin'
        mock_run.return_value = MagicMock(returncode=0, stdout='Apple M1 Pro\n')
        result = get_cpu_model_name()
        self.assertEqual(result, 'Apple M1 Pro')

    @patch('system_monitor.utils.system_info.platform.system')
    @patch('system_monitor.utils.system_info.subprocess.run')
    def test_windows_cpu_model(self, mock_run, mock_system):
        """Test getting CPU model on Windows."""
        mock_system.return_value = 'Windows'
        mock_run.return_value = MagicMock(returncode=0, stdout='Name\nAMD Ryzen 9 5900X\n')
        result = get_cpu_model_name()
        self.assertEqual(result, 'AMD Ryzen 9 5900X')

    @patch('system_monitor.utils.system_info.platform.system')
    @patch('system_monitor.utils.system_info.platform.machine')
    def test_fallback_cpu_model(self, mock_machine, mock_system):
        """Test fallback when platform-specific methods fail."""
        mock_system.return_value = 'Unknown'
        mock_machine.return_value = 'x86_64'
        result = get_cpu_model_name()
        self.assertEqual(result, 'x86_64 CPU')

    @patch('system_monitor.utils.system_info.platform.system')
    def test_exception_handling(self, mock_system):
        """Test exception handling returns Unknown CPU."""
        mock_system.side_effect = Exception('Test error')
        result = get_cpu_model_name()
        self.assertEqual(result, 'Unknown CPU')


class TestGetPerCoreFrequencies(unittest.TestCase):
    """Test get_per_core_frequencies function."""

    @patch('system_monitor.utils.system_info.psutil.cpu_freq')
    def test_per_core_frequencies_available(self, mock_cpu_freq):
        """Test getting per-core frequencies when available."""
        mock_freq = MagicMock()
        mock_freq.current = 3600.0
        mock_cpu_freq.return_value = [mock_freq, mock_freq]
        result = get_per_core_frequencies()
        self.assertEqual(result, [3600.0, 3600.0])

    @patch('system_monitor.utils.system_info.psutil.cpu_freq')
    def test_per_core_frequencies_not_available(self, mock_cpu_freq):
        """Test when per-core frequencies are not available."""
        mock_cpu_freq.return_value = None
        result = get_per_core_frequencies()
        self.assertEqual(result, [])

    @patch('system_monitor.utils.system_info.psutil')
    def test_no_cpu_freq_attribute(self, mock_psutil):
        """Test when psutil doesn't have cpu_freq attribute."""
        del mock_psutil.cpu_freq
        result = get_per_core_frequencies()
        self.assertEqual(result, [])

    @patch('system_monitor.utils.system_info.psutil.cpu_freq')
    def test_exception_handling(self, mock_cpu_freq):
        """Test exception handling returns empty list."""
        mock_cpu_freq.side_effect = Exception('Test error')
        result = get_per_core_frequencies()
        self.assertEqual(result, [])


class TestGetMemoryFrequency(unittest.TestCase):
    """Test get_memory_frequency function."""

    @patch('system_monitor.utils.system_info.platform.system')
    @patch('system_monitor.utils.system_info.subprocess.run')
    def test_linux_memory_frequency(self, mock_run, mock_system):
        """Test getting memory frequency on Linux."""
        mock_system.return_value = 'Linux'
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='Speed: 3200 MHz\n'
        )
        result = get_memory_frequency()
        self.assertEqual(result, 3200.0)

    @patch('system_monitor.utils.system_info.platform.system')
    @patch('system_monitor.utils.system_info.subprocess.run')
    def test_windows_memory_frequency(self, mock_run, mock_system):
        """Test getting memory frequency on Windows."""
        mock_system.return_value = 'Windows'
        mock_run.return_value = MagicMock(returncode=0, stdout='Speed\n2666\n')
        result = get_memory_frequency()
        self.assertEqual(result, 2666.0)

    @patch('system_monitor.utils.system_info.platform.system')
    def test_unsupported_platform(self, mock_system):
        """Test unsupported platform returns 0."""
        mock_system.return_value = 'Unknown'
        result = get_memory_frequency()
        self.assertEqual(result, 0.0)

    @patch('system_monitor.utils.system_info.platform.system')
    @patch('system_monitor.utils.system_info.subprocess.run')
    def test_exception_handling(self, mock_run, mock_system):
        """Test exception handling returns 0."""
        mock_system.return_value = 'Linux'
        mock_run.side_effect = subprocess.TimeoutExpired('dmidecode', 2.0)
        result = get_memory_frequency()
        self.assertEqual(result, 0.0)


class TestGetCpuTemperatures(unittest.TestCase):
    """Test get_cpu_temperatures function."""

    @patch('system_monitor.utils.system_info.psutil.sensors_temperatures')
    def test_cpu_temperatures_coretemp(self, mock_sensors):
        """Test getting CPU temperatures with coretemp sensor."""
        mock_entry = MagicMock()
        mock_entry.label = 'Core 0'
        mock_entry.current = 45.0
        mock_sensors.return_value = {'coretemp': [mock_entry]}
        result = get_cpu_temperatures()
        self.assertEqual(result, [('Core 0', 45.0)])

    @patch('system_monitor.utils.system_info.psutil.sensors_temperatures')
    def test_cpu_temperatures_k10temp(self, mock_sensors):
        """Test getting CPU temperatures with k10temp sensor (AMD)."""
        mock_entry = MagicMock()
        mock_entry.label = 'Tctl'
        mock_entry.current = 55.0
        mock_sensors.return_value = {'k10temp': [mock_entry]}
        result = get_cpu_temperatures()
        self.assertEqual(result, [('Tctl', 55.0)])

    @patch('system_monitor.utils.system_info.psutil.sensors_temperatures')
    def test_no_temperatures_available(self, mock_sensors):
        """Test when no temperature sensors are available."""
        mock_sensors.return_value = None
        result = get_cpu_temperatures()
        self.assertEqual(result, [])

    @patch('system_monitor.utils.system_info.psutil')
    def test_no_sensors_temperatures_attribute(self, mock_psutil):
        """Test when psutil doesn't have sensors_temperatures."""
        if hasattr(mock_psutil, 'sensors_temperatures'):
            del mock_psutil.sensors_temperatures
        result = get_cpu_temperatures()
        self.assertEqual(result, [])

    @patch('system_monitor.utils.system_info.psutil.sensors_temperatures')
    def test_exception_handling(self, mock_sensors):
        """Test exception handling returns empty list."""
        mock_sensors.side_effect = Exception('Test error')
        result = get_cpu_temperatures()
        self.assertEqual(result, [])


class TestGetGpuTemperatures(unittest.TestCase):
    """Test get_gpu_temperatures function."""

    def test_nvml_gpu_temperatures(self):
        """Test getting GPU temperatures via NVML."""
        mock_gpu_provider = MagicMock()
        mock_gpu_provider.method = 'nvml'
        mock_gpu_provider._nvml = MagicMock()
        mock_gpu_provider._nvml_handles = ['handle1']
        mock_gpu_provider._nvml.nvmlDeviceGetTemperature.return_value = 65
        mock_gpu_provider._nvml.NVML_TEMPERATURE_GPU = 0
        
        result = get_gpu_temperatures(mock_gpu_provider)
        self.assertEqual(result, [65.0])

    @patch('system_monitor.utils.system_info.subprocess.run')
    def test_nvidia_smi_gpu_temperatures(self, mock_run):
        """Test getting GPU temperatures via nvidia-smi."""
        mock_gpu_provider = MagicMock()
        mock_gpu_provider.method = 'nvidia-smi'
        mock_run.return_value = MagicMock(stdout='72\n')
        
        result = get_gpu_temperatures(mock_gpu_provider)
        self.assertEqual(result, [72.0])

    def test_no_gpu_method(self):
        """Test when no GPU method is available."""
        mock_gpu_provider = MagicMock()
        mock_gpu_provider.method = 'none'
        
        result = get_gpu_temperatures(mock_gpu_provider)
        self.assertEqual(result, [])

    def test_exception_handling(self):
        """Test exception handling returns empty list."""
        mock_gpu_provider = MagicMock()
        mock_gpu_provider.method = 'nvml'
        mock_gpu_provider._nvml = None
        
        result = get_gpu_temperatures(mock_gpu_provider)
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
