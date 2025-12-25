# sysmon

System Monitor - displays GPU, CPU, Memory, and Disk status (similar to gpustat).

## Installation

```bash
pip install .
```

Or install in development mode:
```bash
pip install -e .
```

## Usage

```bash
# One-time display
sysmon

# Show GPU processes
sysmon -g

# Watch mode (auto-refresh)
sysmon -w

# Watch mode with custom interval
sysmon -i 2

# Combine options
sysmon -i 2 -g
```

## Options

- `-w, --watch`: Interactive watch mode (like top)
- `-i, --interval`: Refresh interval in seconds (implies -w)
- `-g, --gpu-processes`: Show GPU processes
- `--no-color`: Disable colors

## Features

- GPU temperature, utilization, memory usage
- GPU process tracking with user aggregation
- CPU and memory usage
- Disk partition usage (>1TB partitions)
- Handles GPU driver errors gracefully
