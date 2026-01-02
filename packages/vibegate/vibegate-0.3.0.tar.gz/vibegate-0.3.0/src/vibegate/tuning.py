"""Offline deterministic tuning pipeline for evolving checks based on labeled findings."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


@dataclass(frozen=True)
class Label:
    """A label for a finding from labels.yaml."""

    fingerprint: str
    rule_id: str
    label: str  # "false_positive", "true_positive", "acceptable_risk"
    reason: str
    note: str
    created_at: str


@dataclass(frozen=True)
class LabeledFinding:
    """A finding joined with its label."""

    fingerprint: str
    check_id: str
    rule_id: str
    severity: str
    confidence: str
    message: str
    file_path: str | None
    line: int | None
    label: str
    reason: str
    note: str
    trigger_explanation: str | None
    ast_node_type: str | None
    in_type_annotation: bool | None


@dataclass(frozen=True)
class FindingCluster:
    """A cluster of similar findings for analysis."""

    cluster_id: str
    rule_id: str
    trigger_signature: str
    count: int
    examples: List[LabeledFinding]
    top_directories: List[Tuple[str, int]]  # (dir, count)
    action_hints: List[str]


@dataclass(frozen=True)
class TuningMetrics:
    """Summary metrics for the tuning analysis."""

    total_findings: int
    labeled_count: int
    unlabeled_count: int
    false_positive_count: int
    true_positive_count: int
    acceptable_risk_count: int
    rules_with_fps: List[Tuple[str, int]]  # (rule_id, fp_count) sorted by count desc


def load_evidence_findings(evidence_path: Path) -> List[Dict[str, Any]]:
    """Load findings from evidence JSONL file."""
    findings = []
    if not evidence_path.exists():
        return findings

    with evidence_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                if event.get("event_type") == "finding":
                    findings.append(event)
            except json.JSONDecodeError:
                continue

    return findings


def load_labels(labels_path: Path) -> Dict[str, Label]:
    """Load labels from labels.yaml and return a map by fingerprint."""
    if not labels_path.exists():
        return {}

    with labels_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    labels_list = data.get("labels", [])
    if not isinstance(labels_list, list):
        return {}

    labels_map = {}
    for entry in labels_list:
        if not isinstance(entry, dict):
            continue
        fingerprint = entry.get("fingerprint", "")
        if not fingerprint:
            continue
        labels_map[fingerprint] = Label(
            fingerprint=fingerprint,
            rule_id=entry.get("rule_id", ""),
            label=entry.get("label", ""),
            reason=entry.get("reason", ""),
            note=entry.get("note", ""),
            created_at=entry.get("created_at", ""),
        )

    return labels_map


def join_findings_with_labels(
    findings: List[Dict[str, Any]], labels: Dict[str, Label]
) -> Tuple[List[LabeledFinding], List[Dict[str, Any]]]:
    """Join findings with labels by fingerprint.

    Returns (labeled_findings, unlabeled_findings).
    """
    labeled = []
    unlabeled = []

    for finding in findings:
        fingerprint = finding.get("fingerprint", "")
        label = labels.get(fingerprint)

        if label:
            location = finding.get("location", {}) or {}
            labeled.append(
                LabeledFinding(
                    fingerprint=fingerprint,
                    check_id=finding.get("check_id", ""),
                    rule_id=finding.get("rule_id", ""),
                    severity=finding.get("severity", ""),
                    confidence=finding.get("confidence", ""),
                    message=finding.get("message", ""),
                    file_path=location.get("path"),
                    line=location.get("line"),
                    label=label.label,
                    reason=label.reason,
                    note=label.note,
                    trigger_explanation=finding.get("trigger_explanation"),
                    ast_node_type=finding.get("ast_node_type"),
                    in_type_annotation=finding.get("in_type_annotation"),
                )
            )
        else:
            unlabeled.append(finding)

    return labeled, unlabeled


def compute_metrics(
    labeled: List[LabeledFinding], unlabeled: List[Dict[str, Any]]
) -> TuningMetrics:
    """Compute summary metrics for the tuning analysis."""
    total = len(labeled) + len(unlabeled)
    fp_count = sum(1 for f in labeled if f.label == "false_positive")
    tp_count = sum(1 for f in labeled if f.label == "true_positive")
    acceptable_count = sum(1 for f in labeled if f.label == "acceptable_risk")

    # Count FPs by rule
    fp_by_rule: Dict[str, int] = defaultdict(int)
    for finding in labeled:
        if finding.label == "false_positive":
            fp_by_rule[finding.rule_id] += 1

    # Sort rules by FP count descending, then by rule_id for stability
    rules_with_fps = sorted(fp_by_rule.items(), key=lambda x: (-x[1], x[0]))

    return TuningMetrics(
        total_findings=total,
        labeled_count=len(labeled),
        unlabeled_count=len(unlabeled),
        false_positive_count=fp_count,
        true_positive_count=tp_count,
        acceptable_risk_count=acceptable_count,
        rules_with_fps=rules_with_fps,
    )


def _normalize_message(message: str) -> str:
    """Normalize a finding message for clustering.

    Strips file paths, line numbers, and collapses whitespace.
    """
    # Remove file paths (e.g., "/path/to/file.py:123")
    normalized = re.sub(r"\S+\.py:\d+", "<FILE>", message)
    # Remove line/column references
    normalized = re.sub(r"\b(line|col)\s+\d+\b", "<LOC>", normalized)
    # Collapse whitespace
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _compute_trigger_signature(finding: LabeledFinding) -> str:
    """Compute a deterministic trigger signature for clustering."""
    # Prefer trigger_explanation if present
    if finding.trigger_explanation:
        return finding.trigger_explanation

    # Next prefer ast_node_type if present
    if finding.ast_node_type:
        return finding.ast_node_type

    # Fall back to normalized message
    normalized = _normalize_message(finding.message)
    if normalized:
        return normalized

    # Last resort: hash of original message
    return hashlib.sha256(finding.message.encode("utf-8")).hexdigest()[:16]


def cluster_findings(
    findings: List[LabeledFinding], include_acceptable: bool = False
) -> List[FindingCluster]:
    """Cluster findings by rule_id and trigger signature.

    Only clusters false_positive (and optionally acceptable_risk) findings.
    """
    # Filter to FPs (and acceptable if requested)
    target_labels = {"false_positive"}
    if include_acceptable:
        target_labels.add("acceptable_risk")

    findings_to_cluster = [f for f in findings if f.label in target_labels]

    # Group by (rule_id, trigger_signature)
    clusters_map: Dict[Tuple[str, str], List[LabeledFinding]] = defaultdict(list)
    for finding in findings_to_cluster:
        trigger_sig = _compute_trigger_signature(finding)
        key = (finding.rule_id, trigger_sig)
        clusters_map[key].append(finding)

    # Convert to FindingCluster objects
    clusters = []
    for (rule_id, trigger_sig), cluster_findings in clusters_map.items():
        # Compute cluster_id as stable hash
        cluster_key = f"{rule_id}:{trigger_sig}"
        cluster_id = hashlib.sha256(cluster_key.encode("utf-8")).hexdigest()[:16]

        # Count directory occurrences
        dir_counts: Dict[str, int] = defaultdict(int)
        for finding in cluster_findings:
            if finding.file_path:
                # Extract directory bucket (first path component)
                parts = Path(finding.file_path).parts
                if parts:
                    dir_bucket = parts[0]
                    dir_counts[dir_bucket] += 1

        # Sort directories by count desc, then name for stability
        top_dirs = sorted(dir_counts.items(), key=lambda x: (-x[1], x[0]))[:5]

        # Generate action hints
        hints = _generate_action_hints(cluster_findings, top_dirs)

        # Sort examples by file path, line, then fingerprint for determinism
        sorted_examples = sorted(
            cluster_findings,
            key=lambda f: (
                f.file_path or "",
                f.line or 0,
                f.fingerprint,
            ),
        )

        clusters.append(
            FindingCluster(
                cluster_id=cluster_id,
                rule_id=rule_id,
                trigger_signature=trigger_sig,
                count=len(cluster_findings),
                examples=sorted_examples,
                top_directories=top_dirs,
                action_hints=hints,
            )
        )

    # Sort clusters by count desc, then cluster_id for determinism
    clusters.sort(key=lambda c: (-c.count, c.cluster_id))

    return clusters


def _generate_action_hints(
    findings: List[LabeledFinding], top_dirs: List[Tuple[str, int]]
) -> List[str]:
    """Generate deterministic action hints based on cluster patterns."""
    hints = []

    # Check if most findings are in tests/
    if top_dirs:
        top_dir, top_count = top_dirs[0]
        total = len(findings)
        if total > 0:
            percentage = top_count / total
            if top_dir in ("tests", "test") and percentage > 0.8:
                hints.append(
                    "Consider ignore tests/ directory or downgrade severity/confidence for test code"
                )

    # Check for type annotation context
    type_annotation_count = sum(
        1 for f in findings if f.in_type_annotation or _looks_like_typing(f.message)
    )
    total = len(findings)
    if total > 0:
        percentage = type_annotation_count / total
        if percentage > 0.5:
            hints.append(
                "Consider guard: type-annotation context (many findings in type annotations)"
            )

    # Check for file glob patterns
    if top_dirs and len(top_dirs) == 1:
        top_dir, _ = top_dirs[0]
        hints.append(
            f"Consider file-glob suppression for {top_dir}/ or narrow AST predicate"
        )

    # Check for visitor/adapter patterns
    if any(_looks_like_visitor(f.message) for f in findings):
        hints.append(
            "Consider allow broad-except in visitor/adapter layers (NodeVisitor/NodeTransformer pattern detected)"
        )

    return hints


def _looks_like_typing(message: str) -> bool:
    """Check if message suggests type annotation context."""
    typing_indicators = [
        "List[",
        "Dict[",
        "dict[",
        "list[",
        "typing.",
        "Optional[",
        "Union[",
        "Tuple[",
        "tuple[",
    ]
    return any(indicator in message for indicator in typing_indicators)


def _looks_like_visitor(message: str) -> bool:
    """Check if message suggests AST visitor/adapter pattern."""
    visitor_indicators = [
        "NodeVisitor",
        "NodeTransformer",
        "ast.walk",
        "visit_",
        "generic_visit",
    ]
    return any(indicator in message for indicator in visitor_indicators)


def extract_code_snippet(
    file_path: Path, line: int, context_lines: int = 8
) -> str | None:
    """Extract a code snippet from a file around a specific line.

    Args:
        file_path: Path to the source file
        line: Line number (1-indexed)
        context_lines: Number of lines before/after to include

    Returns:
        Code snippet as a string, or None if file doesn't exist
    """
    if not file_path.exists():
        return None

    try:
        with file_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        if not lines or line < 1 or line > len(lines):
            return None

        # Calculate range (1-indexed line to 0-indexed)
        start = max(0, line - 1 - context_lines)
        end = min(len(lines), line + context_lines)

        snippet_lines = []
        for i in range(start, end):
            # Mark the target line
            marker = "→" if i == line - 1 else " "
            snippet_lines.append(f"{i + 1:4d}{marker} {lines[i].rstrip()}")

        return "\n".join(snippet_lines)
    except (OSError, UnicodeDecodeError):
        return None


def write_tuning_pack(
    output_dir: Path,
    repo_root: Path,
    metrics: TuningMetrics,
    clusters: List[FindingCluster],
    max_examples: int = 5,
) -> Tuple[Path, Path, Path]:
    """Write tuning pack artifacts (report, clusters JSON, examples dir).

    Returns (report_path, clusters_json_path, examples_dir_path).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write markdown report
    report_path = output_dir / "tuning_report.md"
    report_path.write_text(
        _generate_markdown_report(metrics, clusters), encoding="utf-8"
    )

    # Write clusters JSON
    clusters_json_path = output_dir / "tuning_clusters.json"
    clusters_json_path.write_text(
        _generate_clusters_json(clusters, max_examples), encoding="utf-8"
    )

    # Write examples directory
    examples_dir = output_dir / "tuning_examples"
    examples_dir.mkdir(parents=True, exist_ok=True)
    for cluster in clusters:
        _write_cluster_examples(cluster, examples_dir, repo_root, max_examples)

    return report_path, clusters_json_path, examples_dir


