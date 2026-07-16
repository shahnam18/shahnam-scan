"""
SHAHNAM SCAN - Utilities Module
================================
Author  : Shahnam Sajid
Contact : @shahnamsajid
License : MIT

Provides terminal color codes, logging, and shared helper functions
used across all scanner modules.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Terminal Color Codes (ANSI escape sequences)
# ---------------------------------------------------------------------------

class Colors:
    """ANSI color constants for colorful terminal output."""

    # Foreground colors
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    ORANGE  = "\033[38;5;208m"
    PURPLE  = "\033[38;5;129m"
    LIME    = "\033[38;5;154m"

    # Styles
    BOLD      = "\033[1m"
    DIM       = "\033[2m"
    UNDERLINE = "\033[4m"
    BLINK     = "\033[5m"

    # Reset
    RESET = "\033[0m"

    @staticmethod
    def supports_color() -> bool:
        """Return True if the running terminal supports ANSI color codes."""
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    @classmethod
    def strip(cls, text: str) -> str:
        """Return *text* with all ANSI escape codes removed."""
        import re
        ansi_escape = re.compile(r"\033\[[0-9;]*m")
        return ansi_escape.sub("", text)


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------

def print_section_header(title: str, color: str = Colors.CYAN) -> None:
    """Print a styled section divider with *title*."""
    width = 60
    border = "─" * width
    print(f"\n{color}{Colors.BOLD}┌{border}┐{Colors.RESET}")
    padding = (width - len(title)) // 2
    print(f"{color}{Colors.BOLD}│{' ' * padding}{title}{' ' * (width - len(title) - padding)}│{Colors.RESET}")
    print(f"{color}{Colors.BOLD}└{border}┘{Colors.RESET}\n")


def print_key_value(key: str, value: str,
                    key_color: str = Colors.YELLOW,
                    val_color: str = Colors.WHITE,
                    indent: int = 2) -> None:
    """Print a formatted key → value pair."""
    pad = " " * indent
    print(f"{pad}{key_color}{Colors.BOLD}{key:<28}{Colors.RESET}{val_color}{value}{Colors.RESET}")


def print_status(message: str, status: str = "OK") -> None:
    """Print a status line with a color-coded badge."""
    badge_map = {
        "OK":      (Colors.GREEN,   "✔ OK"),
        "WARN":    (Colors.YELLOW,  "⚠ WARN"),
        "ERROR":   (Colors.RED,     "✘ ERROR"),
        "INFO":    (Colors.CYAN,    "ℹ INFO"),
        "RUNNING": (Colors.MAGENTA, "⟳ RUNNING"),
    }
    color, label = badge_map.get(status.upper(), (Colors.WHITE, status))
    print(f"  {color}{Colors.BOLD}[{label}]{Colors.RESET}  {message}")


def format_bytes(num_bytes: int) -> str:
    """Convert *num_bytes* to a human-readable string (KB / MB / GB / TB)."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def timestamp_str() -> str:
    """Return the current UTC timestamp as a compact string (e.g. 20240715_143022)."""
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: str) -> Path:
    """Create *path* (and parents) if it does not already exist. Return a Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

class Logger:
    """Thin wrapper around the standard :mod:`logging` module.

    Creates a logger that writes to both the console (at WARNING level) and
    an optional log file (at DEBUG level) so that verbose diagnostics are
    captured without cluttering the terminal.
    """

    _instance: logging.Logger | None = None

    @classmethod
    def get(cls, name: str = "shahnam_scan", log_file: str | None = None) -> logging.Logger:
        """Return (and lazily create) the shared logger.

        Parameters
        ----------
        name:
            Logger name; defaults to ``"shahnam_scan"``.
        log_file:
            Optional path for a file handler.  When *None*, only the stream
            handler is attached.
        """
        if cls._instance is not None:
            return cls._instance

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Console handler — WARNING and above only so the UI stays clean
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.WARNING)
        ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(ch)

        # File handler — full DEBUG output (optional)
        if log_file:
            ensure_dir(os.path.dirname(log_file) or ".")
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                                  datefmt="%Y-%m-%d %H:%M:%S")
            )
            logger.addHandler(fh)

        cls._instance = logger
        return logger

    @classmethod
    def reset(cls) -> None:
        """Remove all handlers and clear the cached instance (useful for tests)."""
        if cls._instance:
            cls._instance.handlers.clear()
            cls._instance = None
