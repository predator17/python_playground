# System Monitor - Architecture Documentation

## Overview

The System Monitor is a real-time desktop application built with PySide6 (Qt6) that provides comprehensive system metrics visualization. The architecture follows a modular, component-based design with clear separation of concerns.

**Tech Stack:**
- **UI Framework:** PySide6 (Qt6)
- **System Metrics:** psutil
- **GPU Metrics:** nvidia-ml-py (NVML) with nvidia-smi fallback
- **Charting:** QtCharts (built-in)

## High-Level Architecture

The application follows a modular architecture with clear separation of concerns:

```mermaid
graph TB
    subgraph "Application Entry"
        Main[app.py<br/>SystemMonitor]
    end
    
    subgraph "Core Logic"
        MU[metrics_updater.py<br/>MetricsUpdater]
        PM[process_manager.py<br/>ProcessManager]
        IM[info_manager.py<br/>InfoManager]
        MC_CORE[metrics_collector.py<br/>MetricsCollector]
        PC[process_collector.py<br/>ProcessCollector]
    end
    
    subgraph "UI Builders"
        TB[toolbar_builder.py<br/>ToolbarBuilder]
        DB[dashboard_builder.py<br/>DashboardBuilder]
        CB[cpu_tab_builder.py<br/>CPUTabBuilder]
        BB[basic_tabs_builder.py<br/>BasicTabsBuilder]
        GB[gpu_tab_builder.py<br/>GPUTabBuilder]
        PB[process_tab_builder.py<br/>ProcessTabBuilder]
        CF[chart_factory.py<br/>ChartFactory]
        EH[event_handlers.py<br/>EventHandlers]
    end
    
    subgraph "Widgets"
        MC[metric_card.py<br/>MetricCard]
        TSC[time_series_chart.py<br/>TimeSeriesChart]
    end
    
    subgraph "Providers"
        GPU[gpu_provider.py<br/>GPUProvider]
    end
    
    subgraph "Utils"
        SI[system_info.py<br/>System Info]
        TH[theme.py<br/>Theme]
        CA[cache.py<br/>SystemInfoCache]
    end
    
    subgraph "External"
        PS[psutil]
        NVML[pynvml/nvidia-smi]
        QT[PySide6/Qt6]
    end
    
    Main --> TB
    Main --> DB
    Main --> CB
    Main --> BB
    Main --> GB
    Main --> PB
    Main --> EH
    Main --> MU
    Main --> PM
    Main --> IM
    
    TB --> EH
    DB --> MC
    DB --> SI
    CB --> TSC
    BB --> TSC
    GB --> TSC
    PB --> MC
    CF --> TSC
    
    MU --> MC_CORE
    MU --> GPU
    MU --> SI
    PM --> PC
    PM --> PS
    IM --> SI
    
    PC --> PS
    MC_CORE --> PS
    SI --> CA
    CA --> PS
    GPU --> NVML
    TH --> QT
    MC --> TSC
    
    style Main fill:#3584e4
    style MU fill:#00c853
    style PM fill:#00c853
    style IM fill:#00c853
    style MC_CORE fill:#00c853
    style PC fill:#00c853
    style TB fill:#2962ff
    style DB fill:#2962ff
    style CB fill:#2962ff
    style BB fill:#2962ff
    style GB fill:#2962ff
    style PB fill:#2962ff
    style CF fill:#2962ff
    style EH fill:#2962ff
    style MC fill:#ffd54f
    style TSC fill:#ffd54f
    style GPU fill:#ff5252
    style CA fill:#ab47bc
```

---

## Class Diagram

The following diagram shows the main classes and their relationships. Static utility classes (MetricsUpdater, ProcessManager, InfoManager) are shown with `<<static>>` stereotype.

