# Development container for pre-commit-checklists-demo: everything this
# repository's hooks, test suite and image build need, on top of the
# organization's shared base image. See .devcontainer/README.md for how to
# start it and why each run argument is there.
#
# The base image is pinned by digest. BASE_IMAGE is a build argument only so a
# change to the base image can be tested against this repository before it is
# published.
ARG BASE_IMAGE=ghcr.io/ivan-pinatti-labs/devcontainer-base@sha256:32c98c5e822a95028b08a6d388374f2a342bd72be33969f04e73aa1efe988044
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

USER 1000:1000

# Every asdf plugin, from its repository URL at the commit
# .devcontainer/asdf-plugins pins, never by short name from asdf's plugin
# index. A tool in .tool-versions with no pinned plugin has no plugin at all
# here, so `asdf install` below fails instead of fetching one unreviewed.
COPY --chown=1000:1000 .devcontainer/asdf-plugins /tmp/tool-versions/asdf-plugins
RUN while read -r name url _ commit; do \
    case "${name}" in '' | '#'*) continue ;; esac; \
    asdf plugin add "${name}" "${url}" \
      && git -C "${ASDF_DATA_DIR}/plugins/${name}" checkout --quiet "${commit}" \
      || exit 1; \
  done < /tmp/tool-versions/asdf-plugins

# Every tool .tool-versions pins, installed from that file. It is copied to a
# scratch directory and removed afterwards rather than left in the home
# directory, where asdf would treat it as a global fallback: a tool this
# repository does not pin should be missing in this container, not silently
# supplied.
COPY --chown=1000:1000 .tool-versions /tmp/tool-versions/.tool-versions
WORKDIR /tmp/tool-versions
RUN asdf install \
  && rm -rf /tmp/tool-versions

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
