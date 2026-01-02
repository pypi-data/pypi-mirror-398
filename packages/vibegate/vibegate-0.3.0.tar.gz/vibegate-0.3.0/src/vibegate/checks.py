from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from vibegate.config import (
    ConfigSanityCheck,
    CoverageCheck,
    DependencyHygieneCheck,
    ErrorHandlingCheck,
    DefensiveProgrammingCheck,
    ComplexityCheck,
    DeadCodeCheck,
    GitleaksCheck,
    RuffFormatCheck,
    RuffLintCheck,
    PyrightCheck,
    PytestCheck,
    BanditCheck,
    VulnerabilityCheck,
    RuntimeSmokeCheck,
    VibeGateConfig,
)
from vibegate.findings import Finding, FindingLocation
from vibegate.workspace import filter_workspace_files


@dataclass(frozen=True)
class ToolResult:
    argv: List[str]
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    tool_version: str
    artifacts: List[Path]


@dataclass(frozen=True)
class CheckOutcome:
    check_id: str
    findings: List[Finding]
    skipped_reason: str | None
    tool_result: ToolResult | None


def tool_exists(tool: str) -> bool:
    return shutil.which(tool) is not None


def tool_version(tool: str) -> str:
    try:
        output = subprocess.check_output([tool, "--version"], stderr=subprocess.STDOUT)
        return output.decode("utf-8").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def run_tool(
    tool: str, args: List[str], cwd: Path, timeout: int, env: Dict[str, str]
) -> ToolResult:
    argv = [tool] + args
    started = time.monotonic()
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    duration_ms = int((time.monotonic() - started) * 1000)
    return ToolResult(
        argv=argv,
        stdout=completed.stdout,
        stderr=completed.stderr,
        exit_code=completed.returncode,
        duration_ms=duration_ms,
        tool_version=tool_version(tool),
        artifacts=[],
    )


def _severity_from_pyright(level: str) -> str:
    mapping = {
        "error": "high",
        "warning": "medium",
        "information": "low",
        "hint": "info",
    }
    return mapping.get(level.lower(), "medium")


def run_ruff_format(
    check: RuffFormatCheck, repo_root: Path, env: Dict[str, str]
) -> CheckOutcome:
    if not tool_exists("ruff"):
        return CheckOutcome(check.id, [], "ruff not found", None)

    result = run_tool("ruff", check.args, repo_root, check.timeout_sec, env)
    findings: List[Finding] = []
    if result.exit_code != 0:
        findings.append(
            Finding(
                check_id=check.id,
                finding_type="formatting",
                rule_id="RUFF_FORMAT",
                severity="low",
                message="Ruff formatter reported formatting differences.",
                fingerprint="",
                tool="ruff",
                remediation_hint="Run ruff format to apply formatting.",
            )
        )
    return CheckOutcome(check.id, findings, None, result)


def run_ruff_lint(
    check: RuffLintCheck, repo_root: Path, env: Dict[str, str]
) -> CheckOutcome:
    if not tool_exists("ruff"):
        return CheckOutcome(check.id, [], "ruff not found", None)

    result = run_tool("ruff", check.args, repo_root, check.timeout_sec, env)
    findings: List[Finding] = []
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = []
        for item in payload:
            location = FindingLocation(
                path=item.get("filename"),
                line=item.get("location", {}).get("row"),
                col=item.get("location", {}).get("column"),
                end_line=item.get("end_location", {}).get("row"),
                end_col=item.get("end_location", {}).get("column"),
            )
            findings.append(
                Finding(
                    check_id=check.id,
                    finding_type="lint",
                    rule_id=item.get("code", "RUFF"),
                    severity="medium",
                    message=item.get("message", "Ruff lint finding."),
                    fingerprint="",
                    tool="ruff",
                    remediation_hint=item.get("fix", {}).get("message")
                    if isinstance(item.get("fix"), dict)
                    else None,
                    location=location,
                )
            )
    elif result.exit_code != 0:
        findings.append(
            Finding(
                check_id=check.id,
                finding_type="lint",
                rule_id="RUFF",
                severity="medium",
                message="Ruff reported lint issues.",
                fingerprint="",
                tool="ruff",
            )
        )
    return CheckOutcome(check.id, findings, None, result)


def run_pyright(
    check: PyrightCheck, repo_root: Path, env: Dict[str, str]
) -> CheckOutcome:
    if not tool_exists("pyright"):
        return CheckOutcome(check.id, [], "pyright not found", None)

    result = run_tool("pyright", check.args, repo_root, check.timeout_sec, env)
    findings: List[Finding] = []
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {}
        diagnostics = payload.get("generalDiagnostics", [])
        for item in diagnostics:
            severity = _severity_from_pyright(item.get("severity", "error"))
            location = None
            if "file" in item and "range" in item:
                range_data = item.get("range", {})
                start = range_data.get("start", {})
                end = range_data.get("end", {})
                location = FindingLocation(
                    path=item.get("file"),
                    line=start.get("line", 0) + 1,
                    col=start.get("character", 0) + 1,
                    end_line=end.get("line", 0) + 1,
                    end_col=end.get("character", 0) + 1,
                )
            findings.append(
                Finding(
                    check_id=check.id,
                    finding_type="typecheck",
                    rule_id=item.get("rule") or item.get("ruleId") or "PYRIGHT",
                    severity=severity,
                    message=item.get("message", "Pyright diagnostic."),
                    fingerprint="",
                    tool="pyright",
                    location=location,
                )
            )
    elif result.exit_code != 0:
        findings.append(
            Finding(
                check_id=check.id,
                finding_type="typecheck",
                rule_id="PYRIGHT",
                severity="high",
                message="Pyright reported typecheck errors.",
                fingerprint="",
                tool="pyright",
            )
        )
    return CheckOutcome(check.id, findings, None, result)


def run_pytest(
    check: PytestCheck, repo_root: Path, env: Dict[str, str]
) -> CheckOutcome:
    if not tool_exists("pytest"):
        return CheckOutcome(check.id, [], "pytest not found", None)

    result = run_tool("pytest", check.args, repo_root, check.timeout_sec, env)
    findings: List[Finding] = []
    if result.exit_code != 0:
        message = result.stdout.strip().splitlines()[:1]
        summary = message[0] if message else "Pytest reported failures."
        findings.append(
            Finding(
                check_id=check.id,
                finding_type="tests",
                rule_id="PYTEST_FAILED",
                severity="high",
                message=summary,
                fingerprint="",
                tool="pytest",
            )
        )
    return CheckOutcome(check.id, findings, None, result)


def _default_lockfiles(tool: str) -> List[str]:
    mapping = {
        "uv": ["uv.lock"],
        "poetry": ["poetry.lock"],
        "pdm": ["pdm.lock"],
        "pip-tools": ["requirements.txt"],
        "pip": ["requirements.txt"],
    }
    return mapping.get(tool, [])


