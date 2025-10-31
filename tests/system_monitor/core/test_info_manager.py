"""Unit tests for system_monitor.core.info_manager module."""

#      Copyright (c) 2025 predator. All rights reserved.

import unittest
from unittest.mock import MagicMock, patch
import sys

from system_monitor.core.info_manager import InfoManager


class TestInfoManagerRefreshInfo(unittest.TestCase):
    """Test InfoManager.refresh_info method."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MagicMock()
        self.monitor.info_edit = MagicMock()
        self.monitor.gpu_provider = MagicMock()

    @patch('system_monitor.core.info_manager.get_cpu_model_name')
    @patch('system_monitor.core.info_manager.platform')
    @patch('system_monitor.core.info_manager.psutil')
    def test_refresh_info_cpu_section(self, mock_psutil, mock_platform, mock_cpu_model):
        """Test CPU information section."""
        mock_cpu_model.return_value = "Intel Core i7-9700K"
        mock_platform.machine.return_value = "x86_64"
        mock_platform.architecture.return_value = ("64bit", "ELF")
        mock_psutil.cpu_count.side_effect = [8, 4]  # logical, physical
        mock_freq = MagicMock()
        mock_freq.current = 3600.0
        mock_freq.max = 4900.0
        mock_psutil.cpu_freq.return_value = mock_freq
        
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=16*1024**3, available=8*1024**3, used=8*1024**3, percent=50.0
        )
        mock_psutil.disk_partitions.return_value = []
        self.monitor.gpu_provider.gpu_names.return_value = []
        
        InfoManager.refresh_info(self.monitor)
        
        # Check that setPlainText was called
        self.monitor.info_edit.setPlainText.assert_called_once()
        text = self.monitor.info_edit.setPlainText.call_args[0][0]
        
        self.assertIn("CPU Information", text)
        self.assertIn("Intel Core i7-9700K", text)
        self.assertIn("x86_64", text)

    @patch('system_monitor.core.info_manager.get_cpu_model_name')
    @patch('system_monitor.core.info_manager.platform')
    @patch('system_monitor.core.info_manager.psutil')
    def test_refresh_info_system_section(self, mock_psutil, mock_platform, mock_cpu_model):
        """Test system information section."""
        mock_cpu_model.return_value = "CPU"
        mock_platform.machine.return_value = "x86_64"
        mock_platform.system.return_value = "Linux"
        mock_platform.node.return_value = "hostname"
        mock_platform.release.return_value = "5.15.0"
        mock_platform.version.return_value = "#1 SMP"
        mock_platform.platform.return_value = "Linux-5.15.0"
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_freq.return_value = None
        
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8*1024**3, available=4*1024**3, used=4*1024**3, percent=50.0
        )
        mock_psutil.disk_partitions.return_value = []
        self.monitor.gpu_provider.gpu_names.return_value = []
        
        InfoManager.refresh_info(self.monitor)
        
        text = self.monitor.info_edit.setPlainText.call_args[0][0]
        
        self.assertIn("System Information", text)
        self.assertIn("Linux", text)
        self.assertIn("hostname", text)

    @patch('system_monitor.core.info_manager.get_cpu_model_name')
    @patch('system_monitor.core.info_manager.platform')
    @patch('system_monitor.core.info_manager.psutil')
    def test_refresh_info_memory_section(self, mock_psutil, mock_platform, mock_cpu_model):
        """Test memory information section."""
        mock_cpu_model.return_value = "CPU"
        mock_platform.machine.return_value = "x86_64"
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_freq.return_value = None
        
        mock_mem = MagicMock()
        mock_mem.total = 16 * 1024**3
        mock_mem.available = 8 * 1024**3
        mock_mem.used = 8 * 1024**3
        mock_mem.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_mem
        mock_psutil.disk_partitions.return_value = []
        self.monitor.gpu_provider.gpu_names.return_value = []
        
        InfoManager.refresh_info(self.monitor)
        
        text = self.monitor.info_edit.setPlainText.call_args[0][0]
        
        self.assertIn("Memory Information", text)
        self.assertIn("16.00 GiB", text)
        self.assertIn("50.0%", text)

    @patch('system_monitor.core.info_manager.get_cpu_model_name')
    @patch('system_monitor.core.info_manager.platform')
    @patch('system_monitor.core.info_manager.psutil')
    def test_refresh_info_disk_section(self, mock_psutil, mock_platform, mock_cpu_model):
        """Test disk information section."""
        mock_cpu_model.return_value = "CPU"
        mock_platform.machine.return_value = "x86_64"
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_freq.return_value = None
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8*1024**3, available=4*1024**3, used=4*1024**3, percent=50.0
        )
        
        mock_partition = MagicMock()
        mock_partition.device = "/dev/sda1"
        mock_partition.mountpoint = "/"
        mock_psutil.disk_partitions.return_value = [mock_partition]
        
        mock_usage = MagicMock()
        mock_usage.total = 500 * 1024**3
        mock_usage.used = 250 * 1024**3
        mock_usage.percent = 50.0
        mock_psutil.disk_usage.return_value = mock_usage
        
        self.monitor.gpu_provider.gpu_names.return_value = []
        
        InfoManager.refresh_info(self.monitor)
        
        text = self.monitor.info_edit.setPlainText.call_args[0][0]
        
        self.assertIn("Disk Information", text)
        self.assertIn("/dev/sda1", text)
        self.assertIn("/", text)

    @patch('system_monitor.core.info_manager.get_cpu_model_name')
    @patch('system_monitor.core.info_manager.platform')
    @patch('system_monitor.core.info_manager.psutil')
    def test_refresh_info_gpu_section_with_gpus(self, mock_psutil, mock_platform, mock_cpu_model):
        """Test GPU information section with GPUs present."""
        mock_cpu_model.return_value = "CPU"
        mock_platform.machine.return_value = "x86_64"
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_freq.return_value = None
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8*1024**3, available=4*1024**3, used=4*1024**3, percent=50.0
        )
        mock_psutil.disk_partitions.return_value = []
        
        self.monitor.gpu_provider.gpu_names.return_value = [
            "NVIDIA GeForce RTX 3080",
            "NVIDIA GeForce RTX 3090"
        ]
        
        InfoManager.refresh_info(self.monitor)
        
        text = self.monitor.info_edit.setPlainText.call_args[0][0]
        
        self.assertIn("GPU Information", text)
        self.assertIn("GPU 0: NVIDIA GeForce RTX 3080", text)
        self.assertIn("GPU 1: NVIDIA GeForce RTX 3090", text)

    @patch('system_monitor.core.info_manager.get_cpu_model_name')
    @patch('system_monitor.core.info_manager.platform')
    @patch('system_monitor.core.info_manager.psutil')
    def test_refresh_info_gpu_section_without_gpus(self, mock_psutil, mock_platform, mock_cpu_model):
        """Test GPU information section without GPUs."""
        mock_cpu_model.return_value = "CPU"
        mock_platform.machine.return_value = "x86_64"
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_freq.return_value = None
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8*1024**3, available=4*1024**3, used=4*1024**3, percent=50.0
        )
        mock_psutil.disk_partitions.return_value = []
        
        self.monitor.gpu_provider.gpu_names.return_value = []
        
        InfoManager.refresh_info(self.monitor)
        
        text = self.monitor.info_edit.setPlainText.call_args[0][0]
        
        self.assertIn("GPU Information", text)
        self.assertIn("No NVIDIA GPUs detected", text)

    @patch('system_monitor.core.info_manager.get_cpu_model_name')
    @patch('system_monitor.core.info_manager.platform')
    @patch('system_monitor.core.info_manager.psutil')
    @patch('system_monitor.core.info_manager.sys')
    def test_refresh_info_python_section(self, mock_sys, mock_psutil, mock_platform, mock_cpu_model):
        """Test Python information section."""
        mock_cpu_model.return_value = "CPU"
        mock_platform.machine.return_value = "x86_64"
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_freq.return_value = None
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8*1024**3, available=4*1024**3, used=4*1024**3, percent=50.0
        )
        mock_psutil.disk_partitions.return_value = []
        self.monitor.gpu_provider.gpu_names.return_value = []
        
        mock_sys.version = "3.9.0 (default, Oct  1 2020, 00:00:00)"
        mock_sys.executable = "/usr/bin/python3"
        
        InfoManager.refresh_info(self.monitor)
        
        text = self.monitor.info_edit.setPlainText.call_args[0][0]
        
        self.assertIn("Python Information", text)
        self.assertIn("3.9.0", text)
        self.assertIn("/usr/bin/python3", text)

    @patch('system_monitor.core.info_manager.get_cpu_model_name')
    @patch('system_monitor.core.info_manager.platform')
    @patch('system_monitor.core.info_manager.psutil')
    def test_refresh_info_handles_exceptions(self, mock_psutil, mock_platform, mock_cpu_model):
        """Test refresh_info handles exceptions gracefully."""
        mock_cpu_model.return_value = "CPU"
        mock_platform.machine.return_value = "x86_64"
        mock_platform.architecture.side_effect = Exception("Test error")
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_freq.side_effect = Exception("Test error")
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8*1024**3, available=4*1024**3, used=4*1024**3, percent=50.0
        )
        mock_psutil.disk_partitions.return_value = []
        self.monitor.gpu_provider.gpu_names.return_value = []
        
        # Should not raise
        InfoManager.refresh_info(self.monitor)
        
        self.monitor.info_edit.setPlainText.assert_called_once()

    @patch('system_monitor.core.info_manager.get_cpu_model_name')
    @patch('system_monitor.core.info_manager.platform')
    @patch('system_monitor.core.info_manager.psutil')
    def test_refresh_info_disk_partition_exception(self, mock_psutil, mock_platform, mock_cpu_model):
        """Test refresh_info handles disk partition exceptions."""
        mock_cpu_model.return_value = "CPU"
        mock_platform.machine.return_value = "x86_64"
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_freq.return_value = None
        mock_psutil.virtual_memory.return_value = MagicMock(
            total=8*1024**3, available=4*1024**3, used=4*1024**3, percent=50.0
        )
        
        mock_partition = MagicMock()
        mock_partition.device = "/dev/sda1"
        mock_partition.mountpoint = "/"
        mock_psutil.disk_partitions.return_value = [mock_partition]
        mock_psutil.disk_usage.side_effect = Exception("Permission denied")
        
        self.monitor.gpu_provider.gpu_names.return_value = []
        
        # Should not raise
        InfoManager.refresh_info(self.monitor)
        
        self.monitor.info_edit.setPlainText.assert_called_once()


if __name__ == '__main__':
    unittest.main()
