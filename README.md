# System Monitor (PySide6)

A fast, modern, dark‑themed system monitor for desktop, built with PySide6 and psutil. It provides an at‑a‑glance dashboard plus detailed tabs for CPU, Memory, Network, Disk, GPU, and Processes. Smooth charts, per‑core views, and smart autoscaling make it both practical and pleasing.

> Why another monitor? This project aims to be a compact, hackable example of a real‑time Qt app: easy to run, easy to read, and easy to extend. If you want to learn PySide6/Qt or contribute performance/UX ideas, you’re in the right place!


## Features

- Dark, polished UI with compact “metric cards” and time‑series charts
- Live dashboard with CPU, memory, network, disk, and GPU at a glance
- Per‑core CPU charts arranged as small multiples with distinct colors
- Processes tab (user‑adjustable column widths) showing Top‑N by CPU%
- GPU utilization via NVML (pynvml) or a background `nvidia-smi` fallback
- User‑configurable global update interval (in milliseconds) from the toolbar
- Network/Disk throughput unit switcher (MB/s vs MiB/s) with clear formulas displayed in the UI
- Thoughtful performance choices: monotonic timing, dynamic baselines with time‑constant decay, background GPU polling


## Quick start

Prerequisites:
- Python 3.9+ recommended
- Works on Linux, Windows, and macOS (GPU metrics require NVIDIA tooling and may be unavailable on macOS/Apple Silicon)

Install dependencies:

```bash
pip install -r requirements.txt
# Optional for NVIDIA GPU metrics (NVML):
pip install pynvml
```

Run the app:

```bash
python play.py
```

Tip: The window title shows the current update interval. Use the toolbar spin box to change it at runtime.


## Using the app

- Dashboard tab: High‑level cards with values, progress bars, and compact sparklines
- CPU tab: Overall CPU chart plus a scrollable grid of per‑core charts; summary labels show process/thread counts and Python asyncio task count
- Memory, Network, Disk tabs: Time‑series charts; Network/Disk tabs include a unit selector (MB/s or MiB/s) and display the conversion formulas right in the UI
  - MB/s = bytes/s ÷ 1,000,000
  - MiB/s = bytes/s ÷ 1,048,576
- GPU tab: Per‑GPU utilization series when available (via NVML or `nvidia-smi`)
- Processes tab: Top processes by CPU% (PID, Name, CPU%, Mem%, Threads); column widths are adjustable


## GPU metrics

The app prefers NVML (via `pynvml`) for low‑latency GPU stats. If NVML isn’t available but `nvidia-smi` exists on your system, a lightweight background thread polls `nvidia-smi` at a safe interval and feeds cached values to the UI.

- Install NVML Python bindings: `pip install pynvml`
- Ensure `nvidia-smi` is on your PATH if relying on the fallback (Linux/Windows with NVIDIA drivers)
- If no NVIDIA GPU or tools are present, the GPU tab will indicate that metrics are unavailable


## Project structure

```
python_playground/
├── play.py            # Main application (UI, charts, metrics, GPU provider)
└── requirements.txt   # Runtime dependencies (pynvml optional)
```

Key components (all in `play.py` for simplicity):
- `GPUProvider`: Abstraction over NVML and `nvidia-smi` with cached background polling
- `TimeSeriesChart`: Reusable QtCharts wrapper for efficient live plotting
- `MetricCard`: Compact card with value, bar, and optional sparkline
- `SystemMonitor`: Main window; builds tabs, wires inputs, and runs the update loop


## Contributing

Contributions are very welcome! You can help by fixing bugs, improving performance, polishing UX, or adding features. Here’s how to get started:

1. Fork the repository and create a feature branch
2. Set up a virtual environment and install deps with `pip install -r requirements.txt`
3. Run the app with `python play.py` and verify your changes locally
4. Write clear commit messages and open a pull request describing the change and rationale

Good first contribution ideas:
- Add a settings panel to persist preferences (interval, history length, antialiasing, autoscale toggles)
- Replace sparkline cards with a lightweight custom `QWidget` to reduce chart overhead
- Aggregate Network view (total across interfaces) vs per‑interface toggle
- Disk per‑device throughput and filesystem usage charts
- Alert thresholds (color changes or notifications above user‑defined limits)
- CSV logging and snapshot/export of charts
- AMD/Intel GPU support (e.g., `rocm-smi` or platform APIs), with graceful fallbacks

Code style and tips:
- Keep UI updates on the GUI thread; do background polling in threads and pass results via cached state or signals
- Favor monotonic timers (`QElapsedTimer`) and avoid blocking calls in `on_timer`
- When adding charts, use bounded history and `series.replace()` for efficiency

If you’re unsure where to start, open an issue—we’re happy to help scope a task.


## Troubleshooting

- "Module not found: psutil" or "PySide6": Install dependencies with `pip install -r requirements.txt`
- GPU tab shows "metrics unavailable": Install `pynvml` or ensure `nvidia-smi` is present; otherwise GPU monitoring may not be supported on your system
- High CPU usage: Increase the update interval via the toolbar (e.g., 50–200 ms) and reduce history length if you add new charts


## Roadmap

- Preferences dialog with persisted settings
- Per‑device disk and per‑interface network breakdowns
- Export/snapshot & CSV logging
- Custom lightweight sparkline widget
- Optional alerts and thresholds
- Broader GPU support beyond NVIDIA


## License

No explicit license is provided yet. If you plan to reuse or distribute this code, please open an issue to discuss licensing, or propose a license via PR.


## Acknowledgements

- Built with [PySide6](https://doc.qt.io/qtforpython/) (Qt for Python) and [psutil](https://psutil.readthedocs.io/)
- Optional GPU metrics via [pynvml](https://github.com/nvidia/pynvml) and NVIDIA's `nvidia-smi`


## Screenshots

Screenshots help people discover and trust your project. If you capture some nice shots or short GIFs, please add them here! (Tip: dark background + a busy system shows the charts nicely.)
