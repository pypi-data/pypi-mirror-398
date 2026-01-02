"""Deterministic proposal pack generator for evolving checks based on tuning clusters."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class Proposal:
    """A proposal for addressing a cluster of findings."""

    proposal_id: str
    cluster_id: str
    rule_id: str
    count: int
    primary_hint: str
    rule_refinement_suggestion: str
    config_snippet: str | None
    suppression_snippet: str | None
    regression_snippet_path: str | None
    llm_explanation: str | None = None  # LLM-generated explanation
    llm_fix_prompt: str | None = None  # LLM-generated fix prompt


def load_tuning_clusters(clusters_path: Path) -> List[Dict[str, Any]]:
    """Load clusters from tuning_clusters.json."""
    if not clusters_path.exists():
        return []

    try:
        with clusters_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("clusters", [])
    except (json.JSONDecodeError, OSError):
        return []


def _generate_rule_refinement_suggestion(cluster: Dict[str, Any]) -> str:
    """Generate a concrete rule refinement suggestion based on cluster patterns."""
    rule_id = cluster.get("rule_id", "")
    trigger_sig = cluster.get("trigger_signature", "")
    action_hints = cluster.get("action_hints", [])

    # Start with the primary action hint if available
    if action_hints:
        primary_hint = action_hints[0]

        # Provide concrete suggestions based on hint patterns
        if "type-annotation" in primary_hint.lower():
            return (
                f"Narrow the AST predicate for {rule_id} to exclude type-annotation context "
                "(in_type_annotation=true). This will reduce false positives in type hints."
            )
        elif (
            "visitor" in primary_hint.lower()
            or "nodetransformer" in primary_hint.lower()
        ):
            return (
                f"Allow broad-except patterns in AST visitor/adapter layers for {rule_id}. "
                "NodeVisitor/NodeTransformer patterns often require catching Exception."
            )
        elif "tests/" in primary_hint.lower() or "test code" in primary_hint.lower():
            return (
                f"Consider downgrading severity or confidence for {rule_id} in tests/ directory, "
                "or exclude tests/ from this check entirely."
            )
        elif "file-glob" in primary_hint.lower():
            return (
                f"Add file-glob based filtering for {rule_id} or narrow the AST predicate "
                "to reduce scope of this pattern."
            )

    # Fallback: generic suggestion based on trigger signature
    return (
        f"Review and refine the detection logic for {rule_id}. "
        f"Pattern '{trigger_sig}' triggers {cluster.get('count', 0)} false positives. "
        "Consider adding guards or narrowing the scope."
    )


def _generate_suppression_snippet(cluster: Dict[str, Any]) -> str | None:
    """Generate a copy-pasteable suppression snippet.

    Returns None if the cluster doesn't have enough info for a meaningful suppression.
    """
    rule_id = cluster.get("rule_id", "")
    count = cluster.get("count", 0)
    top_dirs = cluster.get("top_directories", [])

    # If most findings are in a single directory, suggest file-glob suppression
    # Early return if no directory data available
    if not top_dirs or len(top_dirs) < 1:
        # Fall through to per-fingerprint fallback below
        pass
    else:
        # Extract and validate directory entry structure
        top_dir_entry = top_dirs[0]

        # Handle both dict and tuple formats
        if isinstance(top_dir_entry, dict):
            top_dir = top_dir_entry.get("directory", "")
            top_count = top_dir_entry.get("count", 0)
        elif isinstance(top_dir_entry, (tuple, list)) and len(top_dir_entry) >= 2:
            top_dir = top_dir_entry[0]
            top_count = top_dir_entry[1]
        else:
            # Invalid structure - fall through to fallback
            top_dir = ""
            top_count = 0

        # If > 80% in one directory, suggest glob
        if count > 0:
            # Calculate percentage with explicit zero check
            percentage = top_count / count
            if percentage > 0.8:
                snippet = f"""# Suppress {rule_id} in {top_dir}/ (cluster {cluster.get("cluster_id", "")})
