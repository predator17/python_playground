# System Monitor (PySide6)

Fast, elegant, real‑time system monitor for desktop. Built with PySide6 + psutil. Clean dark UI, smooth charts, per‑core CPU, processes view, and optional NVIDIA GPU metrics.

快速、优雅的桌面实时系统监视器。基于 PySide6 与 psutil，深色主题、流畅曲线、按核心显示 CPU、进程视图，并可选支持 NVIDIA GPU 指标。


## Screenshots | 截图

![main](screenshots/main.png)
![cpu](screenshots/cpu.png)
![GPU](screenshots/gpu.png)
![process](screenshots/process.png)


## Features | 功能亮点

- Dashboard cards + time‑series charts for CPU / Memory / Network / Disk / GPU
- **CPU/GPU frequency display** (MHz) in dashboard cards and tabs
- **CPU/GPU model names** shown in dashboard cards (e.g., "AMD Ryzen 5800X", "RTX 3090")
- Separate per‑core CPU mini‑charts with distinct colors + **per-core frequency labels**
- **Memory frequency display** (when available, requires privileges on some systems)
- **GPU VRAM usage charts** with fixed y-axis based on total VRAM
- **GPU temperature monitoring** with dedicated chart (0-100°C)
- **Hierarchical process tree**: CPU Core → Process → Threads with lazy loading
- **Process search/filter** by name or PID with real-time filtering
- **Pause/resume** monitoring (keyboard shortcut: P)
- User‑configurable update intervals: global (default 100ms), GPU refresh, Process refresh
- Unit switcher for throughput: MB/s or MiB/s (formulas shown in UI)
- Non‑blocking GPU stats via NVML or background `nvidia-smi`
- **Performance optimizations**: Background threading for process enumeration, caching for expensive system info queries
- **Efficient design patterns**: Singleton cache, ThreadPoolExecutor for concurrency, Producer-Consumer pattern
- Keyboard shortcuts: P=Pause/Resume, Esc=Quit

- 总览卡片 + 曲线图，覆盖 CPU / 内存 / 网络 / 磁盘 / GPU
- **CPU/GPU 频率显示**（MHz）在仪表盘和各页显示
- **CPU/GPU 型号名称**显示在仪表盘卡片（如"AMD Ryzen 5800X"、"RTX 3090"）
- 按核心分离的 CPU 小图，每个核心不同颜色 + **每核心频率标签**
- **内存频率显示**（可用时，部分系统需权限）
- **GPU 显存使用曲线**，固定 y 轴范围基于总显存
- **GPU 温度监控**，专用曲线图（0-100°C）
- **分层进程树**：CPU 核心 → 进程 → 线程，延迟加载
- **进程搜索/过滤**，按名称或 PID 实时过滤
- **暂停/恢复**监控（快捷键：P）
- 可配置更新间隔：全局（默认 100ms）、GPU 刷新、进程刷新
- 网络/磁盘速率单位可切换：MB/s 或 MiB/s（UI 显示换算公式）
- GPU 指标使用 NVML 或后台 `nvidia-smi`，不会阻塞界面
- 快捷键：P=暂停/恢复，Esc=退出


## Install & Run | 安装与运行

- Python 3.9+
- Linux / Windows / macOS 均可（GPU 指标需 NVIDIA 工具；在 macOS/Apple Silicon 上可能不可用）

Install 依赖：

```bash
pip install -r requirements.txt
# Optional (可选，NVML 绑定):
pip install nvidia-ml-py
```

Run 运行：

```bash
python system_monitor/app.py
# Or use module syntax:
python -m system_monitor.app
```


## Project Structure | 项目结构

