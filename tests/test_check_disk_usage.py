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


def test_usage_percent_computes_used_over_total(monkeypatch, tmp_path):
    """Exact arithmetic, not a range.

    A range check passes for any wrong calculation that still lands between 0
    and 100, which is most of them: used/free, free/total and total/used all
    would. Pinning shutil.disk_usage makes the expected number exact.
    """
    monkeypatch.setattr(check_disk_usage.shutil, "disk_usage", lambda _: (1000, 250, 750))
    assert check_disk_usage.usage_percent(tmp_path) == 25.0


def test_usage_percent_reads_the_real_filesystem(tmp_path):
    """The mocked test above never calls the real thing; this one does."""
    assert 0.0 <= check_disk_usage.usage_percent(tmp_path) <= 100.0


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
    # "/opt/logs" rather than "/tmp" on purpose. The path here is arbitrary,
    # the test only checks that argv wins over the config file, and ruff's
    # S108 flags a hardcoded "/tmp" literal even in an assertion that writes
    # nothing. Picking a path that is not a temp directory keeps the rule at
    # full strength instead of carrying a noqa that someone has to re-evaluate
    # later.
    args = check_disk_usage.parse_args(
        ["--path", "/opt/logs", "--threshold", "10"],
        {"log_dir": "/srv/data", "disk_threshold_percent": 75},
    )
    assert args.path == Path("/opt/logs")
    assert args.threshold == 10.0


# ---------------------------------------------------------------------------
# main: the three exit codes are the script's contract
# ---------------------------------------------------------------------------


def test_main_returns_2_for_a_path_that_does_not_exist(tmp_path, capsys):
    code = check_disk_usage.main(["--path", str(tmp_path / "absent")])
    assert code == 2
    assert "does not exist" in capsys.readouterr().err


def test_main_returns_0_below_the_threshold(monkeypatch, tmp_path, capsys):
    """Pinned at 25% so the outcome does not depend on the host's disk.

    This read the real filesystem against `--threshold 100` before, which is
    only correct while usage is under 100%. On a full disk `percent >=
    threshold` holds and the test fails for a reason that has nothing to do
    with the code.
    """
    monkeypatch.setattr(check_disk_usage.shutil, "disk_usage", lambda _: (1000, 250, 750))
    code = check_disk_usage.main(["--path", str(tmp_path), "--threshold", "90"])
    assert code == 0
    assert "25.0% used" in capsys.readouterr().out


def test_main_returns_1_above_the_threshold(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(check_disk_usage.shutil, "disk_usage", lambda _: (1000, 950, 50))
    code = check_disk_usage.main(["--path", str(tmp_path), "--threshold", "90"])
    assert code == 1
    assert "at or above" in capsys.readouterr().err


def test_main_treats_the_threshold_as_inclusive(monkeypatch, tmp_path, capsys):
    """Exactly at the threshold warns, because the comparison is `>=`.

    The old version of this test used `--threshold 0`, which is met by any
    usage at all and so passed whether the boundary was `>` or `>=`.
    """
    monkeypatch.setattr(check_disk_usage.shutil, "disk_usage", lambda _: (1000, 900, 100))
    code = check_disk_usage.main(["--path", str(tmp_path), "--threshold", "90"])
    assert code == 1
    assert "at or above" in capsys.readouterr().err
