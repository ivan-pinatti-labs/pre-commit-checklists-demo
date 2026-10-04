# Tasks for this repository.
#
# checkmake reads only the first physical line of a .PHONY declaration and
# silently drops backslash continuations, so every .PHONY here is written on
# one line. Splitting one across lines leaves the trailing targets invisible
# to it, and the phonydeclared and minphony rules then report them as
# undeclared. Tracked upstream as checkmake#280.
.PHONY: all help test coverage print-shell-scripts workbench-help

# Bare `make` shows the target list rather than doing something surprising.
# checkmake's minphony rule also wants `all` declared phony; see checkmake.ini.
all: help

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
		'  test                        Run the test suite in the pinned Python image.' \
		'  coverage                    Python and shell coverage in containers, 100% or fail.' \
		'  print-shell-scripts         List the shell scripts coverage measures.' \
		''
	@$(MAKE) --no-print-directory workbench-help

# Coverage of everything this repository writes, held at 100%: the Python
# (lines and branches, .coveragerc) under coverage.py, and the shell (lines;
# kcov reports no branches for bash) under kcov. Writes the two reports
# SonarQube Cloud reads, $(COVERAGE_DIR)/coverage.xml and
# $(COVERAGE_DIR)/shell.xml, and fails if either language is under 100%.
# .github/workflows/sonarqube.yml runs this, and so does the `coverage`
# pre-push hook.
#
# Both tools run in containers that cannot see this checkout. The files git
# would commit (tracked, plus new ones not ignored) go in on standard input
# as a tar stream, and the only host path either container gets is an empty
# scratch directory for its report. Nothing else is mounted: no home
# directory, no SSH agent, no token, and podman passes no environment
# variable that is not named. Both drop every capability; kcov also gets no
# network and a read only root filesystem. The Python container needs the
# network for its pip install. The images are pinned by digest, and Renovate
# moves the digests.
#
# The scratch directory comes from mktemp, so it lands in TMPDIR. In a
# devcontainer-airlock workbench run this as `l2 --engine --net -- make
# coverage`: the engine can only mount paths under the TMPDIR it sets.
#
# Both reports are written before either verdict is given, so CI can still
# hand SonarQube the report of a run that falls short.
COVERAGE_DIR ?= coverage
PODMAN ?= $(if $(CONTAINER_HOST),podman-remote,podman)
# renovate: datasource=docker depName=docker.io/library/python
PYTHON_IMAGE ?= docker.io/library/python:3.14-slim@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151
# renovate: datasource=docker depName=docker.io/kcov/kcov
KCOV_IMAGE ?= docker.io/kcov/kcov:latest@sha256:481289ae32e55e5b733019515acd10948a4f76dfed381765577db909664fc603
# The shell scripts coverage measures, found rather than listed, so a new
# one is held to 100% the moment it exists: every file git would commit
# (tracked, plus new ones not ignored) that ends in .sh or .bash, or whose
# first line is a shebang running sh, bash or dash, except the tests under
# tests/. A path deleted in the working tree is dropped (awk cannot open it,
# and its error is discarded). SHELL_EXCLUDE takes vendored or third party
# paths out, each with a comment saying why; SHELL_EXTRA adds shell files
# neither the extension nor a shebang identifies. Both are empty today.
# tests/test_shell_discovery.py checks this rule and what it finds.
SHELL_EXCLUDE :=
SHELL_EXTRA :=
# A script name outside [A-Za-z0-9._/+-] would reach the recipes as shell text
# (a committed `x;id;#.sh` would run `id`), so discovery marks it UNSAFE: and
# make stops here instead.
_shell_safe = $(if $(filter UNSAFE:,$(1)),$(error a shell script name holds a character outside A-Za-z0-9._/+-; rename it),$(1))
SHELL_SCRIPTS := $(call _shell_safe,$(sort $(filter-out $(SHELL_EXCLUDE),$(shell git ls-files -z --cached --others --exclude-standard | xargs -0 sh -c 'for f do if [ -f "$$f" ]; then printf "%s\0" "$$f"; fi; done' sh | xargs -0 awk 'FNR == 1 { if (FILENAME ~ /\.(sh|bash)$$/ || $$0 ~ /^#![[:space:]]*([^[:space:]]*\/)?(env[[:space:]]+(-[^[:space:]]+[[:space:]]+)*)?(ba|da)?sh([[:space:]]|$$)/) print (FILENAME ~ /^[A-Za-z0-9._\/+-]+$$/ ? FILENAME : "UNSAFE:"); nextfile }' 2>/dev/null | grep -v '^tests/')) $(SHELL_EXTRA)))
_comma := ,
_empty :=
_space := $(_empty) $(_empty)

