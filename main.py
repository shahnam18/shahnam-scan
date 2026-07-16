#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║               SHAHNAM SCAN  v1.0.0                       ║
║   Linux System & Network Information Tool                ║
║   Author  : Shahnam Sajid                                ║
║   Contact : @shahnamsajid                                ║
║   License : MIT                                          ║
╚══════════════════════════════════════════════════════════╝

Entry point for SHAHNAM SCAN.

Supported launch modes
----------------------
Interactive (default)::

    python3 main.py

Non-interactive (full scan + optional export)::

    python3 main.py --scan all --export json
    python3 main.py --scan system --export csv
    python3 main.py --scan network --no-public-ip

For complete help::

    python3 main.py --help
"""

import argparse
import sys
import time

# Guard: Python 3.12+
if sys.version_info < (3, 12):
    sys.exit("SHAHNAM SCAN requires Python 3.12 or later.")

from scanner import SystemScanner, NetworkScanner, ReportGenerator
from scanner.utils import Colors, Logger, print_section_header, print_status

# Module-level logger (file handler added after argparse)
log = Logger.get()


# ---------------------------------------------------------------------------
# ASCII Banner
# ---------------------------------------------------------------------------

BANNER = rf"""
{Colors.CYAN}{Colors.BOLD}
 ███████╗██╗  ██╗ █████╗ ██╗  ██╗███╗   ██╗ █████╗ ███╗   ███╗
 ██╔════╝██║  ██║██╔══██╗██║  ██║████╗  ██║██╔══██╗████╗ ████║
 ███████╗███████║███████║███████║██╔██╗ ██║███████║██╔████╔██║
 ╚════██║██╔══██║██╔══██║██╔══██║██║╚██╗██║██╔══██║██║╚██╔╝██║
 ███████║██║  ██║██║  ██║██║  ██║██║ ╚████║██║  ██║██║ ╚═╝ ██║
 ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}
  ███████╗ ██████╗ █████╗ ███╗   ██╗
  ██╔════╝██╔════╝██╔══██╗████╗  ██║
  ███████╗██║     ███████║██╔██╗ ██║
  ╚════██║██║     ██╔══██║██║╚██╗██║
  ███████║╚██████╗██║  ██║██║ ╚████║
  ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝{Colors.RESET}

{Colors.YELLOW}{'═' * 60}{Colors.RESET}
{Colors.GREEN}{Colors.BOLD}  Linux System & Network Information Tool  v1.0.0{Colors.RESET}
{Colors.WHITE}  Author  : {Colors.CYAN}Shahnam Sajid{Colors.RESET}
{Colors.WHITE}  Contact : {Colors.CYAN}@shahnamsajid{Colors.RESET}
{Colors.WHITE}  License : {Colors.CYAN}MIT{Colors.RESET}
{Colors.YELLOW}{'═' * 60}{Colors.RESET}
"""

MENU = f"""
{Colors.CYAN}{Colors.BOLD}  ┌──────────────────────────────────────┐{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}  │            MAIN MENU                 │{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}  ├──────────────────────────────────────┤{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}  │{Colors.RESET}  {Colors.GREEN}[1]{Colors.RESET}  System Information              {Colors.CYAN}{Colors.BOLD}│{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}  │{Colors.RESET}  {Colors.GREEN}[2]{Colors.RESET}  Network Information             {Colors.CYAN}{Colors.BOLD}│{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}  │{Colors.RESET}  {Colors.GREEN}[3]{Colors.RESET}  Full Scan (System + Network)    {Colors.CYAN}{Colors.BOLD}│{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}  │{Colors.RESET}  {Colors.YELLOW}[4]{Colors.RESET}  Export Last Scan → JSON         {Colors.CYAN}{Colors.BOLD}│{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}  │{Colors.RESET}  {Colors.YELLOW}[5]{Colors.RESET}  Export Last Scan → CSV          {Colors.CYAN}{Colors.BOLD}│{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}  │{Colors.RESET}  {Colors.YELLOW}[6]{Colors.RESET}  Export Last Scan → JSON + CSV   {Colors.CYAN}{Colors.BOLD}│{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}  │{Colors.RESET}  {Colors.RED}[0]{Colors.RESET}  Exit                            {Colors.CYAN}{Colors.BOLD}│{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}  └──────────────────────────────────────┘{Colors.RESET}
"""


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Define and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="shahnam-scan",
        description=(
            "SHAHNAM SCAN — Linux System & Network Information Tool\n"
            "Author: Shahnam Sajid  |  Contact: @shahnamsajid"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py                          # interactive menu
  python3 main.py --scan system            # system info only
  python3 main.py --scan network           # network info only
  python3 main.py --scan all --export json # full scan → JSON
  python3 main.py --scan all --export both # full scan → JSON + CSV
  python3 main.py --no-public-ip           # skip public IP fetch
  python3 main.py --log scan.log           # write debug log to file
  python3 main.py --output-dir /tmp/scans  # custom report directory
        """,
    )

    parser.add_argument(
        "--scan", "-s",
        choices=["system", "network", "all"],
        default=None,
        help="Run a scan in non-interactive mode and exit.",
    )
    parser.add_argument(
        "--export", "-e",
        choices=["json", "csv", "both"],
        default=None,
        help="Export results after scanning (requires --scan).",
    )
    parser.add_argument(
        "--no-public-ip",
        action="store_true",
        default=False,
        help="Skip external public-IP lookup (useful for air-gapped hosts).",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="reports",
        metavar="DIR",
        help="Directory for exported reports (default: reports/).",
    )
    parser.add_argument(
        "--log", "-l",
        default=None,
        metavar="FILE",
        help="Write DEBUG-level log to FILE.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color codes (useful when piping output).",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="SHAHNAM SCAN v1.0.0",
    )

    return parser


