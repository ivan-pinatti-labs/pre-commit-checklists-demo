"""Tests for check_disk_usage.py.

These exist so a dependency bump to this repository has something to fail
against. `requirements.txt` is a `Pin Only` surface, which lets a pyyaml bump
merge unattended, and that is only defensible if something here actually runs
the new pyyaml. `load_config` is the seam that does: it is the one place this
project calls into yaml, so `test_load_config_parses_the_shipped_config`
below is the test that a broken or incompatible pyyaml breaks.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import check_disk_usage  # noqa: E402

# ---------------------------------------------------------------------------
# load_config, the only caller of yaml in this project
# ---------------------------------------------------------------------------


def test_load_config_parses_the_shipped_config():
    """The real config.yaml parses and carries the keys the script reads.

    This is the pyyaml integration test. It reads the file that ships, not a
    fixture, so a pyyaml release that changes how this document parses fails
    here rather than in production.
    """
    config = check_disk_usage.load_config(REPO_ROOT / "config.yaml")
    assert isinstance(config, dict)
    assert config["log_dir"] == "/var/log/myapp"
    assert config["disk_threshold_percent"] == 90
    assert config["retention_days"] == 14
    # Nested mapping, so a parser that flattened structure would be caught.
    assert config["compression"] == {"format": "gzip", "level": 6}


def test_load_config_returns_empty_for_a_missing_file(tmp_path):
    assert check_disk_usage.load_config(tmp_path / "nope.yaml") == {}


def test_load_config_returns_empty_for_an_empty_file(tmp_path):
    """`yaml.safe_load` returns None for an empty document, not {}.

    The `or {}` in load_config is what turns that into a mapping the caller
    can `.get()` on, and without it every default lookup would raise.
    """
    empty = tmp_path / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    assert check_disk_usage.load_config(empty) == {}


def test_load_config_rejects_arbitrary_python_objects(tmp_path):
    """safe_load, not load: a config file must not be able to construct objects."""
    hostile = tmp_path / "hostile.yaml"
    hostile.write_text("!!python/object/apply:os.system ['true']\n", encoding="utf-8")
    with pytest.raises(yaml.YAMLError):
        check_disk_usage.load_config(hostile)


# ---------------------------------------------------------------------------
# usage_percent
# ---------------------------------------------------------------------------


def test_usage_percent_is_a_percentage(tmp_path):
    percent = check_disk_usage.usage_percent(tmp_path)
    assert 0.0 <= percent <= 100.0


# ---------------------------------------------------------------------------
# parse_args: config supplies defaults, the command line overrides them
# ---------------------------------------------------------------------------


def test_parse_args_takes_defaults_from_config():
    args = check_disk_usage.parse_args([], {"log_dir": "/srv/data", "disk_threshold_percent": 75})
    assert args.path == Path("/srv/data")
    assert args.threshold == 75.0


def test_parse_args_falls_back_when_config_is_empty():
    args = check_disk_usage.parse_args([], {})
    assert args.path == Path("/var/log")
    assert args.threshold == 90.0


def test_parse_args_command_line_beats_config():
    args = check_disk_usage.parse_args(
        ["--path", "/tmp", "--threshold", "10"],
        {"log_dir": "/srv/data", "disk_threshold_percent": 75},
    )
    assert args.path == Path("/tmp")
    assert args.threshold == 10.0


# ---------------------------------------------------------------------------
# main: the three exit codes are the script's contract
# ---------------------------------------------------------------------------


def test_main_returns_2_for_a_path_that_does_not_exist(tmp_path, capsys):
    code = check_disk_usage.main(["--path", str(tmp_path / "absent")])
    assert code == 2
    assert "does not exist" in capsys.readouterr().err


def test_main_returns_0_below_the_threshold(tmp_path, capsys):
    code = check_disk_usage.main(["--path", str(tmp_path), "--threshold", "100"])
    assert code == 0
    assert "% used" in capsys.readouterr().out


def test_main_returns_1_at_or_above_the_threshold(tmp_path, capsys):
    """Threshold 0 is always met, so this asserts the boundary is `>=`."""
    code = check_disk_usage.main(["--path", str(tmp_path), "--threshold", "0"])
    assert code == 1
    assert "at or above" in capsys.readouterr().err
