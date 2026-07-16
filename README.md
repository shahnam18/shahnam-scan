# SHAHNAM SCAN

```
 ███████╗██╗  ██╗ █████╗ ██╗  ██╗███╗   ██╗ █████╗ ███╗   ███╗
 ██╔════╝██║  ██║██╔══██╗██║  ██║████╗  ██║██╔══██╗████╗ ████║
 ███████╗███████║███████║███████║██╔██╗ ██║███████║██╔████╔██║
 ╚════██║██╔══██║██╔══██║██╔══██║██║╚██╗██║██╔══██║██║╚██╔╝██║
 ███████║██║  ██║██║  ██║██║  ██║██║ ╚████║██║  ██║██║ ╚═╝ ██║
 ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝

  ███████╗ ██████╗ █████╗ ███╗   ██╗
  ██╔════╝██╔════╝██╔══██╗████╗  ██║
  ███████╗██║     ███████║██╔██╗ ██║
  ╚════██║██║     ██╔══██║██║╚██╗██║
  ███████║╚██████╗██║  ██║██║ ╚████║
  ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝
```

**Linux System & Network Information Tool**

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange?logo=linux)](https://kernel.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Shahnam%20Sajid-purple)](https://github.com/shahnamsajid)

---

## Overview

**SHAHNAM SCAN** is a modular, colorful command-line tool for gathering detailed system and network diagnostics on Linux.  
It is designed to run on Kali Linux, Ubuntu, and Debian without requiring root privileges for standard diagnostics.

### What it does

| Feature | Details |
|---|---|
| 🖥️ OS Information | Distribution name, version, kernel, architecture |
| ⚙️ CPU Metrics | Model, core count, frequency, usage %, load averages |
| 🧠 Memory | RAM total/used/available, swap, visual usage bars |
| 💾 Disk | Mounted partitions with usage bars and colour-coded alerts |
| 🌐 Network Interfaces | All NICs with IPv4/IPv6/MAC, speed, MTU, TX/RX counters |
| 📡 IP Addresses | Local outbound IP + optional public (WAN) IP |
| 🔗 Connectivity | Internet reachability probe + latency measurement |
| 🔍 DNS | Nameservers from `/etc/resolv.conf` |
| 🛣️ Gateway | Default route from `/proc/net/route` |
| 👥 Users | Currently logged-in user sessions |
| 📄 Reports | Export to **JSON** and/or **CSV** with timestamps |
| 📋 Logging | Optional debug log file via `--log` flag |

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.12 or later |
| Operating System | Kali Linux / Ubuntu 22.04+ / Debian 12+ |
| Root / sudo | **Not required** for standard features |

**Python dependencies** (see `requirements.txt`):

```
psutil>=5.9.0
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/shahnamsajid/shahnam-scan.git
cd shahnam-scan
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Make the entry point executable (optional)

```bash
chmod +x main.py
```

---

## Usage

### Interactive mode (default)

Launch the interactive menu — no arguments needed:

```bash
python3 main.py
```

You will see the banner and a numbered menu:

```
  ┌──────────────────────────────────────┐
  │            MAIN MENU                 │
  ├──────────────────────────────────────┤
  │  [1]  System Information             │
  │  [2]  Network Information            │
  │  [3]  Full Scan (System + Network)   │
  │  [4]  Export Last Scan → JSON        │
  │  [5]  Export Last Scan → CSV         │
  │  [6]  Export Last Scan → JSON + CSV  │
  │  [0]  Exit                           │
  └──────────────────────────────────────┘
```

### Non-interactive / scripted mode

Run a specific scan and exit immediately:

```bash
# System information only
python3 main.py --scan system

# Network information only
python3 main.py --scan network

# Full scan and export to JSON
python3 main.py --scan all --export json

# Full scan and export to both formats
python3 main.py --scan all --export both

# Skip external public-IP lookup (air-gapped host)
python3 main.py --scan all --no-public-ip

# Write debug log to file
python3 main.py --scan all --log /var/log/shahnam.log

# Custom report output directory
python3 main.py --scan all --export json --output-dir /tmp/reports

# Disable ANSI colors (for piping / logging)
python3 main.py --scan all --no-color > scan.txt
```

### All options

```
usage: shahnam-scan [-h] [--scan {system,network,all}]
                    [--export {json,csv,both}] [--no-public-ip]
                    [--output-dir DIR] [--log FILE]
                    [--no-color] [--version]

optional arguments:
  -h, --help                    show this help message and exit
  --scan, -s {system,network,all}
                                Run a scan in non-interactive mode and exit.
  --export, -e {json,csv,both}  Export results after scanning.
  --no-public-ip                Skip external public-IP lookup.
  --output-dir, -o DIR          Directory for exported reports (default: reports/).
  --log, -l FILE                Write DEBUG-level log to FILE.
  --no-color                    Disable ANSI color codes.
  --version, -v                 Show version and exit.
```

---

## Output Examples

### System scan (terminal)

```
┌────────────────────────────────────────────────────────────┐
│                   SYSTEM INFORMATION                       │
└────────────────────────────────────────────────────────────┘

  Hostname                    kali-machine
  OS                          Kali GNU/Linux Rolling
  Kernel                      6.6.9-amd64
  Architecture                x86_64
  CPU Model                   Intel(R) Core(TM) i7-10750H @ 2.60GHz
  Physical Cores              6
  Logical Cores               12
  CPU Usage                   [████████░░░░░░░░░░░░░░░░░░░░░░] 27.3%
  RAM Usage                   [███████████████░░░░░░░░░░░░░░░] 48.2%
```

### JSON export (`reports/shahnam_scan_20240715_143022.json`)

```json
{
    "tool": "SHAHNAM SCAN",
    "author": "Shahnam Sajid",
    "contact": "@shahnamsajid",
    "generated": "2024-07-15T14:30:22",
    "system": {
        "hostname": "kali-machine",
        "os_name": "Kali GNU/Linux Rolling",
        "cpu_model": "Intel(R) Core(TM) i7-10750H @ 2.60GHz",
        "cpu_percent": 27.3,
        "ram_total": "15.56 GB",
        "ram_percent": 48.2
    },
    "network": {
        "local_ip": "192.168.1.42",
        "public_ip": "203.0.113.5",
        "internet_connected": true,
        "latency_ms": 12.4
    }
}
```

---

## Project Structure

```
SHAHNAM-SCAN/
├── main.py                  # Entry point — banner, menu, argparse
├── scanner/
│   ├── __init__.py          # Package exports
│   ├── system.py            # OS, CPU, RAM, disk collection & display
│   ├── network.py           # Interfaces, IPs, DNS, connectivity
│   ├── report.py            # JSON and CSV export
│   └── utils.py             # Colors, logger, print helpers, format_bytes
├── requirements.txt         # Python dependencies (psutil)
├── README.md                # This file
├── LICENSE                  # MIT License
└── screenshots/             # Tool screenshots for README
```

---

## Ethical Use

SHAHNAM SCAN collects **read-only diagnostics about the local machine only**.  
It does **not** perform:

- Port scanning of remote hosts
- Packet capture or traffic interception
- Credential harvesting or credential testing
- Wireless network enumeration or deauthentication
- Exploitation of any service or vulnerability
- Any form of unauthorized access

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## Author

**Shahnam Sajid**  
Contact: [@shahnamsajid](https://github.com/shahnamsajid)

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