def _generate_markdown_report(
    metrics: TuningMetrics, clusters: List[FindingCluster]
) -> str:
    """Generate a human-friendly markdown tuning report."""
    lines = [
        "# VibeGate Tuning Report",
        "",
        "## Summary Metrics",
        "",
        f"- **Total Findings**: {metrics.total_findings}",
        f"- **Labeled**: {metrics.labeled_count} ({_percent(metrics.labeled_count, metrics.total_findings)})",
        f"- **Unlabeled**: {metrics.unlabeled_count} ({_percent(metrics.unlabeled_count, metrics.total_findings)})",
        "",
        "### Label Breakdown",
        "",
        f"- **False Positives**: {metrics.false_positive_count}",
        f"- **True Positives**: {metrics.true_positive_count}",
        f"- **Acceptable Risk**: {metrics.acceptable_risk_count}",
        "",
    ]

    if metrics.rules_with_fps:
        lines.extend(
            [
                "### Rules with Most False Positives",
                "",
                "| Rule ID | FP Count |",
                "|---------|----------|",
            ]
        )
        for rule_id, count in metrics.rules_with_fps[:10]:
            lines.append(f"| {rule_id} | {count} |")
        lines.append("")

    if clusters:
        lines.extend(
            [
                "## False Positive Clusters",
                "",
                f"Found {len(clusters)} clusters of similar false positives.",
                "",
            ]
        )

        for cluster in clusters[:20]:  # Limit to top 20 clusters
            lines.extend(
                [
                    f"### Cluster: {cluster.cluster_id}",
                    "",
                    f"- **Rule**: `{cluster.rule_id}`",
                    f"- **Count**: {cluster.count} findings",
                    f"- **Trigger Signature**: {cluster.trigger_signature}",
                    "",
                ]
            )

            if cluster.top_directories:
                lines.append("**Top Directories:**")
                for dir_name, count in cluster.top_directories:
                    lines.append(f"- `{dir_name}/`: {count} findings")
                lines.append("")

            if cluster.action_hints:
                lines.append("**Action Hints:**")
                for hint in cluster.action_hints:
                    lines.append(f"- {hint}")
                lines.append("")

            lines.append(f"See `tuning_examples/{cluster.cluster_id}.md` for examples.")
            lines.append("")
    else:
        lines.extend(
            [
                "## No Clusters Found",
                "",
                "No false positive clusters were identified. This could mean:",
                "- No findings are labeled as false positives",
                "- All checks are performing well",
                "- More labeling is needed to identify patterns",
                "",
            ]
        )

    lines.extend(
        [
            "## Next Steps",
            "",
            "1. Review cluster action hints to identify rule refinement opportunities",
            "2. Examine example code snippets in `tuning_examples/` directory",
            "3. Consider:",
            "   - Adjusting rule severity/confidence levels",
            "   - Adding guards for specific AST contexts (e.g., type annotations)",
            "   - Creating targeted suppressions for known patterns",
            "   - Refining rule predicates to reduce false positives",
            "",
            "Note: This report is for tuning only. To suppress findings in CI/CD, use `.vibegate/suppressions.yaml`.",
            "",
        ]
    )

    return "\n".join(lines)


