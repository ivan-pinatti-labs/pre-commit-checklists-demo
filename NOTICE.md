# Notice

pre-commit-checklists-demo
Copyright 2026 Ivan Pinatti
<https://github.com/ivan-pinatti-labs/pre-commit-checklists-demo>

This product is licensed under the Apache License, Version 2.0. See
[LICENSE.md](LICENSE.md) for the full terms.

## Scope

This repository is a demo consumer of
[pre-commit-checklists](https://github.com/ivan-pinatti-labs/pre-commit-checklists):
[`.pre-commit-config.yaml`](.pre-commit-config.yaml) pins a `repo:` and
`rev:` for that library the way any real consumer would. Nothing from the
library, or from the upstream pre-commit hooks it wraps, is vendored or
copied into this repository; pre-commit clones each pinned repository
itself at run time, under that project's own license. This NOTICE does not
relicense, and is not needed to cover, code this repository never contains.
