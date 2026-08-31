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

## License

By contributing, you agree that your contributions will be licensed under
the Apache License 2.0.

---

See also: [README.md](../README.md)
