"""
SHAHNAM SCAN - System Information Module
=========================================
Author  : Shahnam Sajid
Contact : @shahnamsajid
License : MIT

Collects detailed Linux system information including OS release, kernel
version, CPU, memory, disk usage, uptime, and logged-in users.
All reads are performed without requiring root privileges.
"""

import os
import platform
import re
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import psutil

from scanner.utils import (
    Colors, Logger,
    format_bytes, print_key_value, print_section_header, print_status,
)

log = Logger.get()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CPUInfo:
    """Snapshot of CPU metrics."""
    physical_cores: int = 0
    logical_cores: int = 0
    max_freq_mhz: float = 0.0
    current_freq_mhz: float = 0.0
    cpu_percent: float = 0.0
    model_name: str = "Unknown"
    architecture: str = platform.machine()
    load_avg_1m: float = 0.0
    load_avg_5m: float = 0.0
    load_avg_15m: float = 0.0


@dataclass
class MemoryInfo:
    """Snapshot of system memory (RAM + swap)."""
    total_ram: int = 0
    available_ram: int = 0
    used_ram: int = 0
    ram_percent: float = 0.0
    total_swap: int = 0
    used_swap: int = 0
    swap_percent: float = 0.0


@dataclass
class DiskPartition:
    """Metrics for a single mounted disk partition."""
    device: str = ""
    mountpoint: str = ""
    fstype: str = ""
    total: int = 0
    used: int = 0
    free: int = 0
    percent: float = 0.0


