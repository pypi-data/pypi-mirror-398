from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Sequence, Tuple, TypeGuard

import subprocess
import yaml

from vibegate.artifacts import (
    ArtifactRecord,
    build_fixpack,
    sha256_path,
    write_delta_report,
    write_evidence_graph,
    write_fixpack,
    write_report,
    write_report_html,
)
from vibegate.checks import (
    CheckOutcome,
    ToolResult,
    detect_packaging_tool,
    run_tool,
    run_bandit,
    run_config_sanity,
    run_dependency_hygiene,
    run_error_handling_check,
    run_defensive_programming_check,
    run_complexity_check,
    run_dead_code_check,
    run_coverage_check,
    run_gitleaks,
    run_osv,
    run_pyright,
    run_pytest,
    run_ruff_format,
    run_ruff_lint,
    run_runtime_smoke,
)
from vibegate.config import VibeGateConfig
from vibegate.evidence import EvidenceWriter, load_run_summary
from vibegate.findings import Finding
from vibegate.findings import FindingLocation
from vibegate.policy_semantic import SemanticRule, parse_semantic_rules
from vibegate.plugins.api import CheckPlugin, EmitterPlugin, PluginContext
from vibegate.plugins.loader import LoadedPlugin, load_plugins
from vibegate.plugins.types import Finding as PluginFinding
from vibegate.plugins.types import FindingLocation as PluginFindingLocation
from vibegate.workspace import collect_workspace_files


def _read_state_file(repo_root: Path) -> dict:
    """Read .vibegate/state.json, returning empty dict if missing or invalid."""
    state_path = repo_root / ".vibegate" / "state.json"
    if not state_path.exists():
        return {}
    try:
        with state_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _build_comparison(repo_root: Path, counts: dict[str, int]) -> dict[str, Any] | None:
    state = _read_state_file(repo_root)
    if not isinstance(state, dict):
        return None
    last_run = state.get("last_run")
    if not isinstance(last_run, dict):
        return None
    evidence_rel = last_run.get("evidence_path")
    if not evidence_rel:
        return None
    prev_summary = load_run_summary(repo_root / evidence_rel)
    if not prev_summary:
        return None
    prev_counts = prev_summary.get("counts")
    if not isinstance(prev_counts, dict):
        return None
    counts_delta: dict[str, int] = {}
    for key, value in counts.items():
        prev_value = prev_counts.get(key, 0)
        if isinstance(prev_value, int):
            counts_delta[key] = value - prev_value
    return {
        "baseline_run_id": prev_summary.get("run_id", ""),
        "counts_delta": counts_delta,
        "baseline_counts": prev_counts,
    }


def _baseline_fingerprints(repo_root: Path) -> set[str]:
    state = _read_state_file(repo_root)
    if not isinstance(state, dict):
        return set()
    last_run = state.get("last_run")
    if not isinstance(last_run, dict):
        return set()
    evidence_rel = last_run.get("evidence_path")
    if not evidence_rel:
        return set()
    evidence_path = repo_root / evidence_rel
    if not evidence_path.exists():
        return set()
    fingerprints: set[str] = set()
    try:
        with evidence_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if payload.get("event_type") == "finding":
                    fingerprint = payload.get("fingerprint")
                    if isinstance(fingerprint, str) and fingerprint:
                        fingerprints.add(fingerprint)
    except OSError:
        return set()
    return fingerprints


