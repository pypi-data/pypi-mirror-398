from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from vibegate.config import OutputsConfig
from vibegate.findings import Finding


@dataclass(frozen=True)
class ArtifactRecord:
    name: str
    path: Path
    sha256: str


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_report(
    outputs: OutputsConfig,
    status: str,
    findings: List[Finding],
    skipped_checks: List[dict[str, str]],
) -> ArtifactRecord:
    _ensure_parent(outputs.report_markdown)
    lines = ["# VibeGate Report", "", f"Status: {status}", "", "## Findings", ""]
    if not findings:
        lines.append("No findings detected.")
    else:
        for finding in findings:
            location = ""
            if finding.location and finding.location.path:
                location = f" ({finding.location.path})"
            lines.append(
                f"- [{finding.severity}] {finding.check_id} {finding.rule_id}{location}: {finding.message}"
            )
    if skipped_checks:
        lines.extend(["", "## Skipped Checks", ""])
        for skipped in skipped_checks:
            check_id = skipped.get("check_id", "unknown")
            reason = skipped.get("reason", "unknown")
            lines.append(f"- {check_id}: {reason}")
    outputs.report_markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ArtifactRecord(
        name="report_markdown",
        path=outputs.report_markdown,
        sha256=sha256_path(outputs.report_markdown),
    )


def write_report_html(outputs: OutputsConfig) -> ArtifactRecord:
    _ensure_parent(outputs.report_html)
    markdown = outputs.report_markdown.read_text(encoding="utf-8")
    html = "<pre>" + markdown.replace("&", "&amp;").replace("<", "&lt;") + "</pre>\n"
    outputs.report_html.write_text(html, encoding="utf-8")
    return ArtifactRecord(
        name="report_html",
        path=outputs.report_html,
        sha256=sha256_path(outputs.report_html),
    )


def write_delta_report(
    outputs: OutputsConfig,
    comparison: dict[str, Any] | None,
    new_blocking: List[Finding],
    new_warnings: List[Finding],
) -> ArtifactRecord:
    _ensure_parent(outputs.delta_report_markdown)
    lines = ["# VibeGate Delta Report", ""]
    if not comparison:
        lines.append("No baseline available. Run again to generate deltas.")
    else:
        counts_delta = comparison.get("counts_delta", {})
        lines.append("## Counts delta")
        lines.append("")
        for key in (
            "findings_blocking",
            "findings_warning",
            "findings_unsuppressed",
            "suppressed_total",
        ):
            if key in counts_delta:
                value = counts_delta.get(key, 0)
                prefix = "+" if isinstance(value, int) and value > 0 else ""
                label = key.replace("findings_", "").replace("_", " ")
                lines.append(f"- {label}: {prefix}{value}")
        lines.append("")
        lines.append("## New blocking signals")
        lines.append("")
        if not new_blocking:
            lines.append("None.")
        else:
            for finding in new_blocking:
                location = ""
                if finding.location and finding.location.path:
                    location = f" ({finding.location.path})"
                lines.append(
                    f"- [{finding.severity}] {finding.check_id} {finding.rule_id}{location}: {finding.message}"
                )
        lines.append("")
        lines.append("## New warning signals")
        lines.append("")
        if not new_warnings:
            lines.append("None.")
        else:
            for finding in new_warnings[:20]:
                location = ""
                if finding.location and finding.location.path:
                    location = f" ({finding.location.path})"
                lines.append(
                    f"- [{finding.severity}] {finding.check_id} {finding.rule_id}{location}: {finding.message}"
                )
            if len(new_warnings) > 20:
                lines.append(f"- ... {len(new_warnings) - 20} more")
    outputs.delta_report_markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ArtifactRecord(
        name="delta_report_markdown",
        path=outputs.delta_report_markdown,
        sha256=sha256_path(outputs.delta_report_markdown),
    )


