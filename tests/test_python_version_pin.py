"""Keep every copy of "which Python this repository runs" in step.

The interpreter version is written down in several places, and nothing
derives one from another:

- `python-version` in .github/workflows/pull-request.yml, which decides the
  interpreter CI runs the hooks and the tests on;
- ruff's `target-version` in pyproject.toml, which decides which idioms and
  version dependent rules ruff grades the code against;
- `sonar.python.version` in sonar-project.properties, which SonarQube Cloud's
  Python rules judge the code against;
- every `python:3.X-...` image the Makefile pins, which `make coverage` (and
  so sonarqube.yml) measures the tests in;
- the root Dockerfile's `FROM python:3.X-...`, the hadolint fixture;
- `--python-version` in each hash lock's header, which Renovate replays.

None of these is watched for a tag change. .github/renovate.json5 disables
the `uses-with` depType (so `python-version` is never bumped), leaves the root
Dockerfile unmanaged, and lets the Makefile images move by digest only. Every
Python bump here is therefore a hand edit of several files at once, which is
exactly the kind of pairing a person forgets. This test is the reminder.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github/workflows/pull-request.yml"
RUFF_CONFIG = REPO_ROOT / "pyproject.toml"
SONAR_PROPERTIES = REPO_ROOT / "sonar-project.properties"
MAKEFILE = REPO_ROOT / "Makefile"
DOCKERFILE = REPO_ROOT / "Dockerfile"
LOCKS = [REPO_ROOT / "requirements.txt", REPO_ROOT / "tests/requirements.txt"]

# `python-version: "3.14"`, quoted, as actions/setup-python is given it. The
# quotes are not optional: YAML reads a bare 3.10 as the float 3.1, so an
# unquoted value is a bug worth failing on rather than a spelling to accept.
WORKFLOW_PYTHON = re.compile(
    r'^\s*python-version:\s*"(?P<major>\d+)\.(?P<minor>\d+)"\s*$', re.MULTILINE
)
# `target-version = "py314"`, under [tool.ruff] in pyproject.toml.
RUFF_TARGET = re.compile(r'^target-version\s*=\s*"py(?P<major>\d)(?P<minor>\d+)"\s*$', re.MULTILINE)
SONAR_PYTHON = re.compile(
    r"^sonar\.python\.version=(?P<major>\d+)\.(?P<minor>\d+)\s*$", re.MULTILINE
)
# Any python image the Makefile names, digest pinned or not.
MAKEFILE_PYTHON = re.compile(r"/python:(?P<major>\d+)\.(?P<minor>\d+)-")
DOCKERFILE_PYTHON = re.compile(r"^FROM\s+\S*python:(?P<major>\d+)\.(?P<minor>\d+)-", re.MULTILINE)
LOCK_PYTHON = re.compile(r"--python-version=(?P<major>\d+)\.(?P<minor>\d+)\b")


def ci_python() -> tuple[str, str]:
    """The one interpreter version every pull-request.yml job sets up."""
    versions = set(WORKFLOW_PYTHON.findall(WORKFLOW.read_text()))
    assert len(versions) == 1, (
        f"expected every quoted python-version in {WORKFLOW.name} to agree, "
        f"found {sorted(versions)}"
    )
    return versions.pop()


def test_ruff_target_matches_the_interpreter_ci_runs():
    ruff = RUFF_TARGET.findall(RUFF_CONFIG.read_text())
    assert ruff == [ci_python()], (
        f"{RUFF_CONFIG.name} targets {ruff} but {WORKFLOW.name} runs "
        f"{ci_python()}. Both have to move together."
    )


def test_sonar_python_version_matches_the_interpreter_ci_runs():
    sonar = SONAR_PYTHON.findall(SONAR_PROPERTIES.read_text())
    assert sonar == [ci_python()], (
        f"{SONAR_PROPERTIES.name} analyzes as {sonar} but {WORKFLOW.name} "
        f"runs {ci_python()}. Both have to move together."
    )


def test_every_makefile_python_image_runs_the_same_interpreter_as_ci():
    images = MAKEFILE_PYTHON.findall(MAKEFILE.read_text())
    assert images, f"no python image found in {MAKEFILE.name}"
    assert set(images) == {ci_python()}, (
        f"{MAKEFILE.name} pins python images {images} but {WORKFLOW.name} "
        f"runs {ci_python()}. Renovate moves only their digests, so the tag "
        "is a hand edit."
    )


def test_dockerfile_base_image_runs_the_same_interpreter_as_ci():
    base = DOCKERFILE_PYTHON.findall(DOCKERFILE.read_text())
    assert base == [ci_python()], (
        f"{DOCKERFILE.name} is based on {base} but {WORKFLOW.name} runs "
        f"{ci_python()}. Renovate leaves this file unwatched on purpose."
    )


def test_every_lock_is_compiled_for_the_interpreter_ci_runs():
    for lock in LOCKS:
        header = LOCK_PYTHON.findall(lock.read_text())
        assert header == [ci_python()], (
            f"{lock.relative_to(REPO_ROOT)} is compiled for {header} but "
            f"{WORKFLOW.name} runs {ci_python()}. Recompile it with the "
            "command in docs/CONTRIBUTING.md."
        )
