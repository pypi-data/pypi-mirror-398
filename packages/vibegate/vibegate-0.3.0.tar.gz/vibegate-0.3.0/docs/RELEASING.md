# Releasing VibeGate

This document describes how to release new versions of VibeGate.

## Overview

VibeGate uses **automated semantic versioning** for releases based on conventional commits:

1. **Use conventional commits** - All commits follow conventional commits format
2. **Merge to main** - When PRs are merged, commits are analyzed
3. **Automated release** - semantic-release determines version, updates CHANGELOG, creates tag, and publishes
4. **No manual version bumping** - Everything is automated based on commit history

## Release Methods

### Method 1: Automated Semantic Release (Recommended)

The recommended way to release VibeGate is through the automated semantic-release workflow.

**How it works:**

- Every push to `main` triggers the semantic-release workflow
- Semantic-release analyzes commits since the last release
- If releasable commits exist (`feat`, `fix`, `perf`, `refactor`), it:
  - Determines the next version (major/minor/patch) based on commit types
  - Updates `pyproject.toml`, `CHANGELOG.md`, and commitizen version
  - Creates and pushes a git tag
  - Builds and publishes to PyPI
  - Creates a GitHub Release with changelog notes

**You do nothing!** Just merge PRs with conventional commit messages.

**Version determination:**

- `feat:` commits → minor version bump (0.1.0 → 0.2.0)
- `fix:`, `perf:`, `refactor:` commits → patch version bump (0.1.0 → 0.1.1)
- `feat!:` or `BREAKING CHANGE:` → major version bump (0.1.0 → 1.0.0)
- Other commits (`docs:`, `chore:`, `ci:`, `test:`) → no release

**Example workflow:**

```bash
# Contributors make changes with conventional commits
git commit -m "feat(cli): add verbose output option"
git commit -m "fix(checks): handle empty pyright output"

# Open PR, get it reviewed and merged to main
# → semantic-release automatically runs
# → Version bumped from 0.1.0a5 to 0.2.0a1
# → CHANGELOG updated
# → Tag v0.2.0a1 created
# → Published to PyPI
# → GitHub Release created
```

### Method 2: Manual Semantic Release

If you need to manually trigger a release:

```bash
# Preview what would be released
semantic-release version --print

# Create release locally (for testing)
semantic-release version --no-push --no-tag

# Or trigger the workflow manually from GitHub Actions
# Go to Actions → "semantic release" → Run workflow
```

### Method 3: Manual Release (Legacy)

For situations where semantic-release cannot be used, manual release workflows are available but **deprecated**.

**Using prepare_release workflow (deprecated):**

1. Go to **Actions** → **"prepare release (deprecated)"** → **Run workflow**
2. Enter version manually (e.g., `0.1.0a6`)
3. Review and merge the generated PR
4. Manually create and push the tag

**Manual process:**

```bash
# 1. Update version in pyproject.toml manually
# 2. Update CHANGELOG.md manually
git add pyproject.toml CHANGELOG.md
git commit -m "chore(release): 0.1.0a6"
git push origin main

# 3. Create and push tag
git tag -a v0.1.0a6 -m "v0.1.0a6"
git push origin v0.1.0a6

# 4. The release workflow will handle PyPI publish and GitHub Release
```

## Hotfix Releases

For emergency fixes to a released version:

1. Go to **Actions** → **"hotfix release"** → **Run workflow**
2. Enter the base tag to hotfix (e.g., `v0.1.0a5`)
3. Enter a description of the hotfix
4. The workflow will:
   - Create a hotfix branch from the base tag
   - Increment the version (0.1.0a5 → 0.1.0a6)
   - Update version and CHANGELOG
   - Create a PR for review
5. Review, test, and merge the PR
6. semantic-release will publish the hotfix

**Example:**

```bash
# Input to hotfix workflow:
Base tag: v0.1.0a5
Description: Fix critical bug in check runner

# Workflow creates:
Branch: hotfix/v0.1.0a6
Version: 0.1.0a6
PR: "hotfix: Fix critical bug in check runner (v0.1.0a6)"

# After merge:
→ semantic-release publishes v0.1.0a6
```

## Prerequisites

### One-Time Setup

1. **PyPI Trusted Publisher** - Configure in PyPI project settings:
   - Owner: `maxadamsky`
   - Repository: `VibeGate`
   - Workflow: `semantic-release.yml` (or `release.yml` for manual)
   - Environment: `pypi`

2. **GitHub Environments** - Create in repository Settings → Environments:
   - `pypi` - for production PyPI releases
   - Add protection rules if desired

3. **GitHub Token** - The default `GITHUB_TOKEN` has sufficient permissions