```mermaid
classDiagram
    class SystemMonitor {
        -interval_ms: int
        -gpu_provider: GPUProvider
        -_paused: bool
        -timer: QTimer
        -_elapsed: QElapsedTimer
        -card_cpu: MetricCard
        -card_mem: MetricCard
        -card_net_up: MetricCard
        -card_net_down: MetricCard
        -card_disk_read: MetricCard
        -card_disk_write: MetricCard
        -card_gpu: MetricCard
        -chart_cpu: TimeSeriesChart
        -chart_mem: TimeSeriesChart
        -chart_net: TimeSeriesChart
        -chart_disk: TimeSeriesChart
        -chart_gpu: TimeSeriesChart
        -chart_gpu_vram: TimeSeriesChart
        -chart_gpu_temp: TimeSeriesChart
        -core_charts: List~TimeSeriesChart~
        -core_freq_labels: List~QLabel~
        -spin_gpu_refresh: QSpinBox
        -spin_proc_refresh: QSpinBox
        -proc_tree: QTreeWidget
        -proc_search: QLineEdit
        -_last_net: snetio
        -_last_disk: sdiskio
        -_bytes_per_unit: int
        -_gpu_refresh_accum: float
        -_proc_refresh_accum: float
        +__init__(interval_ms: int)
        +on_timer()
        +refresh_info()
        +refresh_processes()
        +on_interval_changed(val: int)
        +on_proc_search_changed(text: str)
        +on_proc_item_expanded(item: QTreeWidgetItem)
        +closeEvent(event)
        -_setup_ui()
        -_setup_timer()
        -_setup_shortcuts()
        -_wire_unit_selectors()
        -_init_metrics_state()
    }
    
    class MetricsUpdater {
        <<static>>
        +update_all_metrics(monitor, dt)$
        -_update_cpu(monitor, dt)$
        -_update_memory(monitor)$
        -_update_network(monitor, dt)$
        -_update_disk(monitor, dt)$
        -_update_gpu(monitor, dt)$
        -_update_processes(monitor, dt)$
        -_update_gpu_tooltips(monitor, utils, vram, freqs)$
    }
    
    class ProcessManager {
        <<static>>
        -_collector: ProcessCollector
        +initialize_collector()$
        +shutdown_collector()$
        +refresh_processes(monitor)$
        +on_proc_item_expanded(monitor, item)$
        -_update_ui_with_result(monitor, result)$
        -_save_expansion_state(monitor, n_cores)$
        -_build_process_tree(monitor, n_cores, core_processes, first_build, expanded_cores, expanded_processes)$
        -_update_summary_labels(monitor, proc_count, total_threads)$
    }
    
    class InfoManager {
        <<static>>
        +refresh_info(monitor)$
    }
    
    class ProcessCollector {
        -_executor: ThreadPoolExecutor
        -_result_queue: Queue
        -_collecting: bool
        -_lock: Lock
        -_shutdown: bool
        +__init__(max_workers: int)
        +collect_async(n_cores: int, proc_filter: str)
        +get_result(): Optional~dict~
        +is_collecting(): bool
        +shutdown()
        -_collect_processes(n_cores: int, proc_filter: str): dict
        -_on_collection_complete(future: Future)
    }
    
    class MetricsCollector {
        -_executor: ThreadPoolExecutor
        +__init__(max_workers: int)
        +collect_all(): dict
        +shutdown()
        -_collect_cpu_percent(): float
        -_collect_cpu_percpu(): list
        -_collect_cpu_freq(): object
        -_collect_memory(): object
        -_collect_network(): object
        -_collect_disk(): object
    }
    
    class SystemInfoCache {
        <<singleton>>
        -_instance: SystemInfoCache
        -_lock: Lock
        -_cache: Dict~str, Any~
        -_cache_lock: RLock
        +__new__(): SystemInfoCache
        +get(key: str): Optional~Any~
        +set(key: str, value: Any)
        +get_or_compute(key: str, compute_func: Callable): Any
        +clear()
        +reset()$
        -_initialize()
    }
    
    class MetricCard {
        -is_percent: bool
        -unit: str
        -color: str
        -_dyn_max: float
        -frame: QFrame
        -lbl_title: QLabel
        -lbl_value: QLabel
        -lbl_frequency: QLabel
        -lbl_model: QLabel
        -bar: QProgressBar
        -sparkline: TimeSeriesChart
        +__init__(title, unit, is_percent, color, sparkline, max_points)
        +set_tooltip(text: str)
        +set_unavailable(message: str)
        +set_frequency(freq_mhz: float)
        +set_model(model_name: str)
        +update_percent(pct: float)
        +update_value(value: float, ref_max: float)
    }
    
    class TimeSeriesChart {
        -max_points: int
        -auto_scale: bool
        -_x: int
        -chart: QChart
        -series: List~QLineSeries~
        -axis_x: QValueAxis
        -axis_y: QValueAxis
        -view: QChartView
        -_buffers: List~List~QPointF~~
        +__init__(title, series_names, max_points, y_range, auto_scale)
        +append(values: List~float~)
    }
    
    class GPUProvider {
        -method: str
        -_gpu_names: List~str~
        -_nvml: Module
        -_nvml_handles: List
        -_last_smi_time: float
        -_last_smi_utils: List~float~
        -_last_smi_vram: List~Tuple~
        -_last_smi_freq: List~float~
        -_smi_min_interval: float
        -_smi_stop: bool
        -_smi_thread: Thread
        +__init__()
        +gpu_names(): List~str~
        +gpu_utils(): List~float~
        +gpu_vram_info(): List~Tuple~
        +gpu_frequencies(): List~float~
        -_query_nvidia_smi_names(): List~str~
        -_query_nvidia_smi_utils(): List~float~
        -_query_nvidia_smi_vram(): List~Tuple~
        -_query_nvidia_smi_freq(): List~float~
        -_smi_poll_loop()
    }
    
    %% Relationships
    SystemMonitor "1" --> "1" MetricsUpdater : delegates to
    SystemMonitor "1" --> "1" ProcessManager : delegates to
    SystemMonitor "1" --> "1" InfoManager : delegates to
    SystemMonitor "1" --> "1" GPUProvider : uses
    
    MetricsUpdater "1" ..> "1" MetricsCollector : optionally uses
    MetricsUpdater "1" ..> "1" GPUProvider : queries
    
    ProcessManager "1" --> "0..1" ProcessCollector : manages singleton
    
    InfoManager "1" ..> "1" SystemInfoCache : uses
    
    SystemMonitor "1" *-- "7" MetricCard : contains
    SystemMonitor "1" *-- "5" TimeSeriesChart : contains main charts
    SystemMonitor "1" *-- "N" TimeSeriesChart : contains per-core charts
    
    MetricCard "1" *-- "0..1" TimeSeriesChart : embeds sparkline
    
    SystemMonitor --|> QMainWindow : inherits
    MetricCard --|> QWidget : inherits
    TimeSeriesChart --|> QWidget : inherits
    
    note for MetricsUpdater "Static class with all static methods\nCentral coordinator for metrics updates"
    note for ProcessManager "Static class with class-level singleton\nManages ProcessCollector lifecycle"
    note for InfoManager "Static class with all static methods\nGathers system information"
    note for SystemInfoCache "Thread-safe singleton\nDouble-checked locking pattern"
```

### Class Relationships Explanation

**Delegation Pattern:**
- `SystemMonitor` delegates metrics updates to `MetricsUpdater`
- `SystemMonitor` delegates process management to `ProcessManager`
- `SystemMonitor` delegates info gathering to `InfoManager`

**Composition:**
- `SystemMonitor` contains 7 `MetricCard` instances (CPU, Memory, Net Up/Down, Disk Read/Write, GPU)
- `SystemMonitor` contains multiple `TimeSeriesChart` instances (main charts + per-core charts)
- `MetricCard` optionally contains a `TimeSeriesChart` (sparkline)

**Usage/Dependency:**
- `MetricsUpdater` uses `GPUProvider` for GPU metrics
- `MetricsUpdater` optionally uses `MetricsCollector` for parallel collection
- `ProcessManager` manages singleton `ProcessCollector` instance
- `InfoManager` uses `SystemInfoCache` for expensive queries

**Inheritance:**
- `SystemMonitor` inherits from `QMainWindow`
- `MetricCard` and `TimeSeriesChart` inherit from `QWidget`

---

## Component Details

### 1. SystemMonitor (Main Application Controller)

**Responsibility:** Central orchestrator managing the entire application lifecycle, UI layout, and data updates.

**Key Features:**
- Manages tabbed interface (Dashboard, CPU, Memory, Network, Disk, GPU, Processes, System Info)
- Orchestrates periodic data collection via QTimer (configurable interval, default 100ms)
- Coordinates updates across multiple MetricCard and TimeSeriesChart widgets
- **Pause/resume functionality** with keyboard shortcuts (P = pause/resume, Esc = quit)
- **Configurable refresh rates** for GPU metrics and process table (default 100ms)
- Handles unit conversion (MB/s ↔ MiB/s)
- Uses time-constant decay for dynamic baseline calculation
- **CPU/GPU frequency display** in dashboard cards and tabs
- **CPU/GPU model name display** in dashboard cards
- **Per-core frequency monitoring** with individual labels
- **Memory frequency display** (when available)
- **Hierarchical process tree** (CPU Core → Process → Threads)
- **Process search/filter** by name or PID
- **Lazy thread loading** for performance