def detect_packaging_tool(config: VibeGateConfig) -> str:
    if config.packaging.tool != "auto":
        return config.packaging.tool
    for tool in config.packaging.tool_detection_order:
        if tool_exists(tool):
            return tool
    return "pip"


def _script_mentions_uv(value: object) -> bool:
    if isinstance(value, str):
        return "uv" in value.lower()
    if isinstance(value, list):
        return any(_script_mentions_uv(item) for item in value)
    if isinstance(value, dict):
        return any(_script_mentions_uv(item) for item in value.values())
    return False


def _uv_detected(repo_root: Path, workspace_files: List[Path]) -> bool:
    if (repo_root / "uv.lock").exists():
        return True
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        return False
    if pyproject_path not in workspace_files:
        return False
    try:
        payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return False
    tool_payload = payload.get("tool", {})
    if isinstance(tool_payload, dict) and "uv" in tool_payload:
        return True
    project_scripts = payload.get("project", {}).get("scripts", {})
    poetry_scripts = tool_payload.get("poetry", {}).get("scripts", {})
    pdm_scripts = tool_payload.get("pdm", {}).get("scripts", {})
    return any(
        _script_mentions_uv(scripts)
        for scripts in (project_scripts, poetry_scripts, pdm_scripts)
    )


def run_dependency_hygiene(
    check: DependencyHygieneCheck,
    repo_root: Path,
    env: Dict[str, str],
    config: VibeGateConfig,
    workspace_files: List[Path],
) -> CheckOutcome:
    findings: List[Finding] = []
    tool = detect_packaging_tool(config)
    lockfiles = config.packaging.lockfiles or _default_lockfiles(tool)

    if tool == "uv" and not _uv_detected(repo_root, workspace_files):
        return CheckOutcome(check.id, [], "uv not detected in project", None)

    if "lockfile_required" in check.rules:
        if lockfiles and not any((repo_root / path).exists() for path in lockfiles):
            findings.append(
                Finding(
                    check_id=check.id,
                    finding_type="dependency_hygiene",
                    rule_id="LOCKFILE_MISSING",
                    severity="high",
                    message=f"Missing lockfile for packaging tool {tool}.",
                    fingerprint="",
                )
            )

    tool_result = None
    if tool == "uv" and "lockfile_fresh" in check.rules:
        if not tool_exists("uv"):
            return CheckOutcome(check.id, findings, "uv not found", None)
        tool_result = run_tool(
            "uv", ["lock", "--check"], repo_root, check.timeout_sec, env
        )
        if tool_result.exit_code != 0:
            findings.append(
                Finding(
                    check_id=check.id,
                    finding_type="dependency_hygiene",
                    rule_id="LOCKFILE_STALE",
                    severity="medium",
                    message="uv lockfile is out of date.",
                    fingerprint="",
                    tool="uv",
                )
            )

    return CheckOutcome(check.id, findings, None, tool_result)


def run_bandit(
    check: BanditCheck, repo_root: Path, env: Dict[str, str]
) -> CheckOutcome:
    if not tool_exists("bandit"):
        return CheckOutcome(check.id, [], "bandit not found", None)

    # Add venv exclusions to prevent scanning dependencies (fixes #79)
    # Bandit's -x flag takes comma-separated glob patterns as ONE argument
    venv_exclusions = ["-x", ".venv,.venv-*,venv,env,**/site-packages"]

    # Prepend exclusions to user args (user args take precedence for output path, etc.)
    bandit_args = venv_exclusions + check.args

    result = run_tool("bandit", bandit_args, repo_root, check.timeout_sec, env)
    artifacts = [
        repo_root / Path(path) for path in check.args if path.endswith(".json")
    ]
    result = ToolResult(
        argv=result.argv,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        duration_ms=result.duration_ms,
        tool_version=result.tool_version,
        artifacts=artifacts,
    )
    findings: List[Finding] = []
    for artifact in artifacts:
        if not artifact.exists():
            continue
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        for item in payload.get("results", []):
            severity = str(item.get("issue_severity", "medium")).lower()
            findings.append(
                Finding(
                    check_id=check.id,
                    finding_type="sast",
                    rule_id=item.get("test_id", "BANDIT"),
                    severity=severity,
                    message=item.get("issue_text", "Bandit finding."),
                    fingerprint="",
                    tool="bandit",
                    location=FindingLocation(
                        path=item.get("filename"), line=item.get("line_number")
                    ),
                )
            )
    return CheckOutcome(check.id, findings, None, result)


def run_gitleaks(
    check: GitleaksCheck, repo_root: Path, env: Dict[str, str]
) -> CheckOutcome:
    if not tool_exists("gitleaks"):
        return CheckOutcome(check.id, [], "gitleaks not found", None)

    result = run_tool("gitleaks", check.args, repo_root, check.timeout_sec, env)
    artifacts = [
        repo_root / Path(path) for path in check.args if path.endswith(".json")
    ]
    result = ToolResult(
        argv=result.argv,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        duration_ms=result.duration_ms,
        tool_version=result.tool_version,
        artifacts=artifacts,
    )
    findings: List[Finding] = []
    for artifact in artifacts:
        if not artifact.exists():
            continue
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        for item in payload:
            findings.append(
                Finding(
                    check_id=check.id,
                    finding_type="secrets",
                    rule_id=item.get("RuleID", "GITLEAKS"),
                    severity="high",
                    message=item.get("Description", "Secret detected."),
                    fingerprint="",
                    tool="gitleaks",
                    location=FindingLocation(
                        path=item.get("File"), line=item.get("StartLine")
                    ),
                )
            )
    return CheckOutcome(check.id, findings, None, result)


def run_osv(
    check: VulnerabilityCheck, repo_root: Path, env: Dict[str, str]
) -> CheckOutcome:
    if check.mode == "skip":
        return CheckOutcome(check.id, [], "vulnerability check disabled", None)
    if check.local_db is None or not (repo_root / check.local_db.path).exists():
        return CheckOutcome(check.id, [], "offline DB snapshot not configured", None)
    if not tool_exists("osv-scanner"):
        return CheckOutcome(check.id, [], "osv-scanner not found", None)

    result = run_tool("osv-scanner", check.args, repo_root, check.timeout_sec, env)
    findings: List[Finding] = []
    if result.exit_code != 0:
        message = result.stdout.strip().splitlines()[:1]
        summary = message[0] if message else "osv-scanner reported vulnerabilities."
        findings.append(
            Finding(
                check_id=check.id,
                finding_type="vulnerability",
                rule_id="OSV",
                severity="high",
                message=summary,
                fingerprint="",
                tool="osv-scanner",
            )
        )
    return CheckOutcome(check.id, findings, None, result)


