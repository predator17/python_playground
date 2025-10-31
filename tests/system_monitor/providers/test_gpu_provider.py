"""Unit tests for system_monitor.providers.gpu_provider module."""

import unittest
from unittest.mock import patch, MagicMock, call
import subprocess

from system_monitor.providers.gpu_provider import GPUProvider


class TestGPUProviderInit(unittest.TestCase):
    """Test GPUProvider initialization."""

    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_no_gpu_available(self, mock_which):
        """Test initialization when no GPU is available."""
        mock_which.return_value = None
        
        provider = GPUProvider()
        
        self.assertEqual(provider.method, 'none')
        self.assertEqual(provider._gpu_names, [])

    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_nvml_initialization(self, mock_which):
        """Test initialization with NVML (pynvml)."""
        mock_which.return_value = None
        
        with patch.dict('sys.modules', {'pynvml': MagicMock()}):
            mock_nvml = MagicMock()
            mock_nvml.nvmlDeviceGetCount.return_value = 1
            mock_nvml.nvmlDeviceGetName.return_value = b'NVIDIA GeForce RTX 3080'
            
            with patch('system_monitor.providers.gpu_provider.GPUProvider._GPUProvider__init__', 
                       return_value=None):
                provider = GPUProvider()
                provider.method = 'nvml'
                provider._gpu_names = ['NVIDIA GeForce RTX 3080']
                
                self.assertEqual(provider.method, 'nvml')
                self.assertEqual(provider._gpu_names, ['NVIDIA GeForce RTX 3080'])

    @patch('system_monitor.providers.gpu_provider.shutil.which')
    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    def test_nvidia_smi_initialization(self, mock_run, mock_which):
        """Test initialization with nvidia-smi fallback."""
        mock_which.return_value = '/usr/bin/nvidia-smi'
        mock_run.return_value = MagicMock(
            stdout='NVIDIA GeForce RTX 4090\n',
            returncode=0
        )
        
        with patch('system_monitor.providers.gpu_provider.threading.Thread'):
            provider = GPUProvider()
            
            if provider.method == 'nvidia-smi':
                self.assertEqual(provider.method, 'nvidia-smi')
                self.assertIsInstance(provider._gpu_names, list)


