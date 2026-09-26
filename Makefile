# Tasks for this repository.
#
# checkmake reads only the first physical line of a .PHONY declaration and
# silently drops backslash continuations, so every .PHONY here is written on
# one line. Splitting one across lines leaves the trailing targets invisible
# to it, and the phonydeclared and minphony rules then report them as
# undeclared. Tracked upstream as checkmake#280.
.PHONY: all help test workbench-help

# Bare `make` shows the target list rather than doing something surprising.
# checkmake's minphony rule also wants `all` declared phony; see checkmake.ini.
all: help

# The test suite, with its pinned requirements, in a virtual environment kept
# in L2's own per repository home, where it survives between runs and pip
# keeps it in step with requirements.txt and tests/requirements.txt. `l2
# --net` lets pip reach PyPI through the egress proxy; outside a workbench
# there is no l2, and the same commands run as they are.
L2_NET := $(if $(shell command -v l2 2>/dev/null),l2 --net --,)
test:
	@$(L2_NET) bash -c 'set -e; v="$$HOME/.cache/tests-venv"; python3 -m venv "$$v"; "$$v/bin/pip" install --quiet --disable-pip-version-check -r requirements.txt -r tests/requirements.txt; "$$v/bin/python" -m pytest tests'

# The workbench targets (make claude, make codex, make unlock and the rest)
# come from a devcontainer-airlock clone, by default the one next to this
# repository's main clone, so every worktree finds the same one. See
# .devcontainer/README.md.
WORKBENCH_HOME ?= $(abspath $(dir $(shell git rev-parse --path-format=absolute --git-common-dir 2>/dev/null))../devcontainer-airlock)
-include $(WORKBENCH_HOME)/host/workbench.mk

ifeq ($(wildcard $(WORKBENCH_HOME)/host/workbench.mk),)
workbench-help:
	@printf '%s\n' \
		'Workbench: no devcontainer-airlock clone at $(WORKBENCH_HOME).' \
		'  Clone ivan-pinatti-labs/devcontainer-airlock there, or set WORKBENCH_HOME,' \
		'  for make claude, make codex, make unlock and the rest (.devcontainer/README.md).'
endif

help:
	@printf '%s\n' \
		'Usage:' \
		'  make <target>' \
		'' \
		'Targets:' \
		'  help                        Show this message.' \
		'  test                        Run the test suite, in L2 in a workbench.' \
		''
	@$(MAKE) --no-print-directory workbench-help
