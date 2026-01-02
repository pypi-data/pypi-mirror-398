from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml
from jsonschema import Draft202012Validator
from platform import python_version

from vibegate.policy_semantic import SemanticPolicyError, parse_semantic_rules
from vibegate.schema_loader import load_schema
from vibegate.workspace import DEFAULT_EXCLUDE_GLOBS


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    language: str
    repo_root: str
    app_module: str | None


@dataclass(frozen=True)
class PackagingConfig:
    tool: str
    python_version: str
    pyproject_path: str
    lockfiles: List[str]
    tool_detection_order: List[str]


@dataclass(frozen=True)
class BaseCheckConfig:
    enabled: bool
    timeout_sec: int


@dataclass(frozen=True)
class RuffFormatCheck(BaseCheckConfig):
    id: str
    paths: List[str]
    args: List[str]


@dataclass(frozen=True)
class RuffLintCheck(BaseCheckConfig):
    id: str
    paths: List[str]
    output_format: str
    args: List[str]


@dataclass(frozen=True)
class PyrightCheck(BaseCheckConfig):
    id: str
    project_file: str
    fail_on_warnings: bool
    args: List[str]


@dataclass(frozen=True)
class PytestCheck(BaseCheckConfig):
    id: str
    args: List[str]


@dataclass(frozen=True)
class DependencyHygieneCheck(BaseCheckConfig):
    id: str
    mode: str
    rules: List[str]


@dataclass(frozen=True)
class BanditCheck(BaseCheckConfig):
    id: str
    severity_threshold: str
    confidence_threshold: str
    args: List[str]


@dataclass(frozen=True)
class GitleaksCheck(BaseCheckConfig):
    id: str
    args: List[str]


@dataclass(frozen=True)
class VulnLocalDbConfig:
    path: str
    snapshot_id: str | None


@dataclass(frozen=True)
class VulnerabilityCheck(BaseCheckConfig):
    id: str
    deterministic_required: bool
    mode: str
    local_db: VulnLocalDbConfig | None
    args: List[str]


@dataclass(frozen=True)
class ConfigSanityCheck(BaseCheckConfig):
    id: str
    rules: List[str]
    include_globs: List[str]
    exclude_globs: List[str]


@dataclass(frozen=True)
class RuntimeSmokeCheck(BaseCheckConfig):
    id: str
    command: str
    health_url: str
    startup_timeout_sec: int


@dataclass(frozen=True)
class ErrorHandlingCheck(BaseCheckConfig):
    id: str
    rules: List[str]
    exclude_globs: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DefensiveProgrammingCheck(BaseCheckConfig):
    id: str
    require_none_checks: bool = True
    require_bounds_checks: bool = True
    exclude_globs: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ComplexityCheck(BaseCheckConfig):
    id: str
    max_function_lines: int = 50
    max_nesting_depth: int = 4
    max_complexity: int = 10
    detect_duplicates: bool = False
    exclude_globs: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DeadCodeCheck(BaseCheckConfig):
    id: str
    min_confidence: int = 80
    detect_commented_code: bool = True
    exclude_globs: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CoverageCheck(BaseCheckConfig):
    id: str
    minimum_coverage: float = 80.0
    target_coverage: float = 90.0
    fail_on_missing_tests: bool = True


@dataclass(frozen=True)
class ChecksConfig:
    formatting: RuffFormatCheck
    lint: RuffLintCheck
    typecheck: PyrightCheck
    tests: PytestCheck
    dependency_hygiene: DependencyHygieneCheck
    sast: BanditCheck
    secrets: GitleaksCheck
    vulnerability: VulnerabilityCheck
    config_sanity: ConfigSanityCheck
    runtime_smoke: RuntimeSmokeCheck
    error_handling: ErrorHandlingCheck
    defensive_coding: DefensiveProgrammingCheck
    complexity: ComplexityCheck
    dead_code: DeadCodeCheck
    coverage: CoverageCheck


