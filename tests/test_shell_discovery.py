"""Check the rule the Makefile uses to find the shell scripts coverage measures.

`make coverage` holds every shell script this repository writes at 100% of
its lines, and finds those scripts rather than reading a hand written list:
a file git would commit that ends in .sh or .bash, or whose first line is a
shebang running sh, bash or dash, except the tests under tests/, minus
SHELL_EXCLUDE, plus SHELL_EXTRA.

These tests run where the rest of the suite runs, including the coverage
container, which has the tree but no .git and no git. So they apply the same
rule in Python over the files present, check it finds the scripts this
repository is known to have and nothing under tests/, check the `coverage`
pre-push hook would fire for each of them, and check the Makefile still
holds the discovery rule, so a hand list cannot creep back in.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = REPO_ROOT / "Makefile"
PRE_COMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"

# The same two tests the Makefile's awk program applies, on the file name and
# on the first line.
SHELL_NAME = re.compile(r"\.(sh|bash)$")
SHELL_SHEBANG = re.compile(r"^#![ \t]*([^ \t]*/)?(env[ \t]+(-[^ \t]+[ \t]+)*)?(ba|da)?sh([ \t]|$)")
# Not what git would commit: its own data, and the .gitignore entries that
# can hold a file here (caches, virtual environments, reports, worktrees).
SKIPPED_DIRS = {
    ".git",
    ".claude",
    ".ruff_cache",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
    "coverage",
    "node_modules",
}
# Scripts this repository is known to have. Every one has to be found.
KNOWN_SCRIPTS = {"rotate-logs.sh"}


def is_shell_script(path: Path) -> bool:
    if SHELL_NAME.search(path.name):
        return True
    try:
        with path.open("rb") as handle:
            first = handle.readline().decode("utf-8", "replace").rstrip("\r\n")
    except OSError:
        return False
    return bool(SHELL_SHEBANG.search(first))


def discover(root: Path) -> set[str]:
    """The Makefile's rule, over the files present under `root`."""
    found = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in SKIPPED_DIRS for part in relative.parts):
            continue
        if not path.is_file() or relative.parts[0] == "tests":
            continue
        if is_shell_script(path):
            found.add(relative.as_posix())
    return found


def makefile_list(name: str) -> list[str]:
    match = re.search(rf"^{name} :=(.*)$", MAKEFILE.read_text(), re.MULTILINE)
    assert match, f"{MAKEFILE.name} no longer defines {name}"
    return match.group(1).split()


def test_the_rule_recognizes_shell_by_name_or_shebang(tmp_path):
    files = {
        "a.sh": "echo\n",
        "b.bash": "echo\n",
        "c": "#!/bin/sh\n",
        "d": "#!/usr/bin/env bash\n",
        "e": "#!/usr/bin/env -S bash -e\n",
        "f": "#! /bin/dash\n",
        "g": "#!/usr/bin/env python3\n",
        "h": "#!/usr/bin/bashful\n",
        "i.txt": "echo\n",
        "tests/t.sh": "#!/bin/sh\n",
    }
    for name, text in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text)
    assert discover(tmp_path) == {"a.sh", "b.bash", "c", "d", "e", "f"}


def test_discovery_finds_the_known_scripts_and_no_tests():
    found = discover(REPO_ROOT) - set(makefile_list("SHELL_EXCLUDE"))
    found |= set(makefile_list("SHELL_EXTRA"))
    assert KNOWN_SCRIPTS <= found, f"discovery missed {sorted(KNOWN_SCRIPTS - found)}"
    assert not [path for path in found if path.startswith("tests/")]


def test_the_coverage_hook_fires_for_every_discovered_script():
    match = re.search(
        r"- id: coverage\n(?:\s+\w+:.*\n)*?\s+files: '(?P<files>[^']+)'",
        PRE_COMMIT_CONFIG.read_text(),
    )
    assert match, f"no files: pattern on the coverage hook in {PRE_COMMIT_CONFIG.name}"
    pattern = re.compile(match.group("files"))
    missed = sorted(path for path in discover(REPO_ROOT) if not pattern.search(path))
    assert not missed, f"the coverage hook would not run when these change: {missed}"


def test_the_makefile_discovers_rather_than_lists():
    text = MAKEFILE.read_text()
    definition = re.search(r"^SHELL_SCRIPTS :=(.*)$", text, re.MULTILINE)
    assert definition, f"{MAKEFILE.name} no longer defines SHELL_SCRIPTS"
    rule = definition.group(1)
    for piece in (
        "git ls-files -z --cached --others --exclude-standard",
        "xargs -0 awk",
        r"\.(sh|bash)$$",
        "(ba|da)?sh",
        "grep -v '^tests/'",
        "$(filter-out $(SHELL_EXCLUDE)",
        "$(SHELL_EXTRA)",
    ):
        assert piece in rule, f"SHELL_SCRIPTS in {MAKEFILE.name} lost {piece!r}"