```
system_monitor/
├── __init__.py
├── app.py                          # Main application entry point (154 lines)
├── core/                           # Core application logic
│   ├── __init__.py
│   ├── info_manager.py             # System information gathering (93 lines)
│   ├── metrics_collector.py        # Parallel metrics collection (126 lines)
│   ├── metrics_updater.py          # Real-time metrics update logic (233 lines)
│   ├── process_collector.py        # Background process collection (174 lines)
│   └── process_manager.py          # Process tree management (222 lines)
├── providers/                      # Data providers
│   ├── __init__.py
│   └── gpu_provider.py             # GPU metrics (NVML/nvidia-smi) (196 lines)
├── ui/                             # UI builders and event handlers
│   ├── __init__.py
│   ├── basic_tabs_builder.py       # Memory/Network/Disk tabs (79 lines)
│   ├── chart_factory.py            # Chart creation factory (53 lines)
│   ├── cpu_tab_builder.py          # CPU tab with per-core charts (106 lines)
│   ├── dashboard_builder.py        # Dashboard with metric cards (82 lines)
│   ├── event_handlers.py           # Event handling logic (85 lines)
│   ├── gpu_tab_builder.py          # GPU tab builder (89 lines)
│   ├── process_tab_builder.py      # Process/Info tabs (80 lines)
│   └── toolbar_builder.py          # Toolbar builder (78 lines)
├── utils/                          # Utility functions
│   ├── __init__.py
│   ├── cache.py                    # Caching singleton for expensive queries (98 lines)
│   ├── system_info.py              # System info helpers (188 lines)
│   └── theme.py                    # Dark theme styling (152 lines)
└── widgets/                        # Custom Qt widgets
    ├── __init__.py
    ├── metric_card.py              # Dashboard metric card (167 lines)
    └── time_series_chart.py        # Real-time chart widget (97 lines)
```

## Usage tips | 使用提示

- **Update intervals**: Three controls in toolbar
  - Global interval (default 100ms): affects dashboard and all tabs
  - GPU refresh (default 100ms): separate control for GPU metrics
  - Process refresh (default 100ms): separate control for process tree updates
- **Pause/Resume**: Press `P` or click toolbar button to pause/resume monitoring
- **Units** (MB/s vs MiB/s): switch in Network/Disk tabs. Formulas shown in UI:
  - MB/s = bytes/s ÷ 1,000,000
  - MiB/s = bytes/s ÷ 1,048,576
- **CPU tab**: per‑core charts with frequency labels below each chart; summary shows processes/threads and Python asyncio task count
- **Memory tab**: displays RAM frequency (MHz) when available (may require root/admin on some systems)
- **GPU tab**: shows utilization, VRAM usage, temperature, and frequency for each GPU
- **Processes tab**: hierarchical tree (CPU Core → Process → Threads)
  - Click to expand CPU cores to see processes pinned to that core
  - Click processes to see their threads (lazy loaded)
  - Use search box to filter by name or PID
- **Keyboard shortcuts**: P = Pause/Resume, Esc = Quit

- **更新间隔**：工具栏三个控制项
  - 全局间隔（默认 100ms）：影响仪表盘和所有页面
  - GPU 刷新（默认 100ms）：GPU 指标的独立控制
  - 进程刷新（默认 100ms）：进程树更新的独立控制
- **暂停/恢复**：按 `P` 或点击工具栏按钮暂停/恢复监控
- **单位**（MB/s 与 MiB/s）：在 网络/磁盘 页切换。UI 内显示换算公式：
  - MB/s = 字节/秒 ÷ 1,000,000
  - MiB/s = 字节/秒 ÷ 1,048,576
- **CPU 页**：每核心图表，每个图表下方有频率标签；底部显示进程/线程与 Python 协程数量
- **内存页**：显示 RAM 频率（MHz），可用时（部分系统需要 root/管理员权限）
- **GPU 页**：显示每个 GPU 的利用率、显存使用、温度和频率
- **进程页**：分层树结构（CPU 核心 → 进程 → 线程）
  - 点击展开 CPU 核心查看固定到该核心的进程
  - 点击进程查看其线程（延迟加载）
  - 使用搜索框按名称或 PID 过滤
- **快捷键**：P = 暂停/恢复，Esc = 退出


## Contributing | 参与贡献

PRs welcome! Fork → branch → change → PR with a short description.
欢迎提 PR！Fork → 新分支 → 修改 → 提交 PR，并附简要说明。


## License | 许可证

No license specified yet. Open an issue or PR if you need one.
尚未指定许可证，如有需求请提 Issue 或 PR 讨论。