### Local Tools

For manual semantic-release operations:

```bash
python -m pip install -e ".[dev]"
```

## Pre-Release Validation

Before any release (automated or manual), these checks run automatically:

```bash
ruff check .           # Linting
ruff format --check .  # Formatting
pyright                # Type checking
pytest                 # Tests
python -m vibegate check .  # Gate the repo with VibeGate
```

All checks must pass before publishing to PyPI.

## Testing with TestPyPI

To test releases without affecting production PyPI:

1. Use the `release` workflow with manual dispatch
2. Select `testpypi` as the index
3. Verify the test release:

```bash
python -m venv .venv-test
source .venv-test/bin/activate
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    vibegate==<VERSION>
vibegate --help
vibegate doctor .
```

## Version Format

VibeGate follows [PEP 440](https://peps.python.org/pep-0440/) versioning:

| Format | Example | Use Case |
|--------|---------|----------|
| `X.Y.Z` | `1.0.0` | Stable release |
| `X.Y.ZaN` | `0.1.0a5` | Alpha pre-release |
| `X.Y.ZbN` | `0.1.0b1` | Beta pre-release |
| `X.Y.ZrcN` | `0.1.0rc1` | Release candidate |

## Changelog Format

CHANGELOG.md follows [Keep a Changelog](https://keepachangelog.com/) format and is **automatically updated** by semantic-release:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features (from feat: commits)

### Changed
- Changes to existing features

### Fixed
- Bug fixes (from fix: commits)

### Performance
- Performance improvements (from perf: commits)
```

## What Gets Published

When a release is created:

1. **Quality checks** run (ruff, pyright, pytest, vibegate)
2. **Build artifacts** created (sdist and wheel)
3. **PyPI publish** via Trusted Publisher
4. **GitHub Release** created with:
   - Changelog notes extracted automatically
   - Build artifacts attached
   - Pre-release flag set for alpha/beta/rc versions

## Regular VibeGate Evolution

To keep rule quality sharp, run the full evolution loop regularly:

```bash
python -m vibegate evolve .
```

The scheduled **"vibegate evolve"** workflow runs weekly and uploads tuning artifacts.

## Release Drafter

The Release Drafter workflow automatically maintains a draft release with categorized changes from merged PRs. This provides a preview of the next release notes.

View draft releases at: `https://github.com/maxadamsky/VibeGate/releases`

## Troubleshooting

### "No release needed - no version bump"

This means no releasable commits (feat, fix, perf, refactor) were found since the last release. Only commits that don't trigger releases (docs, chore, ci, test) were added.

**Solution:** This is expected behavior. No release is needed.

### "Tag already exists"

You cannot re-release an existing version.

**Solution:**
- For automated releases, this shouldn't happen
- For manual releases, choose a different version number

### "Invalid version format"

Version must match PEP 440: `X.Y.Z` or `X.Y.Z{a|b|rc}N`

**Solution:** Use a valid version format

### "Protected branch update failed"

The workflow cannot push directly to protected branches.

**Solution:**
- Ensure the GitHub token has appropriate permissions
- Check branch protection rules allow the workflow to push

### PyPI publish fails

Common causes:
- Version already exists on PyPI
- Trusted Publisher not configured correctly
- Environment protection rules blocking publish

**Solution:**
- Verify Trusted Publisher configuration
- Check GitHub environment settings
- Ensure version is unique

### Commit message validation fails

PR commits don't follow conventional commits format.

**Solution:**
- Use conventional commit format: `<type>(<scope>): <subject>`
- Valid types: feat, fix, docs, style, refactor, perf, test, build, ci, chore
- Install pre-commit hooks to validate locally

## Rollback

If a bad release is published:

1. **PyPI**: [Yank the release](https://pypi.org/help/#yanked) from PyPI
   ```bash
   pip install twine
   twine upload --repository pypi --skip-existing dist/*
   ```

2. **GitHub**: Delete or edit the GitHub Release

3. **Hotfix**: Use the hotfix workflow to release a fixed version

**Note:** Yanking hides the version from default installs but doesn't delete it. Users can still install yanked versions explicitly.

## Best Practices

1. **Always use conventional commits** - Required for automated releases
2. **Keep commits focused** - One logical change per commit
3. **Write clear commit messages** - They become the changelog
4. **Test before merging** - All CI checks must pass
5. **Use draft releases** - Review the draft release before merging
6. **Hotfixes for emergencies only** - Prefer regular releases when possible
7. **Semantic versioning** - Breaking changes require major version bump

## Additional Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [PEP 440 - Version Identification](https://peps.python.org/pep-0440/)
- [python-semantic-release](https://python-semantic-release.readthedocs.io/)