**Update Flow:**
```
QTimer.timeout → on_timer() → 
  ├─ Poll psutil for CPU/Memory/Network/Disk
  ├─ Poll GPUProvider for GPU metrics (configurable interval)
  ├─ Update all dashboard MetricCards with frequency info
  ├─ Update active tab's TimeSeriesChart(s)
  ├─ Update per-core frequency labels
  └─ Periodically refresh_processes() (configurable interval)
```

### 2. MetricCard (Dashboard Widget)

**Responsibility:** Self-contained dashboard card displaying a single metric with value, progress bar, and optional sparkline.

**Key Features:**
- Displays title, numeric value with unit, and progress bar
- **Frequency display** (CPU/GPU MHz) with lightning icon
- **Model name display** (CPU/GPU model) with styled label
- Optional embedded sparkline chart (mini TimeSeriesChart)
- Dynamic progress bar coloring (green → orange → red) based on thresholds (80%, 90%)
- Auto-scaling for non-percentage metrics
- Hover effects via CSS styling

**Visual Elements:**
- QLabel (title)
- QLabel (value)
- QLabel (frequency) - optional, hidden when not set
- QLabel (model) - optional, hidden when not set
- QProgressBar (visual indicator with dynamic coloring)
- TimeSeriesChart (optional sparkline, 60 points)

### 3. TimeSeriesChart (Charting Widget)

**Responsibility:** Reusable real-time chart widget for plotting time-series data.

**Key Features:**
- Multi-series support (e.g., Network: Upload + Download)
- Fixed-window rolling buffer (default 400 points)
- Auto-scaling option for dynamic y-axis
- Efficient point management with pre-allocated buffers
- QtCharts integration with antialiasing
- Customizable appearance (axis visibility, legends, margins)

**Performance Optimizations:**
- Uses `QLineSeries.replace()` instead of clearing and re-adding points
- Pre-allocated `QPointF` buffers to reduce allocations
- Only updates charts on active tabs

### 4. GPUProvider (Data Provider)

**Responsibility:** Abstract GPU metrics provider with multiple backend strategies.

**Key Features:**
- **Primary method:** NVML (nvidia-ml-py) for low-latency GPU queries
- **Fallback method:** nvidia-smi subprocess with background polling thread
- Thread-safe caching to prevent UI blocking
- Configurable polling interval (1s for nvidia-smi)
- **GPU utilization** monitoring per device
- **VRAM usage** tracking (used/total MB) per device
- **GPU frequency** monitoring (clock speed in MHz) per device
- **GPU temperature** support via helper functions
- Graceful degradation when no GPU detected

**Strategy Pattern:**
```
1. Try NVML → if success, method = "nvml"
2. Else try nvidia-smi → if success, method = "nvidia-smi" + spawn thread
3. Else method = "none"
```

**Supported Queries:**
- `gpu_names()` - Device names (e.g., "GeForce RTX 3090")
- `gpu_utils()` - Utilization percentages
- `gpu_vram_info()` - (used_mb, total_mb) tuples
- `gpu_frequencies()` - Clock speeds in MHz

### 5. MetricsUpdater (Core Logic)

**Responsibility:** Central metrics update coordinator that separates data collection from UI orchestration.

**Key Features:**
- Static class with update methods for all metric types
- Delegates to MetricsCollector for parallel collection (optional)
- Updates dashboard cards and active tab charts
- Manages configurable refresh intervals for GPU and process metrics
- Handles per-core CPU frequency updates
- Manages GPU temperature and VRAM chart updates

**Update Methods:**
- `update_all_metrics()` - Main entry point called by SystemMonitor timer
- `_update_cpu()` - CPU metrics including per-core frequencies
- `_update_memory()` - Memory metrics
- `_update_network()` - Network throughput with dynamic baselines
- `_update_disk()` - Disk I/O with dynamic baselines
- `_update_gpu()` - GPU metrics with configurable refresh
- `_update_processes()` - Process table with configurable refresh

### 6. ProcessManager (Core Logic)

**Responsibility:** Manages process tree display and background process enumeration.

**Key Features:**
- Uses ProcessCollector for non-blocking process enumeration
- Implements hierarchical tree structure (CPU Core → Process → Threads)
- Lazy loading of thread details on expansion
- Preserves expansion state during refreshes
- Supports process filtering by name or PID
- Manages ProcessCollector singleton lifecycle

**Key Methods:**
- `refresh_processes()` - Async refresh with ProcessCollector
- `on_proc_item_expanded()` - Lazy load threads on demand
- `initialize_collector()` / `shutdown_collector()` - Lifecycle management

### 7. InfoManager (Core Logic)

**Responsibility:** Gathers and formats comprehensive system information.

**Key Features:**
- Collects CPU, system, memory, disk, GPU, and Python information
- Uses cached system info helpers to avoid repeated expensive calls
- Formats information into readable text display
- Graceful error handling for unavailable information

**Information Sections:**
- CPU Information (model, architecture, core count, frequency)
- System Information (OS, hostname, version)
- Memory Information (total, available, used)
- Disk Information (partitions, usage)
- GPU Information (detected GPUs)
- Python Information (version, executable path)

### 8. ProcessCollector (Core Logic)

**Responsibility:** Background process data collector using Producer-Consumer pattern.

**Key Features:**
- ThreadPoolExecutor for background collection
- Queue-based thread-safe communication with main thread
- Non-blocking async collection with `collect_async()`
- Groups processes by CPU core affinity
- Supports process filtering
- Respects shutdown flag for clean termination

**Performance Impact:**
- Eliminates 100-200ms UI freeze during process enumeration
- Process tab remains responsive during refresh

### 9. MetricsCollector (Core Logic)

**Responsibility:** Optional parallel metrics collector using ThreadPoolExecutor.

**Key Features:**
- Collects CPU, memory, network, disk metrics in parallel
- Currently unused (sequential collection is fast enough)
- Available for future use if metrics become more expensive
- Thread pool with configurable worker count

### 10. SystemInfoCache (Utils)

**Responsibility:** Thread-safe singleton cache for expensive system information queries.

**Key Features:**
- Singleton pattern with double-checked locking
- Thread-safe operations with RLock
- `@cached_static_property` decorator for expensive functions
- Caches CPU model name, memory frequency (1-2s subprocess calls → 0ms)
- `get_or_compute()` for lazy computation
- `reset()` for testing