def run_config_sanity(
    check: ConfigSanityCheck, repo_root: Path, workspace_files: List[Path]
) -> CheckOutcome:
    findings: List[Finding] = []
    files = filter_workspace_files(
        workspace_files, repo_root, check.include_globs, check.exclude_globs
    )

    debug_pattern = re.compile(r"debug=True")
    debug_env_pattern = re.compile(r"DEBUG\s*=\s*True")
    app_debug_pattern = re.compile(r"app\.debug\s*=\s*True")
    reload_pattern = re.compile(r"--reload|reload=True")
    cors_pattern = re.compile(
        r"allow_origins\s*=\s*\[\"\*\"\]|allow_origin_regex\s*=\s*\".*\*"
    )
    secret_pattern = re.compile(r"(SECRET|TOKEN|API_KEY|PASSWORD)\s*[:=]\s*['\"]")
    placeholder_comment_pattern = re.compile(
        r"#\s*(TODO|FIXME|XXX|HACK|WIP)\b", re.IGNORECASE
    )
    not_implemented_pattern = re.compile(r"raise\s+NotImplementedError")
    placeholder_docstring_pattern = re.compile(
        r'""".*(?:TODO|placeholder|implement this).*"""', re.IGNORECASE | re.DOTALL
    )

    for path in files:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except FileNotFoundError:
            continue

        # Check for placeholder docstrings in the entire file content
        if "no_placeholder_docstrings" in check.rules and path.suffix == ".py":
            if placeholder_docstring_pattern.search(content):
                # Try to find the line number
                lines = content.splitlines()
                for idx, line in enumerate(lines, start=1):
                    if '"""' in line and (
                        re.search(
                            r"TODO|placeholder|implement this", line, re.IGNORECASE
                        )
                    ):
                        findings.append(
                            Finding(
                                check_id=check.id,
                                finding_type="config_sanity",
                                rule_id="no_placeholder_docstrings",
                                severity="medium",
                                message="Placeholder content detected in docstring.",
                                fingerprint="",
                                location=FindingLocation(
                                    path=str(path.relative_to(repo_root)), line=idx
                                ),
                            )
                        )
                        break

        for idx, line in enumerate(content.splitlines(), start=1):
            if "no_debug_true" in check.rules and path.suffix == ".py":
                if (
                    debug_pattern.search(line)
                    or debug_env_pattern.search(line)
                    or app_debug_pattern.search(line)
                ):
                    findings.append(
                        Finding(
                            check_id=check.id,
                            finding_type="config_sanity",
                            rule_id="no_debug_true",
                            severity="high",
                            message="Debug mode appears to be enabled.",
                            fingerprint="",
                            location=FindingLocation(
                                path=str(path.relative_to(repo_root)), line=idx
                            ),
                        )
                    )
            if "no_uvicorn_reload_in_prod" in check.rules:
                if reload_pattern.search(line):
                    findings.append(
                        Finding(
                            check_id=check.id,
                            finding_type="config_sanity",
                            rule_id="no_uvicorn_reload_in_prod",
                            severity="medium",
                            message="Uvicorn reload appears enabled.",
                            fingerprint="",
                            location=FindingLocation(
                                path=str(path.relative_to(repo_root)), line=idx
                            ),
                        )
                    )
            if "no_allow_all_cors" in check.rules:
                if cors_pattern.search(line):
                    findings.append(
                        Finding(
                            check_id=check.id,
                            finding_type="config_sanity",
                            rule_id="no_allow_all_cors",
                            severity="medium",
                            message="CORS allow-all configuration detected.",
                            fingerprint="",
                            location=FindingLocation(
                                path=str(path.relative_to(repo_root)), line=idx
                            ),
                        )
                    )
            if "no_hardcoded_secrets_like_patterns" in check.rules:
                if secret_pattern.search(line):
                    findings.append(
                        Finding(
                            check_id=check.id,
                            finding_type="config_sanity",
                            rule_id="no_hardcoded_secrets_like_patterns",
                            severity="high",
                            message="Potential hardcoded secret detected.",
                            fingerprint="",
                            location=FindingLocation(
                                path=str(path.relative_to(repo_root)), line=idx
                            ),
                        )
                    )
            if "no_placeholder_comments" in check.rules and path.suffix == ".py":
                if placeholder_comment_pattern.search(line):
                    findings.append(
                        Finding(
                            check_id=check.id,
                            finding_type="config_sanity",
                            rule_id="no_placeholder_comments",
                            severity="medium",
                            message="Placeholder comment detected (TODO/FIXME/XXX/HACK/WIP).",
                            fingerprint="",
                            location=FindingLocation(
                                path=str(path.relative_to(repo_root)), line=idx
                            ),
                        )
                    )
            if "no_not_implemented" in check.rules and path.suffix == ".py":
                if not_implemented_pattern.search(line):
                    findings.append(
                        Finding(
                            check_id=check.id,
                            finding_type="config_sanity",
                            rule_id="no_not_implemented",
                            severity="high",
                            message="NotImplementedError detected in code.",
                            fingerprint="",
                            location=FindingLocation(
                                path=str(path.relative_to(repo_root)), line=idx
                            ),
                        )
                    )
    return CheckOutcome(check.id, findings, None, None)


def _scan_python_files(
    repo_root: Path, workspace_files: List[Path], exclude_globs: List[str] | None = None
) -> List[Path]:
    """Scan for Python files in workspace."""
    if exclude_globs is None:
        exclude_globs = []
    return filter_workspace_files(
        workspace_files, repo_root, ["**/*.py"], exclude_globs
    )


