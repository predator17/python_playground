# System Monitor Tests

Comprehensive test suite for the system_monitor application.

## Test Structure

```
tests/
├── __init__.py
├── README.md (this file)
└── system_monitor/
    ├── __init__.py
    ├── utils/
    │   ├── __init__.py
    │   ├── test_system_info.py  # Tests for system information utilities
    │   └── test_theme.py         # Tests for theme utilities
    ├── providers/
    │   ├── __init__.py
    │   └── test_gpu_provider.py  # Tests for GPU data provider
    └── widgets/
        ├── __init__.py
        └── test_widgets.py       # Tests for UI widgets
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r test-requirements.txt
```

### Run All Tests

```bash
# From project root
pytest

# With coverage report
pytest --cov=system_monitor --cov-report=html

# Verbose output
pytest -v
```

### Run Specific Test Files

```bash
# Test system_info utilities
pytest tests/system_monitor/utils/test_system_info.py

# Test GPU provider
pytest tests/system_monitor/providers/test_gpu_provider.py

# Test widgets
pytest tests/system_monitor/widgets/test_widgets.py

# Test theme
pytest tests/system_monitor/utils/test_theme.py
```

### Run Specific Test Classes or Methods

```bash
# Run a specific test class
pytest tests/system_monitor/utils/test_system_info.py::TestGetCpuModelName

# Run a specific test method
pytest tests/system_monitor/utils/test_system_info.py::TestGetCpuModelName::test_linux_cpu_model
```

## Test Coverage

The test suite covers:

### Utils Module (system_info.py)
- `get_cpu_model_name()` - CPU model detection across platforms (Linux, macOS, Windows)
- `get_per_core_frequencies()` - Per-core CPU frequency retrieval
- `get_memory_frequency()` - RAM frequency detection
- `get_cpu_temperatures()` - CPU temperature sensor reading
- `get_gpu_temperatures()` - GPU temperature retrieval (NVML and nvidia-smi)

### Utils Module (theme.py)
- `apply_dark_theme()` - Dark theme application and styling

### Providers Module (gpu_provider.py)
- `GPUProvider` initialization (NVML and nvidia-smi fallback)
- GPU name queries
- GPU utilization queries
- GPU VRAM information queries
- GPU frequency queries
- Background polling for nvidia-smi

### Widgets Module
- `TimeSeriesChart` - Real-time chart widget
  - Initialization and configuration
  - Data appending
  - Auto-scaling
- `MetricCard` - Metric display card
  - Initialization
  - Percentage updates
  - Warning color application
  - Frequency and model display
  - Unavailable state handling

## Test Framework

- **Framework**: pytest
- **Mocking**: unittest.mock
- **Coverage**: pytest-cov

## Notes

- Tests use extensive mocking to avoid dependencies on actual hardware and system state
- PySide6 widgets are mocked to allow testing without a display server
- GPU tests mock both NVML library and nvidia-smi command-line tool
- Platform-specific tests mock platform.system() to simulate different operating systems

## Contributing

When adding new features to system_monitor:

1. Add corresponding unit tests in the appropriate test file
2. Ensure tests are isolated and don't depend on external state
3. Use mocks for system calls, subprocess execution, and hardware queries
4. Aim for high code coverage (>80%)
5. Run the full test suite before submitting changes