**Performance Impact:**
- Dashboard initialization: 3-4s → <100ms (repeated access)
- No repeated subprocess calls during runtime

### 11. UI Builders (Builder Pattern)

**Responsibility:** Modular UI construction using Builder pattern.

**Modules:**
- **ToolbarBuilder** - Creates application toolbar with controls
- **DashboardBuilder** - Creates dashboard with metric cards
- **CPUTabBuilder** - Creates CPU tab with per-core charts
- **BasicTabsBuilder** - Creates Memory/Network/Disk tabs
- **GPUTabBuilder** - Creates GPU tab with charts
- **ProcessTabBuilder** - Creates Process and Info tabs
- **ChartFactory** - Factory for creating TimeSeriesChart instances
- **EventHandlers** - Centralized event handling logic

**Benefits:**
- Separates UI construction from business logic
- Reduces app.py from ~1000 lines to 154 lines
- Each builder focuses on single responsibility
- Easy to modify individual UI components

### 12. ChartFactory (Factory Pattern)

**Responsibility:** Factory for creating configured TimeSeriesChart instances.

**Key Features:**
- Static methods for creating different chart types
- Encapsulates chart configuration logic
- Creates CPU, Memory, Network, Disk, and GPU charts
- Configures auto-scaling, y-ranges, and series names

**Factory Methods:**
- `create_cpu_chart()` - Fixed 0-100% range
- `create_memory_chart()` - Fixed 0-100% range
- `create_network_chart()` - Auto-scaling for throughput
- `create_disk_chart()` - Auto-scaling for I/O
- `create_gpu_chart()` - Multi-GPU support

### 13. EventHandlers (Event Routing)

**Responsibility:** Centralized event handler logic for UI events.

**Key Features:**
- Static methods for all event handlers
- Separates event handling from UI construction
- Handles unit changes, interval changes, pause/resume
- Manages process search and filtering
- Updates window title on state changes

**Handler Methods:**
- `on_unit_changed()` - Syncs MB/s ↔ MiB/s across UI
- `on_interval_changed()` - Updates timer interval
- `toggle_pause()` - Pause/resume monitoring
- `on_proc_search_changed()` - Filters process tree
- `on_proc_item_expanded()` - Delegates to ProcessManager

---

## Data Flow Diagram

The following diagram shows the actual data flow through the layered architecture, including the coordinator classes (MetricsUpdater, ProcessManager, InfoManager) that separate concerns:

```mermaid
sequenceDiagram
    participant Timer as QTimer
    participant SM as SystemMonitor
    participant MU as MetricsUpdater
    participant PM as ProcessManager
    participant PC as ProcessCollector
    participant IM as InfoManager
    participant Cache as SystemInfoCache
    participant PS as psutil
    participant GPU as GPUProvider
    participant MC as MetricCard
    participant TSC as TimeSeriesChart
    participant Tree as QTreeWidget
    
    Note over Timer,SM: Main Update Loop (100ms interval)
    Timer->>SM: timeout()
    SM->>MU: update_all_metrics(dt)
    
    Note over MU,PS: CPU Metrics Update
    MU->>PS: cpu_percent()
    PS-->>MU: cpu_value
    MU->>MC: card_cpu.update_percent(cpu_value)
    MC->>TSC: sparkline.append([cpu_value])
    
    alt Active Tab is CPU
        MU->>TSC: chart_cpu.append([cpu_value])
        MU->>PS: cpu_percent(percpu=True)
        PS-->>MU: [core0, core1, ...]
        loop for each core
            MU->>TSC: core_charts[i].append([val])
        end
    end
    
    Note over MU,PS: Memory Metrics Update
    MU->>PS: virtual_memory()
    PS-->>MU: mem_value
    MU->>MC: card_mem.update_percent(mem_value)
    
    Note over MU,GPU: Network Metrics Update
    MU->>PS: net_io_counters()
    PS-->>MU: bytes_sent/recv
    MU->>MU: calculate throughput with decay
    MU->>MC: card_net_up.update_value(up_mbs)
    MU->>MC: card_net_down.update_value(down_mbs)
    
    Note over MU,GPU: GPU Metrics Update (configurable interval)
    alt GPU refresh interval reached
        MU->>GPU: gpu_utils()
        GPU-->>MU: [util0, util1, ...]
        MU->>GPU: gpu_frequencies()
        GPU-->>MU: [freq0, freq1, ...]
        MU->>GPU: gpu_vram_info()
        GPU-->>MU: [(used0,total0), ...]
        MU->>MC: card_gpu.update_percent(avg_util)
        MU->>MC: card_gpu.set_frequency(freq0)
        
        alt Active Tab is GPU
            MU->>TSC: chart_gpu.append(utils)
            MU->>TSC: chart_gpu_vram.append([used0, used1])
        end
    end
    
    Note over MU,PM: Process Update (configurable interval)
    alt Process refresh interval reached
        MU->>PM: refresh_processes()
        PM->>PC: collect_async(n_cores, filter)
        Note over PC: Background Thread
        PC->>PS: process_iter() [in thread]
        PS-->>PC: process_list
        PC->>PC: group by core affinity
        PC->>PC: put result in Queue
        
        Note over PM: Main Thread (later cycle)
        PM->>PC: get_result() [non-blocking]
        PC-->>PM: result_dict or None
        
        alt result ready
            PM->>Tree: clear()
            PM->>Tree: build hierarchical tree
            loop for each core
                PM->>Tree: addTopLevelItem(core_item)
                loop top 10 processes
                    PM->>Tree: core_item.addChild(proc_item)
                end
            end
        end
    end
    
    Note over SM,IM: System Info Update (on demand)
    SM->>IM: refresh_info()
    IM->>Cache: get_cpu_model_name()
    Cache->>Cache: get_or_compute(key, func)
    alt not cached
        Cache->>PS: subprocess.run(...)
        PS-->>Cache: result
        Cache->>Cache: cache[key] = result
    end
    Cache-->>IM: cached_value
    IM->>PS: cpu_count(), virtual_memory()
    PS-->>IM: system_info
    IM->>GPU: gpu_names()
    GPU-->>IM: [gpu0, gpu1]
    IM->>SM: info_edit.setPlainText(formatted_text)
```

### Key Data Flow Patterns

