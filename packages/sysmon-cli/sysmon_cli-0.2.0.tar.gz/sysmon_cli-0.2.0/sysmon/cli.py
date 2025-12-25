#!/usr/bin/env python3
"""
sysmon - A system monitoring tool similar to gpustat
Displays GPU, CPU, Memory, and Disk information in real-time
"""

import subprocess
import os
import sys
import time
import re
import curses
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# ANSI color codes for non-curses output
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'


def get_gpu_info() -> List[dict]:
    """Get GPU information using nvidia-smi"""
    gpus = []

    # First, get all GPU indices from -L output
    try:
        result = subprocess.run(
            ['nvidia-smi', '-L'],
            capture_output=True, text=True, timeout=5
        )

        gpu_indices = []
        full_output = result.stdout + result.stderr

        for line in full_output.strip().split('\n'):
            if line.strip():
                # Try to match "GPU X: ..." format
                match = re.match(r'GPU (\d+):', line.strip())
                if match:
                    gpu_indices.append(int(match.group(1)))
                # Also check for error messages that might indicate GPU 0
                elif 'Unable to determine the device handle' in line and 'gpu' in line.lower():
                    # Try to extract GPU index from PCI address or assume 0
                    # Format: "Unable to determine the device handle for gpu 0000:4F:00.0"
                    # This doesn't give us the index directly, but we can assume it's 0
                    # if we see errors and then GPUs starting from 1
                    if 0 not in gpu_indices:
                        gpu_indices.append(0)

        # If we found GPUs, determine the full range
        if gpu_indices:
            min_idx = min(gpu_indices)
            max_idx = max(gpu_indices)
            # Create a complete list from 0 to max
            all_indices = list(range(min_idx, max_idx + 1))
        else:
            return []
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return []

    # Query each GPU individually
    for idx in all_indices:
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,temperature.gpu,utilization.gpu,memory.used,memory.total',
                 '--format=csv,noheader,nounits', '-i', str(idx)],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                line = result.stdout.strip()
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 5:
                    def parse_int(val):
                        try:
                            return int(val)
                        except (ValueError, TypeError):
                            return None

                    gpus.append({
                        'index': int(parts[0]),
                        'temp': parse_int(parts[1]),
                        'util': parse_int(parts[2]),
                        'mem_used': parse_int(parts[3]),
                        'mem_total': parse_int(parts[4]),
                        'processes': [],
                        'error': None
                    })
            else:
                # GPU query failed
                gpus.append({
                    'index': idx,
                    'temp': None,
                    'util': None,
                    'mem_used': None,
                    'mem_total': None,
                    'processes': [],
                    'error': 'Not Supported'
                })
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            gpus.append({
                'index': idx,
                'temp': None,
                'util': None,
                'mem_used': None,
                'mem_total': None,
                'processes': [],
                'error': 'Not Supported'
            })

    return gpus


def get_gpu_processes() -> Dict[int, List[dict]]:
    """Get processes running on each GPU"""
    processes = defaultdict(list)

    # Get all GPU indices first
    try:
        result = subprocess.run(
            ['nvidia-smi', '-L'],
            capture_output=True, text=True, timeout=5
        )

        gpu_indices = []
        full_output = result.stdout + result.stderr

        for line in full_output.strip().split('\n'):
            if line.strip():
                match = re.match(r'GPU (\d+):', line.strip())
                if match:
                    gpu_indices.append(int(match.group(1)))
                elif 'Unable to determine the device handle' in line and 'gpu' in line.lower():
                    if 0 not in gpu_indices:
                        gpu_indices.append(0)

        if not gpu_indices:
            return {}
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return {}

    # Query processes for each GPU individually
    for idx in gpu_indices:
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_memory',
                 '--format=csv,noheader,nounits', '-i', str(idx)],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if not line.strip():
                        continue
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 3:
                        pid = parts[1]
                        mem = parts[2]

                        # Get username from pid
                        try:
                            user_result = subprocess.run(
                                ['ps', '-o', 'user=', '-p', pid],
                                capture_output=True, text=True, timeout=2
                            )
                            username = user_result.stdout.strip() or 'unknown'
                            # Truncate long usernames
                            if len(username) > 8:
                                username = username[:8]
                        except:
                            username = 'unknown'

                        processes[idx].append({
                            'pid': pid,
                            'user': username,
                            'mem': int(mem) if mem.isdigit() else 0
                        })
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

    return processes