class ErrorHandlingVisitor(ast.NodeVisitor):
    """AST visitor to detect error handling issues."""

    def __init__(self, file_path: Path, repo_root: Path, check: ErrorHandlingCheck):
        self.file_path = file_path
        self.repo_root = repo_root
        self.check = check
        self.findings: List[Finding] = []
        self.has_logging_import = False

    def visit_Import(self, node: ast.Import) -> None:
        """Check for logging import."""
        for alias in node.names:
            if alias.name == "logging":
                self.has_logging_import = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check for logging import from."""
        if node.module == "logging":
            self.has_logging_import = True
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Visit try/except blocks to detect error handling issues."""
        for handler in node.handlers:
            # Check for bare except
            if "bare_except" in self.check.rules:
                if handler.type is None:
                    self.findings.append(
                        Finding(
                            check_id=self.check.id,
                            finding_type="error_handling",
                            rule_id="bare_except",
                            severity="high",
                            message="Bare except clause without exception type",
                            fingerprint="",
                            tool="vibegate",
                            remediation_hint="Specify exception type: except ValueError:",
                            location=FindingLocation(
                                path=str(self.file_path.relative_to(self.repo_root)),
                                line=handler.lineno,
                            ),
                        )
                    )

            # Check for empty except body
            if "empty_except" in self.check.rules:
                if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                    self.findings.append(
                        Finding(
                            check_id=self.check.id,
                            finding_type="error_handling",
                            rule_id="empty_except",
                            severity="high",
                            message="Empty except block swallows errors silently",
                            fingerprint="",
                            tool="vibegate",
                            remediation_hint="Add logging or re-raise exception",
                            location=FindingLocation(
                                path=str(self.file_path.relative_to(self.repo_root)),
                                line=handler.lineno,
                            ),
                        )
                    )

            # Check for generic Exception catch
            if "generic_exceptions" in self.check.rules:
                if (
                    isinstance(handler.type, ast.Name)
                    and handler.type.id == "Exception"
                ):
                    self.findings.append(
                        Finding(
                            check_id=self.check.id,
                            finding_type="error_handling",
                            rule_id="generic_exceptions",
                            severity="medium",
                            message="Catching generic Exception - too broad",
                            fingerprint="",
                            tool="vibegate",
                            remediation_hint="Catch specific exception types",
                            location=FindingLocation(
                                path=str(self.file_path.relative_to(self.repo_root)),
                                line=handler.lineno,
                            ),
                        )
                    )

            # Check for missing logging (heuristic)
            if "missing_logging" in self.check.rules:
                if self.has_logging_import:
                    # Check if handler body contains logging calls
                    has_logging = self._has_logging_call(handler.body)
                    if not has_logging and len(handler.body) > 0:
                        # Not empty and no logging - could be an issue
                        self.findings.append(
                            Finding(
                                check_id=self.check.id,
                                finding_type="error_handling",
                                rule_id="missing_logging",
                                severity="low",
                                message="Exception handler may benefit from logging",
                                fingerprint="",
                                tool="vibegate",
                                remediation_hint="Consider adding logging.error() or logging.exception()",
                                location=FindingLocation(
                                    path=str(
                                        self.file_path.relative_to(self.repo_root)
                                    ),
                                    line=handler.lineno,
                                ),
                            )
                        )

        self.generic_visit(node)

    def _has_logging_call(self, body: List[ast.stmt]) -> bool:
        """Check if body contains logging calls."""
        for stmt in body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                if isinstance(stmt.value.func, ast.Attribute):
                    if isinstance(stmt.value.func.value, ast.Name):
                        if stmt.value.func.value.id == "logging":
                            return True
                    elif isinstance(stmt.value.func.value, ast.Attribute):
                        # Handle cases like logger.error()
                        if isinstance(stmt.value.func.value.value, ast.Name):
                            if stmt.value.func.value.value.id in (
                                "logging",
                                "logger",
                                "log",
                            ):
                                return True
            elif isinstance(stmt, (ast.If, ast.For, ast.While, ast.Try)):
                # Recursively check nested structures
                if hasattr(stmt, "body") and self._has_logging_call(stmt.body):
                    return True
        return False


def run_error_handling_check(
    check: ErrorHandlingCheck, repo_root: Path, workspace_files: List[Path]
) -> CheckOutcome:
    """Run error handling checks using AST analysis."""
    findings: List[Finding] = []
    python_files = _scan_python_files(repo_root, workspace_files, check.exclude_globs)

    for py_file in python_files:
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))
            visitor = ErrorHandlingVisitor(py_file, repo_root, check)
            visitor.visit(tree)
            findings.extend(visitor.findings)
        except SyntaxError:
            # Skip files with syntax errors (caught by other checks)
            continue
        except Exception:
            # Skip files that can't be parsed
            continue

    return CheckOutcome(check.id, findings, None, None)