@dataclass
class SystemInfo:
    """Aggregated system information snapshot."""
    hostname: str = ""
    os_name: str = ""
    os_version: str = ""
    kernel: str = ""
    architecture: str = ""
    python_version: str = ""
    boot_time: str = ""
    uptime: str = ""
    current_user: str = ""
    cpu: CPUInfo = field(default_factory=CPUInfo)
    memory: MemoryInfo = field(default_factory=MemoryInfo)
    disks: list[DiskPartition] = field(default_factory=list)
    users: list[str] = field(default_factory=list)
    scanned_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict suitable for JSON / CSV export."""
        return {
            "hostname":       self.hostname,
            "os_name":        self.os_name,
            "os_version":     self.os_version,
            "kernel":         self.kernel,
            "architecture":   self.architecture,
            "python_version": self.python_version,
            "boot_time":      self.boot_time,
            "uptime":         self.uptime,
            "current_user":   self.current_user,
            "scanned_at":     self.scanned_at,
            # CPU
            "cpu_model":          self.cpu.model_name,
            "cpu_physical_cores": self.cpu.physical_cores,
            "cpu_logical_cores":  self.cpu.logical_cores,
            "cpu_max_freq_mhz":   self.cpu.max_freq_mhz,
            "cpu_cur_freq_mhz":   self.cpu.current_freq_mhz,
            "cpu_percent":        self.cpu.cpu_percent,
            "load_avg_1m":        self.cpu.load_avg_1m,
            "load_avg_5m":        self.cpu.load_avg_5m,
            "load_avg_15m":       self.cpu.load_avg_15m,
            # Memory
            "ram_total":    format_bytes(self.memory.total_ram),
            "ram_used":     format_bytes(self.memory.used_ram),
            "ram_available":format_bytes(self.memory.available_ram),
            "ram_percent":  self.memory.ram_percent,
            "swap_total":   format_bytes(self.memory.total_swap),
            "swap_used":    format_bytes(self.memory.used_swap),
            "swap_percent": self.memory.swap_percent,
            # Disks (flatten to string)
            "disks": "; ".join(
                f"{d.mountpoint}({d.device}) {format_bytes(d.used)}/{format_bytes(d.total)} {d.percent}%"
                for d in self.disks
            ),
            "logged_in_users": ", ".join(self.users),
        }


# ---------------------------------------------------------------------------
# Scanner class
# ---------------------------------------------------------------------------

class SystemScanner:
    """Collect and display Linux system information.

    Usage::

        scanner = SystemScanner()
        info = scanner.scan()
        scanner.display(info)
    """

    # Paths to read CPU model name from (tried in order)
    _CPU_INFO_PATH = "/proc/cpuinfo"
    _OS_RELEASE_PATH = "/etc/os-release"

    def scan(self) -> SystemInfo:
        """Run all system checks and return a populated :class:`SystemInfo`."""
        log.debug("Starting system scan …")
        info = SystemInfo(scanned_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        self._collect_os(info)
        self._collect_cpu(info)
        self._collect_memory(info)
        self._collect_disks(info)
        self._collect_uptime(info)
        self._collect_users(info)

        log.debug("System scan complete.")
        return info

    # ------------------------------------------------------------------
    # Private collection methods
    # ------------------------------------------------------------------

    def _collect_os(self, info: SystemInfo) -> None:
        """Populate OS / hostname / kernel / architecture fields."""
        try:
            info.hostname = socket.gethostname()
        except Exception as exc:
            log.warning("Could not resolve hostname: %s", exc)
            info.hostname = "unknown"

        info.kernel = platform.uname().release
        info.architecture = platform.machine()
        info.python_version = platform.python_version()
        info.current_user = os.environ.get("USER", os.environ.get("LOGNAME", "unknown"))

        # Read /etc/os-release for a friendly distro name
        try:
            os_data = self._parse_key_value_file(self._OS_RELEASE_PATH)
            info.os_name = os_data.get("PRETTY_NAME", platform.system()).strip('"')
            info.os_version = os_data.get("VERSION_ID", "").strip('"')
        except FileNotFoundError:
            info.os_name = platform.system()
            info.os_version = platform.release()

    def _collect_cpu(self, info: SystemInfo) -> None:
        """Populate CPU metrics."""
        cpu = info.cpu
        try:
            cpu.physical_cores = psutil.cpu_count(logical=False) or 0
            cpu.logical_cores = psutil.cpu_count(logical=True) or 0

            freq = psutil.cpu_freq()
            if freq:
                cpu.max_freq_mhz = round(freq.max, 2)
                cpu.current_freq_mhz = round(freq.current, 2)

            # Non-blocking percentage sample (interval=None → since last call)
            cpu.cpu_percent = psutil.cpu_percent(interval=0.5)

            load = os.getloadavg()
            cpu.load_avg_1m, cpu.load_avg_5m, cpu.load_avg_15m = (
                round(load[0], 2), round(load[1], 2), round(load[2], 2)
            )

            cpu.model_name = self._read_cpu_model()
            cpu.architecture = platform.machine()

        except Exception as exc:
            log.warning("CPU collection error: %s", exc)

    def _collect_memory(self, info: SystemInfo) -> None:
        """Populate RAM and swap metrics."""
        try:
            vm = psutil.virtual_memory()
            info.memory.total_ram     = vm.total
            info.memory.available_ram = vm.available
            info.memory.used_ram      = vm.used
            info.memory.ram_percent   = vm.percent

            sw = psutil.swap_memory()
            info.memory.total_swap  = sw.total
            info.memory.used_swap   = sw.used
            info.memory.swap_percent = sw.percent

        except Exception as exc:
            log.warning("Memory collection error: %s", exc)

    def _collect_disks(self, info: SystemInfo) -> None:
        """Collect disk usage for all real (non-virtual) mounted partitions."""
        try:
            for part in psutil.disk_partitions(all=False):
                # Skip pseudo file systems
                if part.fstype in ("", "tmpfs", "devtmpfs", "squashfs", "overlay"):
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    info.disks.append(DiskPartition(
                        device     = part.device,
                        mountpoint = part.mountpoint,
                        fstype     = part.fstype,
                        total      = usage.total,
                        used       = usage.used,
                        free       = usage.free,
                        percent    = usage.percent,
                    ))
                except PermissionError:
                    log.debug("No permission to read %s — skipping.", part.mountpoint)
        except Exception as exc:
            log.warning("Disk collection error: %s", exc)

    def _collect_uptime(self, info: SystemInfo) -> None:
        """Calculate system uptime and boot time."""
        try:
            boot_ts = psutil.boot_time()
            boot_dt = datetime.fromtimestamp(boot_ts)
            info.boot_time = boot_dt.strftime("%Y-%m-%d %H:%M:%S")

            delta = timedelta(seconds=int(time.time() - boot_ts))
            days    = delta.days
            hours   = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            info.uptime = f"{days}d {hours}h {minutes}m"
        except Exception as exc:
            log.warning("Uptime collection error: %s", exc)
            info.uptime = "Unknown"

    def _collect_users(self, info: SystemInfo) -> None:
        """List currently logged-in user sessions."""
        try:
            seen: set[str] = set()
            for user in psutil.users():
                label = f"{user.name} (terminal: {user.terminal or 'N/A'})"
                if label not in seen:
                    seen.add(label)
                    info.users.append(label)
        except Exception as exc:
            log.warning("User collection error: %s", exc)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_cpu_model() -> str:
        """Parse the CPU model name from /proc/cpuinfo."""
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except (FileNotFoundError, PermissionError):
            pass
        return platform.processor() or "Unknown"

    @staticmethod
    def _parse_key_value_file(path: str) -> dict[str, str]:
        """Parse a shell-style KEY=VALUE file (e.g. /etc/os-release)."""
        result: dict[str, str] = {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, _, value = line.partition("=")
                        result[key.strip()] = value.strip().strip('"')
        except (FileNotFoundError, PermissionError):
            pass
        return result

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def display(self, info: SystemInfo) -> None:
        """Pretty-print the system information to stdout."""

        # ── OS ──────────────────────────────────────────────────────────
        print_section_header("SYSTEM INFORMATION", Colors.CYAN)

        print_key_value("Hostname",         info.hostname)
        print_key_value("OS",               info.os_name)
        print_key_value("OS Version",       info.os_version)
        print_key_value("Kernel",           info.kernel)
        print_key_value("Architecture",     info.architecture)
        print_key_value("Python Version",   info.python_version)
        print_key_value("Current User",     info.current_user)
        print_key_value("Boot Time",        info.boot_time)
        print_key_value("Uptime",           info.uptime)
        print_key_value("Scanned At",       info.scanned_at)

        if info.users:
            print_key_value("Logged-in Users", "")
            for user in info.users:
                print(f"      {Colors.WHITE}• {user}{Colors.RESET}")

        # ── CPU ─────────────────────────────────────────────────────────
        print_section_header("CPU INFORMATION", Colors.MAGENTA)

        print_key_value("Model",            info.cpu.model_name)
        print_key_value("Architecture",     info.cpu.architecture)
        print_key_value("Physical Cores",   str(info.cpu.physical_cores))
        print_key_value("Logical Cores",    str(info.cpu.logical_cores))
        print_key_value("Max Frequency",    f"{info.cpu.max_freq_mhz:.0f} MHz")
        print_key_value("Current Frequency",f"{info.cpu.current_freq_mhz:.0f} MHz")
        print_key_value("CPU Usage",        self._bar(info.cpu.cpu_percent))
        print_key_value("Load Average",
                        f"1m: {info.cpu.load_avg_1m}  5m: {info.cpu.load_avg_5m}  15m: {info.cpu.load_avg_15m}")

        # ── Memory ──────────────────────────────────────────────────────
        print_section_header("MEMORY INFORMATION", Colors.YELLOW)

        m = info.memory
        print_key_value("Total RAM",        format_bytes(m.total_ram))
        print_key_value("Used RAM",         f"{format_bytes(m.used_ram)} ({m.ram_percent}%)")
        print_key_value("Available RAM",    format_bytes(m.available_ram))
        print_key_value("RAM Usage",        self._bar(m.ram_percent))
        print_key_value("Total Swap",       format_bytes(m.total_swap))
        print_key_value("Used Swap",        f"{format_bytes(m.used_swap)} ({m.swap_percent}%)")

        # ── Disks ───────────────────────────────────────────────────────
        print_section_header("DISK INFORMATION", Colors.GREEN)

        if info.disks:
            for disk in info.disks:
                color = Colors.RED if disk.percent >= 90 else Colors.YELLOW if disk.percent >= 70 else Colors.GREEN
                print(f"\n  {Colors.BOLD}{Colors.CYAN}{disk.mountpoint}{Colors.RESET}  "
                      f"{Colors.DIM}({disk.device} · {disk.fstype}){Colors.RESET}")
                print_key_value("  Total",   format_bytes(disk.total), indent=4)
                print_key_value("  Used",    f"{format_bytes(disk.used)} ({disk.percent}%)", indent=4)
                print_key_value("  Free",    format_bytes(disk.free), indent=4)
                print(f"    {color}{self._bar(disk.percent, width=40)}{Colors.RESET}")
        else:
            print_status("No readable disk partitions found.", "WARN")

    # ------------------------------------------------------------------
    # Internal display helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _bar(percent: float, width: int = 30) -> str:
        """Return a colored ASCII progress bar for *percent*."""
        filled = int(width * percent / 100)
        empty  = width - filled

        if percent >= 90:
            color = Colors.RED
        elif percent >= 70:
            color = Colors.YELLOW
        else:
            color = Colors.GREEN

        bar  = f"{color}{'█' * filled}{'░' * empty}{Colors.RESET}"
        return f"[{bar}] {percent:.1f}%"
