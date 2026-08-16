# pre-commit-checklists-demo

A small, realistic project that consumes
[pre-commit-checklists](https://github.com/ivan-pinatti/pre-commit-checklists)
the way a real user would, so you can see the library working before you
adopt it yourself: real sample files, a real `.pre-commit-config.yaml`
pinned to a `rev:` tag, and real hooks catching real problems.

This is not the library itself, and not another copy of it. It is a tiny
log rotation and disk usage utility, the kind of small script collection
almost every project ends up with, wired up to twelve of the library's
hook ids.

## What's here

| File | Exercises |
| --- | --- |
| [`rotate-logs.sh`](rotate-logs.sh) | `checklist-dev-shell`, `checklist-basic` |
| [`check_disk_usage.py`](check_disk_usage.py) | `checklist-dev-python`, `checklist-basic` |
| [`requirements.txt`](requirements.txt) | `checklist-dev-python` (`requirements-txt-fixer`) |
| [`config.yaml`](config.yaml) | `checklist-yaml` |
| [`pyproject.toml`](pyproject.toml) | `checklist-toml` |
| [`README.md`](README.md) (this file) | `checklist-markdown`, `checklist-spell` |
| `.secrets.baseline` | `checklist-security-credentials` |

`.editorconfig`, `.yamllint.yml`, `.markdownlint.yaml`, and `.cspell.json`
are the tool configs the hooks above need; each was copied straight from
the library's `templates/` directory.

`checklist-git-valid-branches`, `checklist-git-commit-msg`, and
`checklist-git-protected-branches` aren't file-based; they run against your
branch name and commit message instead, see below.

Not every hook id the library ships is wired up here. There's no
`.env` file, no `.github/workflows/`, no `.tf`, `.js`, `.ts`, `.json`, or
`.xml` in this demo, so `checklist-dev-dotenv`, `checklist-github-actions`,
`checklist-dev-terraform`, `checklist-dev-javascript`,
`checklist-dev-typescript`, `checklist-json`, and `checklist-xml` are left
out of [`.pre-commit-config.yaml`](.pre-commit-config.yaml) rather than
listed with nothing to check. See the library's [hook catalogue][catalogue]
for those.

[catalogue]: https://github.com/ivan-pinatti/pre-commit-checklists/blob/main/docs/hook-catalogue.md

## How to run it

```shell
pip install pre-commit detect-secrets
pre-commit install
pre-commit run --all-files
```

Try a commit too, since the commit-msg stage above only runs on a real
`git commit`, not on `pre-commit run --all-files`:

```shell
git commit --allow-empty -m "not a conventional commit"   # rejected
git commit --allow-empty -m "docs: try the commit-msg hook"   # accepted
```

## Pointing this at the published library

`pre-commit-checklists` is not published yet, so
[`.pre-commit-config.yaml`](.pre-commit-config.yaml)'s `repo:` line points
at a local, tagged clone on the machine this demo was built on, instead of
GitHub. The mechanism pre-commit uses to fetch either one is identical, a
`git clone` of whatever `repo:` names, so the change needed once the
library is public is exactly one line: the `repo:` value itself, from

```yaml
repo: file:///home/ivan/wo/personal/pre-commit-checklists-local-clone
```

to

```yaml
repo: https://github.com/ivan-pinatti/pre-commit-checklists
```

`rev: v1.0.0` stays as it is: the local clone was tagged `v1.0.0` to match
the library's planned first release tag, precisely so this is a one-line
swap rather than a two-line one.

## What's verified, and what isn't yet

Verified on this machine, with commands and exit codes recorded when this
demo was built:

- `pre-commit run --all-files` against the local, tagged clone: every hook
  above runs and passes.
- A real `git commit` through the installed `commit-msg` hook: a
  non-conventional message is rejected, a conventional one succeeds.
- A deliberately planted fake secret was caught and blocked by
  `checklist-security-credentials` before being removed again.

Not verified, because it can't be until the library has a real tag: the
`https://github.com/...` + `rev: vX.Y.Z` path itself. The local-clone path
above exercises the same pre-commit machinery, but not GitHub's actual
hosting, auth, or archive-fetch behavior. Re-run `pre-commit run
--all-files` here after making the one-line swap once a release exists, and
treat that as the real first test of the published path, not this one.