# WARNING: This is a broad suppression. Consider narrowing the rule instead.
# Recommended: Use per-fingerprint suppressions for finer control.
# - rule_id: "{rule_id}"
#   path_glob: "{top_dir}/**/*.py"
#   justification: "Known pattern in {top_dir} - cluster analysis shows FPs"
#   expires_at: "2026-12-31T00:00:00Z"
#   actor: "team"
"""
                return snippet
        else:
            # count is 0 - skip directory-based suggestion and fall through to fallback
            pass

    # Fallback: suggest per-fingerprint suppression (noisy)
    examples = cluster.get("examples", [])
    if examples:
        fingerprint = examples[0].get("fingerprint", "")
        snippet = f"""# Suppress specific finding (cluster {cluster.get("cluster_id", "")})
# Note: This is a single-fingerprint suppression. You may need to repeat this
# for all {count} findings in this cluster, which is noisy.
# Recommended: Refine the rule instead.
# - fingerprint: "{fingerprint}"
#   rule_id: "{rule_id}"
#   justification: "False positive - see cluster analysis"
#   expires_at: "2026-12-31T00:00:00Z"
#   actor: "team"
"""
        return snippet

    return None


def _extract_regression_snippet(
    cluster: Dict[str, Any], cluster_dir: Path, repo_root: Path
) -> str | None:
    """Extract a code snippet for regression testing.

    Returns relative path to the generated snippet file.
    """
    examples = cluster.get("examples", [])
    if not examples:
        return None

    cluster_dir.mkdir(parents=True, exist_ok=True)

    # Collect unique code snippets
    snippets = []
    seen_files = set()

    for example in examples[:3]:  # Top 3 examples
        file_path_str = example.get("file_path")
        line = example.get("line")

        if not file_path_str or not line:
            continue

        # Avoid duplicates from same file
        if file_path_str in seen_files:
            continue
        seen_files.add(file_path_str)

        file_path = repo_root / file_path_str
        if not file_path.exists():
            continue

        try:
            with file_path.open("r", encoding="utf-8") as f:
                lines = f.readlines()

            if line < 1 or line > len(lines):
                continue

            # Extract context around the line
            start = max(0, line - 1 - 4)
            end = min(len(lines), line + 4)
            snippet_lines = lines[start:end]

            snippet_text = "".join(snippet_lines).rstrip()
            snippets.append(f"# From {file_path_str}:{line}\n{snippet_text}")

        except (OSError, UnicodeDecodeError):
            continue

    if not snippets:
        return None

    # Write snippet file
    snippet_file = cluster_dir / "should_not_trigger.py"
    snippet_content = '"""Regression snippets that should NOT trigger the rule."""\n\n'
    snippet_content += "\n\n# " + "=" * 60 + "\n\n".join(snippets)

    snippet_file.write_text(snippet_content, encoding="utf-8")

    # Write README
    readme_file = cluster_dir / "README.md"
    readme_content = f"""# Regression Snippets: {cluster.get("cluster_id", "")}

**Rule**: `{cluster.get("rule_id", "")}`
**Trigger Signature**: {cluster.get("trigger_signature", "")}

## Purpose

These code snippets should NOT trigger the rule {cluster.get("rule_id", "")} after refinement.
They represent false positive patterns identified during tuning.

## Snippets

See `should_not_trigger.py` for {len(snippets)} example(s) extracted from the codebase.

## Usage

