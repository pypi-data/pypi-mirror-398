# Contributing to VibeGate

Thanks for helping improve VibeGate! This guide covers local setup, style rules, and how to add new checks while keeping the system deterministic.

## Development setup

1) Ensure Python 3.10+ is available.
2) Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

If you use uv, the equivalent is:

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

3) Install pre-commit hooks (recommended):

```bash
pre-commit install
pre-commit install --hook-type commit-msg
```

This sets up automatic code quality checks and commit message validation that run before each commit.

## Running tests and checks

```bash
pytest
ruff check .
ruff format --check .
pyright
```

To apply formatting locally:

```bash
ruff format .
```

To run VibeGate from source without relying on the console script:

```bash
python -m vibegate check .
```

To reproduce the CI smoke workflow locally (build wheel, install, run checks):

```bash
./scripts/ci_smoke.sh
```

On Windows:

```powershell
./scripts/ci_smoke.ps1
```

## Commit message format

VibeGate uses [Conventional Commits](https://www.conventionalcommits.org/) for automated version bumping and changelog generation.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature (triggers minor version bump)
- **fix**: Bug fix (triggers patch version bump)
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring (triggers patch version bump)
- **perf**: Performance improvements (triggers patch version bump)
- **test**: Test additions or updates
- **build**: Build system or dependency changes
- **ci**: CI configuration changes
- **chore**: Maintenance tasks

### Scope (optional)

The scope specifies what part of the codebase is affected:
- `cli`: CLI commands
- `runner`: Check orchestration
- `checks`: Check implementations
- `config`: Configuration handling
- `plugins`: Plugin system
- `deps`: Dependencies

### Examples

```bash
feat(cli): add new doctor command to check tool versions
fix(checks): correct parsing of pyright output
docs: update RELEASING.md with semantic-release workflow
refactor(runner): simplify fingerprint generation logic
chore(deps): update ruff to 0.14.9
```

### Breaking Changes

For breaking changes, add `!` after the type/scope and include `BREAKING CHANGE:` in the footer:

```bash
feat(config)!: remove deprecated check configuration

BREAKING CHANGE: The old check format is no longer supported.
Migrate to the new format described in the migration guide.
```

## Submitting pull requests

1) Fork the repository and create a feature branch from `main`.
2) Make focused changes with **conventional commit messages** (see above).
3) Run the test and lint commands before opening a PR (or install pre-commit hooks).
4) Open a pull request using the PR template, describing what changed, why, and how to test it.
5) Ensure all CI checks pass, including commit message validation.

### PR Title

Your PR title should also follow conventional commits format, as it will be used in the changelog:

```
feat(cli): add new doctor command
fix(checks): correct pyright output parsing
docs: update contributing guide
```

## Adding a new check

1) **Define the config** in `src/vibegate/config.py` (look for existing `*Check` dataclasses and the `VibeGateConfig` tree).
2) **Wire the schema** in `schema/vibegate.schema.json` so the check can be configured from `vibegate.yaml`.
   - After editing schemas, run `python scripts/sync_schemas.py` (or `make sync-schemas`) to update the packaged copies.
3) **Implement the runner** in `src/vibegate/checks.py` by adding a `run_*` function that returns a `CheckOutcome` and uses `run_tool` for command execution.
4) **Register it in orchestration** in `src/vibegate/runner.py` so it is executed and its artifacts are captured.
5) **Update docs/tests** as needed in `README.md`, `docs/`, and `tests/` to reflect the new check.

## Determinism expectations

VibeGate is designed to be deterministic and reproducible.

- Avoid network access during checks unless the check is explicitly about network behavior.
- Sort or stabilize any list output before emitting findings.
- Record tool versions using existing helpers (e.g., `tool_version`).
- Keep check outputs reproducible: avoid timestamps in user-visible artifacts unless they are part of the canonical evidence format.
- Prefer fixed tool versions and pinned dependencies.

If you are unsure whether a change impacts determinism, call it out in your PR and add coverage in tests.