def _generate_clusters_json(clusters: List[FindingCluster], max_examples: int) -> str:
    """Generate machine-readable clusters JSON."""
    clusters_data = []

    for cluster in clusters:
        examples_data = []
        for finding in cluster.examples[:max_examples]:
            examples_data.append(
                {
                    "fingerprint": finding.fingerprint,
                    "file_path": finding.file_path,
                    "line": finding.line,
                    "severity": finding.severity,
                    "confidence": finding.confidence,
                    "message": finding.message,
                    "reason": finding.reason,
                    "note": finding.note,
                }
            )

        clusters_data.append(
            {
                "cluster_id": cluster.cluster_id,
                "rule_id": cluster.rule_id,
                "trigger_signature": cluster.trigger_signature,
                "count": cluster.count,
                "top_directories": [
                    {"directory": d, "count": c} for d, c in cluster.top_directories
                ],
                "action_hints": cluster.action_hints,
                "examples": examples_data,
            }
        )

    return json.dumps({"clusters": clusters_data}, indent=2, sort_keys=True)


def _write_cluster_examples(
    cluster: FindingCluster,
    examples_dir: Path,
    repo_root: Path,
    max_examples: int,
) -> None:
    """Write examples for a single cluster to a markdown file."""
    example_file = examples_dir / f"{cluster.cluster_id}.md"

    lines = [
        f"# Cluster: {cluster.cluster_id}",
        "",
        f"**Rule**: `{cluster.rule_id}`",
        f"**Count**: {cluster.count} findings",
        f"**Trigger Signature**: {cluster.trigger_signature}",
        "",
    ]

    if cluster.action_hints:
        lines.append("## Action Hints")
        lines.append("")
        for hint in cluster.action_hints:
            lines.append(f"- {hint}")
        lines.append("")

    lines.extend(["## Examples", ""])

    for i, finding in enumerate(cluster.examples[:max_examples], 1):
        lines.extend(
            [
                f"### Example {i}",
                "",
                f"- **File**: `{finding.file_path}`",
                f"- **Line**: {finding.line}",
                f"- **Severity**: {finding.severity}",
                f"- **Confidence**: {finding.confidence}",
                f"- **Reason**: {finding.reason}",
                "",
                f"**Message**: {finding.message}",
                "",
            ]
        )

        if finding.note:
            lines.extend([f"**Note**: {finding.note}", ""])

        # Extract code snippet
        if finding.file_path and finding.line:
            file_path = repo_root / finding.file_path
            snippet = extract_code_snippet(file_path, finding.line)
            if snippet:
                lines.extend(["**Code Snippet**:", "", "```python", snippet, "```", ""])
            else:
                lines.extend(["**Code Snippet**: (file not found or unreadable)", ""])

        lines.append("---")
        lines.append("")

    example_file.write_text("\n".join(lines), encoding="utf-8")


def _percent(part: int, total: int) -> str:
    """Format percentage string."""
    if total == 0:
        return "0%"
    else:
        return f"{100 * part / total:.1f}%"
