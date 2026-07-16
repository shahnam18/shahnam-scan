"""
SHAHNAM SCAN - Network Information Module
==========================================
Author  : Shahnam Sajid
Contact : @shahnamsajid
License : MIT

Collects network interface details, local/public IP addresses, DNS
configuration, default gateway, open listening ports (no root needed
for the process's own ports), and internet connectivity status.
All operations are strictly read-only and non-intrusive.
"""

import ipaddress
import json
import re
import socket
import subprocess
import urllib.request
from dataclasses import dataclass, field
from typing import Any

import psutil

from scanner.utils import (
    Colors, Logger,
    format_bytes, print_key_value, print_section_header, print_status,
)

log = Logger.get()

# Timeout (seconds) for external HTTP/DNS probes
_TIMEOUT_SEC = 5

# Public IP lookup services (tried in order; first successful result wins)
_PUBLIC_IP_URLS = [
    "https://api.ipify.org",
    "https://icanhazip.com",
    "https://checkip.amazonaws.com",
]

# Connectivity probe targets (host, port)
_CONNECTIVITY_PROBES = [
    ("8.8.8.8",     53),   # Google DNS
    ("1.1.1.1",     53),   # Cloudflare DNS
    ("208.67.222.222", 53),# OpenDNS
]

# Well-known DNS resolvers for display
_DNS_RESOLV_CONF = "/etc/resolv.conf"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class InterfaceAddress:
    """A single address (IPv4, IPv6, or MAC) bound to a network interface."""
    family: str = ""     # "IPv4", "IPv6", or "MAC"
    address: str = ""
    netmask: str = ""
    broadcast: str = ""


@dataclass
class NetworkInterface:
    """Aggregated information about one network interface."""
    name: str = ""
    is_up: bool = False
    speed_mbps: int = 0
    mtu: int = 0
    addresses: list[InterfaceAddress] = field(default_factory=list)
    bytes_sent: int = 0
    bytes_recv: int = 0
    packets_sent: int = 0
    packets_recv: int = 0
    errors_in: int = 0
    errors_out: int = 0

    @property
    def ipv4(self) -> str:
        """Return the first IPv4 address (or empty string)."""
        for a in self.addresses:
            if a.family == "IPv4":
                return a.address
        return ""

    @property
    def mac(self) -> str:
        """Return the MAC / hardware address (or empty string)."""
        for a in self.addresses:
            if a.family == "MAC":
                return a.address
        return ""