class DefensiveProgrammingVisitor(ast.NodeVisitor):
    """AST visitor to detect defensive programming issues."""

    def __init__(
        self, file_path: Path, repo_root: Path, check: DefensiveProgrammingCheck
    ):
        self.file_path = file_path
        self.repo_root = repo_root
        self.check = check
        self.findings: List[Finding] = []
        self.parent_nodes: List[ast.AST] = []
        self.guarded_attributes: Dict[str, List[int]] = {}
        self.guarded_dicts: Dict[str, List[int]] = {}
        self.guarded_lists: Dict[str, List[int]] = {}

    def visit(self, node: ast.AST) -> None:
        """Visit node and maintain parent stack."""
        self.parent_nodes.append(node)
        super().visit(node)
        self.parent_nodes.pop()

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Check attribute access for None guards."""
        if self.check.require_none_checks:
            # Check if this attribute access is guarded
            if not self._has_none_guard(node.value):
                # Only report if it's not a method call on a known safe object
                if not isinstance(node.value, (ast.Constant, ast.Name, ast.Call)):
                    self.findings.append(
                        Finding(
                            check_id=self.check.id,
                            finding_type="defensive_coding",
                            rule_id="missing_none_check",
                            severity="medium",
                            message=f"Attribute access '{node.attr}' without None check",
                            fingerprint="",
                            tool="vibegate",
                            remediation_hint="Add 'if obj is not None:' guard before attribute access",
                            location=FindingLocation(
                                path=str(self.file_path.relative_to(self.repo_root)),
                                line=node.lineno,
                            ),
                        )
                    )
        self.generic_visit(node)

    def _is_type_annotation(self, node: ast.Subscript) -> bool:
        """Check if this subscript is part of a type annotation (safe, false positive)."""
        # Type annotations appear in function signatures, variable annotations, dataclass fields.
        # Strategy: Check all ancestors in parent_nodes to see if any indicate annotation context.
        # This handles nested subscripts like List[dict[str, str]] automatically since any
        # ancestor being in an annotation context means this subscript is also a type annotation.

        # parent_nodes contains all ancestors including current node (current is last)
        # Check all ancestors (skip current node itself which is at index -1)
        ancestors = self.parent_nodes[:-1] if len(self.parent_nodes) > 1 else []

        for ancestor in ancestors:
            # Function parameter annotations (func(arg: List[str]))
            if isinstance(ancestor, ast.arg):
                return True
            # Variable annotations (x: List[str] = ...) or dataclass field annotations
            if isinstance(ancestor, ast.AnnAssign):
                # If we're inside an AnnAssign, any subscript is part of the type annotation
                return True
            # Function return type annotations
            if isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if ancestor.returns and self._is_nested_in(node, ancestor.returns):
                    return True
        return False

    def _is_nested_in(self, needle: ast.AST, haystack: ast.AST) -> bool:
        """Check if needle AST node is nested within haystack."""
        for child in ast.walk(haystack):
            if child == needle:
                return True
        return False

    def _is_ast_node_access(self, node: ast.Subscript) -> bool:
        """Check if this subscript access is actually AST node attribute access (safe)."""
        # AST node attributes like node.attr, node.value, node.id are accessed via attributes,
        # not subscripts. But if the value is a known AST node variable, the subscript
        # is likely accessing a container property that's guaranteed to exist.
        # However, we can't reliably detect this without type information.
        # Instead, check if we're in an AST visitor context (visiting AST nodes)
        # This is a heuristic: if the parent is an AST visitor method, skip
        for parent in reversed(self.parent_nodes):
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if function name starts with 'visit_' (AST visitor pattern)
                if parent.name.startswith("visit_"):
                    return True
                # Also check if it's in a visitor class context
                if any(
                    isinstance(p, ast.ClassDef) and "Visitor" in p.name
                    for p in self.parent_nodes
                ):
                    return True
        return False

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Check dictionary/list access for bounds/keys checks."""
        # Skip type annotations (false positives)
        if self._is_type_annotation(node):
            self.generic_visit(node)
            return

        # Skip AST node attribute accesses (these are safe, not dict access)
        if self._is_ast_node_access(node):
            self.generic_visit(node)
            return

        # Skip string slicing operations (they use Slice nodes, not Index/Constant)
        # String slicing like base[:77] has a Slice node as the slice, not a dict key
        if isinstance(node.slice, ast.Slice):
            self.generic_visit(node)
            return

        if isinstance(node.value, ast.Name) or isinstance(node.value, ast.Attribute):
            var_name = self._get_variable_name(node.value)
            if var_name:
                # Check for dictionary access
                if self.check.require_bounds_checks:
                    # Heuristic: if we can't determine it's a dict, check anyway
                    if not self._has_dict_key_check(
                        var_name, node
                    ) and not self._has_dict_get_pattern(node):
                        self.findings.append(
                            Finding(
                                check_id=self.check.id,
                                finding_type="defensive_coding",
                                rule_id="missing_dict_key_check",
                                severity="medium",
                                message="Dictionary access without key check or .get()",
                                fingerprint="",
                                tool="vibegate",
                                remediation_hint="Use .get() method or check 'key in dict' before access",
                                location=FindingLocation(
                                    path=str(
                                        self.file_path.relative_to(self.repo_root)
                                    ),
                                    line=node.lineno,
                                ),
                            )
                        )
                    # Check for list indexing
                    elif not self._has_list_length_check(var_name, node):
                        self.findings.append(
                            Finding(
                                check_id=self.check.id,
                                finding_type="defensive_coding",
                                rule_id="missing_bounds_check",
                                severity="medium",
                                message="List indexing without length validation",
                                fingerprint="",
                                tool="vibegate",
                                remediation_hint="Add length check: 'if idx < len(list):' before indexing",
                                location=FindingLocation(
                                    path=str(
                                        self.file_path.relative_to(self.repo_root)
                                    ),
                                    line=node.lineno,
                                ),
                            )
                        )
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Check division operations for zero divisor."""
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            # Skip Path division operations (Path / str)
            if self._is_path_division(node):
                self.generic_visit(node)
                return

            if self.check.require_bounds_checks:
                if not self._has_zero_check(node.right):
                    self.findings.append(
                        Finding(
                            check_id=self.check.id,
                            finding_type="defensive_coding",
                            rule_id="missing_zero_check",
                            severity="high",
                            message="Division operation without zero divisor check",
                            fingerprint="",
                            tool="vibegate",
                            remediation_hint="Add check: 'if divisor != 0:' before division",
                            location=FindingLocation(
                                path=str(self.file_path.relative_to(self.repo_root)),
                                line=node.lineno,
                            ),
                        )
                    )
        self.generic_visit(node)

    def _has_none_guard(self, node: ast.AST) -> bool:
        """Check if attribute access is guarded by None check."""
        if isinstance(node, ast.Name):
            var_name = node.id
            # Check parent if statements
            for parent in reversed(self.parent_nodes):
                if isinstance(parent, ast.If):
                    test = parent.test
                    if isinstance(test, ast.Compare):
                        if (
                            len(test.ops) == 1
                            and isinstance(test.ops[0], ast.IsNot)
                            and isinstance(test.left, ast.Name)
                            and test.left.id == var_name
                            and isinstance(test.comparators[0], ast.Constant)
                            and test.comparators[0].value is None
                        ):
                            return True
        return False

    def _get_variable_name(self, node: ast.AST) -> str | None:
        """Get variable name from node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _has_dict_key_check(self, var_name: str, node: ast.Subscript) -> bool:
        """Check if dictionary access has key check."""
        # Look for 'key in dict' or 'dict.get(key)' patterns
        for parent in reversed(self.parent_nodes):
            if isinstance(parent, ast.If):
                test = parent.test
                if isinstance(test, ast.Compare):
                    if (
                        len(test.ops) == 1
                        and isinstance(test.ops[0], ast.In)
                        and isinstance(test.left, ast.Name)
                    ):
                        # Check if comparing against the dict variable
                        if (
                            isinstance(test.comparators[0], ast.Name)
                            and test.comparators[0].id == var_name
                        ):
                            return True
        return False

    def _has_dict_get_pattern(self, node: ast.Subscript) -> bool:
        """Check if this is actually a .get() call (which is safe)."""
        # This would be caught at a different level, but we can check parent
        for parent in reversed(self.parent_nodes):
            if isinstance(parent, ast.Call):
                if isinstance(parent.func, ast.Attribute) and parent.func.attr == "get":
                    return True
        return False

    def _has_list_length_check(self, var_name: str, node: ast.Subscript) -> bool:
        """Check if list indexing has length check."""
        # Extract index value, ensuring it's an int or None
        index_value: int | None = None
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
            index_value = node.slice.value

        for parent in reversed(self.parent_nodes):
            if not isinstance(parent, ast.If):
                continue

            if self._check_truthiness_guard(parent.test, var_name, index_value):
                return True
            if self._check_length_comparison(parent.test, var_name, index_value):
                return True
            if self._check_compound_length_guard(parent.test, var_name, index_value):
                return True

        return False

    def _check_truthiness_guard(
        self, test: ast.AST, var_name: str, index_value: int | None
    ) -> bool:
        """Check for 'if list:' pattern (safe for [0] only)."""
        if isinstance(test, ast.Name) and test.id == var_name:
            return index_value == 0
        return False

    def _check_length_comparison(
        self, test: ast.AST, var_name: str, index_value: int | None
    ) -> bool:
        """Check for 'if len(list) >= N:' pattern."""
        if not isinstance(test, ast.Compare):
            return False

        if len(test.ops) != 1 or not isinstance(test.ops[0], (ast.Gt, ast.GtE)):
            return False

        if len(test.comparators) != 1 or not isinstance(
            test.comparators[0], ast.Constant
        ):
            return False

        if not isinstance(test.left, ast.Call):
            return False

        call = test.left
        if not (
            isinstance(call.func, ast.Name)
            and call.func.id == "len"
            and len(call.args) == 1
            and isinstance(call.args[0], ast.Name)
            and call.args[0].id == var_name
        ):
            return False

        # Extract required length, ensuring it's an int
        if not (
            isinstance(test.comparators[0], ast.Constant)
            and isinstance(test.comparators[0].value, int)
        ):
            return True  # Has length check but can't verify index safety

        required_len: int = test.comparators[0].value
        if index_value is None:
            return True  # Has length check, unknown index

        if isinstance(test.ops[0], ast.Gt):
            return index_value <= required_len
        else:  # GtE
            return index_value < required_len

    def _check_compound_length_guard(
        self, test: ast.AST, var_name: str, index_value: int | None
    ) -> bool:
        """Check for 'if list and len(list) >= N:' pattern."""
        if not (isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And)):
            return False

        has_guard = False
        for value in test.values:
            # Truthiness check
            if isinstance(value, ast.Name) and value.id == var_name:
                has_guard = True
            # Length check
            if self._check_length_comparison(value, var_name, index_value):
                has_guard = True

        return has_guard

    def _is_path_division(self, node: ast.BinOp) -> bool:
        """Check if this is a Path division operation (Path / str) rather than math division."""
        # Path division typically: Path / str or Path-like variable / str
        # Check if right operand is a string constant or variable (in file/dir context)
        right_is_str = isinstance(node.right, ast.Constant) and isinstance(
            node.right.value, str
        )

        # Also check if right is a variable name that's likely a string (in os.walk context)
        # In os.walk, dirs and filenames are always strings
        right_is_likely_str = False
        if isinstance(node.right, ast.Name):
            # Common string variable names in file operations
            str_names = {"name", "filename", "dirname", "entry", "rel_path", "rel_root"}
            if node.right.id.lower() in str_names or node.right.id.endswith("name"):
                right_is_likely_str = True

        # Check if left operand looks like a Path
        left = node.left
        left_is_path = False

        # Handle nested Path operations: (Path.cwd() / "schema") / filename
        # If left is itself a BinOp with /, it's likely a Path operation
        if isinstance(left, ast.BinOp) and isinstance(left.op, ast.Div):
            # Recursively check if the nested operation is Path division
            left_is_path = self._is_path_division(left)

        if isinstance(left, ast.Name):
            # Common Path variable names
            path_names = {
                "path",
                "repo_root",
                "root",
                "base",
                "dir",
                "directory",
                "cwd",
                "rel_root",
                "git_dir",
                "artifacts_root",
                "cwd",
            }
            if (
                left.id.lower() in path_names
                or left.id.endswith("_path")
                or left.id.endswith("_dir")
                or left.id.endswith("_root")
            ):
                left_is_path = True
        elif isinstance(left, ast.Attribute):
            # Check if it's Path.xxx or pathlib.Path
            if left.attr in ["parent", "stem", "suffix", "name", "cwd"]:
                left_is_path = True
            # Check for common Path construction patterns (Path.cwd(), pathlib.Path)
            if isinstance(left.value, ast.Name) and left.value.id == "Path":
                left_is_path = True
        elif isinstance(left, ast.Call):
            # Check if it's Path(...) constructor
            if isinstance(left.func, ast.Name) and left.func.id == "Path":
                left_is_path = True
            if isinstance(left.func, ast.Attribute) and left.func.attr == "Path":
                left_is_path = True
            # Path.cwd() / "schema"
            if isinstance(left.func, ast.Attribute) and left.func.attr == "cwd":
                if (
                    isinstance(left.func.value, ast.Name)
                    and left.func.value.id == "Path"
                ):
                    left_is_path = True

        # If left is clearly a Path, and right is string or likely string, it's Path division
        if left_is_path and (right_is_str or right_is_likely_str):
            return True

        # If left is a Path constructor/attribute, assume right is string (Path operations)
        if left_is_path:
            return True

        # Also check if result is used in Path context (assigned to path variable)
        if right_is_str and isinstance(left, (ast.Name, ast.Attribute, ast.Call)):
            # If right is string constant and left looks Path-like, it's likely Path division
            return True

        return False

    def _has_zero_check(self, node: ast.AST) -> bool:
        """Check if divisor has zero check.

        Detects control flow guards like:
        - if divisor != 0:
        - if divisor > 0:
        - if divisor >= 0: (weaker but accepted)
        - if total > 0 and ...: (division inside condition)
        - else branch after "if divisor == 0:" (inverse logic)
        """
        # Constant folding: if divisor is a non-zero constant, it's safe
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value != 0

        # Check for variable guards
        if isinstance(node, ast.Name):
            var_name = node.id
            # Check parent if statements for zero checks
            for parent in reversed(self.parent_nodes):
                if isinstance(parent, ast.If):
                    test = parent.test

                    # Handle simple comparisons: if divisor > 0, if divisor != 0, etc.
                    if isinstance(test, ast.Compare):
                        if (
                            len(test.ops) == 1
                            and len(test.comparators) == 1
                            and isinstance(test.left, ast.Name)
                            and test.left.id == var_name
                            and isinstance(test.comparators[0], ast.Constant)
                            and test.comparators[0].value == 0
                        ):
                            # Accept: !=, >, >= as protective guards in body
                            if isinstance(test.ops[0], (ast.NotEq, ast.Gt, ast.GtE)):
                                return True

                            # Accept: == 0 if we're in the else branch (inverse logic)
                            # Check if current node is in the else branch
                            if isinstance(test.ops[0], ast.Eq):
                                if self._is_in_else_branch(parent):
                                    return True

                    # Handle compound conditions: if var > 0 and ...:
                    # The division might be nested in the condition itself
                    if self._check_compound_guard(test, var_name):
                        return True

        return False

    def _is_in_else_branch(self, if_node: ast.If) -> bool:
        """Check if current position is in the else branch of an if statement."""
        # Walk backwards through parent nodes to find our position relative to if_node
        # If we're a descendant of if_node.orelse, we're in the else branch
        if not if_node.orelse:
            return False

        # Check if any of the current node's ancestors are in the else branch
        for i, parent in enumerate(self.parent_nodes):
            if parent == if_node:
                # Found the if node, check if we came from orelse
                if i + 1 < len(self.parent_nodes):
                    next_parent = self.parent_nodes[i + 1]
                    # Check if next_parent is in if_node.orelse
                    for else_node in if_node.orelse:
                        if self._is_nested_in(next_parent, else_node):
                            return True
                return False
        return False

    def _check_compound_guard(self, test: ast.AST, var_name: str) -> bool:
        """Check if test contains a zero guard for var_name in compound conditions.

        Handles patterns like: if total > 0 and percentage > 0.8:
        """
        if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
            # Check each value in the And operation
            for value in test.values:
                if isinstance(value, ast.Compare):
                    if (
                        len(value.ops) == 1
                        and len(value.comparators) == 1
                        and isinstance(value.left, ast.Name)
                        and value.left.id == var_name
                        and isinstance(value.comparators[0], ast.Constant)
                        and value.comparators[0].value == 0
                        and isinstance(value.ops[0], (ast.NotEq, ast.Gt, ast.GtE))
                    ):
                        return True
        return False