# Builds $$out/src.tar: the files git would commit (tracked, plus new ones
# not ignored), minus any deleted in the working tree, each step checked,
# so the containers never measure a partial tree.
_sources := git ls-files -z --cached --others --exclude-standard --deduplicate \
		>"$$out/all" || exit 1; \
	xargs -0 sh -c 'for f do if [ -e "$$f" ] || [ -L "$$f" ]; then printf "%s\0" "$$f"; fi; done' sh \
		<"$$out/all" >"$$out/list" || exit 1; \
	tar --create --owner=0 --group=0 --numeric-owner --null --files-from="$$out/list" --file="$$out/src.tar" || exit 1
_unpack := set -e; mkdir /tmp/w; tar -x --no-same-owner -C /tmp/w; cd /tmp/w
_locked := --cap-drop=ALL --security-opt no-new-privileges
_pip_install := pip install --quiet --disable-pip-version-check --root-user-action=ignore \
	--require-hashes --only-binary=:all: -r tests/requirements.txt

# The test suite, in the same pinned Python image `make coverage` uses, so
# the tests run on one interpreter everywhere and never on the host's Python.
# The container is locked down the same way: the source goes in as the tar
# stream above, nothing is mounted, every capability is dropped. It needs the
# network for its pip install from the hash locked tests/requirements.txt.
# In a devcontainer-airlock workbench run this as `l2 --engine --net -- make
# test`.
test:
	@set -u; out="$$(mktemp -d)"; trap 'rm -rf "$$out"' EXIT; \
	$(_sources); \
	$(PODMAN) run <"$$out/src.tar" --rm --interactive $(_locked) \
		"$(PYTHON_IMAGE)" sh -c '$(_unpack); $(_pip_install); python -m pytest tests'

print-shell-scripts:
	@printf '%s\n' $(SHELL_SCRIPTS)

coverage:
	@set -u; out="$$(mktemp -d)"; trap 'rm -rf "$$out"' EXIT; \
	$(_sources); \
	mkdir "$$out/python" "$$out/shell"; py=0; sh=0; \
	$(PODMAN) run <"$$out/src.tar" --rm --interactive $(_locked) \
		-v "$$out/python:/out:rw,Z" "$(PYTHON_IMAGE)" sh -c '$(_unpack); \
			$(_pip_install); \
			coverage run -m pytest tests -q; \
			coverage xml -q --fail-under=0 -o /out/coverage.xml; \
			coverage report' || py=$$?; \
	$(PODMAN) run <"$$out/src.tar" --rm --interactive $(_locked) \
		--network=none --read-only --tmpfs /tmp \
		-v "$$out/shell:/out:rw,Z" "$(KCOV_IMAGE)" sh -c '$(_unpack); \
			kcov --include-path=$(subst $(_space),$(_comma),$(addprefix /tmp/w/,$(SHELL_SCRIPTS))) /out/kcov \
				tests/rotate-logs.test.sh; \
			python3 scripts/kcov_to_sonar.py /tmp/w /out/kcov/rotate-logs.test.sh.*/cobertura.xml \
				/out/shell.xml $(SHELL_SCRIPTS)' || sh=$$?; \
	mkdir -p "$(COVERAGE_DIR)" && rm -f "$(COVERAGE_DIR)/coverage.xml" "$(COVERAGE_DIR)/shell.xml" || exit 1; \
	for report in "$$out/python/coverage.xml" "$$out/shell/shell.xml"; do \
		if [ -f "$$report" ]; then cp "$$report" "$(COVERAGE_DIR)"/ || exit 1; fi; \
	done; \
	test "$$py" -eq 0 && test "$$sh" -eq 0 && \
		test -s "$(COVERAGE_DIR)/coverage.xml" && test -s "$(COVERAGE_DIR)/shell.xml"