@dataclass
class NetworkInfo:
    """Complete network snapshot for the current host."""
    hostname: str = ""
    fqdn: str = ""
    local_ip: str = ""
    public_ip: str = ""
    default_gateway: str = ""
    dns_servers: list[str] = field(default_factory=list)
    interfaces: list[NetworkInterface] = field(default_factory=list)
    internet_connected: bool = False
    latency_ms: float = -1.0
    scanned_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict suitable for JSON / CSV export."""
        ifaces = []
        for iface in self.interfaces:
            ifaces.append({
                "name":         iface.name,
                "is_up":        iface.is_up,
                "ipv4":         iface.ipv4,
                "mac":          iface.mac,
                "speed_mbps":   iface.speed_mbps,
                "mtu":          iface.mtu,
                "bytes_sent":   format_bytes(iface.bytes_sent),
                "bytes_recv":   format_bytes(iface.bytes_recv),
            })
        return {
            "hostname":          self.hostname,
            "fqdn":              self.fqdn,
            "local_ip":          self.local_ip,
            "public_ip":         self.public_ip,
            "default_gateway":   self.default_gateway,
            "dns_servers":       ", ".join(self.dns_servers),
            "internet_connected":self.internet_connected,
            "latency_ms":        self.latency_ms,
            "scanned_at":        self.scanned_at,
            "interfaces":        ifaces,
        }


# ---------------------------------------------------------------------------
# Scanner class
# ---------------------------------------------------------------------------

class NetworkScanner:
    """Collect and display network information for the current host.

    Usage::

        scanner = NetworkScanner()
        info = scanner.scan(fetch_public_ip=True)
        scanner.display(info)
    """

    def scan(self, fetch_public_ip: bool = True) -> NetworkInfo:
        """Run all network checks and return a populated :class:`NetworkInfo`.

        Parameters
        ----------
        fetch_public_ip:
            When *True*, attempt to resolve the machine's public IP via an
            external HTTP service.  Set to *False* for fully offline runs.
        """
        log.debug("Starting network scan …")
        from datetime import datetime
        info = NetworkInfo(scanned_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        self._collect_hostname(info)
        self._collect_interfaces(info)
        self._collect_local_ip(info)
        self._collect_gateway(info)
        self._collect_dns(info)
        self._check_connectivity(info)

        if fetch_public_ip:
            self._collect_public_ip(info)

        log.debug("Network scan complete.")
        return info

    # ------------------------------------------------------------------
    # Private collection methods
    # ------------------------------------------------------------------

    def _collect_hostname(self, info: NetworkInfo) -> None:
        """Resolve hostname and FQDN."""
        try:
            info.hostname = socket.gethostname()
            info.fqdn     = socket.getfqdn()
        except Exception as exc:
            log.warning("Hostname resolution failed: %s", exc)
            info.hostname = "unknown"
            info.fqdn     = "unknown"

    def _collect_interfaces(self, info: NetworkInfo) -> None:
        """Enumerate all network interfaces with their addresses and counters."""
        try:
            addrs   = psutil.net_if_addrs()
            stats   = psutil.net_if_stats()
            io_ctrs = psutil.net_io_counters(pernic=True)

            for name, addr_list in addrs.items():
                iface = NetworkInterface(name=name)

                # Stats (speed / MTU / is_up)
                if name in stats:
                    st = stats[name]
                    iface.is_up     = st.isup
                    iface.speed_mbps= st.speed
                    iface.mtu       = st.mtu

                # Address family mapping
                family_map = {
                    psutil.AF_LINK: "MAC",
                    socket.AF_INET: "IPv4",
                    socket.AF_INET6:"IPv6",
                }

                for addr in addr_list:
                    family_name = family_map.get(addr.family, f"AF_{addr.family}")
                    iface.addresses.append(InterfaceAddress(
                        family    = family_name,
                        address   = addr.address or "",
                        netmask   = addr.netmask or "",
                        broadcast = addr.broadcast or "",
                    ))

                # I/O counters
                if name in io_ctrs:
                    ctr = io_ctrs[name]
                    iface.bytes_sent   = ctr.bytes_sent
                    iface.bytes_recv   = ctr.bytes_recv
                    iface.packets_sent = ctr.packets_sent
                    iface.packets_recv = ctr.packets_recv
                    iface.errors_in    = ctr.errin
                    iface.errors_out   = ctr.errout

                info.interfaces.append(iface)

        except Exception as exc:
            log.warning("Interface enumeration failed: %s", exc)

    def _collect_local_ip(self, info: NetworkInfo) -> None:
        """Determine the primary outbound local IPv4 address.

        Opens a UDP socket towards 8.8.8.8 without actually sending any
        data — the OS fills in the source address automatically.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(_TIMEOUT_SEC)
                s.connect(("8.8.8.8", 80))
                info.local_ip = s.getsockname()[0]
        except Exception:
            # Fall back: pick first non-loopback IPv4
            for iface in info.interfaces:
                ip = iface.ipv4
                if ip and not ip.startswith("127."):
                    info.local_ip = ip
                    return
            info.local_ip = "127.0.0.1"

    def _collect_gateway(self, info: NetworkInfo) -> None:
        """Parse the default gateway from /proc/net/route."""
        try:
            with open("/proc/net/route", "r", encoding="utf-8") as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 3 and parts[1] == "00000000":
                        # Gateway is stored as little-endian hex
                        gw_hex = parts[2]
                        gw_bytes = bytes.fromhex(gw_hex)[::-1]
                        info.default_gateway = socket.inet_ntoa(gw_bytes)
                        return
        except Exception:
            pass

        # Fallback: `ip route` command
        try:
            out = subprocess.check_output(
                ["ip", "route", "show", "default"],
                text=True, timeout=_TIMEOUT_SEC,
                stderr=subprocess.DEVNULL,
            )
            match = re.search(r"via\s+(\S+)", out)
            if match:
                info.default_gateway = match.group(1)
        except Exception as exc:
            log.debug("Gateway detection fallback failed: %s", exc)
            info.default_gateway = "Unknown"

    def _collect_dns(self, info: NetworkInfo) -> None:
        """Read DNS nameservers from /etc/resolv.conf."""
        try:
            with open(_DNS_RESOLV_CONF, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("nameserver"):
                        parts = line.split()
                        if len(parts) >= 2:
                            info.dns_servers.append(parts[1])
        except (FileNotFoundError, PermissionError) as exc:
            log.debug("Cannot read resolv.conf: %s", exc)

    def _check_connectivity(self, info: NetworkInfo) -> None:
        """Probe connectivity by attempting a TCP connection to DNS resolvers."""
        import time
        for host, port in _CONNECTIVITY_PROBES:
            try:
                start = time.monotonic()
                with socket.create_connection((host, port), timeout=_TIMEOUT_SEC):
                    elapsed = (time.monotonic() - start) * 1000
                    info.internet_connected = True
                    info.latency_ms = round(elapsed, 2)
                    return
            except (socket.timeout, OSError):
                continue
        info.internet_connected = False

    def _collect_public_ip(self, info: NetworkInfo) -> None:
        """Fetch the public (WAN) IP address via HTTP."""
        for url in _PUBLIC_IP_URLS:
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "SHAHNAM-SCAN/1.0"}
                )
                with urllib.request.urlopen(req, timeout=_TIMEOUT_SEC) as resp:
                    raw = resp.read().decode("utf-8").strip()
                    # Validate it looks like an IP
                    ipaddress.ip_address(raw)
                    info.public_ip = raw
                    return
            except Exception as exc:
                log.debug("Public IP probe %s failed: %s", url, exc)

        info.public_ip = "Unavailable"

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def display(self, info: NetworkInfo) -> None:
        """Pretty-print the network information to stdout."""

        # ── Overview ────────────────────────────────────────────────────
        print_section_header("NETWORK OVERVIEW", Colors.CYAN)

        print_key_value("Hostname",        info.hostname)
        print_key_value("FQDN",            info.fqdn)
        print_key_value("Local IP",        info.local_ip)
        print_key_value("Public IP",       info.public_ip or "Not fetched")
        print_key_value("Default Gateway", info.default_gateway)
        print_key_value("DNS Servers",     ", ".join(info.dns_servers) if info.dns_servers else "None found")

        # Connectivity badge
        if info.internet_connected:
            print_status(f"Internet reachable  (latency ≈ {info.latency_ms} ms)", "OK")
        else:
            print_status("No internet connectivity detected", "ERROR")

        # ── Interfaces ──────────────────────────────────────────────────
        print_section_header("NETWORK INTERFACES", Colors.MAGENTA)

        if not info.interfaces:
            print_status("No network interfaces found.", "WARN")
            return

        for iface in info.interfaces:
            status_color = Colors.GREEN if iface.is_up else Colors.RED
            status_label = "UP" if iface.is_up else "DOWN"

            print(f"\n  {Colors.BOLD}{Colors.CYAN}{iface.name:<12}{Colors.RESET}"
                  f"  {status_color}{Colors.BOLD}[{status_label}]{Colors.RESET}"
                  f"  {Colors.DIM}MTU: {iface.mtu}  Speed: {iface.speed_mbps} Mbps{Colors.RESET}")

            for addr in iface.addresses:
                if addr.family == "IPv4":
                    print_key_value(f"    IPv4",    addr.address, indent=4)
                    if addr.netmask:
                        print_key_value(f"    Netmask",  addr.netmask, indent=4)
                    if addr.broadcast:
                        print_key_value(f"    Broadcast",addr.broadcast, indent=4)
                elif addr.family == "IPv6":
                    # Shorten link-local to keep output tidy
                    a6 = addr.address.split("%")[0]
                    print_key_value(f"    IPv6",    a6, indent=4)
                elif addr.family == "MAC":
                    print_key_value(f"    MAC",     addr.address, indent=4)

            # I/O counters (only show if the interface has any traffic)
            if iface.bytes_sent + iface.bytes_recv > 0:
                print_key_value("    TX", format_bytes(iface.bytes_sent), indent=4)
                print_key_value("    RX", format_bytes(iface.bytes_recv), indent=4)
                if iface.errors_in or iface.errors_out:
                    print_key_value("    Errors",
                                    f"in={iface.errors_in}  out={iface.errors_out}",
                                    val_color=Colors.YELLOW, indent=4)
