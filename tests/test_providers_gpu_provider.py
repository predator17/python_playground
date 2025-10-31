"""Tests for GPUProvider module."""

#      Copyright (c) 2025 predator. All rights reserved.

import pytest
from unittest.mock import MagicMock, patch, Mock
import time


class TestGPUProvider:
    """Test GPUProvider class."""

    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_init_no_gpu(self, mock_which):
        """Test GPUProvider initialization with no GPU."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        # Mock no pynvml and no nvidia-smi
        mock_which.return_value = None
        
        with patch.dict('sys.modules', {'pynvml': None}):
            provider = GPUProvider()
        
        assert provider.method == "none"
        assert provider.gpu_names() == []

    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_init_nvml_success(self, mock_which):
        """Test GPUProvider initialization with NVML."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        # Mock pynvml
        mock_nvml = MagicMock()
        mock_nvml.nvmlDeviceGetCount.return_value = 2
        mock_handle1 = MagicMock()
        mock_handle2 = MagicMock()
        mock_nvml.nvmlDeviceGetHandleByIndex.side_effect = [mock_handle1, mock_handle2]
        mock_nvml.nvmlDeviceGetName.side_effect = ["GPU 0", b"GPU 1"]
        
        with patch.dict('sys.modules', {'pynvml': mock_nvml}):
            with patch('builtins.__import__', return_value=mock_nvml):
                provider = GPUProvider()
        
        assert provider.method == "nvml"
        assert len(provider.gpu_names()) == 2
        assert "GPU 0" in provider.gpu_names()
        assert "GPU 1" in provider.gpu_names()

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_init_nvidia_smi_fallback(self, mock_which, mock_subprocess):
        """Test GPUProvider falls back to nvidia-smi."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        mock_which.return_value = "/usr/bin/nvidia-smi"
        mock_result = MagicMock()
        mock_result.stdout = "GPU 0\nGPU 1\n"
        mock_subprocess.return_value = mock_result
        
        # Mock import to fail (no pynvml)
        with patch.dict('sys.modules', {'pynvml': None}):
            with patch('builtins.__import__', side_effect=ImportError):
                provider = GPUProvider()
        
        assert provider.method == "nvidia-smi"
        assert len(provider.gpu_names()) == 2

    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_init_nvml_exception(self, mock_which):
        """Test GPUProvider handles NVML initialization exception."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        mock_which.return_value = None
        mock_nvml = MagicMock()
        mock_nvml.nvmlInit.side_effect = Exception("NVML error")
        
        with patch.dict('sys.modules', {'pynvml': mock_nvml}):
            with patch('builtins.__import__', return_value=mock_nvml):
                provider = GPUProvider()
        
        assert provider.method == "none"
        assert provider._nvml is None

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_query_nvidia_smi_names(self, mock_which, mock_subprocess):
        """Test _query_nvidia_smi_names."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        mock_which.return_value = "/usr/bin/nvidia-smi"
        mock_result = MagicMock()
        mock_result.stdout = "NVIDIA GeForce RTX 3080\nNVIDIA GeForce RTX 3090\n"
        mock_subprocess.return_value = mock_result
        
        with patch.dict('sys.modules', {'pynvml': None}):
            with patch('builtins.__import__', side_effect=ImportError):
                provider = GPUProvider()
        
        # Names should be queried during init
        assert "NVIDIA GeForce RTX 3080" in provider.gpu_names()
        assert "NVIDIA GeForce RTX 3090" in provider.gpu_names()

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    def test_query_nvidia_smi_utils(self, mock_subprocess):
        """Test _query_nvidia_smi_utils."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        provider.method = "nvidia-smi"
        
        mock_result = MagicMock()
        mock_result.stdout = "45\n67\n"
        mock_subprocess.return_value = mock_result
        
        utils = provider._query_nvidia_smi_utils()
        
        assert utils == [45.0, 67.0]

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    def test_query_nvidia_smi_utils_invalid(self, mock_subprocess):
        """Test _query_nvidia_smi_utils handles invalid data."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        mock_result = MagicMock()
        mock_result.stdout = "45\ninvalid\n"
        mock_subprocess.return_value = mock_result
        
        utils = provider._query_nvidia_smi_utils()
        
        assert utils == [45.0, 0.0]

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    def test_query_nvidia_smi_vram(self, mock_subprocess):
        """Test _query_nvidia_smi_vram."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        mock_result = MagicMock()
        mock_result.stdout = "1024, 8192\n2048, 10240\n"
        mock_subprocess.return_value = mock_result
        
        vram = provider._query_nvidia_smi_vram()
        
        assert vram == [(1024.0, 8192.0), (2048.0, 10240.0)]

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    def test_query_nvidia_smi_vram_invalid(self, mock_subprocess):
        """Test _query_nvidia_smi_vram handles invalid data."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        mock_result = MagicMock()
        mock_result.stdout = "1024, 8192\ninvalid\n"
        mock_subprocess.return_value = mock_result
        
        vram = provider._query_nvidia_smi_vram()
        
        assert vram == [(1024.0, 8192.0), (0.0, 0.0)]

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    def test_query_nvidia_smi_freq(self, mock_subprocess):
        """Test _query_nvidia_smi_freq."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        mock_result = MagicMock()
        mock_result.stdout = "1500\n1600\n"
        mock_subprocess.return_value = mock_result
        
        freqs = provider._query_nvidia_smi_freq()
        
        assert freqs == [1500.0, 1600.0]

    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    def test_query_nvidia_smi_freq_invalid(self, mock_subprocess):
        """Test _query_nvidia_smi_freq handles invalid data."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        mock_result = MagicMock()
        mock_result.stdout = "1500\ninvalid\n"
        mock_subprocess.return_value = mock_result
        
        freqs = provider._query_nvidia_smi_freq()
        
        assert freqs == [1500.0, 0.0]

    def test_gpu_names_returns_copy(self):
        """Test gpu_names returns a copy of the list."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        provider._gpu_names = ["GPU 0", "GPU 1"]
        
        names1 = provider.gpu_names()
        names2 = provider.gpu_names()
        
        assert names1 == names2
        assert names1 is not names2  # Different objects

    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_gpu_utils_nvml(self, mock_which):
        """Test gpu_utils with NVML method."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        mock_nvml = MagicMock()
        mock_nvml.nvmlDeviceGetCount.return_value = 1
        mock_handle = MagicMock()
        mock_nvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_nvml.nvmlDeviceGetName.return_value = "GPU 0"
        
        mock_util = MagicMock()
        mock_util.gpu = 75
        mock_nvml.nvmlDeviceGetUtilizationRates.return_value = mock_util
        
        with patch.dict('sys.modules', {'pynvml': mock_nvml}):
            with patch('builtins.__import__', return_value=mock_nvml):
                provider = GPUProvider()
                provider._nvml = mock_nvml
                provider._nvml_handles = [mock_handle]
        
        utils = provider.gpu_utils()
        
        assert utils == [75.0]

    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_gpu_utils_nvml_exception(self, mock_which):
        """Test gpu_utils handles NVML exception."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        mock_nvml = MagicMock()
        mock_nvml.nvmlDeviceGetCount.return_value = 1
        mock_handle = MagicMock()
        mock_nvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_nvml.nvmlDeviceGetName.return_value = "GPU 0"
        mock_nvml.nvmlDeviceGetUtilizationRates.side_effect = Exception("NVML error")
        
        with patch.dict('sys.modules', {'pynvml': mock_nvml}):
            with patch('builtins.__import__', return_value=mock_nvml):
                provider = GPUProvider()
                provider._nvml = mock_nvml
                provider._nvml_handles = [mock_handle]
        
        utils = provider.gpu_utils()
        
        assert utils == [0.0]

    def test_gpu_utils_nvidia_smi(self):
        """Test gpu_utils with nvidia-smi method."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        provider.method = "nvidia-smi"
        provider._last_smi_utils = [45.0, 67.0]
        
        utils = provider.gpu_utils()
        
        assert utils == [45.0, 67.0]

    def test_gpu_utils_no_method(self):
        """Test gpu_utils with no GPU method."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        provider.method = "none"
        
        utils = provider.gpu_utils()
        
        assert utils == []

    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_gpu_vram_info_nvml(self, mock_which):
        """Test gpu_vram_info with NVML method."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        mock_nvml = MagicMock()
        mock_nvml.nvmlDeviceGetCount.return_value = 1
        mock_handle = MagicMock()
        mock_nvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_nvml.nvmlDeviceGetName.return_value = "GPU 0"
        
        mock_mem_info = MagicMock()
        mock_mem_info.used = 2048 * 1024 * 1024  # 2048 MB
        mock_mem_info.total = 8192 * 1024 * 1024  # 8192 MB
        mock_nvml.nvmlDeviceGetMemoryInfo.return_value = mock_mem_info
        
        with patch.dict('sys.modules', {'pynvml': mock_nvml}):
            with patch('builtins.__import__', return_value=mock_nvml):
                provider = GPUProvider()
                provider._nvml = mock_nvml
                provider._nvml_handles = [mock_handle]
        
        vram = provider.gpu_vram_info()
        
        assert len(vram) == 1
        assert vram[0] == (2048.0, 8192.0)

    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_gpu_vram_info_nvml_exception(self, mock_which):
        """Test gpu_vram_info handles NVML exception."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        mock_nvml = MagicMock()
        mock_nvml.nvmlDeviceGetCount.return_value = 1
        mock_handle = MagicMock()
        mock_nvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_nvml.nvmlDeviceGetName.return_value = "GPU 0"
        mock_nvml.nvmlDeviceGetMemoryInfo.side_effect = Exception("NVML error")
        
        with patch.dict('sys.modules', {'pynvml': mock_nvml}):
            with patch('builtins.__import__', return_value=mock_nvml):
                provider = GPUProvider()
                provider._nvml = mock_nvml
                provider._nvml_handles = [mock_handle]
        
        vram = provider.gpu_vram_info()
        
        assert vram == [(0.0, 0.0)]

    def test_gpu_vram_info_nvidia_smi(self):
        """Test gpu_vram_info with nvidia-smi method."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        provider.method = "nvidia-smi"
        provider._last_smi_vram = [(1024.0, 8192.0), (2048.0, 10240.0)]
        
        vram = provider.gpu_vram_info()
        
        assert vram == [(1024.0, 8192.0), (2048.0, 10240.0)]

    def test_gpu_vram_info_no_method(self):
        """Test gpu_vram_info with no GPU method."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        provider.method = "none"
        
        vram = provider.gpu_vram_info()
        
        assert vram == []

    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_gpu_frequencies_nvml(self, mock_which):
        """Test gpu_frequencies with NVML method."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        mock_nvml = MagicMock()
        mock_nvml.nvmlDeviceGetCount.return_value = 1
        mock_handle = MagicMock()
        mock_nvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_nvml.nvmlDeviceGetName.return_value = "GPU 0"
        mock_nvml.NVML_CLOCK_GRAPHICS = 0
        mock_nvml.nvmlDeviceGetClockInfo.return_value = 1500
        
        with patch.dict('sys.modules', {'pynvml': mock_nvml}):
            with patch('builtins.__import__', return_value=mock_nvml):
                provider = GPUProvider()
                provider._nvml = mock_nvml
                provider._nvml_handles = [mock_handle]
        
        freqs = provider.gpu_frequencies()
        
        assert freqs == [1500.0]

    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_gpu_frequencies_nvml_exception(self, mock_which):
        """Test gpu_frequencies handles NVML exception."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        mock_nvml = MagicMock()
        mock_nvml.nvmlDeviceGetCount.return_value = 1
        mock_handle = MagicMock()
        mock_nvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_nvml.nvmlDeviceGetName.return_value = "GPU 0"
        mock_nvml.NVML_CLOCK_GRAPHICS = 0
        mock_nvml.nvmlDeviceGetClockInfo.side_effect = Exception("NVML error")
        
        with patch.dict('sys.modules', {'pynvml': mock_nvml}):
            with patch('builtins.__import__', return_value=mock_nvml):
                provider = GPUProvider()
                provider._nvml = mock_nvml
                provider._nvml_handles = [mock_handle]
        
        freqs = provider.gpu_frequencies()
        
        assert freqs == [0.0]

    def test_gpu_frequencies_nvidia_smi(self):
        """Test gpu_frequencies with nvidia-smi method."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        provider.method = "nvidia-smi"
        provider._last_smi_freq = [1500.0, 1600.0]
        
        freqs = provider.gpu_frequencies()
        
        assert freqs == [1500.0, 1600.0]

    def test_gpu_frequencies_no_method(self):
        """Test gpu_frequencies with no GPU method."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        provider = GPUProvider()
        provider.method = "none"
        
        freqs = provider.gpu_frequencies()
        
        assert freqs == []

    @patch('system_monitor.providers.gpu_provider.threading.Thread')
    @patch('system_monitor.providers.gpu_provider.time.sleep')
    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_smi_poll_loop(self, mock_which, mock_subprocess, mock_sleep, mock_thread):
        """Test _smi_poll_loop updates cached values."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        mock_which.return_value = "/usr/bin/nvidia-smi"
        
        # Mock subprocess results for initialization
        mock_result_init = MagicMock()
        mock_result_init.stdout = "GPU 0\n"
        
        # Mock subsequent calls for polling
        mock_result_utils = MagicMock()
        mock_result_utils.stdout = "75\n"
        mock_result_vram = MagicMock()
        mock_result_vram.stdout = "2048, 8192\n"
        mock_result_freq = MagicMock()
        mock_result_freq.stdout = "1500\n"
        
        mock_subprocess.side_effect = [
            mock_result_init,  # Initial names query
            mock_result_utils,  # Poll: utils
            mock_result_vram,   # Poll: vram
            mock_result_freq,   # Poll: freq
        ]
        
        # Make sleep raise after first iteration to exit loop
        mock_sleep.side_effect = [None, Exception("Stop")]
        
        # Mock thread to prevent actual background thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        with patch.dict('sys.modules', {'pynvml': None}):
            with patch('builtins.__import__', side_effect=ImportError):
                provider = GPUProvider()
                
                # Run one iteration of poll loop manually
                try:
                    provider._smi_poll_loop()
                except Exception:
                    pass
        
        # Verify cached values were updated
        assert provider._last_smi_utils == [75.0]
        assert provider._last_smi_vram == [(2048.0, 8192.0)]
        assert provider._last_smi_freq == [1500.0]

    @patch('system_monitor.providers.gpu_provider.threading.Thread')
    @patch('system_monitor.providers.gpu_provider.time.sleep')
    @patch('system_monitor.providers.gpu_provider.subprocess.run')
    @patch('system_monitor.providers.gpu_provider.shutil.which')
    def test_smi_poll_loop_exception(self, mock_which, mock_subprocess, mock_sleep, mock_thread):
        """Test _smi_poll_loop handles exceptions."""
        from system_monitor.providers.gpu_provider import GPUProvider
        
        mock_which.return_value = "/usr/bin/nvidia-smi"
        mock_result = MagicMock()
        mock_result.stdout = "GPU 0\n"
        mock_subprocess.side_effect = [
            mock_result,  # Init
            Exception("Query error"),  # Poll fails
        ]
        
        # Make sleep raise after first iteration to exit loop
        mock_sleep.side_effect = [None, Exception("Stop")]
        
        # Mock thread to prevent actual background thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        with patch.dict('sys.modules', {'pynvml': None}):
            with patch('builtins.__import__', side_effect=ImportError):
                provider = GPUProvider()
                
                # Should not crash
                try:
                    provider._smi_poll_loop()
                except Exception as e:
                    if str(e) != "Stop":
                        raise