# ---------------------------------------------------------------------------
# Core scan helpers
# ---------------------------------------------------------------------------

def run_system_scan() -> dict:
    """Execute and display the system scan; return serialised data."""
    scanner = SystemScanner()
    print_status("Collecting system information …", "RUNNING")
    info = scanner.scan()
    scanner.display(info)
    return info.to_dict()


def run_network_scan(fetch_public_ip: bool = True) -> dict:
    """Execute and display the network scan; return serialised data."""
    scanner = NetworkScanner()
    label   = "Collecting network information …"
    if not fetch_public_ip:
        label += " (public IP skipped)"
    print_status(label, "RUNNING")
    info = scanner.scan(fetch_public_ip=fetch_public_ip)
    scanner.display(info)
    return info.to_dict()


def export_results(
    system_data: dict | None,
    network_data: dict | None,
    fmt: str,
    output_dir: str,
) -> None:
    """Export *system_data* and *network_data* in the requested format."""
    reporter = ReportGenerator(output_dir=output_dir)
    print_section_header("EXPORTING REPORT", Colors.YELLOW)

    if fmt == "json":
        reporter.save_json(system_data, network_data)
    elif fmt == "csv":
        reporter.save_csv(system_data, network_data)
    elif fmt == "both":
        reporter.save_both(system_data, network_data)


# ---------------------------------------------------------------------------
# Interactive menu
# ---------------------------------------------------------------------------

def interactive_menu(args: argparse.Namespace) -> None:
    """Run the interactive menu loop."""
    system_data:  dict | None = None
    network_data: dict | None = None

    while True:
        print(MENU)
        try:
            choice = input(
                f"  {Colors.BOLD}{Colors.WHITE}Select option:{Colors.RESET} "
            ).strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{Colors.YELLOW}  Goodbye!{Colors.RESET}\n")
            sys.exit(0)

        if choice == "1":
            system_data = run_system_scan()

        elif choice == "2":
            network_data = run_network_scan(not args.no_public_ip)

        elif choice == "3":
            system_data  = run_system_scan()
            network_data = run_network_scan(not args.no_public_ip)

        elif choice == "4":
            if system_data is None and network_data is None:
                print_status("No scan data yet. Run a scan first (options 1–3).", "WARN")
            else:
                export_results(system_data, network_data, "json", args.output_dir)

        elif choice == "5":
            if system_data is None and network_data is None:
                print_status("No scan data yet. Run a scan first (options 1–3).", "WARN")
            else:
                export_results(system_data, network_data, "csv", args.output_dir)

        elif choice == "6":
            if system_data is None and network_data is None:
                print_status("No scan data yet. Run a scan first (options 1–3).", "WARN")
            else:
                export_results(system_data, network_data, "both", args.output_dir)

        elif choice == "0":
            print(f"\n{Colors.CYAN}  Thank you for using SHAHNAM SCAN!{Colors.RESET}")
            print(f"  {Colors.WHITE}Author: Shahnam Sajid  |  @shahnamsajid{Colors.RESET}\n")
            sys.exit(0)

        else:
            print_status(f"Invalid choice '{choice}'. Please enter 0–6.", "WARN")

        # Brief pause so the user can read the output
        time.sleep(0.3)


# ---------------------------------------------------------------------------
# Non-interactive mode
# ---------------------------------------------------------------------------

def non_interactive(args: argparse.Namespace) -> None:
    """Run a single scan pass and optionally export, then exit."""
    system_data:  dict | None = None
    network_data: dict | None = None

    if args.scan in ("system", "all"):
        system_data = run_system_scan()

    if args.scan in ("network", "all"):
        network_data = run_network_scan(not args.no_public_ip)

    if args.export:
        export_results(system_data, network_data, args.export, args.output_dir)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Application entry point."""
    parser = build_parser()
    args   = parser.parse_args()

    # Re-initialise logger with optional file handler
    Logger.reset()
    log = Logger.get(log_file=args.log)

    # Optionally strip colours (e.g. when piped)
    if args.no_color or not Colors.supports_color():
        for attr in vars(Colors):
            if not attr.startswith("_") and isinstance(getattr(Colors, attr), str):
                setattr(Colors, attr, "")

    # Always print the banner
    print(BANNER)

    if args.scan:
        # Non-interactive / scripted mode
        non_interactive(args)
    else:
        # Interactive menu
        interactive_menu(args)


if __name__ == "__main__":
    main()
