#!/usr/bin/env python3
"""
htop-style system monitor using sparkback braille line graphs with color support.

Displays real-time CPU, memory, and network statistics using high-resolution
braille sparklines with color gradients.

Requires: psutil (uv add psutil)
"""

import sys
import time

import psutil

# Add parent directory to path for development
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from sparkback.spark import (
    BrailleLineGraphStyle,
    apply_color_to_output,
    ANSI_RESET,
)

# ANSI escape codes
CLEAR_SCREEN = "\033[2J"
CURSOR_HOME = "\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
WHITE = "\033[37m"

# History length for graphs
HISTORY_LEN = 60


class SystemMonitor:
    """Collects and stores system statistics history."""

    def __init__(self):
        self.cpu_count = psutil.cpu_count()
        self.cpu_histories = [[] for _ in range(self.cpu_count)]
        self.mem_history = []
        self.swap_history = []
        self.net_in_history = []
        self.net_out_history = []
        self.last_net = psutil.net_io_counters()
        self.last_time = time.time()

    def update(self):
        """Collect current system stats and update histories."""
        # CPU per-core
        cpu_percents = psutil.cpu_percent(percpu=True)
        for i, pct in enumerate(cpu_percents):
            self.cpu_histories[i].append(pct)
            self.cpu_histories[i] = self.cpu_histories[i][-HISTORY_LEN:]

        # Memory
        mem = psutil.virtual_memory()
        self.mem_history.append(mem.percent)
        self.mem_history = self.mem_history[-HISTORY_LEN:]

        # Swap
        swap = psutil.swap_memory()
        self.swap_history.append(swap.percent)
        self.swap_history = self.swap_history[-HISTORY_LEN:]

        # Network (bytes per second)
        now = time.time()
        elapsed = now - self.last_time
        net = psutil.net_io_counters()

        if elapsed > 0:
            bytes_in = (net.bytes_recv - self.last_net.bytes_recv) / elapsed
            bytes_out = (net.bytes_sent - self.last_net.bytes_sent) / elapsed
            # Convert to MB/s, cap at reasonable display range
            mb_in = min(bytes_in / 1024 / 1024, 1000)
            mb_out = min(bytes_out / 1024 / 1024, 1000)
        else:
            mb_in = mb_out = 0

        self.net_in_history.append(mb_in)
        self.net_out_history.append(mb_out)
        self.net_in_history = self.net_in_history[-HISTORY_LEN:]
        self.net_out_history = self.net_out_history[-HISTORY_LEN:]

        self.last_net = net
        self.last_time = now


def render_graph(data: list, height: int = 2, color_scheme: str = "gradient") -> list:
    """Render data as a colored braille graph.

    Always pads data to HISTORY_LEN so graphs have consistent width.
    New data appears on the right and scrolls left over time.
    """
    if not data:
        data = [0]

    # Pad data on the left to maintain consistent graph width
    # Use the first value for padding to avoid visual jumps
    if len(data) < HISTORY_LEN:
        padding = [data[0]] * (HISTORY_LEN - len(data))
        padded_data = padding + data
    else:
        padded_data = data

    style = BrailleLineGraphStyle(height=height, filled=False)
    graph = style.scale_data(padded_data)
    colored = apply_color_to_output(graph, padded_data, color_scheme)
    return ["".join(row) for row in colored]


