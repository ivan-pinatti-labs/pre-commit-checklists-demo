# Development container for pre-commit-checklists-demo: everything this
# repository's hooks, test suite and image build need, on top of the
# organization's shared base image. See .devcontainer/README.md for how to
# start it and why each run argument is there.
#
# The base image is pinned by digest. BASE_IMAGE is a build argument only so a
# change to the base image can be tested against this repository before it is
# published.
ARG BASE_IMAGE=ghcr.io/ivan-pinatti-labs/devcontainer-base@sha256:db75fbbf8972f6f1d7746c06238fbf15a387e224947e0e0dd5bf4d5fe3844d0b
FROM ${BASE_IMAGE}

USER 0:0

# python3-venv: the test dependencies go into a virtual environment, because
# Ubuntu marks its own Python as externally managed and pip refuses to install
# into it.
#
# Unpinned for the same reason as in the base image: Ubuntu ships security
# fixes by moving a package's version within a release.
# hadolint ignore=DL3008
RUN apt-get update \
  && apt-get install -y --no-install-recommends python3-venv \
  && rm -rf /var/lib/apt/lists/*

# github-cli from GitHub's own signed repository, whose key the base image
# checks against a fingerprint and installs without enabling the repository,
# so the source entry here is what opts in. pre-commit from Ubuntu.
#
# Versions are deliberately unpinned: Ubuntu and GitHub both ship security
# fixes by moving a version inside a release. That makes this layer rolling
# rather than reproducible, and the two should not be confused: the digest
# above fixes what this builds on and says nothing about what apt resolves on
# top. See the base image's docs/TOOL_SOURCES.md.
# hadolint ignore=DL3008
RUN printf '%s\n' \
      'deb [arch=amd64 signed-by=/usr/share/keyrings/github-cli.gpg] https://cli.github.com/packages stable main' \
      > /etc/apt/sources.list.d/github-cli.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
    gh \
    pre-commit \
  && rm -rf /var/lib/apt/lists/*

USER 1000:1000

# The demo's own dependency and its test suite's, from the same two
# requirements files CI installs.
ENV VIRTUAL_ENV=/home/dev/.local/share/demo/tests-venv
COPY --chown=1000:1000 requirements.txt /tmp/deps/requirements.txt
COPY --chown=1000:1000 tests/requirements.txt /tmp/deps/tests-requirements.txt
RUN python3 -m venv "${VIRTUAL_ENV}" \
  && "${VIRTUAL_ENV}/bin/pip" install --no-cache-dir \
    --requirement /tmp/deps/requirements.txt \
    --requirement /tmp/deps/tests-requirements.txt \
  && rm -rf /tmp/deps
ENV PATH=${VIRTUAL_ENV}/bin:${PATH}

WORKDIR /workspace