def _counts_by_check(findings: List[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        check_id = finding.check_id or "unknown"
        counts[check_id] = counts.get(check_id, 0) + 1
    return counts


def _load_baseline_findings(repo_root: Path) -> List[Finding]:
    state = _read_state_file(repo_root)
    if not isinstance(state, dict):
        return []
    last_run = state.get("last_run")
    if not isinstance(last_run, dict):
        return []
    evidence_rel = last_run.get("evidence_path")
    if not evidence_rel:
        return []
    evidence_path = repo_root / evidence_rel
    if not evidence_path.exists():
        return []
    findings: List[Finding] = []
    suppressed: set[str] = set()
    try:
        with evidence_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if payload.get("event_type") == "suppression_applied":
                    fingerprint = payload.get("fingerprint")
                    if isinstance(fingerprint, str) and fingerprint:
                        suppressed.add(fingerprint)
                if payload.get("event_type") == "finding":
                    fingerprint = payload.get("fingerprint") or ""
                    if fingerprint in suppressed:
                        continue
                    findings.append(
                        Finding(
                            check_id=payload.get("check_id", "unknown"),
                            finding_type=payload.get("finding_type", "finding"),
                            rule_id=payload.get("rule_id", "unknown"),
                            severity=payload.get("severity", "low"),
                            message=payload.get("message", ""),
                            fingerprint=fingerprint,
                            confidence=payload.get("confidence", "high"),
                            rule_version=payload.get("rule_version", "1"),
                        )
                    )
    except OSError:
        return []
    return findings


def _baseline_check_counts(repo_root: Path, policy) -> dict[str, int]:
    baseline_findings = _load_baseline_findings(repo_root)
    if not baseline_findings:
        return {}
    blocking, warnings = _apply_policy(baseline_findings, policy)
    return _counts_by_check(blocking + warnings)


def _write_state_file(
    repo_root: Path, evidence_path: Path, report_paths: List[Path]
) -> None:
    """Write .vibegate/state.json with last run metadata."""
    state_dir = repo_root / ".vibegate"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "state.json"

    # Preserve existing tune/propose data if present
    existing_state = _read_state_file(repo_root)

    state_data = {
        "version": 1,
        "last_run": {
            "evidence_path": str(evidence_path.relative_to(repo_root)),
            "report_paths": [str(p.relative_to(repo_root)) for p in report_paths],
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
    }

    if "last_run" in existing_state:
        state_data["previous_run"] = existing_state["last_run"]

    # Preserve last_tune and last_propose if they exist
    if "last_tune" in existing_state:
        state_data["last_tune"] = existing_state["last_tune"]
    if "last_propose" in existing_state:
        state_data["last_propose"] = existing_state["last_propose"]

    state_path.write_text(json.dumps(state_data, indent=2), encoding="utf-8")


def write_tune_state(
    repo_root: Path,
    out_dir: Path,
    report_path: Path,
    clusters_path: Path,
    examples_dir: Path,
) -> None:
    """Update state.json with last_tune metadata."""
    state_dir = repo_root / ".vibegate"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "state.json"

    # Preserve existing state
    existing_state = _read_state_file(repo_root)

    # Update last_tune
    existing_state["last_tune"] = {
        "out_dir": str(out_dir.relative_to(repo_root)),
        "report_path": str(report_path.relative_to(repo_root)),
        "clusters_path": str(clusters_path.relative_to(repo_root)),
        "examples_dir": str(examples_dir.relative_to(repo_root)),
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    state_path.write_text(
        json.dumps(existing_state, indent=2, sort_keys=True), encoding="utf-8"
    )


def write_propose_state(
    repo_root: Path, out_dir: Path, report_path: Path, proposals_path: Path
) -> None:
    """Update state.json with last_propose metadata."""
    state_dir = repo_root / ".vibegate"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "state.json"

    # Preserve existing state
    existing_state = _read_state_file(repo_root)

    # Update last_propose
    existing_state["last_propose"] = {
        "out_dir": str(out_dir.relative_to(repo_root)),
        "report_path": str(report_path.relative_to(repo_root)),
        "proposals_path": str(proposals_path.relative_to(repo_root)),
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    state_path.write_text(
        json.dumps(existing_state, indent=2, sort_keys=True), encoding="utf-8"
    )


@dataclass(frozen=True)
class SuppressionRecord:
    fingerprint: str
    rule_id: str | None
    justification: str
    expires_at: str
    actor: str | None


def _fingerprint(finding: Finding) -> str:
    location_path = ""
    start_line = ""
    end_line = ""
    if finding.location and finding.location.path:
        location_path = finding.location.path
        start_line = str(finding.location.line or "")
        end_line = str(finding.location.end_line or "")
    payload = (
        f"{finding.check_id}|{finding.rule_id}|{location_path}|"
        f"{start_line}|{end_line}|{finding.message}"
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _apply_fingerprints(findings: List[Finding]) -> List[Finding]:
    updated = []
    for finding in findings:
        updated.append(
            Finding(
                check_id=finding.check_id,
                finding_type=finding.finding_type,
                rule_id=finding.rule_id,
                severity=finding.severity,
                message=finding.message,
                fingerprint=_fingerprint(finding),
                confidence=finding.confidence,
                rule_version=finding.rule_version,
                tool=finding.tool,
                remediation_hint=finding.remediation_hint,
                location=finding.location,
                trigger_explanation=finding.trigger_explanation,
                ast_node_type=finding.ast_node_type,
                in_type_annotation=finding.in_type_annotation,
            )
        )
    return updated


def _finding_sort_key(finding: Finding) -> tuple:
    path = finding.location.path if finding.location and finding.location.path else ""
    line = (
        finding.location.line
        if finding.location and finding.location.line is not None
        else 0
    )
    return (finding.check_id, finding.rule_id, path, line, finding.message)


def _dedupe_findings(findings: List[Finding]) -> List[Finding]:
    seen = set()
    deduped = []
    for finding in findings:
        if finding.fingerprint in seen:
            continue
        seen.add(finding.fingerprint)
        deduped.append(finding)
    return deduped


def _load_suppressions(
    config: VibeGateConfig, repo_root: Path
) -> List[SuppressionRecord]:
    path = repo_root / config.suppressions.path
    if not path.exists():
        return []
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if payload.get("schema_version") != "v1alpha1":
        return []
    records = []
    now = datetime.now(timezone.utc)
    for item in payload.get("suppressions") or []:
        justification = item.get("justification")
        expires_at = item.get("expires_at")
        actor = item.get("actor")
        if config.suppressions.policy.require_justification and not justification:
            continue
        if config.suppressions.policy.require_expiry and not expires_at:
            continue
        if config.suppressions.policy.require_actor and not actor:
            continue
        try:
            expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            continue
        if expires_dt <= now:
            continue
        records.append(
            SuppressionRecord(
                fingerprint=item.get("fingerprint", ""),
                rule_id=item.get("rule_id"),
                justification=justification,
                expires_at=expires_at,
                actor=actor,
            )
        )
    return records


def _apply_suppressions(
    findings: List[Finding],
    suppressions: List[SuppressionRecord],
    evidence: EvidenceWriter,
) -> Tuple[List[Finding], List[Finding]]:
    suppressed = []
    unsuppressed = []
    suppression_map = {record.fingerprint: record for record in suppressions}
    for finding in findings:
        record = suppression_map.get(finding.fingerprint)
        if record and (record.rule_id is None or record.rule_id == finding.rule_id):
            suppressed.append(finding)
            evidence.suppression_applied(
                {
                    "rule_id": finding.rule_id,
                    "fingerprint": finding.fingerprint,
                    "justification": record.justification,
                    "expires_at": record.expires_at,
                    "actor": record.actor,
                }
            )
        else:
            unsuppressed.append(finding)
    return suppressed, unsuppressed


def _matches_policy_rule(
    finding: Finding, severity: str, confidences: List[str]
) -> bool:
    return finding.severity == severity and finding.confidence in confidences


def _apply_policy(
    findings: List[Finding], policy
) -> Tuple[List[Finding], List[Finding]]:
    """Classify findings into blocking (fail_on) vs warnings (warn_on).

    Returns (blocking_findings, warning_findings).
    """
    blocking = []
    warnings = []
    semantic_rules = parse_semantic_rules(policy.semantic) if policy.semantic else []

    for finding in findings:
        semantic_action = _semantic_action(finding, semantic_rules)
        if semantic_action == "allow":
            warnings.append(finding)
            continue
        if semantic_action == "block":
            blocking.append(finding)
            continue
        if semantic_action == "warn":
            warnings.append(finding)
            continue
        is_blocking = False
        for rule in policy.fail_on:
            if _matches_policy_rule(finding, rule.severity, rule.confidence):
                is_blocking = True
                break

        if is_blocking:
            blocking.append(finding)
        else:
            # Check if it matches warn_on rules
            is_warning = False
            for rule in policy.warn_on:
                if _matches_policy_rule(finding, rule.severity, rule.confidence):
                    is_warning = True
                    break
            if is_warning:
                warnings.append(finding)
            # If it doesn't match any policy rules, treat as warning by default
            else:
                warnings.append(finding)

    return blocking, warnings


def _semantic_action(finding: Finding, rules: List[SemanticRule]) -> str | None:
    for rule in rules:
        if rule.selector == "severity":
            if finding.severity != rule.value:
                continue
            if rule.confidences and finding.confidence not in rule.confidences:
                continue
            return rule.action
        if rule.selector == "check":
            if finding.check_id == rule.value:
                return rule.action
            continue
        if rule.selector == "rule":
            if finding.rule_id == rule.value:
                return rule.action
            continue
    return None


def _apply_delta_policy(
    status: str,
    blocking: List[Finding],
    warnings: List[Finding],
    counts: dict[str, int],
    comparison: dict[str, Any] | None,
    delta_policy,
    per_check_delta: dict[str, int],
) -> tuple[str, str]:
    if not delta_policy or not delta_policy.enabled:
        reason = "blocking findings present" if blocking else "no blocking findings"
        return status, reason
    if status != "FAIL" or not blocking:
        return status, "no blocking findings"
    if not comparison or not isinstance(comparison.get("counts_delta"), dict):
        return status, "blocking findings present (no baseline for delta policy)"

    counts_delta = comparison["counts_delta"]
    blocking_delta = counts_delta.get("findings_blocking", 0)
    warning_delta = counts_delta.get("findings_warning", 0)
    unsuppressed_delta = counts_delta.get("findings_unsuppressed", 0)
    if not all(
        isinstance(value, int)
        for value in (blocking_delta, warning_delta, unsuppressed_delta)
    ):
        return status, "blocking findings present (invalid delta data)"

    allowed = (
        blocking_delta <= delta_policy.allow_blocking_increase
        and warning_delta <= delta_policy.allow_warning_increase
        and unsuppressed_delta <= delta_policy.allow_unsuppressed_increase
    )
    if not allowed:
        return status, "blocking findings present (delta policy exceeded)"

    for check_id, limit in delta_policy.per_signal.items():
        delta = per_check_delta.get(check_id, 0)
        if delta > limit:
            return (
                status,
                f"blocking findings present (delta for {check_id} exceeded {limit})",
            )

    reason = (
        "blocking findings within delta policy "
        f"(blocking {blocking_delta:+d}, warnings {warning_delta:+d}, unsuppressed {unsuppressed_delta:+d})"
    )
    return "PASS", reason


def _env_allowlist(config: VibeGateConfig) -> dict[str, str]:
    env = dict(os.environ)
    env.update(config.determinism.env)
    return env


def _plugin_logger() -> logging.Logger:
    return logging.getLogger("vibegate.plugins")


def _is_check_plugin(plugin: object) -> TypeGuard[CheckPlugin]:
    return hasattr(plugin, "run")


def _is_emitter_plugin(plugin: object) -> TypeGuard[EmitterPlugin]:
    return hasattr(plugin, "emit")


def _instantiate_plugin(loaded: LoadedPlugin, logger: logging.Logger) -> object | None:
    plugin = loaded.plugin
    config = loaded.config
    if hasattr(plugin, "run") or hasattr(plugin, "emit"):
        return plugin
    if isinstance(plugin, type):
        try:
            return plugin(config)
        except TypeError:
            try:
                return plugin()
            except TypeError as exc:
                logger.warning(
                    "Failed to initialize plugin '%s': %s",
                    loaded.name,
                    exc,
                )
                return None
    if callable(plugin):
        try:
            return plugin(config)
        except TypeError:
            try:
                return plugin()
            except TypeError:
                return plugin
    return plugin


def _convert_plugin_location(
    location: PluginFindingLocation | None,
) -> FindingLocation | None:
    if not location:
        return None
    return FindingLocation(
        path=location.path,
        line=location.line,
        col=location.col,
        end_line=location.end_line,
        end_col=location.end_col,
    )


def _convert_plugin_finding(finding: PluginFinding) -> Finding:
    return Finding(
        check_id=finding.check_id,
        finding_type=finding.finding_type,
        rule_id=finding.rule_id,
        severity=finding.severity,
        message=finding.message,
        fingerprint=finding.fingerprint,
        confidence=finding.confidence,
        rule_version=finding.rule_version,
        tool=finding.tool,
        remediation_hint=finding.remediation_hint,
        location=_convert_plugin_location(finding.location),
        trigger_explanation=finding.trigger_explanation,
        ast_node_type=finding.ast_node_type,
        in_type_annotation=finding.in_type_annotation,
    )


def _convert_finding_location(
    location: FindingLocation | None,
) -> PluginFindingLocation | None:
    if not location:
        return None
    return PluginFindingLocation(
        path=location.path,
        line=location.line,
        col=location.col,
        end_line=location.end_line,
        end_col=location.end_col,
    )


def _convert_finding_to_plugin(finding: Finding) -> PluginFinding:
    return PluginFinding(
        check_id=finding.check_id,
        finding_type=finding.finding_type,
        rule_id=finding.rule_id,
        severity=finding.severity,
        message=finding.message,
        fingerprint=finding.fingerprint,
        confidence=finding.confidence,
        rule_version=finding.rule_version,
        tool=finding.tool,
        remediation_hint=finding.remediation_hint,
        location=_convert_finding_location(finding.location),
        trigger_explanation=finding.trigger_explanation,
        ast_node_type=finding.ast_node_type,
        in_type_annotation=finding.in_type_annotation,
    )


def _plugin_tool_runner(
    config: VibeGateConfig,
    tool: str,
    args: List[str],
    cwd: Path,
    timeout: int,
    env: dict[str, str],
) -> ToolResult:
    combined_env = _env_allowlist(config)
    combined_env.update(env)
    return run_tool(tool, args, cwd, timeout, combined_env)


def _record_tool_exec(outcome: CheckOutcome, evidence: EvidenceWriter) -> None:
    if not outcome.tool_result:
        return
    artifacts = [
        {"path": str(path), "sha256": sha256_path(path)}
        for path in outcome.tool_result.artifacts
        if path.exists()
    ]
    evidence.tool_exec(
        check_id=outcome.check_id,
        tool=outcome.tool_result.argv[0],
        tool_version=outcome.tool_result.tool_version,
        argv=outcome.tool_result.argv,
        cwd=str(evidence.repo_root),
        duration_ms=outcome.tool_result.duration_ms,
        exit_code=outcome.tool_result.exit_code,
        artifacts=artifacts,
    )


def _tooling_findings(config: VibeGateConfig, repo_root: Path) -> List[Finding]:
    requirements: list[tuple[str, str]] = []
    if config.checks.formatting.enabled:
        requirements.append((config.checks.formatting.id, "ruff"))
    if config.checks.lint.enabled:
        requirements.append((config.checks.lint.id, "ruff"))
    if config.checks.typecheck.enabled:
        requirements.append((config.checks.typecheck.id, "pyright"))
    if config.checks.tests.enabled:
        requirements.append((config.checks.tests.id, "pytest"))
    if config.checks.sast.enabled:
        requirements.append((config.checks.sast.id, "bandit"))
    if config.checks.secrets.enabled:
        requirements.append((config.checks.secrets.id, "gitleaks"))
    vulnerability = config.checks.vulnerability
    if (
        vulnerability.enabled
        and vulnerability.mode != "skip"
        and vulnerability.local_db is not None
        and (repo_root / vulnerability.local_db.path).exists()
    ):
        requirements.append((vulnerability.id, "osv-scanner"))

    findings = []
    for check_id, tool in requirements:
        if shutil.which(tool):
            continue
        findings.append(
            Finding(
                check_id=check_id,
                finding_type="tooling",
                rule_id="MISSING_TOOL",
                severity="high",
                message=(
                    f"Required tool '{tool}' not found for enabled check {check_id}."
                ),
                fingerprint="",
                confidence="high",
                tool=tool,
                remediation_hint=(
                    f"Install {tool} (pipx install {tool} or pip install {tool}) "
                    "or disable the check in vibegate.yaml."
                ),
            )
        )
    return findings


def _run_check_plugins(
    config: VibeGateConfig,
    repo_root: Path,
    workspace_files: Sequence[Path],
    evidence: EvidenceWriter,
) -> List[Finding]:
    logger = _plugin_logger()
    loaded_plugins = load_plugins("vibegate.checks", config.plugins.checks, logger)
    findings: List[Finding] = []
    context = PluginContext(
        repo_root=repo_root,
        config=config,
        workspace_files=workspace_files,
        tool_runner=lambda tool, args, cwd, timeout, env: _plugin_tool_runner(
            config, tool, list(args), cwd, timeout, env
        ),
        logger=logger,
        evidence=evidence,
    )

    for loaded in loaded_plugins:
        plugin = _instantiate_plugin(loaded, logger)
        if plugin is None:
            continue
        if not _is_check_plugin(plugin):
            logger.warning(
                "Plugin '%s' does not implement run() and will be skipped.",
                loaded.name,
            )
            continue
        try:
            plugin_findings = plugin.run(context)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Plugin '%s' failed during run(): %s", loaded.name, exc)
            continue
        if not plugin_findings:
            continue
        for finding in plugin_findings:
            if isinstance(finding, Finding):
                findings.append(finding)
                continue
            try:
                findings.append(_convert_plugin_finding(finding))
            except AttributeError:
                logger.warning(
                    "Plugin '%s' produced an invalid finding and it was ignored.",
                    loaded.name,
                )
    return findings


def _ensure_emitter_artifact_path(
    plugin_name: str, repo_root: Path, path: Path, logger: logging.Logger
) -> Path | None:
    resolved = path if path.is_absolute() else repo_root / path
    if not resolved.exists():
        logger.warning("Emitter '%s' returned missing artifact %s.", plugin_name, path)
        return None
    artifacts_root = repo_root / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    try:
        resolved.relative_to(artifacts_root)
        return resolved
    except ValueError:
        target_name = f"{plugin_name}-{resolved.name}" if resolved.name else plugin_name
        target = artifacts_root / target_name
        if resolved.is_dir():
            logger.warning(
                "Emitter '%s' produced a directory artifact which is unsupported.",
                plugin_name,
            )
            return None
        shutil.copy2(resolved, target)
        return target


def _run_emitter_plugins(
    config: VibeGateConfig,
    repo_root: Path,
    workspace_files: Sequence[Path],
    findings: List[Finding],
    evidence: EvidenceWriter,
) -> List[ArtifactRecord]:
    logger = _plugin_logger()
    loaded_plugins = load_plugins("vibegate.emitters", config.plugins.emitters, logger)
    if not loaded_plugins:
        return []
    plugin_findings = [_convert_finding_to_plugin(finding) for finding in findings]
    context = PluginContext(
        repo_root=repo_root,
        config=config,
        workspace_files=workspace_files,
        tool_runner=lambda tool, args, cwd, timeout, env: _plugin_tool_runner(
            config, tool, list(args), cwd, timeout, env
        ),
        logger=logger,
        evidence=evidence,
    )
    artifacts: List[ArtifactRecord] = []
    for loaded in loaded_plugins:
        plugin = _instantiate_plugin(loaded, logger)
        if plugin is None:
            continue
        if not _is_emitter_plugin(plugin):
            logger.warning(
                "Plugin '%s' does not implement emit() and will be skipped.",
                loaded.name,
            )
            continue
        try:
            output = plugin.emit(context, plugin_findings)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Emitter '%s' failed during emit(): %s", loaded.name, exc)
            continue
        if not output:
            continue
        artifact_path = _ensure_emitter_artifact_path(
            loaded.name, repo_root, Path(output), logger
        )
        if not artifact_path:
            continue
        if not artifact_path.is_file():
            logger.warning(
                "Emitter '%s' produced a non-file artifact and it was ignored.",
                loaded.name,
            )
            continue
        artifacts.append(
            ArtifactRecord(
                name=f"emitter_{loaded.name}",
                path=artifact_path,
                sha256=sha256_path(artifact_path),
            )
        )
    return artifacts


def _run_all_checks(
    config: VibeGateConfig,
    repo_root: Path,
    workspace_files: Sequence[Path],
    evidence: EvidenceWriter,
) -> Tuple[List[Finding], List[dict[str, str]]]:
    env = _env_allowlist(config)
    findings: List[Finding] = _tooling_findings(config, repo_root)
    skipped_checks: List[dict[str, str]] = []
    checks = [
        ("formatting", config.checks.formatting, run_ruff_format),
        ("lint", config.checks.lint, run_ruff_lint),
        ("typecheck", config.checks.typecheck, run_pyright),
        ("tests", config.checks.tests, run_pytest),
        (
            "dependency_hygiene",
            config.checks.dependency_hygiene,
            run_dependency_hygiene,
        ),
        ("sast", config.checks.sast, run_bandit),
        ("secrets", config.checks.secrets, run_gitleaks),
        ("vulnerability", config.checks.vulnerability, run_osv),
        ("config_sanity", config.checks.config_sanity, run_config_sanity),
        ("runtime_smoke", config.checks.runtime_smoke, run_runtime_smoke),
        ("error_handling", config.checks.error_handling, run_error_handling_check),
        (
            "defensive_coding",
            config.checks.defensive_coding,
            run_defensive_programming_check,
        ),
        ("complexity", config.checks.complexity, run_complexity_check),
        ("dead_code", config.checks.dead_code, run_dead_code_check),
        ("coverage", config.checks.coverage, run_coverage_check),
    ]

    for check_key, check, runner in checks:
        evidence.check_start(check.id, check_key, check.enabled)
        if not check.enabled:
            skipped_checks.append({"check_id": check.id, "reason": "disabled"})
            evidence.check_end(
                check.id,
                check_key,
                "SKIPPED",
                0,
                None,
                "disabled",
                0,
            )
            continue
        started = time.monotonic()
        if runner is run_dependency_hygiene:
            outcome = runner(check, repo_root, env, config, workspace_files)
        elif runner is run_config_sanity:
            outcome = runner(check, repo_root, workspace_files)
        elif runner is run_error_handling_check:
            outcome = runner(check, repo_root, workspace_files)
        elif runner is run_defensive_programming_check:
            outcome = runner(check, repo_root, workspace_files)
        elif runner is run_complexity_check:
            outcome = runner(check, repo_root, workspace_files)
        elif runner is run_dead_code_check:
            outcome = runner(check, repo_root, workspace_files, env)
        elif runner is run_coverage_check:
            outcome = runner(repo_root, check)
        else:
            outcome = runner(check, repo_root, env)
        duration_ms = int((time.monotonic() - started) * 1000)
        skipped_reason = None
        if outcome.skipped_reason:
            skipped_reason = f"SKIPPED: {outcome.skipped_reason}"
            skipped_checks.append(
                {
                    "check_id": outcome.check_id,
                    "reason": skipped_reason,
                }
            )
        if outcome.tool_result:
            _record_tool_exec(outcome, evidence)
        findings.extend(outcome.findings)
        if outcome.skipped_reason:
            status = "SKIPPED"
        elif outcome.findings or (
            outcome.tool_result and outcome.tool_result.exit_code != 0
        ):
            status = "FAIL"
        else:
            status = "PASS"
        evidence.check_end(
            check.id,
            check_key,
            status,
            duration_ms,
            outcome.tool_result.exit_code if outcome.tool_result else None,
            skipped_reason,
            len(outcome.findings),
        )

    findings.extend(_run_check_plugins(config, repo_root, workspace_files, evidence))

    return findings, skipped_checks


def _selected_packaging(config: VibeGateConfig) -> dict[str, object]:
    tool = detect_packaging_tool(config)
    lockfiles = config.packaging.lockfiles
    if not lockfiles:
        from vibegate.checks import _default_lockfiles

        lockfiles = _default_lockfiles(tool)
    return {"tool": tool, "lockfiles": lockfiles}


def _toolchain_versions() -> List[dict[str, str]]:
    tools = ["ruff", "pyright", "pytest", "bandit", "gitleaks", "osv-scanner", "uv"]
    versions = []
    for tool in tools:
        if not shutil.which(tool):
            continue
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if result.returncode != 0:
            continue
        output = (result.stdout or result.stderr or "").strip()
        if not output:
            continue
        versions.append({"tool": tool, "version": output.splitlines()[0].strip()})
    return versions


def run_check(
    config: VibeGateConfig, repo_root: Path
) -> tuple[List[ArtifactRecord], str]:
    evidence = EvidenceWriter(config, repo_root)
    evidence.start_run(_selected_packaging(config), _toolchain_versions())

    started = time.monotonic()
    workspace_files = collect_workspace_files(repo_root)
    findings, skipped_checks = _run_all_checks(
        config, repo_root, workspace_files, evidence
    )
    findings = _apply_fingerprints(findings)
    findings = _dedupe_findings(findings)
    findings = sorted(findings, key=_finding_sort_key)

    for finding in findings:
        evidence.finding(finding.event_payload())

    suppressions = _load_suppressions(config, repo_root)
    suppressed, unsuppressed = _apply_suppressions(findings, suppressions, evidence)

    # Apply policy to determine blocking vs warning findings
    blocking, warnings = _apply_policy(unsuppressed, config.policy)

    duration_ms = int((time.monotonic() - started) * 1000)
    counts = {
        "findings_total": len(findings),
        "findings_unsuppressed": len(unsuppressed),
        "findings_blocking": len(blocking),
        "findings_warning": len(warnings),
        "suppressed_total": len(suppressed),
    }
    comparison = _build_comparison(repo_root, counts)
    current_per_check = _counts_by_check(blocking + warnings)
    baseline_per_check = _baseline_check_counts(repo_root, config.policy)
    per_check_delta = {
        check_id: current_per_check.get(check_id, 0)
        - baseline_per_check.get(check_id, 0)
        for check_id in set(current_per_check) | set(baseline_per_check)
    }
    baseline_fingerprints = _baseline_fingerprints(repo_root)
    new_blocking = [
        finding
        for finding in blocking
        if finding.fingerprint not in baseline_fingerprints
    ]
    new_warnings = [
        finding
        for finding in warnings
        if finding.fingerprint not in baseline_fingerprints
    ]
    status = "FAIL" if blocking else "PASS"
    status, reason = _apply_delta_policy(
        status,
        blocking,
        warnings,
        counts,
        comparison,
        config.policy.delta,
        per_check_delta,
    )
    decision = {
        "status": status,
        "reason": reason,
        "blocking_count": len(blocking),
        "warning_count": len(warnings),
        "suppressed_count": len(suppressed),
    }
    report_artifacts = [
        write_report(config.outputs, status, unsuppressed, skipped_checks)
    ]
    if config.outputs.emit_html:
        report_artifacts.append(write_report_html(config.outputs))
    report_artifacts.append(
        write_delta_report(config.outputs, comparison, new_blocking, new_warnings)
    )
    evidence.run_summary(
        status,
        duration_ms,
        counts,
        skipped_checks,
        decision=decision,
        comparison=comparison,
    )

    evidence_sha = (
        sha256_path(config.outputs.evidence_jsonl)
        if config.outputs.evidence_jsonl.exists()
        else ""
    )
    contract_sha = (
        sha256_path(config.contract_path)
        if config.contract_path and config.contract_path.exists()
        else ""
    )
    fixpack_payload = build_fixpack(
        evidence.run_id, unsuppressed, contract_sha, evidence_sha
    )
    fixpack_artifacts = write_fixpack(config.outputs, fixpack_payload, status)
    emitter_artifacts = _run_emitter_plugins(
        config, repo_root, workspace_files, unsuppressed, evidence
    )

    evidence_artifact = ArtifactRecord(
        name="evidence_jsonl",
        path=config.outputs.evidence_jsonl,
        sha256=sha256_path(config.outputs.evidence_jsonl),
    )
    all_artifacts = report_artifacts + fixpack_artifacts + emitter_artifacts
    graph_artifact = write_evidence_graph(
        config.outputs,
        config.outputs.evidence_jsonl,
        all_artifacts + [evidence_artifact],
    )
    all_artifacts.append(graph_artifact)

    # Write state file for seamless tune UX
    _write_state_file(
        repo_root,
        config.outputs.evidence_jsonl,
        [
            artifact.path
            for artifact in all_artifacts
            if artifact.path.suffix in (".md", ".html")
        ],
    )

    return all_artifacts, status


def run_fixpack(
    config: VibeGateConfig, repo_root: Path
) -> tuple[List[ArtifactRecord], str]:
    evidence = EvidenceWriter(config, repo_root)
    evidence.start_run(_selected_packaging(config), _toolchain_versions())

    started = time.monotonic()
    workspace_files = collect_workspace_files(repo_root)
    findings, skipped_checks = _run_all_checks(
        config, repo_root, workspace_files, evidence
    )
    findings = _apply_fingerprints(findings)
    findings = _dedupe_findings(findings)
    findings = sorted(findings, key=_finding_sort_key)

    for finding in findings:
        evidence.finding(finding.event_payload())

    suppressions = _load_suppressions(config, repo_root)
    suppressed, unsuppressed = _apply_suppressions(findings, suppressions, evidence)

    # Apply policy to determine blocking vs warning findings
    blocking, warnings = _apply_policy(unsuppressed, config.policy)

    duration_ms = int((time.monotonic() - started) * 1000)
    counts = {
        "findings_total": len(findings),
        "findings_unsuppressed": len(unsuppressed),
        "findings_blocking": len(blocking),
        "findings_warning": len(warnings),
        "suppressed_total": len(suppressed),
    }
    comparison = _build_comparison(repo_root, counts)
    current_per_check = _counts_by_check(blocking + warnings)
    baseline_per_check = _baseline_check_counts(repo_root, config.policy)
    per_check_delta = {
        check_id: current_per_check.get(check_id, 0)
        - baseline_per_check.get(check_id, 0)
        for check_id in set(current_per_check) | set(baseline_per_check)
    }
    baseline_fingerprints = _baseline_fingerprints(repo_root)
    new_blocking = [
        finding
        for finding in blocking
        if finding.fingerprint not in baseline_fingerprints
    ]
    new_warnings = [
        finding
        for finding in warnings
        if finding.fingerprint not in baseline_fingerprints
    ]
    status = "FAIL" if blocking else "PASS"
    status, reason = _apply_delta_policy(
        status,
        blocking,
        warnings,
        counts,
        comparison,
        config.policy.delta,
        per_check_delta,
    )
    decision = {
        "status": status,
        "reason": reason,
        "blocking_count": len(blocking),
        "warning_count": len(warnings),
        "suppressed_count": len(suppressed),
    }
    evidence.run_summary(
        status,
        duration_ms,
        counts,
        skipped_checks,
        decision=decision,
        comparison=comparison,
    )

    evidence_sha = (
        sha256_path(config.outputs.evidence_jsonl)
        if config.outputs.evidence_jsonl.exists()
        else ""
    )
    contract_sha = (
        sha256_path(config.contract_path)
        if config.contract_path and config.contract_path.exists()
        else ""
    )
    fixpack_payload = build_fixpack(
        evidence.run_id, unsuppressed, contract_sha, evidence_sha
    )
    fixpack_artifacts = write_fixpack(config.outputs, fixpack_payload, status)
    emitter_artifacts = _run_emitter_plugins(
        config, repo_root, workspace_files, unsuppressed, evidence
    )

    report_artifacts = [
        write_report(config.outputs, status, unsuppressed, skipped_checks)
    ]
    if config.outputs.emit_html:
        report_artifacts.append(write_report_html(config.outputs))
    report_artifacts.append(
        write_delta_report(config.outputs, comparison, new_blocking, new_warnings)
    )

    evidence_artifact = ArtifactRecord(
        name="evidence_jsonl",
        path=config.outputs.evidence_jsonl,
        sha256=sha256_path(config.outputs.evidence_jsonl),
    )
    all_artifacts = report_artifacts + fixpack_artifacts + emitter_artifacts
    graph_artifact = write_evidence_graph(
        config.outputs,
        config.outputs.evidence_jsonl,
        all_artifacts + [evidence_artifact],
    )
    all_artifacts.append(graph_artifact)

    # Write state file for seamless tune UX
    _write_state_file(
        repo_root,
        config.outputs.evidence_jsonl,
        [
            artifact.path
            for artifact in all_artifacts
            if artifact.path.suffix in (".md", ".html")
        ],
    )

    return all_artifacts, status
