# Contributing

This repository is a worked example of consuming the pre-commit-checklists
library, not the library itself. For the conventions that apply to any
change here (forking, installing pre-commit, Conventional Commits, opening
a draft pull request), see the library's own
[CONTRIBUTING.md](https://github.com/ivan-pinatti-labs/pre-commit-checklists/blob/main/docs/CONTRIBUTING.md).

Bugs and ideas specific to this demo: open an issue at
[ivan-pinatti-labs/pre-commit-checklists-demo](https://github.com/ivan-pinatti-labs/pre-commit-checklists-demo/issues/new).

## What contributions here look like

- Reporting a sample file, or this demo's own config, that does not
  exercise a hook id the way a real consumer would.
- Adding a sample file that exercises a hook id this demo doesn't wire up
  yet. Add both the file and the hook id entry to
  [`.pre-commit-config.yaml`](../.pre-commit-config.yaml), and update the
  "What's here" table in [`README.md`](../README.md) to match.
- Bumping the `rev:` this demo is pinned to, once a new library release
  ships.

## Running the checks

Install [`pre-commit`](https://pre-commit.com/#install) and
[`detect-secrets`](https://github.com/Yelp/detect-secrets) if you don't
have them yet, then run `pre-commit install` in your clone. `git clone`
does not carry hooks over, so do this in every clone, including throwaway
ones. You'll also need Docker on `PATH` for the Dockerfile checklist.

`pre-commit run --all-files` runs the same checklists this demo consumes
from the library; see [`.pre-commit-config.yaml`](../.pre-commit-config.yaml)
for exactly which hook ids and at which git stage.

`make coverage` runs the Python tests under coverage.py and the shell tests
under kcov, each in a podman container, and fails unless both reach 100%: the
Python by lines and branches, the shell by lines. It needs podman on `PATH`.
It also runs as a pre-push hook, so run `pre-commit install` again in an
existing clone to pick up the pre-push stage. A new script ships with tests
that reach every line of it. The shell scripts measured are not listed by
hand: the Makefile finds every `.sh` or `.bash` file, and every file whose
shebang runs `sh`, `bash` or `dash`, outside `tests/`, so a new one is held
to 100% as soon as it exists. `make print-shell-scripts` shows the set, and
`SHELL_EXCLUDE` in the Makefile takes a vendored script out of it.

## Updating the Python dependencies

`requirements.in` (the runtime pyyaml) and `tests/requirements.in` (the test
environment) carry the exact pins. Each `requirements.txt` next to them is a
lock compiled from it with every hash, which `pip install --require-hashes`
checks. Renovate bumps both. To change one by hand, edit the `.in` file and
regenerate the lock in a container, from that file's directory:

```bash
podman run --rm -v "$PWD:/w:rw,Z" -w /w ghcr.io/astral-sh/uv:python3.14-trixie-slim \
  uv pip compile --generate-hashes --python-version=3.14 --exclude-newer=P7D \
  --output-file=requirements.txt requirements.in
```

That is the command in the lock's own header, which Renovate replays.
`--exclude-newer=P7D` leaves out anything released in the last seven days,
dependencies of dependencies included. Keep pyyaml's pin equal in both `.in`
files.

### A security fix younger than seven days

The seven day window also holds back a security release, and Renovate
cannot make an exception: it replays the header's command as written, so its
pull request for a vulnerability alert fails to regenerate the lock and says
so. Update that one package by hand, in the same container and from the
lock's directory, letting it past the window and asking for its newest
release (`--upgrade-package`; without it, uv keeps the version already in the
lock, so a vulnerable dependency of a dependency would not move):

```bash
podman run --rm -v "$PWD:/w:rw,Z" -w /w ghcr.io/astral-sh/uv:python3.14-trixie-slim \
  uv pip compile --generate-hashes --python-version=3.14 --exclude-newer=P7D \
  --exclude-newer-package "<package>=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --upgrade-package "<package>" \
  --output-file=requirements.txt requirements.in
```

Then edit the lock's header back to the standard command above, by hand,
removing `--exclude-newer-package` (uv does not record `--upgrade-package`
there). Left in, the per package date is fixed, so it would hold that
package at today's releases for good. Read the lock's diff before
committing: the other pins are kept as preferences, not guarantees, so uv
moves another package too when the fix needs it, and each such move gets
the same review as the fix. The next Renovate update replays the standard
command once the fix is past the window.

## License

By contributing, you agree that your contributions will be licensed under
the Apache License 2.0.

---

See also: [README.md](../README.md)