def format_bar(value: float, width: int = 10, color: str = GREEN) -> str:
    """Create a simple progress bar."""
    value = max(0, min(100, value))
    filled = int(value / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{color}{bar}{ANSI_RESET}"


def format_bytes(bytes_per_sec: float) -> str:
    """Format bytes/sec as human readable."""
    if bytes_per_sec < 1:
        return f"{bytes_per_sec * 1024:5.1f} KB/s"
    elif bytes_per_sec < 1024:
        return f"{bytes_per_sec:5.1f} MB/s"
    else:
        return f"{bytes_per_sec / 1024:5.1f} GB/s"


def get_color_for_value(value: float, low: float = 50, high: float = 80) -> str:
    """Get color based on value thresholds."""
    if value < low:
        return GREEN
    elif value < high:
        return YELLOW
    return RED


def print_header():
    """Print the header section."""
    hostname = psutil.os.uname().nodename if hasattr(psutil.os, 'uname') else "localhost"
    print(f"{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════════╗{ANSI_RESET}")
    print(f"{BOLD}{CYAN}║{ANSI_RESET}  {BOLD}sparkback system monitor{ANSI_RESET} - {hostname:<43} {BOLD}{CYAN}║{ANSI_RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════════════════╝{ANSI_RESET}")
    print()


def main():
    monitor = SystemMonitor()

    # Initial CPU read (first call returns 0)
    psutil.cpu_percent(percpu=True)
    time.sleep(0.1)

    print(CLEAR_SCREEN + CURSOR_HOME + HIDE_CURSOR)
    print_header()

    try:
        while True:
            monitor.update()

            # Move cursor to position after header
            print("\033[5;1H")

            # System info
            load1, load5, load15 = psutil.getloadavg()
            uptime_secs = time.time() - psutil.boot_time()
            uptime_hours = int(uptime_secs // 3600)
            uptime_mins = int((uptime_secs % 3600) // 60)

            print(f"{DIM}Load: {load1:.2f} {load5:.2f} {load15:.2f}  |  "
                  f"Uptime: {uptime_hours}h {uptime_mins}m  |  "
                  f"Procs: {len(psutil.pids())}{ANSI_RESET}")
            print()

            # CPU Section
            print(f"{BOLD}{WHITE}CPU Usage ({monitor.cpu_count} cores){ANSI_RESET}")
            print(f"{DIM}{'─' * 72}{ANSI_RESET}")

            # Show up to 8 cores, 2 per row
            cores_per_row = 2
            for row_start in range(0, min(monitor.cpu_count, 8), cores_per_row):
                # Graph lines (3 rows per graph)
                line1_parts = []
                line2_parts = []
                line3_parts = []

                for i in range(row_start, min(row_start + cores_per_row, monitor.cpu_count, 8)):
                    history = monitor.cpu_histories[i]
                    current = history[-1] if history else 0
                    color = get_color_for_value(current)

                    graph_lines = render_graph(history, height=3, color_scheme="gradient")

                    label = f"{CYAN}CPU{i:<2}{ANSI_RESET}"
                    bar = format_bar(current, 8, color)
                    pct = f"{color}{current:5.1f}%{ANSI_RESET}"

                    line1_parts.append(f"{label}[{bar}]{pct} {graph_lines[0]}")
                    line2_parts.append(f"{'':21}{graph_lines[1]}")
                    line3_parts.append(f"{'':21}{graph_lines[2]}")

                print("  ".join(line1_parts))
                print("  ".join(line2_parts))
                print("  ".join(line3_parts))

            if monitor.cpu_count > 8:
                print(f"{DIM}  ... and {monitor.cpu_count - 8} more cores{ANSI_RESET}")

            print()

            # Memory Section
            print(f"{BOLD}{WHITE}Memory{ANSI_RESET}")
            print(f"{DIM}{'─' * 72}{ANSI_RESET}")

            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            mem_graph = render_graph(monitor.mem_history, height=3, color_scheme="cyan")
            mem_color = get_color_for_value(mem.percent, 60, 85)
            mem_used_gb = mem.used / 1024 / 1024 / 1024
            mem_total_gb = mem.total / 1024 / 1024 / 1024

            print(f"{GREEN}Mem {ANSI_RESET} [{format_bar(mem.percent, 8, mem_color)}] "
                  f"{mem_color}{mem.percent:5.1f}%{ANSI_RESET} "
                  f"{DIM}{mem_used_gb:.1f}/{mem_total_gb:.1f}GB{ANSI_RESET}  {mem_graph[0]}")
            print(f"{'':42}{mem_graph[1]}")
            print(f"{'':42}{mem_graph[2]}")

            swap_graph = render_graph(monitor.swap_history, height=3, color_scheme="magenta")
            swap_color = get_color_for_value(swap.percent, 30, 60)
            swap_used_gb = swap.used / 1024 / 1024 / 1024
            swap_total_gb = swap.total / 1024 / 1024 / 1024

            print(f"{MAGENTA}Swap{ANSI_RESET} [{format_bar(swap.percent, 8, swap_color)}] "
                  f"{swap_color}{swap.percent:5.1f}%{ANSI_RESET} "
                  f"{DIM}{swap_used_gb:.1f}/{swap_total_gb:.1f}GB{ANSI_RESET}  {swap_graph[0]}")
            print(f"{'':42}{swap_graph[1]}")
            print(f"{'':42}{swap_graph[2]}")

            print()

            # Network Section
            print(f"{BOLD}{WHITE}Network I/O{ANSI_RESET}")
            print(f"{DIM}{'─' * 72}{ANSI_RESET}")

            net_in_graph = render_graph(monitor.net_in_history, height=3, color_scheme="green")
            net_out_graph = render_graph(monitor.net_out_history, height=3, color_scheme="blue")

            current_in = monitor.net_in_history[-1] if monitor.net_in_history else 0
            current_out = monitor.net_out_history[-1] if monitor.net_out_history else 0

            print(f"{GREEN}▼ In {ANSI_RESET} {format_bytes(current_in):>12}  {net_in_graph[0]}")
            print(f"{'':20}{net_in_graph[1]}")
            print(f"{'':20}{net_in_graph[2]}")
            print(f"{BLUE}▲ Out{ANSI_RESET} {format_bytes(current_out):>12}  {net_out_graph[0]}")
            print(f"{'':20}{net_out_graph[1]}")
            print(f"{'':20}{net_out_graph[2]}")

            print()

            # Disk I/O (if available)
            try:
                disk = psutil.disk_io_counters()
                if disk:
                    print(f"{BOLD}{WHITE}Disk I/O{ANSI_RESET}")
                    print(f"{DIM}{'─' * 72}{ANSI_RESET}")
                    print(f"{CYAN}Read: {ANSI_RESET} {disk.read_bytes / 1024 / 1024 / 1024:6.1f} GB total  "
                          f"{CYAN}Write:{ANSI_RESET} {disk.write_bytes / 1024 / 1024 / 1024:6.1f} GB total")
                    print()
            except Exception:
                pass

            # Footer
            print(f"{DIM}Press Ctrl+C to exit | Refreshing every 1s{ANSI_RESET}")

            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        print(SHOW_CURSOR)
        print(f"\n{CYAN}Monitor stopped.{ANSI_RESET}")


if __name__ == "__main__":
    main()