def get_cpu_info() -> Tuple[float, int, int]:
    """Get CPU usage and memory info"""
    # CPU usage
    try:
        with open('/proc/stat', 'r') as f:
            line = f.readline()
        parts = line.split()[1:]
        idle = int(parts[3])
        total = sum(int(p) for p in parts[:8])
        
        time.sleep(0.1)
        
        with open('/proc/stat', 'r') as f:
            line = f.readline()
        parts = line.split()[1:]
        idle2 = int(parts[3])
        total2 = sum(int(p) for p in parts[:8])
        
        cpu_percent = 100 * (1 - (idle2 - idle) / max(1, total2 - total))
    except:
        cpu_percent = 0.0
    
    # Memory info
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        
        mem_total = int(re.search(r'MemTotal:\s+(\d+)', meminfo).group(1)) // 1024  # MB
        mem_avail = int(re.search(r'MemAvailable:\s+(\d+)', meminfo).group(1)) // 1024  # MB
        mem_used = mem_total - mem_avail
    except:
        mem_total, mem_used = 0, 0
    
    return cpu_percent, mem_used, mem_total


def get_disk_info() -> List[dict]:
    """Get disk information for partitions > 1TB"""
    disks = []
    try:
        # Get disk usage
        result = subprocess.run(['df', '-B1'], capture_output=True, text=True, timeout=5)

        for line in result.stdout.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 6:
                device = parts[0]
                total = int(parts[1])
                used = int(parts[2])
                available = int(parts[3])
                # Parse percentage directly from df (e.g., "61%")
                use_pct_str = parts[4].rstrip('%')
                try:
                    use_pct = int(use_pct_str)
                except ValueError:
                    use_pct = 100 * used // max(1, used + available)
                mount = parts[5]

                # Filter: > 1TB and real filesystems
                if total > 1e12 and not mount.startswith('/boot') and not mount.startswith('/snap'):
                    disks.append({
                        'device': device,
                        'mount': mount,
                        'used': used,
                        'total': total,
                        'use_pct': use_pct,
                        'read_speed': 0,
                        'write_speed': 0
                    })
    except:
        pass
    
    # Get disk I/O stats
    try:
        with open('/proc/diskstats', 'r') as f:
            diskstats1 = f.read()
        time.sleep(0.1)
        with open('/proc/diskstats', 'r') as f:
            diskstats2 = f.read()
        
        def parse_diskstats(content):
            stats = {}
            for line in content.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 14:
                    dev = parts[2]
                    # sectors read (field 6) and written (field 10), sector = 512 bytes
                    stats[dev] = {
                        'read': int(parts[5]) * 512,
                        'write': int(parts[9]) * 512
                    }
            return stats
        
        stats1 = parse_diskstats(diskstats1)
        stats2 = parse_diskstats(diskstats2)
        
        for disk in disks:
            # Extract device name from path
            dev = disk['device'].split('/')[-1]
            # Try with and without partition number
            base_dev = re.sub(r'\d+$', '', dev)
            
            for d in [dev, base_dev]:
                if d in stats1 and d in stats2:
                    disk['read_speed'] = (stats2[d]['read'] - stats1[d]['read']) * 10  # per second
                    disk['write_speed'] = (stats2[d]['write'] - stats1[d]['write']) * 10
                    break
    except:
        pass
    
    return disks


def aggregate_user_processes(processes: List[dict]) -> List[dict]:
    """Aggregate processes by user: user(count, total_mem)"""
    user_stats = defaultdict(lambda: {'count': 0, 'mem': 0})
    for proc in processes:
        user = proc['user']
        user_stats[user]['count'] += 1
        user_stats[user]['mem'] += proc['mem']

    result = []
    for user, stats in user_stats.items():
        result.append({
            'user': user,
            'count': stats['count'],
            'mem': stats['mem']
        })
    return result