@dataclass(frozen=True)
class OutputsConfig:
    report_markdown: Path
    report_html: Path
    emit_html: bool
    evidence_jsonl: Path
    evidence_graph_json: Path
    delta_report_markdown: Path
    fixpack_json: Path
    fixpack_yaml: Path
    emit_fixpack_yaml: bool
    fixpack_md: Path


@dataclass(frozen=True)
class SuppressionsPolicy:
    require_justification: bool
    require_expiry: bool
    max_days_default: int
    require_actor: bool


@dataclass(frozen=True)
class SuppressionsConfig:
    path: Path
    policy: SuppressionsPolicy


@dataclass(frozen=True)
class PolicyRule:
    severity: str
    confidence: List[str]


@dataclass(frozen=True)
class GatePolicy:
    fail_on: List[PolicyRule]
    warn_on: List[PolicyRule]
    semantic: List[str]
    delta: "DeltaPolicy"


@dataclass(frozen=True)
class DeltaPolicy:
    enabled: bool
    allow_blocking_increase: int
    allow_warning_increase: int
    allow_unsuppressed_increase: int
    per_signal: Dict[str, int]


@dataclass(frozen=True)
class DeterminismConfig:
    tool_versions: Dict[str, str]
    env: Dict[str, str]


@dataclass(frozen=True)
class PluginGroupConfig:
    enabled: List[str]
    disabled: List[str]
    config: Dict[str, Dict[str, Any]]


@dataclass(frozen=True)
class PluginsConfig:
    checks: PluginGroupConfig
    emitters: PluginGroupConfig


@dataclass(frozen=True)
class OllamaConfig:
    """Configuration for Ollama LLM provider."""

    base_url: str
    model: str
    temperature: float


@dataclass(frozen=True)
class LLMFeaturesConfig:
    """Configuration for which LLM features are enabled."""

    explain_findings: bool
    generate_prompts: bool


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for LLM integration."""

    enabled: bool
    provider: str  # "ollama" (more providers in future)
    cache_dir: str
    ollama: OllamaConfig
    features: LLMFeaturesConfig


@dataclass(frozen=True)
class VibeGateConfig:
    schema_version: str
    project: ProjectConfig
    packaging: PackagingConfig
    checks: ChecksConfig
    outputs: OutputsConfig
    suppressions: SuppressionsConfig
    policy: GatePolicy
    determinism: DeterminismConfig
    plugins: PluginsConfig
    llm: LLMConfig | None  # Optional - not all users will use LLM features
    contract_path: Path | None


class ConfigError(RuntimeError):
    pass


DEFAULT_ENV = {
    "TZ": "UTC",
    "LC_ALL": "C",
    "PYTHONHASHSEED": "0",
}


def _resolve_output_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _validate_config(data: dict[str, Any], schema: dict[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda err: err.path)
    if not errors:
        return
    messages = []
    missing_fields: list[str] = []
    for error in errors:
        path = ".".join(str(part) for part in error.path) or "<root>"
        messages.append(f"{path}: {error.message}")
        if error.validator == "required" and isinstance(error.instance, dict):
            required = [
                name for name in error.validator_value if name not in error.instance
            ]
            for name in required:
                if path == "<root>":
                    missing_fields.append(name)
                else:
                    missing_fields.append(f"{path}.{name}")
    missing_fields = sorted(set(missing_fields))
    header = "Your vibegate.yaml is invalid or missing required fields."
    remediation_lines = [
        "Remediation:",
        "- Run: vibegate init . --force (this overwrites vibegate.yaml)",
        "- Or fix the required fields listed below.",
    ]
    missing_lines = []
    if missing_fields:
        missing_lines = ["Missing required fields:"] + [
            f"- {field}" for field in missing_fields
        ]
    schema_lines = ["Schema validation errors:"] + messages
    full_message = "\n".join(
        [header, *remediation_lines, *missing_lines, *schema_lines]
    )
    raise ConfigError(full_message)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge override into base with deterministic rules.

    - Dict values are merged recursively by key.
    - Lists and scalars replace the base value entirely (no concatenation).
    """
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _strip_profile_fields(data: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value for key, value in data.items() if key not in {"profile", "profiles"}
    }