def run_defensive_programming_check(
    check: DefensiveProgrammingCheck,
    repo_root: Path,
    workspace_files: List[Path],
) -> CheckOutcome:
    """Run defensive programming checks using AST analysis."""
    findings: List[Finding] = []
    python_files = _scan_python_files(repo_root, workspace_files, check.exclude_globs)

    for py_file in python_files:
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))
            visitor = DefensiveProgrammingVisitor(py_file, repo_root, check)
            visitor.visit(tree)
            findings.extend(visitor.findings)
        except SyntaxError:
            continue
        except Exception:
            continue

    return CheckOutcome(check.id, findings, None, None)


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor to detect complexity issues."""

    def __init__(
        self, file_path: Path, repo_root: Path, check: ComplexityCheck, content: str
    ):
        self.file_path = file_path
        self.repo_root = repo_root
        self.check = check
        self.content = content
        self.findings: List[Finding] = []
        self.nesting_depth = 0
        self.max_nesting = 0

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Analyze function complexity."""
        # Calculate function length
        func_lines = self._count_function_lines(node)
        if func_lines > self.check.max_function_lines:
            self.findings.append(
                Finding(
                    check_id=self.check.id,
                    finding_type="complexity",
                    rule_id="function_too_long",
                    severity="medium",
                    message=f"Function '{node.name}' is {func_lines} lines (max: {self.check.max_function_lines})",
                    fingerprint="",
                    tool="vibegate",
                    remediation_hint=f"Split function into smaller functions (max {self.check.max_function_lines} lines)",
                    location=FindingLocation(
                        path=str(self.file_path.relative_to(self.repo_root)),
                        line=node.lineno,
                    ),
                )
            )

        # Reset nesting for this function
        old_nesting = self.nesting_depth
        self.nesting_depth = 0
        self.max_nesting = 0

        # Visit function body to calculate nesting and complexity
        for stmt in node.body:
            self.visit(stmt)

        # Check nesting depth
        if self.max_nesting > self.check.max_nesting_depth:
            self.findings.append(
                Finding(
                    check_id=self.check.id,
                    finding_type="complexity",
                    rule_id="nesting_too_deep",
                    severity="medium",
                    message=f"Function '{node.name}' has nesting depth {self.max_nesting} (max: {self.check.max_nesting_depth})",
                    fingerprint="",
                    tool="vibegate",
                    remediation_hint=f"Refactor to reduce nesting (max depth {self.check.max_nesting_depth})",
                    location=FindingLocation(
                        path=str(self.file_path.relative_to(self.repo_root)),
                        line=node.lineno,
                    ),
                )
            )

        # Calculate cyclomatic complexity
        complexity = self._calculate_complexity(node)
        if complexity > self.check.max_complexity:
            self.findings.append(
                Finding(
                    check_id=self.check.id,
                    finding_type="complexity",
                    rule_id="complexity_too_high",
                    severity="medium",
                    message=f"Function '{node.name}' has cyclomatic complexity {complexity} (max: {self.check.max_complexity})",
                    fingerprint="",
                    tool="vibegate",
                    remediation_hint=f"Simplify function logic to reduce complexity (max {self.check.max_complexity})",
                    location=FindingLocation(
                        path=str(self.file_path.relative_to(self.repo_root)),
                        line=node.lineno,
                    ),
                )
            )

        # Restore nesting
        self.nesting_depth = old_nesting

    def visit_If(self, node: ast.If) -> None:
        """Track nesting for if statements."""
        self.nesting_depth += 1
        self.max_nesting = max(self.max_nesting, self.nesting_depth)
        self.generic_visit(node)
        self.nesting_depth -= 1

    def visit_For(self, node: ast.For | ast.AsyncFor) -> None:
        """Track nesting for for loops."""
        self.nesting_depth += 1
        self.max_nesting = max(self.max_nesting, self.nesting_depth)
        self.generic_visit(node)
        self.nesting_depth -= 1

    def visit_While(self, node: ast.While) -> None:
        """Track nesting for while loops."""
        self.nesting_depth += 1
        self.max_nesting = max(self.max_nesting, self.nesting_depth)
        self.generic_visit(node)
        self.nesting_depth -= 1

    def visit_Try(self, node: ast.Try) -> None:
        """Track nesting for try blocks."""
        self.nesting_depth += 1
        self.max_nesting = max(self.max_nesting, self.nesting_depth)
        self.generic_visit(node)
        self.nesting_depth -= 1

    def visit_With(self, node: ast.With | ast.AsyncWith) -> None:
        """Track nesting for with statements."""
        self.nesting_depth += 1
        self.max_nesting = max(self.max_nesting, self.nesting_depth)
        self.generic_visit(node)
        self.nesting_depth -= 1

    def _count_function_lines(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> int:
        """Count lines in function body."""
        if not node.body:
            return 0
        start_line = node.lineno
        end_line = node.body[-1].end_lineno or start_line
        return end_line - start_line + 1

    def _calculate_complexity(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        return complexity


def run_complexity_check(
    check: ComplexityCheck, repo_root: Path, workspace_files: List[Path]
) -> CheckOutcome:
    """Run complexity checks using AST analysis."""
    findings: List[Finding] = []
    python_files = _scan_python_files(repo_root, workspace_files, check.exclude_globs)

    for py_file in python_files:
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))
            visitor = ComplexityVisitor(py_file, repo_root, check, content)
            visitor.visit(tree)
            findings.extend(visitor.findings)
        except SyntaxError:
            continue
        except Exception:
            continue

    return CheckOutcome(check.id, findings, None, None)


