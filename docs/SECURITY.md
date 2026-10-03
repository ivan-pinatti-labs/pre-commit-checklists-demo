# Security Vulnerabilities

Please report through the GitHub Report Security Issues page:
<https://github.com/ivan-pinatti-labs/pre-commit-checklists-demo/security/advisories/new>

## What scans what

| Code | Scanned by | Where |
| --- | --- | --- |
| `rotate-logs.sh` | shellcheck, shfmt, shebang checks | `checklist-dev-shell`, every commit |
| Python | ruff, check-ast, debug-statements | `checklist-dev-python`, every commit |
| `Dockerfile` | hadolint | `checklist-dev-docker`, every commit |
| `.github/workflows/*` | actionlint, zizmor | `checklist-github-actions`, every commit |
| Everything | detect-secrets | `checklist-security-credentials`, every commit |
| Everything SonarQube Cloud has an analyzer for: Python, shell, the `Dockerfile`, YAML, `.github/workflows/*`, secrets | SonarQube Cloud, Sonar way quality gate, plus 100% coverage of the Python and the shell | `sonarqube.yml`, every pull request from a branch of this repository and every push to `main` |

Two layers, deliberately. The pre-commit hooks fail before anything is
pushed; SonarQube Cloud reads the whole repository at once on every pull
request from a branch of this repository (a fork's pull request cannot
receive its token, so a maintainer pushes the branch here first). Neither
replaces the other: SonarQube's shell rules are few and different from
shellcheck's, not a superset of them.

SonarQube Cloud replaced CodeQL here, both `codeql.yml` and the
GitHub-managed Code Quality setup. CodeQL only ever analyzed the Python, and
it cannot read shell or a `Dockerfile` at all. Its old alerts in the Security
tab stop updating; they are history, not current findings.

The quality gate is the Free plan's built-in "Sonar way", which cannot be
edited. It fails when new code is rated below A for reliability, security or
maintainability, when a new security hotspot is left unreviewed, when less
than 80% of new code is covered, or when more than 3% of it is duplicated.
On a change under 20 new lines SonarQube Cloud skips the coverage and
duplication conditions; the 100% gate below still applies. A new bug or
vulnerability always fails it; a code smell does once the new code's
technical debt passes the A threshold. Editing a line makes it new code, so
an old finding on that line counts against the pull request.
Fix what a rule asks for, or mark the single finding false positive or
accepted in SonarQube Cloud with the reason; no `# NOSONAR` comments.