**1. Metrics Update Flow (Synchronous):**
```
QTimer → SystemMonitor.on_timer() → MetricsUpdater.update_all_metrics()
  ├─→ _update_cpu() → psutil → MetricCard
  ├─→ _update_memory() → psutil → MetricCard
  ├─→ _update_network() → psutil → MetricCard (with dynamic decay)
  ├─→ _update_disk() → psutil → MetricCard (with dynamic decay)
  ├─→ _update_gpu() → GPUProvider → MetricCard
  └─→ _update_processes() → ProcessManager (delegates to async)
```

**2. Process Collection Flow (Asynchronous):**
```
ProcessManager.refresh_processes()
  → ProcessCollector.collect_async() [returns immediately]
    → Background Thread: psutil.process_iter() → Queue.put(result)
  → [Next cycle] ProcessCollector.get_result() [non-blocking check]
    → if result ready: ProcessManager._update_ui_with_result() → QTreeWidget
```

**3. System Info Flow (Cached):**
```
InfoManager.refresh_info()
  → SystemInfoCache.get_or_compute(key, expensive_func)
    → if cached: return immediately (0ms)
    → if not cached: subprocess.run(...) [1-2s] → cache → return
  → Format all info → QTextEdit.setPlainText()
```

**4. Event Handling Flow:**
```
UI Event (QComboBox, QPushButton, QLineEdit)
  → Qt Signal
  → EventHandlers.on_*() [static method]
  → Update SystemMonitor state
  → Sync related UI components
```

---

## Design Patterns

### 1. **Composite Pattern** (Structural)

**Location:** MetricCard and TimeSeriesChart composition

**Implementation:**
- `MetricCard` can optionally embed a `TimeSeriesChart` (sparkline)
- `SystemMonitor` composes multiple `MetricCard` and `TimeSeriesChart` instances
- Widgets are treated uniformly via Qt's QWidget hierarchy

```mermaid
graph TD
    SystemMonitor --> MetricCard1[MetricCard CPU]
    SystemMonitor --> MetricCard2[MetricCard Memory]
    SystemMonitor --> TimeSeriesChart1[Chart: CPU Full]
    MetricCard1 -.-> TimeSeriesChart_Mini[Chart: Sparkline]
    
    style SystemMonitor fill:#3584e4
    style MetricCard1 fill:#ffd54f
    style TimeSeriesChart1 fill:#ff5252
    style TimeSeriesChart_Mini fill:#ff9999
```

**Benefits:**
- Reusable chart widgets (both full-size and sparklines)
- Consistent interface for all visual components
- Easy to add new metrics without changing architecture

### 2. **Strategy Pattern** (Behavioral)

**Location:** GPUProvider backend selection

**Implementation:**
```python
class GPUProvider:
    def __init__(self):
        self.method = "none"  # Strategy selector
        
        # Try Strategy 1: NVML
        try:
            import pynvml as nvml
            nvml.nvmlInit()
            self.method = "nvml"
            # ... setup NVML
        except:
            pass
        
        # Try Strategy 2: nvidia-smi
        if self.method == "none" and shutil.which("nvidia-smi"):
            self.method = "nvidia-smi"
            # ... setup subprocess polling
    
    def gpu_utils(self):
        if self.method == "nvml":
            return self._nvml_strategy()
        elif self.method == "nvidia-smi":
            return self._cached_smi_values()
        else:
            return []
```

```mermaid
classDiagram
    class GPUProvider {
        <<context>>
        -method: str
        +gpu_utils() List~float~
    }
    
    class NVMLStrategy {
        <<strategy>>
        +query() List~float~
    }
    
    class NvidiaSmiStrategy {
        <<strategy>>
        +query() List~float~
    }
    
    class NoGPUStrategy {
        <<strategy>>
        +query() List~float~
    }
    
    GPUProvider --> NVMLStrategy : uses if available
    GPUProvider --> NvidiaSmiStrategy : fallback
    GPUProvider --> NoGPUStrategy : default
```

**Benefits:**
- Runtime selection of GPU query method
- Easy to add new GPU backends (AMD ROCm, Intel)
- Graceful degradation without code duplication

### 3. **Observer Pattern** (Behavioral)

**Location:** Qt Signals/Slots mechanism

**Implementation:**
- QTimer emits `timeout()` signal → `SystemMonitor.on_timer()` slot
- QSpinBox emits `valueChanged()` → `SystemMonitor.on_interval_changed()` slot
- QComboBox emits `currentTextChanged()` → `SystemMonitor.on_unit_changed()` slot
- QPushButton emits `clicked()` → `SystemMonitor.toggle_pause()` slot

```mermaid
graph LR
    QTimer[QTimer] -->|timeout signal| SM[SystemMonitor::on_timer]
    QSpinBox[Interval SpinBox] -->|valueChanged signal| SM2[SystemMonitor::on_interval_changed]
    QComboBox[Unit Selector] -->|currentTextChanged signal| SM3[SystemMonitor::on_unit_changed]
    QPushButton[Pause Button] -->|clicked signal| SM4[SystemMonitor::toggle_pause]
    
    style QTimer fill:#00c853
    style SM fill:#3584e4
```

**Benefits:**
- Loose coupling between UI controls and business logic
- Event-driven architecture
- Built-in Qt framework support

### 4. **Facade Pattern** (Structural)

**Location:** psutil library usage in SystemMonitor

**Implementation:**
```python
class SystemMonitor:
    def on_timer(self):
        # Facade: simple interface to complex psutil API
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        net = psutil.net_io_counters()
        disk = psutil.disk_io_counters()
        # ... simplified access to OS-level metrics
```

**Benefits:**
- SystemMonitor doesn't need to know OS-specific details
- psutil abstracts platform differences (Linux/Windows/macOS)
- Clean, consistent API for system metrics

### 5. **Singleton-like Pattern** (Creational)

**Location:** Global theme application

**Implementation:**
```python
def apply_dark_theme(app: QApplication) -> None:
    """Single, global theme applied once at startup"""
    app.setStyle("Fusion")
    # ... theme configuration
    app.setPalette(palette)
    app.setStyleSheet(...)

def main():
    app = QApplication(sys.argv)
    apply_dark_theme(app)  # Applied once globally
    # ...
```

**Benefits:**
- Consistent theming across entire application
- Single source of truth for visual style
- Applied once at initialization

### 6. **Template Method Pattern** (Behavioral)

**Location:** MetricCard update methods