def _resolve_profile_override(
    raw: dict[str, Any], cli_overrides: dict[str, Any]
) -> dict[str, Any]:
    selected_profile = cli_overrides.get("profile") or raw.get("profile")
    if not selected_profile:
        return {}
    profiles = raw.get("profiles", {})
    if not isinstance(profiles, dict) or selected_profile not in profiles:
        raise ConfigError(
            f"Selected profile '{selected_profile}' does not exist in profiles."
        )
    override = profiles[selected_profile]
    if not isinstance(override, dict):
        raise ConfigError(
            f"Profile overrides for '{selected_profile}' must be a mapping."
        )
    return override


def _resolve_config_data(
    defaults: dict[str, Any],
    base: dict[str, Any],
    profile_override: dict[str, Any],
    cli_overrides: dict[str, Any],
) -> dict[str, Any]:
    """Merge config layers in order: defaults -> base -> profile -> cli."""
    merged = _deep_merge(defaults, base)
    if profile_override:
        merged = _deep_merge(merged, profile_override)
    if cli_overrides:
        merged = _deep_merge(merged, cli_overrides)
    return merged


def _default_contract(repo_root: Path) -> dict[str, Any]:
    return {
        "schema_version": "v1alpha1",
        "project": {
            "name": repo_root.name,
            "language": "python",
            "repo_root": ".",
            "app_module": "app.main:app",
        },
        "packaging": {
            "tool": "auto",
            "python_version": python_version(),
            "pyproject_path": "pyproject.toml",
            "lockfiles": [],
            "tool_detection_order": ["uv", "poetry", "pdm", "pip-tools", "pip"],
        },
        "checks": {
            "formatting": {
                "enabled": True,
                "timeout_sec": 300,
                "id": "formatting.ruff",
                "paths": ["."],
                "args": ["format", "--check", "."],
            },
            "lint": {
                "enabled": True,
                "timeout_sec": 300,
                "id": "lint.ruff",
                "paths": ["."],
                "output_format": "json",
                "args": ["check", "--output-format", "json", "."],
            },
            "typecheck": {
                "enabled": True,
                "timeout_sec": 300,
                "id": "typecheck.pyright",
                "project_file": "pyproject.toml",
                "fail_on_warnings": False,
                "args": [".", "--outputjson"],
            },
            "tests": {
                "enabled": True,
                "timeout_sec": 300,
                "id": "tests.pytest",
                "args": ["-q"],
            },
            "dependency_hygiene": {
                "enabled": True,
                "timeout_sec": 300,
                "id": "deps.hygiene",
                "mode": "auto",
                "rules": ["lockfile_required", "lockfile_fresh"],
            },
            "sast": {
                "enabled": False,
                "timeout_sec": 300,
                "id": "sast.bandit",
                "severity_threshold": "medium",
                "confidence_threshold": "low",
                "args": ["-r", ".", "-f", "json", "-o", "artifacts/bandit.json"],
            },
            "secrets": {
                "enabled": False,
                "timeout_sec": 300,
                "id": "secrets.gitleaks",
                "args": [
                    "dir",
                    ".",
                    "--report-format",
                    "json",
                    "--report-path",
                    "artifacts/gitleaks.json",
                ],
            },
            "vulnerability": {
                "enabled": False,
                "timeout_sec": 300,
                "id": "vuln.osv_scanner",
                "deterministic_required": True,
                "mode": "offline",
                "local_db": {"path": ".vibegate/osv-db"},
                "args": ["--offline", "."],
            },
            "config_sanity": {
                "enabled": True,
                "timeout_sec": 300,
                "id": "config.sanity",
                "rules": ["no_debug_true", "no_uvicorn_reload_in_prod"],
                "include_globs": [
                    "**/*.py",
                    "**/*.toml",
                    "**/*.yaml",
                    "**/*.yml",
                    "**/*.env",
                    "**/*.ini",
                ],
                "exclude_globs": list(DEFAULT_EXCLUDE_GLOBS),
            },
            "runtime_smoke": {
                "enabled": False,
                "timeout_sec": 300,
                "id": "runtime.smoke",
                "command": "uvicorn app.main:app --host 127.0.0.1 --port 8000",
                "health_url": "http://127.0.0.1:8000/healthz",
                "startup_timeout_sec": 20,
            },
            "error_handling": {
                "enabled": True,
                "timeout_sec": 300,
                "id": "error_handling.ast",
                "rules": ["bare_except", "empty_except", "generic_exceptions"],
            },
            "defensive_coding": {
                "enabled": True,
                "timeout_sec": 300,
                "id": "defensive_coding.ast",
                "require_none_checks": True,
                "require_bounds_checks": True,
            },
            "complexity": {
                "enabled": True,
                "timeout_sec": 300,
                "id": "complexity.ast",
                "max_function_lines": 50,
                "max_nesting_depth": 4,
                "max_complexity": 10,
                "detect_duplicates": False,
            },
            "dead_code": {
                "enabled": False,
                "timeout_sec": 300,
                "id": "dead_code.tool",
                "min_confidence": 80,
                "detect_commented_code": True,
            },
            "coverage": {
                "enabled": False,
                "timeout_sec": 300,
                "id": "coverage.pytest",
                "minimum_coverage": 80.0,
                "target_coverage": 90.0,
                "fail_on_missing_tests": True,
            },
        },
        "outputs": {
            "report_markdown": "artifacts/vibegate_report.md",
            "report_html": "artifacts/vibegate_report.html",
            "emit_html": True,
            "evidence_jsonl": "evidence/vibegate.jsonl",
            "evidence_graph_json": "artifacts/evidence_graph.json",
            "delta_report_markdown": "artifacts/vibegate_delta.md",
            "fixpack_json": "artifacts/fixpack.json",
            "fixpack_yaml": "artifacts/fixpack.yaml",
            "emit_fixpack_yaml": True,
        },
        "suppressions": {
            "path": ".vibegate/suppressions.yaml",
            "policy": {
                "require_justification": True,
                "require_expiry": True,
                "max_days_default": 90,
                "require_actor": False,
            },
        },
        "policy": {
            "fail_on": [
                {"severity": "critical", "confidence": ["high", "medium", "low"]},
                {"severity": "high", "confidence": ["high"]},
            ],
            "warn_on": [
                {"severity": "high", "confidence": ["medium", "low"]},
                {"severity": "medium", "confidence": ["high", "medium", "low"]},
                {"severity": "low", "confidence": ["high", "medium", "low"]},
            ],
            "semantic": [],
            "delta": {
                "enabled": False,
                "allow_blocking_increase": 0,
                "allow_warning_increase": 0,
                "allow_unsuppressed_increase": 0,
                "per_signal": {},
            },
        },
        "determinism": {
            "tool_versions": {},
            "env": dict(DEFAULT_ENV),
        },
        "plugins": {
            "checks": {"enabled": [], "disabled": [], "config": {}},
            "emitters": {"enabled": [], "disabled": [], "config": {}},
        },
    }