def _load_evidence_events(path: Path) -> List[dict[str, Any]]:
    if not path.exists():
        return []
    events: List[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _evidence_graph(
    evidence_path: Path, artifacts: Iterable[ArtifactRecord]
) -> dict[str, Any]:
    events = _load_evidence_events(evidence_path)
    run_id = ""
    for event in events:
        if isinstance(event, dict) and event.get("run_id"):
            run_id = str(event.get("run_id"))
            break

    run_node_id = f"run:{run_id}" if run_id else "run:unknown"
    nodes: List[dict[str, Any]] = []
    edges: List[dict[str, str]] = []

    run_start = next(
        (event for event in events if event.get("event_type") == "run_start"), None
    )
    run_summary = next(
        (event for event in events if event.get("event_type") == "run_summary"), None
    )

    run_attributes: Dict[str, Any] = {"run_id": run_id}
    if run_start:
        run_attributes.update(
            {
                "started_at": run_start.get("ts"),
                "vibegate": run_start.get("vibegate", {}),
                "selected_packaging": run_start.get("selected_packaging", {}),
                "toolchain": run_start.get("toolchain", []),
                "repo": run_start.get("repo", {}),
                "contract": run_start.get("contract", {}),
            }
        )
    nodes.append({"id": run_node_id, "type": "run", "attributes": run_attributes})

    if run_summary:
        decision_node_id = f"decision:{run_id or 'unknown'}"
        nodes.append(
            {
                "id": decision_node_id,
                "type": "decision",
                "attributes": {
                    "result": run_summary.get("result"),
                    "duration_ms": run_summary.get("duration_ms"),
                    "counts": run_summary.get("counts", {}),
                    "decision": run_summary.get("decision", {}),
                    "comparison": run_summary.get("comparison", {}),
                },
            }
        )
        edges.append({"from": run_node_id, "to": decision_node_id, "type": "decides"})

    check_nodes: Dict[str, dict[str, Any]] = {}
    check_id_to_key: Dict[str, str] = {}

    def _ensure_check_node(check_key: str, check_id: str | None) -> str:
        key = check_key or check_id or "unknown"
        if key not in check_nodes:
            check_nodes[key] = {
                "id": f"signal:{key}",
                "type": "signal",
                "attributes": {"check_key": key, "check_id": check_id or "unknown"},
            }
        return key

    for event in events:
        if event.get("event_type") == "check_start":
            check_key = str(event.get("check_key", "unknown"))
            check_id = str(event.get("check_id", "unknown"))
            check_id_to_key[check_id] = check_key
            _ensure_check_node(check_key, check_id)
            check_nodes[check_key]["attributes"]["enabled"] = event.get("enabled")
        if event.get("event_type") == "check_end":
            check_key = str(event.get("check_key", "unknown"))
            check_id = str(event.get("check_id", "unknown"))
            check_id_to_key[check_id] = check_key
            _ensure_check_node(check_key, check_id)
            check_nodes[check_key]["attributes"].update(
                {
                    "status": event.get("status"),
                    "duration_ms": event.get("duration_ms"),
                    "exit_code": event.get("exit_code"),
                    "skipped_reason": event.get("skipped_reason"),
                    "findings_count": event.get("findings_count"),
                }
            )

    for check in check_nodes.values():
        nodes.append(check)
        edges.append({"from": run_node_id, "to": check["id"], "type": "signal"})

    tool_exec_nodes: List[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") != "tool_exec":
            continue
        seq = event.get("seq")
        node_id = f"tool_exec:{seq}" if seq else f"tool_exec:{len(tool_exec_nodes)}"
        tool_exec_nodes.append(
            {
                "id": node_id,
                "type": "tool_exec",
                "attributes": {
                    "check_id": event.get("check_id"),
                    "tool": event.get("tool"),
                    "tool_version": event.get("tool_version"),
                    "command": event.get("command", {}),
                    "duration_ms": event.get("duration_ms"),
                    "exit_code": event.get("exit_code"),
                    "artifacts": event.get("artifacts", []),
                },
            }
        )
        check_id = str(event.get("check_id", "unknown"))
        check_key = check_id_to_key.get(check_id, check_id)
        check_key = _ensure_check_node(check_key, check_id)
        edges.append(
            {
                "from": f"signal:{check_key}",
                "to": node_id,
                "type": "executes",
            }
        )

    nodes.extend(tool_exec_nodes)

    finding_nodes: Dict[str, dict[str, Any]] = {}
    for event in events:
        if event.get("event_type") != "finding":
            continue
        fingerprint = str(event.get("fingerprint", ""))
        if not fingerprint:
            continue
        node_id = f"finding:{fingerprint}"
        if node_id not in finding_nodes:
            finding_nodes[node_id] = {
                "id": node_id,
                "type": "finding",
                "attributes": {
                    "check_id": event.get("check_id"),
                    "rule_id": event.get("rule_id"),
                    "severity": event.get("severity"),
                    "confidence": event.get("confidence"),
                    "message": event.get("message"),
                    "location": event.get("location", {}),
                    "fingerprint": fingerprint,
                },
            }
        check_id = str(event.get("check_id", "unknown"))
        check_key = check_id_to_key.get(check_id, check_id)
        check_key = _ensure_check_node(check_key, check_id)
        edges.append(
            {
                "from": f"signal:{check_key}",
                "to": node_id,
                "type": "emits",
            }
        )

    nodes.extend(finding_nodes.values())

    for event in events:
        if event.get("event_type") != "suppression_applied":
            continue
        seq = event.get("seq")
        node_id = (
            f"suppression:{seq}"
            if seq
            else f"suppression:{event.get('fingerprint', '')}"
        )
        nodes.append(
            {
                "id": node_id,
                "type": "suppression",
                "attributes": {
                    "rule_id": event.get("rule_id"),
                    "fingerprint": event.get("fingerprint"),
                    "justification": event.get("justification"),
                    "actor": event.get("actor"),
                    "applied_at": event.get("applied_at"),
                    "expires_at": event.get("expires_at"),
                },
            }
        )
        fingerprint = str(event.get("fingerprint", ""))
        if fingerprint:
            finding_id = f"finding:{fingerprint}"
            edges.append({"from": finding_id, "to": node_id, "type": "suppressed_by"})

    for artifact in artifacts:
        node_id = f"artifact:{artifact.name}"
        nodes.append(
            {
                "id": node_id,
                "type": "artifact",
                "attributes": {
                    "name": artifact.name,
                    "path": str(artifact.path),
                    "sha256": artifact.sha256,
                },
            }
        )
        edges.append({"from": run_node_id, "to": node_id, "type": "produces"})

    unique_nodes: Dict[str, dict[str, Any]] = {}
    for node in nodes:
        node_id = node.get("id")
        if not node_id:
            continue
        unique_nodes[str(node_id)] = node
    nodes_sorted = [unique_nodes[node_id] for node_id in sorted(unique_nodes)]
    edge_keys = {
        (edge.get("from", ""), edge.get("to", ""), edge.get("type", ""))
        for edge in edges
    }
    edges_sorted = [
        {"from": from_id, "to": to_id, "type": edge_type}
        for from_id, to_id, edge_type in sorted(edge_keys)
    ]

    return {
        "schema_version": "v1",
        "run_id": run_id,
        "nodes": nodes_sorted,
        "edges": edges_sorted,
    }


def write_evidence_graph(
    outputs: OutputsConfig, evidence_path: Path, artifacts: Iterable[ArtifactRecord]
) -> ArtifactRecord:
    _ensure_parent(outputs.evidence_graph_json)
    graph = _evidence_graph(evidence_path, artifacts)
    outputs.evidence_graph_json.write_text(
        json.dumps(graph, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return ArtifactRecord(
        name="evidence_graph_json",
        path=outputs.evidence_graph_json,
        sha256=sha256_path(outputs.evidence_graph_json),
    )


def _severity_rank(severity: str) -> int:
    order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
    return order.get(severity, 0)


def _finding_path(finding: Finding) -> str:
    if finding.location and finding.location.path:
        return finding.location.path
    return ""


def _ordering_key(finding: Finding) -> tuple:
    return (
        -_severity_rank(finding.severity),
        _finding_path(finding),
        finding.rule_id,
        finding.fingerprint,
    )


TASK_TYPE_ORDER = [
    "dependency_fix",
    "vulnerability_fix",
    "secret_removal",
    "security_fix",
    "type_fix",
    "lint_fix",
    "formatting_fix",
    "test_fix",
    "config_fix",
    "runtime_fix",
]

FINDING_TO_TASK_TYPE = {
    "dependency_hygiene": "dependency_fix",
    "vulnerability": "vulnerability_fix",
    "secrets": "secret_removal",
    "sast": "security_fix",
    "typecheck": "type_fix",
    "lint": "lint_fix",
    "formatting": "formatting_fix",
    "tests": "test_fix",
    "config_sanity": "config_fix",
    "runtime_smoke": "runtime_fix",
}

GROUP_TITLES = {
    "dependency_fix": "Dependency hygiene fixes",
    "vulnerability_fix": "Vulnerability fixes",
    "secret_removal": "Secret removals",
    "security_fix": "Security fixes",
    "type_fix": "Typecheck fixes",
    "lint_fix": "Lint fixes",
    "formatting_fix": "Formatting fixes",
    "test_fix": "Test fixes",
    "config_fix": "Config sanity fixes",
    "runtime_fix": "Runtime smoke fixes",
}


def _task_title(finding: Finding, task_type: str) -> str:
    base = finding.message
    if len(base) > 80:
        base = base[:77] + "..."
    return f"{task_type.replace('_', ' ').title()}: {base}"


def _verification_commands(finding: Finding) -> List[str]:
    commands = ["vibegate check"]
    if finding.finding_type == "lint":
        commands.append("ruff check --output-format json .")
    elif finding.finding_type == "formatting":
        commands.append("ruff format --check .")
    elif finding.finding_type == "typecheck":
        commands.append("pyright --outputjson .")
    elif finding.finding_type == "tests":
        commands.append("pytest -q")
    return commands


def build_fixpack(
    run_id: str,
    findings: List[Finding],
    contract_sha: str,
    evidence_sha: str,
) -> dict[str, Any]:
    grouped: dict[str, List[Finding]] = {task_type: [] for task_type in TASK_TYPE_ORDER}
    for finding in findings:
        task_type = FINDING_TO_TASK_TYPE.get(finding.finding_type)
        if task_type:
            grouped[task_type].append(finding)

    groups: List[dict[str, Any]] = []
    task_order = 1
    group_order = 1

    for task_type in TASK_TYPE_ORDER:
        items = sorted(grouped.get(task_type, []), key=_ordering_key)
        if not items:
            continue
        tasks: List[dict[str, Any]] = []
        for finding in items:
            file_targets = []
            if finding.location and finding.location.path:
                file_targets.append(finding.location.path)
            tasks.append(
                {
                    "id": f"{task_type}-{task_order}",
                    "type": task_type,
                    "order": task_order,
                    "title": _task_title(finding, task_type),
                    "description": finding.message,
                    "file_targets": file_targets,
                    "references": [finding.fingerprint],
                    "depends_on": [],
                    "acceptance_criteria": [
                        "The underlying issue is resolved without regressions.",
                        "Relevant checks report no remaining findings.",
                    ],
                    "verification_commands": _verification_commands(finding),
                }
            )
            task_order += 1
        groups.append(
            {
                "id": f"{task_type}_group",
                "title": GROUP_TITLES.get(
                    task_type, task_type.replace("_", " ").title()
                ),
                "order": group_order,
                "tasks": tasks,
            }
        )
        group_order += 1

    return {
        "schema_version": "v1alpha1",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {"contract_sha256": contract_sha, "evidence_sha256": evidence_sha},
        "groups": groups,
    }


def write_fixpack(
    outputs: OutputsConfig, fixpack: dict[str, Any], result: str
) -> List[ArtifactRecord]:
    records: List[ArtifactRecord] = []
    _ensure_parent(outputs.fixpack_json)
    outputs.fixpack_json.write_text(
        json.dumps(fixpack, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    records.append(
        ArtifactRecord(
            "fixpack_json", outputs.fixpack_json, sha256_path(outputs.fixpack_json)
        )
    )

    _ensure_parent(outputs.fixpack_md)
    outputs.fixpack_md.write_text(_fixpack_markdown(fixpack, result), encoding="utf-8")
    records.append(
        ArtifactRecord(
            "fixpack_md", outputs.fixpack_md, sha256_path(outputs.fixpack_md)
        )
    )

    if outputs.emit_fixpack_yaml:
        _ensure_parent(outputs.fixpack_yaml)
        outputs.fixpack_yaml.write_text(
            yaml.safe_dump(fixpack, sort_keys=False), encoding="utf-8"
        )
        records.append(
            ArtifactRecord(
                "fixpack_yaml", outputs.fixpack_yaml, sha256_path(outputs.fixpack_yaml)
            )
        )

    return records


def _fixpack_markdown(fixpack: dict[str, Any], result: str) -> str:
    run_id = fixpack.get("run_id", "unknown")
    groups = fixpack.get("groups", [])
    total_tasks = sum(len(group.get("tasks", [])) for group in groups)
    lines = [
        f"Fix Pack for run {run_id}",
        "",
        "Summary",
        "",
        f"PASS/FAIL: {result}",
        f"Task count: {total_tasks}",
        "Ordering: Apply tasks in order.",
        "",
    ]
    for group in sorted(groups, key=lambda g: g.get("order", 0)):
        lines.append(f"## {group.get('title', 'Untitled')}")
        tasks = group.get("tasks", [])
        for task in sorted(tasks, key=lambda t: t.get("order", 0)):
            lines.append("")
            lines.append(
                f"[{task.get('order', 0)}] {task.get('title', 'Untitled')} ({task.get('type', 'unknown')})"
            )
            lines.append("Files:")
            file_targets = task.get("file_targets", [])
            if file_targets:
                for path in file_targets:
                    lines.append(f"- {path}")
            else:
                lines.append("- (none)")
            lines.append("Why:")
            lines.append(task.get("description", ""))
            lines.append("Steps:")
            lines.append("- Address the issue described above.")
            lines.append("Acceptance criteria:")
            for item in task.get("acceptance_criteria", []):
                lines.append(f"- {item}")
            lines.append("Verification commands:")
            for cmd in task.get("verification_commands", []):
                lines.append(f"- {cmd}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"