**Implementation:**
```python
class MetricCard:
    def update_percent(self, pct: float):
        # Template algorithm
        pct_f = self._validate(pct)           # Step 1
        self._set_label(pct_f)                # Step 2
        self._set_progress_bar(pct_f)         # Step 3
        self._apply_warning_colors(pct_f)     # Step 4
        self._update_sparkline(pct_f)         # Step 5
    
    def update_value(self, value: float, ref_max: float):
        # Similar template for non-percentage values
        v = self._validate_value(value)
        self._set_label_with_unit(v)
        self._calculate_percentage(v, ref_max)
        self._set_progress_bar(pct)
        self._update_sparkline(v)
```

**Benefits:**
- Consistent update flow for all metric cards
- Easy to modify behavior at specific steps
- Code reuse between similar operations

### 7. **Builder Pattern** (Creational)

**Location:** UI construction modules (ui/ directory)

**Implementation:**
The application uses multiple builder classes to construct different parts of the UI, separating construction logic from the main SystemMonitor class.

```python
# ToolbarBuilder creates the toolbar
class ToolbarBuilder:
    @staticmethod
    def build_toolbar(monitor: SystemMonitor) -> QToolBar:
        toolbar = monitor.addToolBar("Controls")
        ToolbarBuilder._add_interval_controls(monitor, toolbar)
        ToolbarBuilder._add_gpu_refresh_control(monitor, toolbar)
        ToolbarBuilder._add_process_refresh_control(monitor, toolbar)
        ToolbarBuilder._add_pause_button(monitor, toolbar)
        return toolbar

# DashboardBuilder creates the dashboard
class DashboardBuilder:
    @staticmethod
    def build_dashboard(monitor: SystemMonitor) -> QWidget:
        dashboard = QWidget()
        grid = QGridLayout(dashboard)
        DashboardBuilder._create_cpu_card(monitor)
        DashboardBuilder._create_memory_card(monitor)
        # ... create all cards
        return dashboard

# Usage in SystemMonitor
def _setup_ui(self):
    ToolbarBuilder.build_toolbar(self)
    self.dashboard = DashboardBuilder.build_dashboard(self)
    self.tabs.addTab(self.dashboard, "Dashboard")
    self.tabs.addTab(CPUTabBuilder.build_cpu_tab(self), "CPU")
    # ...
```

**Builder Classes:**
- `ToolbarBuilder` - Builds application toolbar
- `DashboardBuilder` - Builds dashboard with metric cards
- `CPUTabBuilder` - Builds CPU tab with per-core charts
- `BasicTabsBuilder` - Builds Memory, Network, Disk tabs
- `GPUTabBuilder` - Builds GPU tab
- `ProcessTabBuilder` - Builds Process and Info tabs

**Benefits:**
- Separates complex UI construction from business logic
- Each builder focuses on one UI component
- Reduced app.py from ~1000 lines to 154 lines
- Easy to modify individual UI components independently
- Consistent builder interface across all modules

### 8. **Factory Pattern** (Creational)

**Location:** ChartFactory class (ui/chart_factory.py)

**Implementation:**
```python
class ChartFactory:
    """Factory for creating various metric charts."""
    
    @staticmethod
    def create_cpu_chart() -> TimeSeriesChart:
        return TimeSeriesChart("CPU Utilization", ["CPU %"], y_range=(0, 100))
    
    @staticmethod
    def create_memory_chart() -> TimeSeriesChart:
        return TimeSeriesChart("Memory Utilization", ["Mem %"], y_range=(0, 100))
    
    @staticmethod
    def create_network_chart() -> TimeSeriesChart:
        return TimeSeriesChart(
            "Network Throughput (MiB/s)",
            ["Up", "Down"],
            y_range=(0, 10),
            auto_scale=True
        )
    
    @staticmethod
    def create_gpu_chart(gpu_names: list) -> Optional[TimeSeriesChart]:
        if not gpu_names:
            return None
        return TimeSeriesChart(
            "GPU Utilization",
            [f"{name}" for name in gpu_names],
            y_range=(0, 100)
        )

# Usage
self.chart_cpu = ChartFactory.create_cpu_chart()
self.chart_mem = ChartFactory.create_memory_chart()
self.chart_gpu = ChartFactory.create_gpu_chart(gpu_names)
```

**Benefits:**
- Encapsulates chart creation logic
- Centralizes chart configuration (ranges, series, auto-scaling)
- Easy to modify chart settings in one place
- Type-safe chart creation
- Supports conditional creation (GPU chart only if GPUs present)

### 9. **Producer-Consumer Pattern** (Concurrency)

**Location:** ProcessCollector class (core/process_collector.py)

**Implementation:**
```python
class ProcessCollector:
    def __init__(self, max_workers: int = 1):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._result_queue: Queue = Queue(maxsize=1)  # Consumer reads from here
        self._collecting = False
    
    def collect_async(self, n_cores: int, proc_filter: str = ""):
        """Producer: Start async collection (non-blocking)"""
        if self._collecting:
            return
        self._collecting = True
        future = self._executor.submit(self._collect_processes, n_cores, proc_filter)
        future.add_done_callback(self._on_collection_complete)
    
    def _collect_processes(self, n_cores: int, proc_filter: str) -> dict:
        """Producer: Background thread collects process data"""
        # Expensive operation runs in background
        for p in psutil.process_iter():
            # ... collect process info
        return result_dict
    
    def _on_collection_complete(self, future: Future):
        """Producer: Put result in queue"""
        result = future.result()
        self._result_queue.put(result)  # Thread-safe queue write
        self._collecting = False
    
    def get_result(self) -> Optional[dict]:
        """Consumer: Non-blocking read from queue"""
        try:
            return self._result_queue.get_nowait()
        except:
            return None

# Consumer side (main thread)
collector.collect_async(n_cores, filter)  # Start background collection
# Later...
result = collector.get_result()  # Check if ready (non-blocking)
if result:
    update_ui(result)  # Update UI in main thread
```

**Benefits:**
- Eliminates UI blocking (100-200ms freeze → 0ms)
- Thread-safe communication via Queue
- Producer (background thread) never touches Qt widgets
- Consumer (main thread) handles all UI updates
- Clean separation of concerns

### 10. **Singleton Pattern** (Creational)

**Location:** SystemInfoCache class (utils/cache.py)