def default_contract(repo_root: Path) -> dict[str, Any]:
    return _default_contract(repo_root)


def load_config(
    repo_root: Path,
    *,
    cli_overrides: dict[str, Any] | None = None,
) -> VibeGateConfig:
    contract_path = repo_root / "vibegate.yaml"
    schema = load_schema("vibegate.schema.json", repo_root=repo_root)
    defaults = _default_contract(repo_root)
    cli_overrides = cli_overrides or {}
    if not isinstance(cli_overrides, dict):
        raise ConfigError("CLI overrides must be a mapping.")

    if contract_path.exists():
        raw = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise ConfigError("vibegate.yaml must contain a mapping at the root.")
        _validate_config(raw, schema)
        profile_override = _resolve_profile_override(raw, cli_overrides)
        data = _resolve_config_data(
            defaults,
            _strip_profile_fields(raw),
            profile_override,
            _strip_profile_fields(cli_overrides),
        )
    else:
        data = _resolve_config_data(
            defaults,
            {},
            {},
            _strip_profile_fields(cli_overrides),
        )

    project_raw = data["project"]
    packaging_raw = data["packaging"]
    outputs_raw = data["outputs"]
    suppressions_raw = data["suppressions"]
    suppressions_policy_raw = suppressions_raw["policy"]
    policy_raw = data["policy"]
    determinism_raw = data["determinism"]
    checks_raw = data["checks"]
    plugins_raw = data.get("plugins", {})

    project = ProjectConfig(
        name=project_raw["name"],
        language=project_raw["language"],
        repo_root=project_raw.get("repo_root", "."),
        app_module=project_raw.get("app_module"),
    )

    packaging = PackagingConfig(
        tool=packaging_raw["tool"],
        python_version=packaging_raw["python_version"],
        pyproject_path=packaging_raw.get("pyproject_path", "pyproject.toml"),
        lockfiles=list(packaging_raw.get("lockfiles", [])),
        tool_detection_order=list(
            packaging_raw.get(
                "tool_detection_order", ["uv", "poetry", "pdm", "pip-tools", "pip"]
            )
        ),
    )

    checks = ChecksConfig(
        formatting=RuffFormatCheck(
            enabled=checks_raw["formatting"]["enabled"],
            timeout_sec=checks_raw["formatting"].get("timeout_sec", 300),
            id=checks_raw["formatting"].get("id", "formatting.ruff"),
            paths=list(checks_raw["formatting"].get("paths", ["."])),
            args=list(checks_raw["formatting"].get("args", ["format", "--check", "."])),
        ),
        lint=RuffLintCheck(
            enabled=checks_raw["lint"]["enabled"],
            timeout_sec=checks_raw["lint"].get("timeout_sec", 300),
            id=checks_raw["lint"].get("id", "lint.ruff"),
            paths=list(checks_raw["lint"].get("paths", ["."])),
            output_format=checks_raw["lint"].get("output_format", "json"),
            args=list(
                checks_raw["lint"].get(
                    "args", ["check", "--output-format", "json", "."]
                )
            ),
        ),
        typecheck=PyrightCheck(
            enabled=checks_raw["typecheck"]["enabled"],
            timeout_sec=checks_raw["typecheck"].get("timeout_sec", 300),
            id=checks_raw["typecheck"].get("id", "typecheck.pyright"),
            project_file=checks_raw["typecheck"].get("project_file", "pyproject.toml"),
            fail_on_warnings=checks_raw["typecheck"].get("fail_on_warnings", False),
            args=list(checks_raw["typecheck"].get("args", [".", "--outputjson"])),
        ),
        tests=PytestCheck(
            enabled=checks_raw["tests"]["enabled"],
            timeout_sec=checks_raw["tests"].get("timeout_sec", 300),
            id=checks_raw["tests"].get("id", "tests.pytest"),
            args=list(checks_raw["tests"].get("args", ["-q"])),
        ),
        dependency_hygiene=DependencyHygieneCheck(
            enabled=checks_raw["dependency_hygiene"]["enabled"],
            timeout_sec=checks_raw["dependency_hygiene"].get("timeout_sec", 300),
            id=checks_raw["dependency_hygiene"].get("id", "deps.hygiene"),
            mode=checks_raw["dependency_hygiene"].get("mode", "auto"),
            rules=list(
                checks_raw["dependency_hygiene"].get(
                    "rules", ["lockfile_required", "lockfile_fresh"]
                )
            ),
        ),
        sast=BanditCheck(
            enabled=checks_raw["sast"]["enabled"],
            timeout_sec=checks_raw["sast"].get("timeout_sec", 300),
            id=checks_raw["sast"].get("id", "sast.bandit"),
            severity_threshold=checks_raw["sast"].get("severity_threshold", "medium"),
            confidence_threshold=checks_raw["sast"].get("confidence_threshold", "low"),
            args=list(
                checks_raw["sast"].get(
                    "args", ["-r", ".", "-f", "json", "-o", "artifacts/bandit.json"]
                )
            ),
        ),
        secrets=GitleaksCheck(
            enabled=checks_raw["secrets"]["enabled"],
            timeout_sec=checks_raw["secrets"].get("timeout_sec", 300),
            id=checks_raw["secrets"].get("id", "secrets.gitleaks"),
            args=list(
                checks_raw["secrets"].get(
                    "args",
                    [
                        "dir",
                        ".",
                        "--report-format",
                        "json",
                        "--report-path",
                        "artifacts/gitleaks.json",
                    ],
                )
            ),
        ),
        vulnerability=VulnerabilityCheck(
            enabled=checks_raw["vulnerability"]["enabled"],
            timeout_sec=checks_raw["vulnerability"].get("timeout_sec", 300),
            id=checks_raw["vulnerability"].get("id", "vuln.osv_scanner"),
            deterministic_required=checks_raw["vulnerability"].get(
                "deterministic_required", True
            ),
            mode=checks_raw["vulnerability"].get("mode", "offline"),
            local_db=VulnLocalDbConfig(
                path=checks_raw["vulnerability"]
                .get("local_db", {})
                .get("path", ".vibegate/osv-db"),
                snapshot_id=checks_raw["vulnerability"]
                .get("local_db", {})
                .get("snapshot_id"),
            )
            if checks_raw["vulnerability"].get("local_db") is not None
            else None,
            args=list(checks_raw["vulnerability"].get("args", ["--offline", "."])),
        ),
        config_sanity=ConfigSanityCheck(
            enabled=checks_raw["config_sanity"]["enabled"],
            timeout_sec=checks_raw["config_sanity"].get("timeout_sec", 300),
            id=checks_raw["config_sanity"].get("id", "config.sanity"),
            rules=list(
                checks_raw["config_sanity"].get(
                    "rules", ["no_debug_true", "no_uvicorn_reload_in_prod"]
                )
            ),
            include_globs=list(
                checks_raw["config_sanity"].get(
                    "include_globs",
                    [
                        "**/*.py",
                        "**/*.toml",
                        "**/*.yaml",
                        "**/*.yml",
                        "**/*.env",
                        "**/*.ini",
                    ],
                )
            ),
            exclude_globs=list(
                checks_raw["config_sanity"].get(
                    "exclude_globs", list(DEFAULT_EXCLUDE_GLOBS)
                )
            ),
        ),
        runtime_smoke=RuntimeSmokeCheck(
            enabled=checks_raw["runtime_smoke"]["enabled"],
            timeout_sec=checks_raw["runtime_smoke"].get("timeout_sec", 300),
            id=checks_raw["runtime_smoke"].get("id", "runtime.smoke"),
            command=checks_raw["runtime_smoke"].get(
                "command", "uvicorn app.main:app --host 127.0.0.1 --port 8000"
            ),
            health_url=checks_raw["runtime_smoke"].get(
                "health_url", "http://127.0.0.1:8000/healthz"
            ),
            startup_timeout_sec=checks_raw["runtime_smoke"].get(
                "startup_timeout_sec", 20
            ),
        ),
        error_handling=ErrorHandlingCheck(
            enabled=checks_raw["error_handling"]["enabled"],
            timeout_sec=checks_raw["error_handling"].get("timeout_sec", 300),
            id=checks_raw["error_handling"].get("id", "error_handling.ast"),
            rules=list(
                checks_raw["error_handling"].get(
                    "rules", ["bare_except", "empty_except", "generic_exceptions"]
                )
            ),
            exclude_globs=list(checks_raw["error_handling"].get("exclude_globs", [])),
        ),
        defensive_coding=DefensiveProgrammingCheck(
            enabled=checks_raw["defensive_coding"]["enabled"],
            timeout_sec=checks_raw["defensive_coding"].get("timeout_sec", 300),
            id=checks_raw["defensive_coding"].get("id", "defensive_coding.ast"),
            require_none_checks=bool(
                checks_raw["defensive_coding"].get("require_none_checks", True)
            ),
            require_bounds_checks=bool(
                checks_raw["defensive_coding"].get("require_bounds_checks", True)
            ),
            exclude_globs=list(checks_raw["defensive_coding"].get("exclude_globs", [])),
        ),
        complexity=ComplexityCheck(
            enabled=checks_raw["complexity"]["enabled"],
            timeout_sec=checks_raw["complexity"].get("timeout_sec", 300),
            id=checks_raw["complexity"].get("id", "complexity.ast"),
            max_function_lines=int(
                checks_raw["complexity"].get("max_function_lines", 50)
            ),
            max_nesting_depth=int(checks_raw["complexity"].get("max_nesting_depth", 4)),
            max_complexity=int(checks_raw["complexity"].get("max_complexity", 10)),
            detect_duplicates=bool(
                checks_raw["complexity"].get("detect_duplicates", False)
            ),
            exclude_globs=list(checks_raw["complexity"].get("exclude_globs", [])),
        ),
        dead_code=DeadCodeCheck(
            enabled=checks_raw["dead_code"]["enabled"],
            timeout_sec=checks_raw["dead_code"].get("timeout_sec", 300),
            id=checks_raw["dead_code"].get("id", "dead_code.tool"),
            min_confidence=int(checks_raw["dead_code"].get("min_confidence", 80)),
            detect_commented_code=bool(
                checks_raw["dead_code"].get("detect_commented_code", True)
            ),
            exclude_globs=list(checks_raw["dead_code"].get("exclude_globs", [])),
        ),
        coverage=CoverageCheck(
            enabled=checks_raw["coverage"]["enabled"],
            timeout_sec=checks_raw["coverage"].get("timeout_sec", 300),
            id=checks_raw["coverage"].get("id", "coverage.pytest"),
            minimum_coverage=float(
                checks_raw["coverage"].get("minimum_coverage", 80.0)
            ),
            target_coverage=float(checks_raw["coverage"].get("target_coverage", 90.0)),
            fail_on_missing_tests=bool(
                checks_raw["coverage"].get("fail_on_missing_tests", True)
            ),
        ),
    )

    report_markdown = _resolve_output_path(
        repo_root,
        Path(outputs_raw.get("report_markdown", "artifacts/vibegate_report.md")),
    )
    report_html = _resolve_output_path(
        repo_root,
        Path(outputs_raw.get("report_html", "artifacts/vibegate_report.html")),
    )
    evidence_jsonl = _resolve_output_path(
        repo_root, Path(outputs_raw.get("evidence_jsonl", "evidence/vibegate.jsonl"))
    )
    evidence_graph_json = _resolve_output_path(
        repo_root,
        Path(outputs_raw.get("evidence_graph_json", "artifacts/evidence_graph.json")),
    )
    delta_report_markdown = _resolve_output_path(
        repo_root,
        Path(outputs_raw.get("delta_report_markdown", "artifacts/vibegate_delta.md")),
    )
    fixpack_json = _resolve_output_path(
        repo_root, Path(outputs_raw.get("fixpack_json", "artifacts/fixpack.json"))
    )
    fixpack_yaml = _resolve_output_path(
        repo_root, Path(outputs_raw.get("fixpack_yaml", "artifacts/fixpack.yaml"))
    )
    fixpack_md = _resolve_output_path(repo_root, fixpack_json.with_suffix(".md"))

    outputs = OutputsConfig(
        report_markdown=report_markdown,
        report_html=report_html,
        emit_html=bool(outputs_raw.get("emit_html", True)),
        evidence_jsonl=evidence_jsonl,
        evidence_graph_json=evidence_graph_json,
        delta_report_markdown=delta_report_markdown,
        fixpack_json=fixpack_json,
        fixpack_yaml=fixpack_yaml,
        emit_fixpack_yaml=bool(outputs_raw.get("emit_fixpack_yaml", True)),
        fixpack_md=fixpack_md,
    )

    suppressions = SuppressionsConfig(
        path=Path(suppressions_raw.get("path", ".vibegate/suppressions.yaml")),
        policy=SuppressionsPolicy(
            require_justification=bool(
                suppressions_policy_raw.get("require_justification", True)
            ),
            require_expiry=bool(suppressions_policy_raw.get("require_expiry", True)),
            max_days_default=int(suppressions_policy_raw.get("max_days_default", 90)),
            require_actor=bool(suppressions_policy_raw.get("require_actor", False)),
        ),
    )

    fail_on_rules = [
        PolicyRule(severity=rule["severity"], confidence=list(rule["confidence"]))
        for rule in policy_raw.get("fail_on", [])
    ]
    warn_on_rules = [
        PolicyRule(severity=rule["severity"], confidence=list(rule["confidence"]))
        for rule in policy_raw.get("warn_on", [])
    ]
    semantic_rules = policy_raw.get("semantic", [])
    if not isinstance(semantic_rules, list) or not all(
        isinstance(item, str) for item in semantic_rules
    ):
        raise ConfigError("policy.semantic must be a list of strings.")
    try:
        parse_semantic_rules(semantic_rules)
    except SemanticPolicyError as exc:
        raise ConfigError(f"policy.semantic invalid: {exc}") from exc
    delta_raw = policy_raw.get("delta", {})
    if not isinstance(delta_raw, dict):
        raise ConfigError("policy.delta must be a mapping.")
    per_signal_raw = delta_raw.get("per_signal", {})
    if not isinstance(per_signal_raw, dict):
        raise ConfigError("policy.delta.per_signal must be a mapping.")
    per_signal = {}
    for key, value in per_signal_raw.items():
        if not isinstance(key, str):
            raise ConfigError("policy.delta.per_signal keys must be strings.")
        try:
            per_signal[key] = int(value)
        except (TypeError, ValueError) as exc:
            raise ConfigError(
                "policy.delta.per_signal values must be integers."
            ) from exc
    delta_policy = DeltaPolicy(
        enabled=bool(delta_raw.get("enabled", False)),
        allow_blocking_increase=int(delta_raw.get("allow_blocking_increase", 0)),
        allow_warning_increase=int(delta_raw.get("allow_warning_increase", 0)),
        allow_unsuppressed_increase=int(
            delta_raw.get("allow_unsuppressed_increase", 0)
        ),
        per_signal=per_signal,
    )
    policy = GatePolicy(
        fail_on=fail_on_rules,
        warn_on=warn_on_rules,
        semantic=semantic_rules,
        delta=delta_policy,
    )

    determinism = DeterminismConfig(
        tool_versions=dict(determinism_raw.get("tool_versions", {})),
        env=dict(determinism_raw.get("env", DEFAULT_ENV)),
    )

    plugins = PluginsConfig(
        checks=PluginGroupConfig(
            enabled=list(plugins_raw.get("checks", {}).get("enabled", [])),
            disabled=list(plugins_raw.get("checks", {}).get("disabled", [])),
            config=dict(plugins_raw.get("checks", {}).get("config", {})),
        ),
        emitters=PluginGroupConfig(
            enabled=list(plugins_raw.get("emitters", {}).get("enabled", [])),
            disabled=list(plugins_raw.get("emitters", {}).get("disabled", [])),
            config=dict(plugins_raw.get("emitters", {}).get("config", {})),
        ),
    )

    # LLM config is optional
    llm = None
    llm_raw = data.get("llm", {})
    if llm_raw and llm_raw.get("enabled", False):
        ollama_raw = llm_raw.get("ollama", {})
        features_raw = llm_raw.get("features", {})

        llm = LLMConfig(
            enabled=bool(llm_raw.get("enabled", False)),
            provider=llm_raw.get("provider", "ollama"),
            cache_dir=llm_raw.get("cache_dir", ".vibegate/llm_cache"),
            ollama=OllamaConfig(
                base_url=ollama_raw.get("base_url", "http://localhost:11434"),
                model=ollama_raw.get("model", "codellama:7b"),
                temperature=float(ollama_raw.get("temperature", 0.3)),
            ),
            features=LLMFeaturesConfig(
                explain_findings=bool(features_raw.get("explain_findings", True)),
                generate_prompts=bool(features_raw.get("generate_prompts", True)),
            ),
        )

    return VibeGateConfig(
        schema_version=data["schema_version"],
        project=project,
        packaging=packaging,
        checks=checks,
        outputs=outputs,
        suppressions=suppressions,
        policy=policy,
        determinism=determinism,
        plugins=plugins,
        llm=llm,
        contract_path=contract_path if contract_path.exists() else None,
    )