class DeadCodeVisitor(ast.NodeVisitor):
    """AST visitor to detect unreachable code."""

    def __init__(self, file_path: Path, repo_root: Path, check: DeadCodeCheck):
        self.file_path = file_path
        self.repo_root = repo_root
        self.check = check
        self.findings: List[Finding] = []

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check for unreachable code after return/raise."""
        if not node.body:
            return

        for i, stmt in enumerate(node.body):
            # Check if this statement is a return or raise
            if isinstance(stmt, (ast.Return, ast.Raise)):
                # Check if there are more statements after this
                if i + 1 < len(node.body):
                    next_stmt = node.body[i + 1]
                    # Skip docstrings and comments (they're OK)
                    if not (
                        isinstance(next_stmt, ast.Expr)
                        and isinstance(next_stmt.value, ast.Constant)
                        and isinstance(next_stmt.value.value, str)
                    ):
                        self.findings.append(
                            Finding(
                                check_id=self.check.id,
                                finding_type="dead_code",
                                rule_id="unreachable_code",
                                severity="low",
                                message=f"Unreachable code after {type(stmt).__name__.lower()} statement",
                                fingerprint="",
                                tool="vibegate",
                                remediation_hint="Remove unreachable code or refactor control flow",
                                location=FindingLocation(
                                    path=str(
                                        self.file_path.relative_to(self.repo_root)
                                    ),
                                    line=next_stmt.lineno,
                                ),
                            )
                        )
                        break  # Only report first unreachable block

        self.generic_visit(node)


def run_dead_code_check(
    check: DeadCodeCheck,
    repo_root: Path,
    workspace_files: List[Path],
    env: Dict[str, str],
) -> CheckOutcome:
    """Run dead code checks using tool integration and AST fallback."""
    findings: List[Finding] = []

    # Try vulture tool integration
    if tool_exists("vulture"):
        python_files = _scan_python_files(
            repo_root, workspace_files, check.exclude_globs
        )
        if python_files:
            # Build paths string
            paths = [str(f.relative_to(repo_root)) for f in python_files]
            try:
                # vulture doesn't have great JSON output, so we'll use AST fallback primarily
                # But we can still try to run it
                result = run_tool(
                    "vulture",
                    ["--min-confidence", str(check.min_confidence)]
                    + paths[:10],  # Limit for performance
                    repo_root,
                    check.timeout_sec,
                    env,
                )
                # Parse vulture output (text format)
                if result.stdout:
                    for line in result.stdout.splitlines():
                        # Vulture format: path:line: unused function/class/variable 'name'
                        if ":" in line and "unused" in line.lower():
                            parts = line.split(":", 2)
                            if len(parts) >= 3:
                                file_path = parts[0]
                                try:
                                    line_no = int(parts[1])
                                    message = parts[2].strip()
                                    findings.append(
                                        Finding(
                                            check_id=check.id,
                                            finding_type="dead_code",
                                            rule_id="unused_code",
                                            severity="low",
                                            message=message,
                                            fingerprint="",
                                            tool="vulture",
                                            remediation_hint="Remove unused code or mark as used",
                                            location=FindingLocation(
                                                path=file_path,
                                                line=line_no,
                                            ),
                                        )
                                    )
                                except ValueError:
                                    continue
            except Exception:
                # If vulture fails, continue with AST fallback
                pass

    # AST fallback for unreachable code
    if check.detect_commented_code:
        python_files = _scan_python_files(
            repo_root, workspace_files, check.exclude_globs
        )
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_file))
                visitor = DeadCodeVisitor(py_file, repo_root, check)
                visitor.visit(tree)
                findings.extend(visitor.findings)

                # Detect commented-out code blocks (heuristic)
                lines = content.splitlines()
                commented_block_start = None
                for idx, line in enumerate(lines, start=1):
                    stripped = line.strip()
                    # Look for consecutive comment lines that look like code
                    if stripped.startswith("#") and len(stripped) > 2:
                        # Check if it looks like code (has common code patterns)
                        comment_content = stripped[1:].strip()
                        if any(
                            pattern in comment_content
                            for pattern in [
                                "def ",
                                "if ",
                                "for ",
                                "while ",
                                "=",
                                "(",
                                ")",
                                "return",
                                "import",
                            ]
                        ):
                            if commented_block_start is None:
                                commented_block_start = idx
                        else:
                            if (
                                commented_block_start is not None
                                and (idx - commented_block_start) >= 3
                            ):
                                # Found a block of 3+ consecutive code-like comments
                                findings.append(
                                    Finding(
                                        check_id=check.id,
                                        finding_type="dead_code",
                                        rule_id="commented_code",
                                        severity="low",
                                        message="Commented-out code block detected",
                                        fingerprint="",
                                        tool="vibegate",
                                        remediation_hint="Remove commented code or convert to documentation",
                                        location=FindingLocation(
                                            path=str(py_file.relative_to(repo_root)),
                                            line=commented_block_start,
                                        ),
                                    )
                                )
                            commented_block_start = None
                    else:
                        if (
                            commented_block_start is not None
                            and (idx - commented_block_start) >= 3
                        ):
                            findings.append(
                                Finding(
                                    check_id=check.id,
                                    finding_type="dead_code",
                                    rule_id="commented_code",
                                    severity="low",
                                    message="Commented-out code block detected",
                                    fingerprint="",
                                    tool="vibegate",
                                    remediation_hint="Remove commented code or convert to documentation",
                                    location=FindingLocation(
                                        path=str(py_file.relative_to(repo_root)),
                                        line=commented_block_start,
                                    ),
                                )
                            )
                        commented_block_start = None

            except SyntaxError:
                continue
            except Exception:
                continue

    return CheckOutcome(check.id, findings, None, None)


def run_runtime_smoke(
    check: RuntimeSmokeCheck, repo_root: Path, env: Dict[str, str]
) -> CheckOutcome:
    return CheckOutcome(check.id, [], "runtime smoke check not implemented", None)


def run_coverage_check(repo_root: Path, config: CoverageCheck) -> CheckOutcome:
    """Run pytest coverage check and validate against thresholds.

    Executes pytest with coverage, parses coverage.json, and validates
    against minimum_coverage and target_coverage thresholds.

    Args:
        repo_root: Repository root directory
        config: Coverage check configuration

    Returns:
        CheckOutcome with findings if coverage below thresholds
    """
    if not tool_exists("pytest"):
        return CheckOutcome(config.id, [], "pytest not found", None)

    # Run pytest with coverage
    coverage_json_path = repo_root / "coverage.json"
    args = [
        "--cov",
        "--cov-report=json",
        "--cov-report=term",
    ]

    # Use deterministic environment for coverage
    env = {
        "COVERAGE_FILE": str(repo_root / ".coverage"),
        "PYTHONHASHSEED": "0",
    }

    result = run_tool("pytest", args, repo_root, config.timeout_sec, env)
    findings: List[Finding] = []

    # Check if coverage.json was generated
    if not coverage_json_path.exists():
        if config.fail_on_missing_tests:
            findings.append(
                Finding(
                    check_id=config.id,
                    finding_type="coverage",
                    rule_id="COVERAGE_FILE_MISSING",
                    severity="high",
                    message="Coverage report not generated - no tests found or pytest-cov not installed",
                    fingerprint="",
                    tool="pytest",
                    remediation_hint="Install pytest-cov: pip install pytest-cov",
                )
            )
        return CheckOutcome(config.id, findings, None, result)

    # Parse coverage.json
    try:
        coverage_data = json.loads(coverage_json_path.read_text(encoding="utf-8"))
        total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0.0)
    except (OSError, json.JSONDecodeError, KeyError) as e:
        findings.append(
            Finding(
                check_id=config.id,
                finding_type="coverage",
                rule_id="COVERAGE_PARSE_ERROR",
                severity="medium",
                message=f"Failed to parse coverage report: {e}",
                fingerprint="",
                tool="pytest",
            )
        )
        return CheckOutcome(config.id, findings, None, result)

    # Validate against minimum threshold (FAIL if below)
    if total_coverage < config.minimum_coverage:
        findings.append(
            Finding(
                check_id=config.id,
                finding_type="coverage",
                rule_id="COVERAGE_BELOW_MINIMUM",
                severity="high",
                message=f"Coverage {total_coverage:.2f}% is below minimum threshold {config.minimum_coverage:.2f}%",
                fingerprint="",
                tool="pytest",
                remediation_hint=f"Add tests to reach minimum {config.minimum_coverage:.2f}% coverage",
            )
        )

    # Validate against target threshold (WARN if below)
    elif total_coverage < config.target_coverage:
        findings.append(
            Finding(
                check_id=config.id,
                finding_type="coverage",
                rule_id="COVERAGE_BELOW_TARGET",
                severity="medium",
                message=f"Coverage {total_coverage:.2f}% is below target threshold {config.target_coverage:.2f}%",
                fingerprint="",
                tool="pytest",
                remediation_hint=f"Add tests to reach target {config.target_coverage:.2f}% coverage",
            )
        )

    return CheckOutcome(config.id, findings, None, result)