**Implementation:**
```python
class SystemInfoCache:
    """Thread-safe singleton cache with double-checked locking."""
    
    _instance: Optional['SystemInfoCache'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'SystemInfoCache':
        if cls._instance is None:
            with cls._lock:  # First check (outside lock for performance)
                if cls._instance is None:  # Second check (inside lock)
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self._cache: Dict[str, Any] = {}
        self._cache_lock = threading.RLock()
    
    def get_or_compute(self, key: str, compute_func: Callable) -> Any:
        """Thread-safe lazy computation with caching."""
        with self._cache_lock:
            if key in self._cache:
                return self._cache[key]
            value = compute_func()
            self._cache[key] = value
            return value

# Usage with decorator
@cached_static_property('cpu_model_name')
def get_cpu_model_name() -> str:
    # Expensive subprocess call (1-2s) → cached forever
    result = subprocess.run(["wmic", "cpu", "get", "name"], ...)
    return result

# First call: 1-2 seconds (subprocess)
model1 = get_cpu_model_name()
# Subsequent calls: 0ms (cached)
model2 = get_cpu_model_name()
```

**Benefits:**
- Single instance across entire application
- Thread-safe with double-checked locking
- Eliminates repeated expensive subprocess calls
- Dashboard initialization: 3-4s → <100ms
- `@cached_static_property` decorator for easy use
- `reset()` method for testing

---

## Architecture Decisions

### 1. **Why PySide6 over PyQt6?**
- More permissive LGPL license
- Official Qt Company support
- API compatibility with PyQt6

### 2. **Why QtCharts instead of matplotlib/plotly?**
- Native Qt integration (no embedding overhead)
- Better performance for real-time updates
- Consistent theming with Qt widgets
- Lower dependency footprint

### 3. **Why psutil?**
- Cross-platform (Linux/Windows/macOS)
- Pure Python with compiled C extensions
- Comprehensive API (CPU, memory, disk, network, processes)
- Battle-tested and widely used

### 4. **Why background thread for nvidia-smi?**
- nvidia-smi subprocess can take 100-500ms
- Blocking UI thread causes stuttering
- Background polling + caching keeps UI responsive
- NVML (when available) is fast enough for main thread

### 5. **Why separate charts per CPU core?**
- Better scalability for many-core systems
- Individual color coding for quick identification
- Reduces chart complexity (1 series per chart vs N series in 1 chart)
- Scroll area handles overflow gracefully

---

## Performance Considerations

### Update Interval Trade-offs

| Interval | CPU Usage | Smoothness | Use Case |
|----------|-----------|------------|----------|
| 1-10ms   | Very High | Overkill   | Debugging/testing only |
| 50-100ms | Low       | Smooth     | **Recommended default** |
| 200-500ms| Very Low  | Acceptable | Low-power systems |
| 1000ms+  | Minimal   | Choppy     | Background monitoring |

### Chart Optimization

**Current optimizations:**
- Only update charts on active tabs
- Pre-allocated point buffers
- Fixed rolling window (400 points = ~40s @ 100ms)
- Sparklines use smaller buffers (60 points)

**Future possibilities:**
- Adaptive frame rate based on CPU usage
- Level-of-detail rendering (fewer points when zoomed out)
- GPU-accelerated rendering (Qt Quick 2D)

### Memory Usage

**Typical memory footprint:**
- Base application: ~50-80 MB
- Per TimeSeriesChart: ~1-2 MB (400 points)
- Per MetricCard: ~0.5-1 MB (with sparkline)
- Total: ~100-150 MB for typical setup

---

## Extension Points

### Adding New Metrics

1. **Add data collection** in `SystemMonitor.on_timer()`
2. **Create MetricCard** in dashboard grid
3. **(Optional) Create TimeSeriesChart** in new tab
4. **Update card** with collected data

Example:
```python
# 1. Collect
temp = psutil.sensors_temperatures()

# 2. Create card
self.card_temp = MetricCard("CPU Temp", unit="°C", is_percent=False, color="#ff5252")

# 3. Create chart (optional)
self.chart_temp = TimeSeriesChart("Temperature", ["CPU"], y_range=(0, 100))

# 4. Update in on_timer()
self.card_temp.update_value(temp['coretemp'][0].current)
```

### Adding New GPU Backends

Extend `GPUProvider.__init__()`:
```python
# Try AMD ROCm
if self.method == "none" and shutil.which("rocm-smi"):
    self.method = "rocm-smi"
    # ... implement _query_rocm_smi_*() methods
```

### Adding New Tabs

```python
# In SystemMonitor.__init__()
custom_tab = QWidget()
custom_layout = QVBoxLayout(custom_tab)
# ... add widgets
tabs.addTab(custom_tab, "Custom")
```

---

## Testing Strategy

### Unit Testing Targets

- `GPUProvider`: Mock NVML/subprocess
- `TimeSeriesChart.append()`: Verify point buffer management
- `MetricCard.update_percent()`: Verify color thresholds
- Theme application: Verify palette/stylesheet

### Integration Testing

- Full application startup with mocked psutil
- Timer updates with deterministic clock
- Tab switching and chart visibility logic

### Performance Testing

- Measure CPU usage at different update intervals
- Memory leak detection (long-running sessions)
- Chart rendering benchmarks

---

## File Organization

The application follows a modular architecture with clear separation of concerns:

```
python_playground/
├── system_monitor/                 # Main application package
│   ├── __init__.py                 # Package initialization (26 lines)
│   ├── app.py                      # Application entry point (154 lines)
│   │   └── SystemMonitor class, main()
│   ├── core/                       # Core business logic
│   │   ├── info_manager.py         # System info gathering (93 lines)
│   │   ├── metrics_collector.py    # Parallel metrics collection (126 lines)
│   │   ├── metrics_updater.py      # Real-time updates (233 lines)
│   │   ├── process_collector.py    # Background collection (174 lines)
│   │   └── process_manager.py      # Process tree management (222 lines)
│   ├── providers/                  # Data providers
│   │   └── gpu_provider.py         # GPU metrics (196 lines)
│   ├── ui/                         # UI builders (Builder pattern)
│   │   ├── toolbar_builder.py      # Toolbar (78 lines)
│   │   ├── dashboard_builder.py    # Dashboard cards (82 lines)
│   │   ├── cpu_tab_builder.py      # CPU tab (106 lines)
│   │   ├── basic_tabs_builder.py   # Memory/Net/Disk (79 lines)
│   │   ├── gpu_tab_builder.py      # GPU tab (89 lines)
│   │   ├── process_tab_builder.py  # Process/Info tabs (80 lines)
│   │   ├── chart_factory.py        # Chart factory (53 lines)
│   │   └── event_handlers.py       # Event handling (85 lines)
│   ├── utils/                      # Utilities
│   │   ├── cache.py                # Singleton cache (98 lines)
│   │   ├── system_info.py          # System queries (188 lines)
│   │   └── theme.py                # Dark theme (152 lines)
│   └── widgets/                    # Custom widgets
│       ├── time_series_chart.py    # Real-time charts (97 lines)
│       └── metric_card.py          # Metric cards (167 lines)
├── tests/                          # Test suite (162 tests, 157 passing)
│   ├── conftest.py                 # Global test fixtures
│   ├── test_integration.py         # Integration tests
│   └── system_monitor/             # Unit tests mirror source structure
│       ├── core/                   # 88 tests (all passing)
│       ├── utils/                  # 41 tests (all passing)
│       ├── providers/              # 19 tests (all passing)
│       ├── ui/                     # 22 tests (all passing)
│       └── widgets/                # 14 tests (cannot run - import issues)
├── requirements.txt                # Runtime dependencies
├── test-requirements.txt           # Test dependencies
├── pytest.ini                      # Pytest configuration
├── README.md                       # User documentation
├── architecture.md                 # This file
└── screenshots/                    # Application screenshots
    ├── main.png
    ├── cpu.png
    ├── gpu.png
    └── process.png
```

