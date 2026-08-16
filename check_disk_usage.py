#!/usr/bin/env python3
"""Warn when a filesystem is above a configured usage threshold.

Reads defaults from config.yaml (disk_threshold_percent, log_dir), and
accepts the same values as command line overrides. Meant to run alongside
rotate-logs.sh, so a full disk and an overdue log rotation get caught by
the same check.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config(config_path: Path) -> dict:
    """Return the parsed config file, or an empty dict if it is missing."""
    if not config_path.exists():
        return {}
    with config_path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def usage_percent(path: Path) -> float:
    """Return the percentage of `path`'s filesystem currently in use."""
    total, used, _free = shutil.disk_usage(path)
    return (used / total) * 100


def parse_args(argv: list[str], config: dict) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(config.get("log_dir", "/var/log")),
        help="Filesystem path to check. Default: config.yaml's log_dir, or /var/log.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=float(config.get("disk_threshold_percent", 90)),
        help="Usage percent above which this exits non-zero. Default: config.yaml's value, or 90.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    config = load_config(DEFAULT_CONFIG_PATH)
    args = parse_args(sys.argv[1:] if argv is None else argv, config)

    if not args.path.exists():
        print(f"Error: '{args.path}' does not exist.", file=sys.stderr)
        return 2

    percent = usage_percent(args.path)
    print(f"{args.path}: {percent:.1f}% used (threshold: {args.threshold:.1f}%)")

    if percent >= args.threshold:
        print(f"Warning: usage at or above the {args.threshold:.1f}% threshold.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