1. Refine the rule to avoid triggering on these patterns
2. Add these snippets to your test suite as regression tests
3. Verify the refined rule passes on these snippets but still catches true positives
"""
    readme_file.write_text(readme_content, encoding="utf-8")

    return str(cluster_dir.relative_to(repo_root / "artifacts" / "proposals"))


def generate_proposals(
    clusters_data: List[Dict[str, Any]],
    repo_root: Path,
    top_n: int = 10,
    include_acceptable: bool = False,
    llm_provider: Any | None = None,  # Optional LLM provider for enhanced proposals
) -> List[Proposal]:
    """Generate deterministic proposals from tuning clusters.

    Args:
        clusters_data: Loaded cluster data from tuning_clusters.json
        repo_root: Repository root path
        top_n: Number of top clusters to generate proposals for
        include_acceptable: Include acceptable_risk clusters (not currently in data)
        llm_provider: Optional LLM provider for generating explanations and fix prompts

    Returns:
        List of Proposal objects, sorted deterministically
    """
    # Sort clusters by count desc, cluster_id asc for determinism
    sorted_clusters = sorted(
        clusters_data,
        key=lambda c: (-c.get("count", 0), c.get("cluster_id", "")),
    )

    proposals = []
    proposals_dir = repo_root / "artifacts" / "proposals"
    regression_snippets_dir = proposals_dir / "regression_snippets"

    for cluster in sorted_clusters[:top_n]:
        cluster_id = cluster.get("cluster_id", "")
        rule_id = cluster.get("rule_id", "")
        count = cluster.get("count", 0)

        # Generate proposal ID
        proposal_key = f"{cluster_id}:{rule_id}"
        proposal_id = hashlib.sha256(proposal_key.encode("utf-8")).hexdigest()[:16]

        # Get primary hint
        action_hints = cluster.get("action_hints", [])
        primary_hint = (
            action_hints[0] if action_hints else "Review cluster for patterns"
        )

        # Generate suggestions
        rule_refinement = _generate_rule_refinement_suggestion(cluster)
        suppression_snippet = _generate_suppression_snippet(cluster)

        # Extract regression snippets
        cluster_snippet_dir = regression_snippets_dir / cluster_id
        regression_snippet_path = _extract_regression_snippet(
            cluster, cluster_snippet_dir, repo_root
        )

        # Generate LLM-enhanced content if provider available
        llm_explanation = None
        llm_fix_prompt = None

        if llm_provider is not None:
            try:
                from vibegate.llm.enhancer import (
                    enhance_cluster_with_llm,
                    generate_cluster_fix_prompt,
                )

                # Generate explanation
                llm_result = enhance_cluster_with_llm(cluster, llm_provider)
                llm_explanation = llm_result.get("explanation")

                # Generate fix prompt
                llm_fix_prompt = generate_cluster_fix_prompt(
                    cluster, rule_refinement, llm_provider
                )

            except Exception as e:
                # LLM enhancement is optional - don't fail if it errors
                import logging

                logging.getLogger(__name__).warning(
                    f"LLM enhancement failed for cluster {cluster_id}: {e}"
                )

        proposals.append(
            Proposal(
                proposal_id=proposal_id,
                cluster_id=cluster_id,
                rule_id=rule_id,
                count=count,
                primary_hint=primary_hint,
                rule_refinement_suggestion=rule_refinement,
                config_snippet=None,  # Config-based filtering not implemented yet
                suppression_snippet=suppression_snippet,
                regression_snippet_path=regression_snippet_path,
                llm_explanation=llm_explanation,
                llm_fix_prompt=llm_fix_prompt,
            )
        )

    return proposals


def write_proposals_json(proposals: List[Proposal], output_path: Path) -> None:
    """Write proposals to JSON file."""
    proposals_data = []

    for proposal in proposals:
        proposal_dict = {
            "proposal_id": proposal.proposal_id,
            "cluster_id": proposal.cluster_id,
            "rule_id": proposal.rule_id,
            "count": proposal.count,
            "primary_hint": proposal.primary_hint,
            "rule_refinement_suggestion": proposal.rule_refinement_suggestion,
            "config_snippet": proposal.config_snippet,
            "suppression_snippet": proposal.suppression_snippet,
            "regression_snippet_path": proposal.regression_snippet_path,
        }

        # Add LLM fields if available
        if proposal.llm_explanation:
            proposal_dict["llm_explanation"] = proposal.llm_explanation
        if proposal.llm_fix_prompt:
            proposal_dict["llm_fix_prompt"] = proposal.llm_fix_prompt

        proposals_data.append(proposal_dict)

    output_data = {"proposals": proposals_data}
    output_path.write_text(
        json.dumps(output_data, indent=2, sort_keys=True), encoding="utf-8"
    )


def write_proposals_markdown(proposals: List[Proposal], output_path: Path) -> None:
    """Write human-friendly proposals markdown report."""
    lines = [
        "# VibeGate Proposed Patch Pack",
        "",
        "This report contains actionable proposals for addressing false positive clusters.",
        "These are suggestions only - review carefully before applying.",
        "",
        "## Summary",
        "",
        f"- **Total Proposals**: {len(proposals)}",
        "",
    ]

    if proposals:
        lines.extend(
            [
                "| Proposal | Rule ID | Count | Primary Hint |",
                "|----------|---------|-------|--------------|",
            ]
        )
        for proposal in proposals[:10]:
            hint_short = (
                proposal.primary_hint[:50] + "..."
                if len(proposal.primary_hint) > 50
                else proposal.primary_hint
            )
            lines.append(
                f"| {proposal.proposal_id} | {proposal.rule_id} | {proposal.count} | {hint_short} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Detailed Proposals",
            "",
        ]
    )

    for i, proposal in enumerate(proposals, 1):
        lines.extend(
            [
                f"### Proposal {i}: {proposal.cluster_id}",
                "",
                f"**Rule**: `{proposal.rule_id}`",
                f"**Affected Findings**: {proposal.count}",
                f"**Proposal ID**: `{proposal.proposal_id}`",
                "",
            ]
        )

        # Add LLM explanation if available
        if proposal.llm_explanation:
            lines.extend(
                [
                    "#### 🤖 AI Explanation",
                    "",
                    f"{proposal.llm_explanation}",
                    "",
                ]
            )

        lines.extend(
            [
                "#### Primary Hint",
                "",
                f"{proposal.primary_hint}",
                "",
                "#### Rule Refinement Suggestion",
                "",
                f"{proposal.rule_refinement_suggestion}",
                "",
            ]
        )

        # Add LLM fix prompt if available
        if proposal.llm_fix_prompt:
            lines.extend(
                [
                    "#### 🔧 AI-Generated Fix Prompt",
                    "",
                    "Copy this prompt to your AI coding assistant:",
                    "",
                    "```",
                    proposal.llm_fix_prompt.strip(),
                    "```",
                    "",
                ]
            )

        if proposal.regression_snippet_path:
            lines.extend(
                [
                    "#### Regression Snippets",
                    "",
                    f"Code snippets extracted to: `artifacts/proposals/{proposal.regression_snippet_path}/`",
                    "",
                    "Use these snippets to:",
                    "- Verify refined rule doesn't trigger false positives",
                    "- Add to regression test suite",
                    "",
                ]
            )

        if proposal.suppression_snippet:
            lines.extend(
                [
                    "#### Copy-Paste Suppression Snippet",
                    "",
                    "**WARNING**: Suppressions are a last resort. Consider refining the rule first.",
                    "",
                    "```yaml",
                    proposal.suppression_snippet.strip(),
                    "```",
                    "",
                ]
            )

        lines.append("---")
        lines.append("")

    lines.extend(
        [
            "## Next Steps",
            "",
            "1. Review each proposal and decide on action (rule refinement vs suppression)",
            "2. For rule refinements:",
            "   - Update rule logic in check implementation",
            "   - Test with regression snippets to ensure no false positives",
            "   - Verify true positives still caught",
            "3. For suppressions:",
            "   - Copy snippet to `.vibegate/suppressions.yaml`",
            "   - Adjust justification and expiry as needed",
            "4. Create a PR with your changes and document the rationale",
            "",
            "Remember: This is guidance, not automation. Review carefully!",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_copy_paste_snippets(proposals: List[Proposal], output_dir: Path) -> None:
    """Write copy-paste ready suppression and config snippets."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect all suppression snippets
    suppression_lines = [
        "# VibeGate Suppression Snippets",
        "# Generated from tuning cluster analysis",
        "# WARNING: Review and adjust before using!",
        "",
        "# Add these to .vibegate/suppressions.yaml",
        "",
    ]

    has_suppressions = False
    for proposal in proposals:
        if proposal.suppression_snippet:
            suppression_lines.append(proposal.suppression_snippet.strip())
            suppression_lines.append("")
            has_suppressions = True

    if has_suppressions:
        snippets_file = output_dir / "suppressions.yaml.snippets"
        snippets_file.write_text("\n".join(suppression_lines), encoding="utf-8")

    # Note: Config snippets would go here if we support config-based filtering
    # For now, we don't have a structured way to express file-glob rules in vibegate.yaml