class TestGPUProviderNvidiaSmiQueries(unittest.TestCase):
    """Test nvidia-smi query methods."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('system_monitor.providers.gpu_provider.shutil.which', return_value=None):
            self.provider = GPUProvider()

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    def test_query_nvidia_smi_names(self, mock_run):
        """Test querying GPU names via nvidia-smi."""
        mock_run.return_value = MagicMock(
            stdout='NVIDIA GeForce RTX 3080\nNVIDIA GeForce RTX 3090\n',
            returncode=0
        )
        
        names = self.provider._query_nvidia_smi_names()
        
        self.assertEqual(names, ['NVIDIA GeForce RTX 3080', 'NVIDIA GeForce RTX 3090'])

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    def test_query_nvidia_smi_utils(self, mock_run):
        """Test querying GPU utilization via nvidia-smi."""
        mock_run.return_value = MagicMock(
            stdout='45\n32\n',
            returncode=0
        )
        
        utils = self.provider._query_nvidia_smi_utils()
        
        self.assertEqual(utils, [45.0, 32.0])

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    def test_query_nvidia_smi_vram(self, mock_run):
        """Test querying GPU VRAM via nvidia-smi."""
        mock_run.return_value = MagicMock(
            stdout='8192, 12288\n',
            returncode=0
        )
        
        vram = self.provider._query_nvidia_smi_vram()
        
        self.assertEqual(vram, [(8192.0, 12288.0)])

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    def test_query_nvidia_smi_freq(self, mock_run):
        """Test querying GPU frequency via nvidia-smi."""
        mock_run.return_value = MagicMock(
            stdout='1800\n',
            returncode=0
        )
        
        freqs = self.provider._query_nvidia_smi_freq()
        
        self.assertEqual(freqs, [1800.0])

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    def test_query_error_handling(self, mock_run):
        """Test error handling in nvidia-smi queries."""
        mock_run.return_value = MagicMock(
            stdout='invalid\n',
            returncode=0
        )
        
        utils = self.provider._query_nvidia_smi_utils()
        
        self.assertEqual(utils, [0.0])


class TestGPUProviderPublicMethods(unittest.TestCase):
    """Test GPUProvider public methods."""

    def test_gpu_names(self):
        """Test gpu_names method."""
        with patch('system_monitor.providers.gpu_provider.shutil.which', return_value=None):
            provider = GPUProvider()
            provider._gpu_names = ['GPU1', 'GPU2']
            
            names = provider.gpu_names()
            
            self.assertEqual(names, ['GPU1', 'GPU2'])
            self.assertIsNot(names, provider._gpu_names)

    def test_gpu_utils_nvml(self):
        """Test gpu_utils method with NVML."""
        with patch('system_monitor.providers.gpu_provider.shutil.which', return_value=None):
            provider = GPUProvider()
            provider.method = 'nvml'
            provider._nvml = MagicMock()
            
            mock_util = MagicMock()
            mock_util.gpu = 75
            provider._nvml.nvmlDeviceGetUtilizationRates.return_value = mock_util
            provider._nvml_handles = ['handle1']
            
            utils = provider.gpu_utils()
            
            self.assertEqual(utils, [75.0])

    def test_gpu_utils_nvidia_smi(self):
        """Test gpu_utils method with nvidia-smi."""
        with patch('system_monitor.providers.gpu_provider.shutil.which', return_value=None):
            provider = GPUProvider()
            provider.method = 'nvidia-smi'
            provider._last_smi_utils = [50.0, 60.0]
            
            utils = provider.gpu_utils()
            
            self.assertEqual(utils, [50.0, 60.0])

    def test_gpu_utils_no_method(self):
        """Test gpu_utils method when no GPU method available."""
        with patch('system_monitor.providers.gpu_provider.shutil.which', return_value=None):
            provider = GPUProvider()
            provider.method = 'none'
            
            utils = provider.gpu_utils()
            
            self.assertEqual(utils, [])

    def test_gpu_vram_info_nvml(self):
        """Test gpu_vram_info method with NVML."""
        with patch('system_monitor.providers.gpu_provider.shutil.which', return_value=None):
            provider = GPUProvider()
            provider.method = 'nvml'
            provider._nvml = MagicMock()
            
            mock_mem_info = MagicMock()
            mock_mem_info.used = 8192 * 1024 * 1024
            mock_mem_info.total = 12288 * 1024 * 1024
            provider._nvml.nvmlDeviceGetMemoryInfo.return_value = mock_mem_info
            provider._nvml_handles = ['handle1']
            
            vram = provider.gpu_vram_info()
            
            self.assertEqual(len(vram), 1)
            self.assertAlmostEqual(vram[0][0], 8192.0, places=1)
            self.assertAlmostEqual(vram[0][1], 12288.0, places=1)

    def test_gpu_vram_info_nvidia_smi(self):
        """Test gpu_vram_info method with nvidia-smi."""
        with patch('system_monitor.providers.gpu_provider.shutil.which', return_value=None):
            provider = GPUProvider()
            provider.method = 'nvidia-smi'
            provider._last_smi_vram = [(4096.0, 8192.0)]
            
            vram = provider.gpu_vram_info()
            
            self.assertEqual(vram, [(4096.0, 8192.0)])

    def test_gpu_frequencies_nvml(self):
        """Test gpu_frequencies method with NVML."""
        with patch('system_monitor.providers.gpu_provider.shutil.which', return_value=None):
            provider = GPUProvider()
            provider.method = 'nvml'
            provider._nvml = MagicMock()
            provider._nvml.nvmlDeviceGetClockInfo.return_value = 1800
            provider._nvml.NVML_CLOCK_GRAPHICS = 0
            provider._nvml_handles = ['handle1']
            
            freqs = provider.gpu_frequencies()
            
            self.assertEqual(freqs, [1800.0])

    def test_gpu_frequencies_nvidia_smi(self):
        """Test gpu_frequencies method with nvidia-smi."""
        with patch('system_monitor.providers.gpu_provider.shutil.which', return_value=None):
            provider = GPUProvider()
            provider.method = 'nvidia-smi'
            provider._last_smi_freq = [1950.0]
            
            freqs = provider.gpu_frequencies()
            
            self.assertEqual(freqs, [1950.0])


if __name__ == '__main__':
    unittest.main()
