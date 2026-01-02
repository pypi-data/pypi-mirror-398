# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.0] - 2025-12-28

### Added
- **Coverage check implementation** (`coverage.pytest`) for enforcing test coverage thresholds
  - Configurable minimum and target coverage percentages
  - Automatic pytest execution with coverage reporting
  - Detailed findings for missing coverage, low coverage, and parse errors
  - Integration with VibeGate's quality gate workflow

## [0.1.0] - 2025-12-27

### Fixed
- Undefined variables in `run_fixpack()` function (`per_check_delta` and `report_artifacts`)
- Pyright type errors in DefensiveProgrammingVisitor AST checker
- Stale suppressions causing CI failures (regenerated all 128 suppressions with current fingerprints)
- Optional dependency import warnings in pyright configuration
- Semantic-release workflow double-commit bug
- Branch protection bypass for automated releases

### Changed
- Configured pyright to treat missing optional dependency imports as warnings instead of errors
- Updated semantic-release workflow to use `--no-commit` flag for better control over release commits

## [0.1.0a8] - 2025-12-26

### Added
- **LLM-powered AI Assistant Features** for generating friendly explanations and detailed fix prompts
  - Optional integration with Ollama for 100% local inference (no data leaves your machine)
  - Support for CodeLlama, DeepSeek Coder, and Mistral models
  - Interactive setup wizard during `vibegate init` for model selection and download
  - Smart caching system to avoid redundant inference calls
  - Integrated into `vibegate propose` command with 🤖 AI Explanation and 🔧 AI-Generated Fix Prompt sections
  - Graceful degradation when LLM features are disabled or unavailable
  - Lazy loading design - Ollama not required unless LLM features are enabled
  - Install with `pip install "vibegate[llm]"` for LLM support
  - New LLM module: `src/vibegate/llm/` with providers, prompts, cache, and setup wizard
  - Comprehensive test coverage with 31 new tests for LLM functionality
- **Semantic policy parsing** module for policy-based finding evaluation
- **Runner event tests** for validating evidence generation

### Fixed
- Missing policy_semantic module causing import errors in CI/CD
- GitHub Actions workflow for semantic-release to properly update version files
- Pre-commit compatibility with type checking for semantic rules

## [0.1.0a7] - 2025-12-25

### Added
- **Complete evolution workflow** with `vibegate evolve` orchestrating triage → tune → propose
- **Tuning system** (`vibegate tune`) for offline clustering and analysis of false positive patterns
- **Proposal pack generator** (`vibegate propose`) creating deterministic, PR-ready patch suggestions
- State tracking in `.vibegate/state.json` for last_tune and last_propose metadata
- Regression test snippet extraction from tuning clusters
- Rule refinement suggestions based on cluster heuristics
- Copy-paste suppression snippets as fallback option
- Comprehensive test coverage for tuning and proposal modules (24 new tests)

### Changed
- Extended Finding dataclass with tuning metadata fields (trigger_explanation, ast_node_type, in_type_annotation)
- Updated plugin Finding type to match core Finding structure
- Enhanced CLI with `--no-propose` flag for evolve command
- Improved documentation for complete evolution workflow

### Fixed
- Type checking errors in propose command with proper Path assertions
- Path resolution in tune command for consistent relative path handling

## [0.1.0a6] - 2025-12-25

### Added
- **Policy-based gating system** with configurable fail_on/warn_on rules based on severity + confidence
- **Confidence levels** for findings ("high", "medium", "low") to indicate certainty
- **Labels system** for tracking false positives and acceptable risks (.vibegate/labels.yaml)
- **Enhanced first-run UX** with friendly error messages and guided configuration
- **Interactive init command** with --yes flag for automated setup
- **vibegate label** CLI command for managing false positive feedback
- Automated semantic versioning via python-semantic-release
- Pre-commit hooks with ruff, pyright, gitleaks, and conventional commits validation
- Commitlint GitHub Action for PR commit validation
- Config profiles with deterministic merge order
- Plugin SDK with entry-point discovery for checks and emitters
- Branch protection setup script
- Comprehensive Makefile targets for development workflows

### Changed
- Findings now include confidence and rule_version fields (backwards compatible)
- Policy section now required in vibegate.yaml schema (with sensible defaults)
- Status determination now based on blocking findings (fail_on) vs warnings (warn_on)
- Evidence schema updated to include confidence, rule_version, and new finding counts
- Improved vibegate.yaml validation with clear remediation guidance
- Enhanced README with quickstart and policy documentation

### Fixed
- All checks now properly assign confidence levels (default: "high")
- Evidence schema validation for all finding events
- Test suite updated to include policy sections in all configs