def format_size(bytes_val: int, precision: int = 0) -> str:
    """Format bytes to human readable (1024-based, like df -h)"""
    TiB = 1024 ** 4
    GiB = 1024 ** 3
    MiB = 1024 ** 2
    KiB = 1024
    if bytes_val >= TiB:
        return f"{bytes_val/TiB:.{precision}f}T"
    elif bytes_val >= GiB:
        return f"{bytes_val/GiB:.{precision}f}G"
    elif bytes_val >= MiB:
        return f"{bytes_val/MiB:.{precision}f}M"
    elif bytes_val >= KiB:
        return f"{bytes_val/KiB:.{precision}f}K"
    return f"{bytes_val}B"


def format_speed(bytes_per_sec: int) -> str:
    """Format speed"""
    if bytes_per_sec >= 1e9:
        return f"{bytes_per_sec/1e9:.1f}G/s"
    elif bytes_per_sec >= 1e6:
        return f"{bytes_per_sec/1e6:.1f}M/s"
    elif bytes_per_sec >= 1e3:
        return f"{bytes_per_sec/1e3:.1f}K/s"
    return f"{bytes_per_sec}B/s"


def get_temp_color(temp: int) -> str:
    """Get color based on temperature"""
    if temp >= 85:
        return Colors.RED
    elif temp >= 75:
        return Colors.YELLOW
    elif temp >= 60:
        return Colors.GREEN
    return Colors.CYAN


def get_util_color(util: int) -> str:
    """Get color based on utilization"""
    if util >= 90:
        return Colors.RED
    elif util >= 70:
        return Colors.YELLOW
    elif util >= 30:
        return Colors.GREEN
    return Colors.CYAN


