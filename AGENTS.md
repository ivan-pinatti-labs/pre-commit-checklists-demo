# pre-commit-checklists-demo agent instructions

Instructions for AI coding agents working in this repository. Claude Code
reads them through `CLAUDE.md`; Codex and CodeRabbit read this file
directly.

## Organization conventions

Shared by every `ivan-pinatti-labs` repository and kept identical across
them, so change it everywhere at once. Where this repository's own sections
are more specific, follow them.

### Everything here is public

- Nothing sensitive, controversial or borderline goes into a commit, pull
  request, issue, comment or committed agent file. That includes secrets,
  tokens, personal paths, email addresses other than a GitHub noreply one,
  host names, LAN addresses and details of anyone's own deployment.
- Personal or machine specific material stays in gitignored files:
  `CLAUDE.local.md` for notes, `.claude/settings.local.json` for settings,
  `.claude/agents/local/` for agents.
- Sensitive content found already committed is reported to a maintainer.
  Never rewrite history or force push to remove it.

### Run binaries in containers, not on the host

A binary that did not come from the operating system's package manager or a
version manager such as asdf (a release download, an installer script, a new
version under evaluation, a scanner, a debugging tool) runs inside a rootless
Podman container, never directly on the host. That holds when validating,
testing, checking a new version and debugging.

```bash
podman run --rm --network=none \
  -v "<only what it needs>:/work:ro,Z" -w /work \
  <image> <binary> [args]
```

- The container gets what the process needs and nothing else. Mount only the
  specific files and folders required, read only. Add network access or
  `:rw` only when the task requires it, and say so.
- Prefer the tool's official image, pinned to a version. For a bare release
  binary use `debian:13-slim` rather than Alpine: glibc builds fail on musl
  with a misleading "No such file or directory".
- On SELinux hosts a bind mount needs a label (`Z`). Do not relabel a large
  tree that other containers also use; copy what is needed into a scratch
  directory and mount that.
- Podman is the default container runtime: rootless, with no daemon.
- Exceptions: the hook environments pre-commit builds, and the containers
  this repository's own `Makefile` or hooks start.

### Parallel work uses worktrees

More than one agent may work in a repository at the same time. Give each task
its own worktree under `.claude/worktrees/<branch>` (gitignored), and never
switch branches in a checkout someone else may be using.

### Writing style

Do not use a hyphen, em dash or en dash as punctuation in prose, code
comments, commit messages or pull request text. Use commas, parentheses or
separate sentences. Hyphens inside compound words and in code, paths, flags
and identifiers are fine.

### Commits and pull requests

- Conventional Commits with an imperative subject. Branch names are lowercase
  slugs such as `fix/flaky-test`. Never commit directly to `main`.
- Open a pull request as a draft and mark it ready once the checks are green;
  marking it ready is what starts CodeRabbit. `docs/MERGE_PIPELINE.md` is the
  authority on required checks and how a pull request merges.
- Answer every CodeRabbit comment on its thread, and say plainly when
  declining one and why.
- Never force push.
- Never add AI attribution: no AI `Co-Authored-By` trailer and no "Generated
  with" line, in commits, pull requests, comments, issues or docs.

## What this repository is

A small, realistic project that consumes `pre-commit-checklists` the way a
real user would: a log rotation and disk usage utility wired up to the
library's hook ids, so people can see the library working before adopting it.

- Every file exists to exercise one or more hook ids. The "What's here" table
  in `README.md` maps each file to the hook ids it exercises; keep it in step
  whenever a file or a hook id is added, removed or renamed.
- Only wire a hook id up when there is a genuine file for it to check. A hook
  id with nothing to check is left out of `.pre-commit-config.yaml` on
  purpose, and `README.md` says why.
- Keep changes representative of how a real consumer adopts the library:
  `.pre-commit-config.yaml` pins a released `rev:` tag, and the tool configs
  (`.editorconfig`, `.yamllint.yml`, `.markdownlint.yaml`, `.cspell.json`)
  were copied from the library's `templates/` directory. When one of those
  configs needs a change, check whether the library's template needs the
  same change.
- `checklist-dev-docker` runs `hadolint-docker` through pre-commit's
  `docker_image` language, which calls the `docker` binary specifically.
