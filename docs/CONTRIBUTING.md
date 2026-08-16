# Contributing

Your inputs and ideas are welcome. The goal is to make contributing to this
project as easy and transparent as possible, whether it's:

- Reporting a bug in one of the sample files or the demo's own config
- Discussing whether a hook id is wired up the way a real consumer would do it
- Submitting a fix
- Proposing a new sample file that exercises a hook id this demo doesn't
  cover yet
- Becoming a maintainer

## GitHub Flow

This project uses [GitHub Flow](https://guides.github.com/introduction/flow/index.html),
so all code changes happen through pull requests.

1. Fork the repo and create your branch from `main`.
2. Install [`pre-commit`](https://pre-commit.com/#install) and
   [`detect-secrets`](https://github.com/Yelp/detect-secrets) if you don't
   have them yet, then run `pre-commit install` in your clone. `git clone`
   does not carry hooks over, so do this in every clone, including
   throwaway ones.
3. Make your change. `pre-commit run --all-files` runs the same checklists
   this demo consumes from the library; see
   [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) for exactly
   which hook ids and at which git stage.
4. If you're adding a sample file to exercise a hook id this demo doesn't
   wire up yet, add both the file and the hook id entry, and update the
   "What's here" table in [`README.md`](../README.md) to match.
5. Open the pull request as a **draft**. Mark it ready once it's green.
6. Adhere to [Conventional Commits](https://www.conventionalcommits.org/)
   for your commit messages and PR title.
7. Issue the pull request.

## Any contributions you make will be under the Apache License 2.0

In short, when you submit code changes, your submissions are understood to be
under the same [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
that covers the project. Feel free to contact the maintainer if that's a
concern.

## Report bugs using GitHub's issues

Bugs are tracked as
[GitHub issues](https://github.com/ivan-pinatti/pre-commit-checklists-demo/issues);
report one by
[opening a new issue](https://github.com/ivan-pinatti/pre-commit-checklists-demo/issues/new).

## Write bug reports with detail and background

A good bug report names the hook id, the `rev:` the library is pinned to
here, the file that triggered (or should have triggered) it, and what you
expected instead.

## Use a Consistent Coding Style

- 2 spaces for indentation, not tabs, matching [`.editorconfig`](../.editorconfig).
- `rotate-logs.sh` uses `#!/usr/bin/env bash` with the explicit
  `set -o errexit`, `set -o pipefail`, `set -o nounset` trio, checked by
  `checklist-dev-shell`.
- Run `pre-commit run --all-files` before pushing.

## License

By contributing, you agree that your contributions will be licensed under
the Apache License 2.0.

## References

This document was adapted from the GitHub Gist
<https://gist.github.com/briandk/3d2e8b3ec8daf5a27a62>.

---

See also: [README.md](../README.md)
