"""
SHAHNAM SCAN - Report Generator Module
========================================
Author  : Shahnam Sajid
Contact : @shahnamsajid
License : MIT

Exports collected system and network data to JSON and CSV formats.
Reports are timestamped and written to the 'reports/' directory by
default (auto-created if absent).
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from scanner.utils import Colors, Logger, ensure_dir, print_status, timestamp_str

log = Logger.get()


class ReportGenerator:
    """Save scan results to disk in JSON or CSV format.

    Parameters
    ----------
    output_dir:
        Directory where reports will be written.  Created automatically
        if it does not exist.  Defaults to ``"reports"``.
    """

    def __init__(self, output_dir: str = "reports") -> None:
        self.output_dir = Path(output_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_json(
        self,
        system_data: dict[str, Any] | None,
        network_data: dict[str, Any] | None,
        filename: str | None = None,
    ) -> str:
        """Write the combined scan data to a JSON file.

        Parameters
        ----------
        system_data:
            Serialised :class:`~scanner.system.SystemInfo` dict.
        network_data:
            Serialised :class:`~scanner.network.NetworkInfo` dict.
        filename:
            Override the auto-generated filename.

        Returns
        -------
        str
            Absolute path of the written file.
        """
        ensure_dir(str(self.output_dir))
        fname = filename or f"shahnam_scan_{timestamp_str()}.json"
        path  = self.output_dir / fname

        payload: dict[str, Any] = {
            "tool":       "SHAHNAM SCAN",
            "author":     "Shahnam Sajid",
            "contact":    "@shahnamsajid",
            "generated":  datetime.now().isoformat(timespec="seconds"),
        }
        if system_data:
            payload["system"] = system_data
        if network_data:
            payload["network"] = network_data

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4, default=str)
            log.debug("JSON report saved: %s", path)
            print_status(f"JSON report → {path}", "OK")
        except OSError as exc:
            log.error("Failed to write JSON report: %s", exc)
            print_status(f"Could not write JSON: {exc}", "ERROR")

        return str(path.resolve())

    def save_csv(
        self,
        system_data: dict[str, Any] | None,
        network_data: dict[str, Any] | None,
        filename: str | None = None,
    ) -> str:
        """Write the combined scan data to a CSV file (flattened key-value rows).

        Parameters
        ----------
        system_data:
            Serialised :class:`~scanner.system.SystemInfo` dict.
        network_data:
            Serialised :class:`~scanner.network.NetworkInfo` dict.
        filename:
            Override the auto-generated filename.

        Returns
        -------
        str
            Absolute path of the written file.
        """
        ensure_dir(str(self.output_dir))
        fname = filename or f"shahnam_scan_{timestamp_str()}.csv"
        path  = self.output_dir / fname

        rows: list[dict[str, str]] = []

        # Meta rows
        rows.append({"section": "meta", "key": "tool",      "value": "SHAHNAM SCAN"})
        rows.append({"section": "meta", "key": "author",    "value": "Shahnam Sajid"})
        rows.append({"section": "meta", "key": "contact",   "value": "@shahnamsajid"})
        rows.append({"section": "meta", "key": "generated", "value": datetime.now().isoformat(timespec="seconds")})

        # System rows
        if system_data:
            for key, value in system_data.items():
                rows.append({"section": "system", "key": key, "value": str(value)})

        # Network rows (exclude nested interfaces list — write separately)
        if network_data:
            interfaces = network_data.pop("interfaces", [])
            for key, value in network_data.items():
                rows.append({"section": "network", "key": key, "value": str(value)})
            for idx, iface in enumerate(interfaces):
                for key, value in iface.items():
                    rows.append({
                        "section": f"interface_{idx}",
                        "key":     key,
                        "value":   str(value),
                    })

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["section", "key", "value"])
                writer.writeheader()
                writer.writerows(rows)
            log.debug("CSV report saved: %s", path)
            print_status(f"CSV report  → {path}", "OK")
        except OSError as exc:
            log.error("Failed to write CSV report: %s", exc)
            print_status(f"Could not write CSV: {exc}", "ERROR")

        return str(path.resolve())

    def save_both(
        self,
        system_data: dict[str, Any] | None,
        network_data: dict[str, Any] | None,
    ) -> tuple[str, str]:
        """Save both JSON and CSV reports and return their paths.

        .. note::
            ``network_data`` is deep-copied internally so that the CSV
            export's mutation of the dict does not affect the JSON export.
        """
        import copy

        # JSON must be written first (CSV pops 'interfaces' from the dict)
        json_path = self.save_json(
            copy.deepcopy(system_data),
            copy.deepcopy(network_data),
        )
        csv_path  = self.save_csv(
            copy.deepcopy(system_data),
            copy.deepcopy(network_data),
        )
        return json_path, csv_path