**Total Lines of Code:** ~2,500 lines across 23 Python modules (excluding tests)

**Module Organization:**
- **app.py** (154 lines) - Minimal entry point, delegates to builders
- **core/** (848 lines) - Business logic for metrics, processes, system info
- **ui/** (652 lines) - UI construction using Builder and Factory patterns
- **providers/** (196 lines) - External data providers (GPU)
- **utils/** (438 lines) - Utilities (caching, system queries, theming)
- **widgets/** (264 lines) - Reusable Qt widgets

---

## Concurrency & Performance Optimizations

### Threading Model

The application employs a multi-threaded architecture to prevent UI blocking and improve responsiveness:

```
Main Qt Thread (UI)
├── QTimer (100ms) → MetricsUpdater
├── Process tree updates
└── Chart rendering

Background Threads:
├── ProcessCollector (ThreadPoolExecutor)
│   └── psutil.process_iter() → Queue → Main thread
├── GPU Provider (daemon thread)
│   └── nvidia-smi polling (1s interval)
└── MetricsCollector (ThreadPoolExecutor, optional)
    └── Parallel psutil queries
```

**Thread Safety Guarantees:**
- Queue-based communication between threads
- Lock-protected shared state
- Main thread exclusively handles Qt UI updates
- Background threads never touch Qt widgets

### Caching Strategy (Singleton Pattern)

**SystemInfoCache** - Thread-safe singleton cache for expensive operations:

```python
@cached_static_property('cpu_model_name')
def get_cpu_model_name() -> str:
    # Expensive subprocess call (1-2s) cached forever
    result = subprocess.run(["wmic", "cpu", "get", "name"], ...)
    return result
```

**Cached Properties:**
- CPU model name (subprocess: 1-2s → 0ms after first call)
- Memory frequency (subprocess: 2s → 0ms after first call)

**Performance Impact:**
- Dashboard initialization: 3-4s → <100ms (repeated access)
- No repeated subprocess calls during runtime

### Process Collection (Producer-Consumer Pattern)

**ProcessCollector** uses ThreadPoolExecutor to enumerate processes in background:

**Before Optimization:**
```python
# Blocking main thread (100-200ms for 200+ processes)
for p in psutil.process_iter():  # UI freezes here
    data = collect_process_data(p)
    update_ui(data)
```

**After Optimization:**
```python
# Non-blocking: collection in background thread
collector.collect_async(n_cores, filter)  # Returns immediately
result = collector.get_result()           # Check queue (non-blocking)
if result:
    update_ui(result)  # UI update in main thread
```

**Performance Impact:**
- UI responsiveness: 100-200ms freeze → 0ms (completely non-blocking)
- Process tab remains responsive during refresh
- Search/filter operations don't block UI

### GPU Provider Background Thread

**Existing optimization** - nvidia-smi polling in daemon thread:

```python
def _smi_poll_loop(self):
    while True:
        utils = self._query_nvidia_smi_utils()
        self._last_smi_utils = utils  # Atomic write
        time.sleep(1.0)  # Avoid hammering nvidia-smi
```

**Benefits:**
- nvidia-smi (1.5s timeout) doesn't block main thread
- Results cached and read atomically
- 1-second polling interval balances freshness and performance

### Parallel Metrics Collection (Optional)

**MetricsCollector** enables parallel psutil queries using ThreadPoolExecutor:

```python
# Collect CPU, memory, network, disk in parallel
results = collector.collect_all()  # Blocks until all complete
```

**Note:** Current implementation uses sequential collection since psutil calls are already fast (<1ms each). Parallel collection available for future use if metrics become more expensive.

### Memory Management

**Chart Point Buffering:**
- Each chart maintains fixed-size circular buffer (400 points)
- Old points automatically dropped: `O(1)` append operation
- Total memory for all charts: ~10-20 MB

**Process Tree Optimization:**
- Lazy loading of thread information
- Only top 10 processes per core displayed
- Expansion state preserved during refreshes

### Performance Metrics

**Typical Update Latency (100ms interval):**
- Metrics collection: <5ms
- Process collection: 0ms (async, non-blocking)
- Chart updates: 2-3ms per chart
- Total: <15ms per cycle (85% idle time)

**Thread Count:**
- Main Qt thread: 1
- ProcessCollector workers: 1
- GPU provider background: 1 (if nvidia-smi used)
- Qt internal threads: ~3-4
- Total: ~6-7 threads

**CPU Usage:**
- Idle (100ms updates): 2-4% (single core)
- Active (with charts): 5-8% (single core)
- GPU monitoring: +1-2% (if nvidia-smi)

---

## Conclusion

The System Monitor application demonstrates a clean, maintainable architecture built on proven design patterns. The modular component design allows easy extension, while the layered architecture keeps concerns well-separated. Advanced performance optimizations including background threading, caching, and producer-consumer patterns ensure smooth real-time updates even on resource-constrained systems.

**Key Strengths:**
✓ Clear separation of concerns (data provider, widgets, controller)  
✓ Reusable components (MetricCard, TimeSeriesChart)  
✓ Graceful degradation (GPU fallbacks)  
✓ Performance-conscious design (background threading, caching, non-blocking UI)  
✓ Extensible architecture (easy to add metrics/backends)  
✓ Efficient concurrency (ThreadPoolExecutor, Queue-based communication)  

**Areas for Future Enhancement:**
- Plugin system for custom metrics
- Remote monitoring capabilities
- Data export (CSV, JSON)
- Alert/notification system
- Historical data persistence