def print_static(show_processes: bool = True, terminal_width: int = None):
    """Print static output (non-interactive)"""
    # Get terminal width
    if terminal_width is None:
        try:
            terminal_width = os.get_terminal_size().columns
        except:
            terminal_width = 120

    # GPU info
    gpus = get_gpu_info()
    processes = get_gpu_processes() if show_processes else {}

    print(f"{Colors.BOLD}=== GPU ==={Colors.RESET}")
    for gpu in gpus:
        idx = gpu['index']
        temp = gpu['temp']
        util = gpu['util']
        mem_used = gpu['mem_used']
        mem_total = gpu['mem_total']
        error = gpu.get('error')

        # Handle None values (driver issues)
        if temp is None or error:
            temp_str = f"  ?°C"
            temp_color = Colors.RESET
        else:
            temp_color = get_temp_color(temp)
            temp_str = f"{temp:3d}°C"

        if util is None or error:
            util_str = f"  ? %"
            util_color = Colors.RESET
        else:
            util_color = get_util_color(util)
            util_str = f"{util:3d} %"

        if mem_used is None or mem_total is None or error:
            mem_str = "    ? /     ? MB"
        else:
            mem_str = f"{mem_used:5d} / {mem_total:5d} MB"

        # Base line
        base_line = f"[{idx}] {temp_color}{temp_str}{Colors.RESET}, {util_color}{util_str}{Colors.RESET} | {mem_str}"

        # Handle processes
        if error:
            print(f"{base_line} | ({error})")
        elif show_processes and idx in processes:
            procs = processes[idx]
            # Aggregate by user
            aggregated = aggregate_user_processes(procs)
            proc_strs = []
            for p in aggregated:
                if p['count'] > 1:
                    proc_strs.append(f"{p['user']}({p['count']},{p['mem']}M)")
                else:
                    proc_strs.append(f"{p['user']}({p['mem']}M)")

            if proc_strs:
                # Calculate base line length (without ANSI codes)
                base_len = len(f"[{idx}] {temp_str}, {util_str} | {mem_str}")
                available_width = terminal_width - base_len - 3  # " | " takes 3 chars

                # Build process string, wrapping to new lines if needed
                current_line = base_line + " |"
                lines = []
                for i, proc_str in enumerate(proc_strs):
                    # +1 for space before proc_str
                    if len(current_line) + 1 + len(proc_str) <= terminal_width:
                        current_line += " " + proc_str
                    else:
                        lines.append(current_line)
                        # Indent continuation lines
                        indent = " " * (base_len + 3)
                        current_line = indent + proc_str
                lines.append(current_line)

                for line in lines:
                    print(line)
            else:
                print(base_line)
        else:
            print(base_line)
    # CPU & Memory
    cpu_percent, mem_used, mem_total = get_cpu_info()
    print(f"{Colors.BOLD}=== CPU & Memory ==={Colors.RESET}")
    cpu_color = get_util_color(int(cpu_percent))
    mem_used_g = mem_used / 1024
    mem_total_g = mem_total / 1024
    print(f"CPU: {cpu_color}{cpu_percent:5.1f} %{Colors.RESET}  |  Memory: {mem_used_g:.1f}G / {mem_total_g:.1f}G ({100*mem_used/max(1,mem_total):.1f}%)")
    # Disk
    disks = get_disk_info()
    if disks:
        print(f"{Colors.BOLD}=== Disk (>1TB) ==={Colors.RESET}")
        for disk in disks:
            used_pct = disk.get('use_pct', 100 * disk['used'] // max(1, disk['total']))
            used_color = Colors.RED if used_pct > 90 else (Colors.YELLOW if used_pct > 75 else Colors.GREEN)
            mount = disk['mount'][:8] if len(disk['mount']) > 8 else disk['mount']
            print(f"{mount:<8} {used_color}{format_size(disk['used'], 1)}{Colors.RESET}/{format_size(disk['total'], 1)}({used_pct}%) R:{format_speed(disk['read_speed'])} W:{format_speed(disk['write_speed'])}")


def interactive_mode(stdscr, refresh_interval=1.0, show_processes_init=False):
    """Interactive mode with curses"""
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()

    # Define color pairs
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_WHITE, -1)

    show_processes = show_processes_init
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        row = 0
        
        # Header
        header = f" sysmon - System Monitor (Press 'g' to toggle GPU processes, 'q' to quit) "
        stdscr.addstr(row, 0, header[:width-1], curses.A_REVERSE)
        row += 1
        
        # GPU section
        gpus = get_gpu_info()
        processes = get_gpu_processes() if show_processes else {}
        
        stdscr.addstr(row, 0, "=== GPU ===", curses.A_BOLD)
        row += 1
        
        for gpu in gpus:
            if row >= height - 1:
                break

            idx = gpu['index']
            temp = gpu['temp']
            util = gpu['util']
            mem_used = gpu['mem_used']
            mem_total = gpu['mem_total']
            error = gpu.get('error')

            # Handle None values (driver issues)
            if temp is None or error:
                temp_str = "  ?°C"
                temp_color = 5  # WHITE
            else:
                temp_color = 1 if temp >= 85 else (2 if temp >= 75 else (3 if temp >= 60 else 4))
                temp_str = f"{temp:3d}°C"

            if util is None or error:
                util_str = "  ? %"
                util_color = 5  # WHITE
            else:
                util_color = 1 if util >= 90 else (2 if util >= 70 else (3 if util >= 30 else 4))
                util_str = f"{util:3d} %"

            if mem_used is None or mem_total is None or error:
                mem_str = "    ? /     ? MB"
            else:
                mem_str = f"{mem_used:5d} / {mem_total:5d} MB"

            col = 0
            stdscr.addstr(row, col, f"[{idx}] ")
            col += 4
            stdscr.addstr(row, col, temp_str, curses.color_pair(temp_color))
            col += 5
            stdscr.addstr(row, col, ", ")
            col += 2
            stdscr.addstr(row, col, util_str, curses.color_pair(util_color))
            col += 5
            stdscr.addstr(row, col, f" | {mem_str}")
            col += 22
            base_col = col

            # Add processes if enabled
            if error:
                stdscr.addstr(row, col, f" | ({error})")
                row += 1
            elif show_processes and idx in processes:
                procs = processes[idx]
                # Aggregate by user
                aggregated = aggregate_user_processes(procs)
                proc_strs = []
                for p in aggregated:
                    if p['count'] > 1:
                        proc_strs.append(f"{p['user']}({p['count']},{p['mem']}M)")
                    else:
                        proc_strs.append(f"{p['user']}({p['mem']}M)")

                if proc_strs:
                    stdscr.addstr(row, col, " |")
                    col += 2
                    for proc_str in proc_strs:
                        if col + 1 + len(proc_str) < width:
                            stdscr.addstr(row, col, " " + proc_str)
                            col += 1 + len(proc_str)
                        else:
                            # Wrap to next line
                            row += 1
                            if row >= height - 1:
                                break
                            col = base_col + 2
                            indent = " " * base_col
                            stdscr.addstr(row, 0, indent)
                            stdscr.addstr(row, col, " " + proc_str)
                            col += 1 + len(proc_str)
                row += 1
            else:
                row += 1
        
        # CPU & Memory section
        if row < height - 3:
            cpu_percent, mem_used, mem_total = get_cpu_info()
            
            stdscr.addstr(row, 0, "=== CPU & Memory ===", curses.A_BOLD)
            row += 1
            
            cpu_color = 1 if cpu_percent >= 90 else (2 if cpu_percent >= 70 else (3 if cpu_percent >= 30 else 4))
            mem_used_g = mem_used / 1024
            mem_total_g = mem_total / 1024
            mem_pct = 100 * mem_used / max(1, mem_total)
            mem_color = 1 if mem_pct >= 90 else (2 if mem_pct >= 75 else 3)
            
            col = 0
            stdscr.addstr(row, col, "CPU: ")
            col += 5
            stdscr.addstr(row, col, f"{cpu_percent:5.1f} %", curses.color_pair(cpu_color))
            col += 8
            stdscr.addstr(row, col, f"  |  Memory: ")
            col += 12
            stdscr.addstr(row, col, f"{mem_used_g:.1f}G", curses.color_pair(mem_color))
            col += 7
            stdscr.addstr(row, col, f" / {mem_total_g:.1f}G ({mem_pct:.1f}%)")
            row += 1
        
        # Disk section
        if row < height - 2:
            disks = get_disk_info()
            if disks:
                stdscr.addstr(row, 0, "=== Disk (>1TB) ===", curses.A_BOLD)
                row += 1
                
                for disk in disks:
                    if row >= height - 1:
                        break
                    
                    used_pct = disk.get('use_pct', 100 * disk['used'] // max(1, disk['total']))
                    used_color = 1 if used_pct > 90 else (2 if used_pct > 75 else 3)
                    
                    mount = disk['mount'][:8] if len(disk['mount']) > 8 else disk['mount']
                    
                    col = 0
                    stdscr.addstr(row, col, f"{mount:<8} ")
                    col += 9
                    stdscr.addstr(row, col, f"{format_size(disk['used'], 1)}", curses.color_pair(used_color))
                    col += len(format_size(disk['used'], 1))
                    stdscr.addstr(row, col, f"/{format_size(disk['total'], 1)}({used_pct}%) R:{format_speed(disk['read_speed'])} W:{format_speed(disk['write_speed'])}")
                    row += 1
        
        stdscr.refresh()
        
        # Handle input
        start_time = time.time()
        while time.time() - start_time < refresh_interval:
            try:
                key = stdscr.getch()
                if key == ord('q') or key == ord('Q'):
                    return
                elif key == ord('g') or key == ord('G'):
                    show_processes = not show_processes
                    break
            except:
                pass
            time.sleep(0.05)


def main():
    import argparse
    from functools import partial

    parser = argparse.ArgumentParser(description='System Monitor - GPU, CPU, Memory, Disk')
    parser.add_argument('-w', '--watch', action='store_true', help='Interactive watch mode (like top)')
    parser.add_argument('-i', '--interval', type=float, default=None, help='Refresh interval in seconds (implies -w)')
    parser.add_argument('-g', '--gpu-processes', action='store_true', help='Show GPU processes')
    parser.add_argument('--no-color', action='store_true', help='Disable colors')

    args = parser.parse_args()

    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')

    # -i implies -w (watch mode)
    if args.watch or args.interval is not None:
        interval = args.interval if args.interval is not None else 1.0
        try:
            curses.wrapper(partial(interactive_mode,
                                   refresh_interval=interval,
                                   show_processes_init=args.gpu_processes))
        except KeyboardInterrupt:
            pass
    else:
        print_static(show_processes=args.gpu_processes)


if __name__ == '__main__':
    main()
