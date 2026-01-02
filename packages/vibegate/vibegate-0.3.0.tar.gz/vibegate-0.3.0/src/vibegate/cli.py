from __future__ import annotations

import importlib
import json
import logging
from pathlib import Path
from typing import List, Optional, Set, Tuple

import typer
import yaml

from vibegate import __version__
from vibegate.checks import tool_exists, tool_version
from vibegate.config import ConfigError, VibeGateConfig, default_contract, load_config
from vibegate.evidence import load_run_summary
from vibegate.runner import run_check, run_fixpack

app = typer.Typer(help="VibeGate CLI")
logger = logging.getLogger(__name__)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the VibeGate version and exit.",
    ),
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def check(
    repo_root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Run VibeGate signals and emit evidence artifacts."""
    repo_root = repo_root.resolve()

    # Friendly error if config doesn't exist
    config_path = repo_root / "vibegate.yaml"
    if not config_path.exists():
        typer.secho(
            "No configuration found. VibeGate requires a vibegate.yaml file.",
            fg=typer.colors.RED,
        )
        typer.echo("\nTo get started, run:")
        typer.secho("  vibegate init .", fg=typer.colors.GREEN, bold=True)
        raise typer.Exit(code=2)

    try:
        config = load_config(repo_root)
    except ConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc

    artifacts, status = run_check(config, repo_root)
    _print_outputs(config, artifacts)
    _print_summary(status, config)
    if status == "FAIL":
        raise typer.Exit(code=1)


@app.command()
def run(
    repo_root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Alias for check."""
    check(repo_root)


@app.command()
def verify(
    repo_root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Alias for check."""
    check(repo_root)


@app.command()
def fixpack(
    repo_root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Emit placeholder fix pack artifacts."""
    repo_root = repo_root.resolve()
    try:
        config = load_config(repo_root)
    except ConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc

    artifacts, status = run_fixpack(config, repo_root)
    _print_outputs(config, artifacts)
    if status == "FAIL":
        raise typer.Exit(code=1)


@app.command("fixpack-list")
def fixpack_list(
    path: Path = typer.Option(
        Path("artifacts/fixpack.json"),
        "--path",
        help="Path to the fixpack JSON file.",
    ),
) -> None:
    """Print a TSV summary of fixpack tasks."""
    if not path.exists():
        typer.secho(f"Fixpack not found at {path}", fg=typer.colors.RED)
        raise typer.Exit(code=2)
    with path.open("r", encoding="utf-8") as handle:
        fixpack = json.load(handle)
    groups = fixpack.get("groups", [])
    if not isinstance(groups, list):
        typer.secho("Fixpack groups are invalid.", fg=typer.colors.RED)
        raise typer.Exit(code=2)
    rows: List[Tuple[int, int, str, str, str]] = []
    for group in groups:
        group_order = group.get("order")
        if not isinstance(group_order, int):
            group_order = 0
        tasks = group.get("tasks", [])
        if not isinstance(tasks, list):
            continue
        for task in tasks:
            task_id = task.get("id", "")
            title = task.get("title", "")
            severity = task.get("severity", "unknown")
            task_order = task.get("order")
            if not isinstance(task_order, int):
                task_order = 0
            rows.append(
                (
                    group_order,
                    task_order,
                    str(task_id),
                    str(title),
                    str(severity),
                )
            )
    for _, _, task_id, title, severity in sorted(
        rows, key=lambda item: (item[0], item[1], item[2])
    ):
        typer.echo(f"{task_id}\t{title}\t{severity}")


def _check_ui_deps() -> tuple[bool, str]:
    missing = []
    for name in ("typing_extensions", "fastapi", "uvicorn"):
        if importlib.util.find_spec(name) is None:
            missing.append(name)
    if missing:
        return (
            False,
            "Missing UI dependency modules: "
            + ", ".join(missing)
            + '. Run: pip install "vibegate[ui]"',
        )
    try:
        import typing_extensions  # noqa: F401
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        return (
            False,
            "UI dependencies import failed. "
            f"{type(exc).__name__}: {exc}. "
            'Reinstall with: pip install --force-reinstall "vibegate[ui]"',
        )
    return True, ""


@app.command()
def ui(
    repo_root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8787, "--port"),
    open_browser: bool = typer.Option(True, "--open/--no-open"),
    static: bool = typer.Option(
        False, "--static", help="Read-only mode; do not run signals from UI"
    ),
    runs_dir: Path = typer.Option(
        Path(".vibegate/ui/runs"),
        "--runs-dir",
        help="Where to store UI run sessions",
    ),
) -> None:
    """Start the local VibeGate UI server."""
    repo_root = repo_root.resolve()
    ok, message = _check_ui_deps()
    if not ok:
        typer.secho(message, fg=typer.colors.RED)
        raise typer.Exit(code=2)
    try:
        from vibegate.ui.server import serve
    except ModuleNotFoundError as exc:
        if exc.name in {
            "fastapi",
            "uvicorn",
            "starlette",
            "typing_extensions",
            "pydantic",
            "pydantic_core",
        }:
            typer.secho(
                'UI dependencies not installed. Run: pip install "vibegate[ui]"',
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=2) from exc
        raise

    try:
        serve(
            repo_root=repo_root,
            host=host,
            port=port,
            open_browser=open_browser,
            static_mode=static,
            runs_dir=runs_dir,
        )
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc


@app.command()
def init(
    repo_root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite vibegate.yaml if it already exists.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip interactive prompts and use recommended defaults.",
    ),
) -> None:
    """Generate a starter vibegate.yaml and supporting directories."""
    import sys

    repo_root = repo_root.resolve()
    if not isinstance(force, bool):
        force = False
    created: List[Path] = []

    # Interactive prompts (only if not --yes and running in TTY)
    use_interactive = not yes and sys.stdin.isatty()
    create_labels = True  # default
    llm_config = None  # LLM configuration from wizard

    if use_interactive:
        typer.echo("Initializing VibeGate configuration...\n")
        create_labels_input = typer.prompt(
            "Create labels.yaml for tracking false positives?",
            default="yes",
            type=str,
        )
        create_labels = create_labels_input.lower() in ("y", "yes", "")

        # Run LLM setup wizard
        try:
            from vibegate.llm.setup import run_llm_setup_wizard

            llm_config = run_llm_setup_wizard()
        except ImportError:
            # LLM module not available (ollama not installed)
            typer.echo(
                "\nNote: Install with 'pip install vibegate[llm]' for AI assistant features"
            )
        except Exception as e:
            typer.secho(f"\nLLM setup failed: {e}", fg=typer.colors.YELLOW)

    contract_path = repo_root / "vibegate.yaml"
    if contract_path.exists() and not force:
        typer.secho(
            "vibegate.yaml already exists. Use --force to overwrite.",
            fg=typer.colors.YELLOW,
        )
    else:
        contract = default_contract(repo_root)
        packaging_tool = _detect_packaging_tool(
            contract.get("packaging", {}).get(
                "tool_detection_order", ["uv", "poetry", "pdm", "pip-tools", "pip"]
            )
        )
        packaging = contract.get("packaging", {})
        packaging["tool"] = packaging_tool
        contract["packaging"] = packaging

        # Add LLM config if wizard completed
        if llm_config:
            contract["llm"] = {
                "enabled": llm_config.get("enabled", True),
                "provider": llm_config.get("provider", "ollama"),
                "cache_dir": ".vibegate/llm_cache",
                "ollama": {
                    "base_url": "http://localhost:11434",
                    "model": llm_config.get("model", "codellama:7b"),
                    "temperature": 0.3,
                },
                "features": {
                    "explain_findings": True,
                    "generate_prompts": True,
                },
            }

        contract_path.write_text(
            yaml.safe_dump(contract, sort_keys=False), encoding="utf-8"
        )
        created.append(contract_path)

    for dirname in ("artifacts", "evidence", ".vibegate"):
        directory = repo_root / dirname
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(directory)

    # Create LLM cache directory if LLM is configured
    if llm_config:
        llm_cache_dir = repo_root / ".vibegate" / "llm_cache"
        if not llm_cache_dir.exists():
            llm_cache_dir.mkdir(parents=True, exist_ok=True)
            created.append(llm_cache_dir)

    suppressions_path = repo_root / ".vibegate" / "suppressions.yaml"
    if not suppressions_path.exists() or force:
        suppressions_path.parent.mkdir(parents=True, exist_ok=True)
        suppressions_path.write_text(_suppressions_template(), encoding="utf-8")
        if suppressions_path not in created:
            created.append(suppressions_path)

    if create_labels:
        labels_path = repo_root / ".vibegate" / "labels.yaml"
        if not labels_path.exists() or force:
            labels_path.parent.mkdir(parents=True, exist_ok=True)
            labels_path.write_text(_labels_template(), encoding="utf-8")
            if labels_path not in created:
                created.append(labels_path)

    typer.echo("\nCreated:")
    if created:
        for path in created:
            typer.echo(f"  - {path.relative_to(repo_root)}")
    else:
        typer.echo("  - (nothing)")

    typer.echo("\nNext steps:")
    typer.echo("  1. vibegate doctor .")
    typer.echo("  2. vibegate run .")


@app.command()
def doctor(
    repo_root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Verify required tools and versions for enabled signals."""
    repo_root = repo_root.resolve()
    try:
        config = load_config(repo_root)
    except ConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc

    required_tools = _required_tools(config)
    missing = [tool for tool in sorted(required_tools) if not tool_exists(tool)]

    mismatches: List[Tuple[str, str, str]] = []
    for tool, expected in config.determinism.tool_versions.items():
        if not tool_exists(tool):
            if tool not in missing:
                missing.append(tool)
            continue
        observed_raw = tool_version(tool)
        observed = _extract_version(observed_raw) or observed_raw
        if observed != expected:
            mismatches.append((tool, expected, observed_raw))

    if missing:
        typer.secho("Missing required tools:", fg=typer.colors.RED)
        for tool in sorted(set(missing)):
            typer.echo(f"- {tool}")

    if mismatches:
        typer.secho("Version mismatches:", fg=typer.colors.RED)
        for tool, expected, observed in mismatches:
            typer.echo(f"- {tool}: expected {expected}, observed {observed}")

    if not missing and not mismatches:
        typer.secho("All required tools are available.", fg=typer.colors.GREEN)

    if missing or mismatches:
        typer.echo("Install guidance:")
        typer.echo(
            '- Recommended tooling: python -m pip install "vibegate[tools]" '
            '(or pipx install "vibegate[tools]")'
        )
        guidance_tools = sorted(set(missing + [tool for tool, _, _ in mismatches]))
        for tool in guidance_tools:
            expected = config.determinism.tool_versions.get(tool)
            typer.echo(f"- {tool}: {_install_guidance(tool, expected)}")
        raise typer.Exit(code=1)


@app.command()
def prompt() -> None:
    """Stub command for future prompt-based workflows."""
    typer.echo("not implemented")


@app.command()
def label(
    fingerprint: str = typer.Argument(..., help="Finding fingerprint to label"),
    false_positive: bool = typer.Option(
        False, "--false-positive", help="Mark as false positive"
    ),
    true_positive: bool = typer.Option(
        False, "--true-positive", help="Mark as true positive"
    ),
    acceptable_risk: bool = typer.Option(
        False, "--acceptable-risk", help="Mark as acceptable risk"
    ),
    reason: str = typer.Option(..., "--reason", help="Short reason tag"),
    note: str = typer.Option("", "--note", help="Optional detailed note"),
    repo_root: Path = typer.Option(
        Path("."),
        "--repo",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Repository root directory",
    ),
) -> None:
    """Label a finding for false positive tracking.

    Labels help track finding quality but do NOT affect CI/CD behavior.
    Use suppressions.yaml to actually suppress findings in CI/CD.
    """
    from datetime import datetime, timezone

    repo_root = repo_root.resolve()

    # Validate exactly one label type
    label_flags = [false_positive, true_positive, acceptable_risk]
    if sum(label_flags) != 1:
        typer.secho(
            "Error: Specify exactly one of --false-positive, --true-positive, or --acceptable-risk",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=2)

    if false_positive:
        label_type = "false_positive"
    elif true_positive:
        label_type = "true_positive"
    else:
        label_type = "acceptable_risk"

    labels_path = repo_root / ".vibegate" / "labels.yaml"

    # Load existing labels or create new structure
    if labels_path.exists():
        with labels_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {"version": 1, "labels": []}

    labels_list = data.get("labels", [])
    if not isinstance(labels_list, list):
        labels_list = []

    # Find or create entry for this fingerprint
    existing_entry = None
    for entry in labels_list:
        if entry.get("fingerprint") == fingerprint:
            existing_entry = entry
            break

    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if existing_entry:
        # Update existing entry
        existing_entry["label"] = label_type
        existing_entry["reason"] = reason
        existing_entry["note"] = note
        existing_entry["created_at"] = now_iso
        typer.echo(f"Updated label for fingerprint: {fingerprint[:12]}...")
    else:
        # Create new entry
        new_entry = {
            "fingerprint": fingerprint,
            "rule_id": "",  # Could be populated from evidence if available
            "label": label_type,
            "reason": reason,
            "note": note,
            "created_at": now_iso,
        }
        labels_list.append(new_entry)
        typer.echo(f"Added label for fingerprint: {fingerprint[:12]}...")

    data["labels"] = labels_list

    # Write back to file
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    with labels_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)

    typer.secho(f"Label '{label_type}' saved to {labels_path}", fg=typer.colors.GREEN)
    typer.echo(f"Reason: {reason}")
    if note:
        typer.echo(f"Note: {note}")


@app.command()
def tune(
    repo_root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Repository root directory",
    ),
    evidence: Optional[Path] = typer.Option(
        None, "--evidence", help="Path to evidence JSONL file"
    ),
    labels: Optional[Path] = typer.Option(
        None, "--labels", help="Path to labels.yaml file"
    ),
    out: Path = typer.Option(
        Path("artifacts/tuning"),
        "--out",
        help="Output directory for tuning pack",
    ),
    max_examples: int = typer.Option(
        5, "--max-examples", help="Maximum examples per cluster"
    ),
    include_acceptable: bool = typer.Option(
        False, "--include-acceptable", help="Include acceptable_risk in analysis"
    ),
    format_type: str = typer.Option(
        "both", "--format", help="Output format: md, json, or both"
    ),
) -> None:
    """Analyze labeled findings and generate tuning recommendations.

    This command loads evidence from the last run and joins it with labels to:
    - Compute false positive rates by rule
    - Cluster similar false positives
    - Generate actionable tuning hints

    Output is deterministic and suitable for version control.
    """
    from vibegate import tuning as tuning_module

    repo_root = repo_root.resolve()

    # Resolve evidence path
    if evidence is None:
        # Try to load from state.json
        state_path = repo_root / ".vibegate" / "state.json"
        if state_path.exists():
            try:
                state_data = json.load(state_path.open("r", encoding="utf-8"))
                evidence_rel = state_data.get("last_run", {}).get("evidence_path")
                if evidence_rel:
                    evidence = repo_root / evidence_rel
            except (json.JSONDecodeError, KeyError, OSError) as exc:
                # State file malformed or missing - will use default evidence path
                # Fallback to default is handled below
                logger.debug(
                    "Could not load evidence path from state file: %s (using defaults)",
                    exc,
                )

        # Fall back to default
        if evidence is None:
            evidence = repo_root / "evidence" / "vibegate.jsonl"

    if not evidence.exists():
        typer.secho(
            f"Evidence file not found: {evidence}",
            fg=typer.colors.RED,
        )
        typer.echo("\nRun 'vibegate check .' first to generate evidence.")
        raise typer.Exit(code=2)

    # Resolve labels path
    if labels is None:
        labels = repo_root / ".vibegate" / "labels.yaml"

    if not labels.exists():
        typer.secho(
            f"Labels file not found: {labels}",
            fg=typer.colors.YELLOW,
        )
        typer.echo("\nNo labels found. Use 'vibegate label' to label findings.")
        typer.echo(
            "Example: vibegate label <fingerprint> --false-positive --reason <reason>"
        )
        raise typer.Exit(code=2)

    # Load evidence and labels
    typer.echo("Loading evidence and labels...")
    findings = tuning_module.load_evidence_findings(evidence)
    labels_map = tuning_module.load_labels(labels)

    if not findings:
        typer.secho("No findings in evidence file.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=0)

    # Join findings with labels
    labeled, unlabeled = tuning_module.join_findings_with_labels(findings, labels_map)

    if not labeled:
        typer.secho(
            "No labeled findings found. Label some findings first.",
            fg=typer.colors.YELLOW,
        )
        typer.echo(
            "\nExample: vibegate label <fingerprint> --false-positive --reason <reason>"
        )
        raise typer.Exit(code=0)

    # Compute metrics
    metrics = tuning_module.compute_metrics(labeled, unlabeled)

    # Check if there are any FPs to analyze
    if metrics.false_positive_count == 0 and not include_acceptable:
        typer.secho(
            "No false positives to analyze. All labeled findings are true positives.",
            fg=typer.colors.GREEN,
        )
        typer.echo("\nNothing to tune!")
        raise typer.Exit(code=0)

    if metrics.false_positive_count == 0 and metrics.acceptable_risk_count == 0:
        typer.secho(
            "No false positives or acceptable risks to analyze.",
            fg=typer.colors.GREEN,
        )
        typer.echo("\nNothing to tune!")
        raise typer.Exit(code=0)

    # Cluster findings
    typer.echo("Clustering findings...")
    clusters = tuning_module.cluster_findings(labeled, include_acceptable)

    if not clusters:
        typer.secho(
            "No clusters generated (this shouldn't happen with FPs).",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(code=0)

    # Write tuning pack
    typer.echo(f"Writing tuning pack to {out}...")
    out_resolved = repo_root / out if not out.is_absolute() else out
    report_path, clusters_json_path, examples_dir = tuning_module.write_tuning_pack(
        out_resolved, repo_root, metrics, clusters, max_examples
    )

    # Update state.json with tune metadata
    from vibegate.runner import write_tune_state

    write_tune_state(
        repo_root, out_resolved, report_path, clusters_json_path, examples_dir
    )

    # Print summary
    typer.echo("\nTuning Pack Created:")
    typer.echo(f"  - Report: {report_path}")
    typer.echo(f"  - Clusters JSON: {clusters_json_path}")
    typer.echo(f"  - Examples: {examples_dir}/")
    typer.echo("")
    typer.secho("Summary:", fg=typer.colors.GREEN)
    typer.echo(f"  - Total findings: {metrics.total_findings}")
    typer.echo(f"  - Labeled: {metrics.labeled_count}")
    typer.echo(f"  - False positives: {metrics.false_positive_count}")
    typer.echo(f"  - Clusters found: {len(clusters)}")
    typer.echo("")
    typer.echo("Review tuning_report.md for actionable insights.")


@app.command()
def propose(
    repo_root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Repository root directory",
    ),
    clusters: Optional[Path] = typer.Option(
        None, "--clusters", help="Path to tuning_clusters.json file"
    ),
    tuning_dir: Optional[Path] = typer.Option(
        None, "--tuning-dir", help="Tuning directory (alternative to --clusters)"
    ),
    out: Path = typer.Option(
        Path("artifacts/proposals"),
        "--out",
        help="Output directory for proposal pack",
    ),
    top: int = typer.Option(
        10, "--top", help="Number of top clusters to generate proposals for"
    ),
    format_type: str = typer.Option(
        "both", "--format", help="Output format: md, json, or both"
    ),
    include_acceptable: bool = typer.Option(
        False, "--include-acceptable", help="Include acceptable_risk clusters"
    ),
) -> None:
    """Generate Proposed Patch Pack from tuning clusters.

    This command takes tuning cluster analysis and generates actionable proposals:
    - Rule refinement suggestions
    - Suppression snippets (copy-pasteable)
    - Regression test snippets

    Output is deterministic and ready for PR review.
    """
    from vibegate import proposals as proposals_module
    from vibegate.runner import write_propose_state

    repo_root = repo_root.resolve()

    # Resolve clusters path
    if clusters is None and tuning_dir is None:
        # Try to load from state.json
        state_path = repo_root / ".vibegate" / "state.json"
        if state_path.exists():
            try:
                state_data = json.load(state_path.open("r", encoding="utf-8"))
                clusters_rel = state_data.get("last_tune", {}).get("clusters_path")
                if clusters_rel:
                    clusters = repo_root / clusters_rel
            except (json.JSONDecodeError, KeyError, OSError) as exc:
                # State file malformed or missing - will use default clusters path
                # Fallback to default is handled below
                logger.debug(
                    "Could not load clusters path from state file: %s (using defaults)",
                    exc,
                )

        # Fall back to default
        if clusters is None:
            clusters = repo_root / "artifacts" / "tuning" / "tuning_clusters.json"

    elif tuning_dir is not None:
        clusters = tuning_dir / "tuning_clusters.json"

    # Type assertion: clusters is always a Path after resolution logic
    assert clusters is not None, "clusters path should be resolved at this point"

    if not clusters.exists():
        typer.secho(
            f"Tuning clusters file not found: {clusters}",
            fg=typer.colors.RED,
        )
        typer.echo("\nRun 'vibegate tune .' first to generate tuning clusters.")
        raise typer.Exit(code=2)

    # Load clusters
    typer.echo("Loading tuning clusters...")
    clusters_data = proposals_module.load_tuning_clusters(clusters)

    if not clusters_data:
        typer.secho(
            "No clusters found in tuning data.",
            fg=typer.colors.YELLOW,
        )
        typer.echo("\nThis means either:")
        typer.echo("  - No false positives were identified during tuning")
        typer.echo("  - The tuning clusters file is empty or invalid")
        typer.echo("\nCreating empty proposal pack...")

        # Still create output directory and report
        out_dir = repo_root / out
        out_dir.mkdir(parents=True, exist_ok=True)

        report_path = out_dir / "proposal_report.md"
        proposals_json_path = out_dir / "proposals.json"

        # Write empty reports
        report_path.write_text(
            "# VibeGate Proposed Patch Pack\n\n"
            "## No Proposals\n\n"
            "No clusters found. This could mean:\n"
            "- All signals are performing well\n"
            "- No false positives identified during tuning\n"
            "- More labeling needed\n",
            encoding="utf-8",
        )

        proposals_json_path.write_text(
            json.dumps({"proposals": []}, indent=2),
            encoding="utf-8",
        )

        # Update state.json
        write_propose_state(repo_root, out_dir, report_path, proposals_json_path)

        typer.echo(f"\nEmpty proposal pack created at {out_dir}")
        raise typer.Exit(code=0)

    # Load LLM provider if configured
    llm_provider = None
    try:
        from vibegate.config import load_config
        from vibegate.llm.enhancer import create_llm_provider_from_config

        config = load_config(repo_root)
        if config.llm and config.llm.enabled:
            typer.echo("🤖 LLM enabled - enhancing proposals with AI explanations...")
            llm_provider = create_llm_provider_from_config(config.llm)
            if llm_provider is None:
                typer.secho(
                    "⚠️  LLM configured but not available. Proposals will not include AI content.",
                    fg=typer.colors.YELLOW,
                )
    except Exception as e:
        typer.secho(
            f"⚠️  Failed to load LLM provider: {e}",
            fg=typer.colors.YELLOW,
        )

    # Generate proposals
    typer.echo(f"Generating proposals for top {top} clusters...")
    proposals = proposals_module.generate_proposals(
        clusters_data,
        repo_root,
        top_n=top,
        include_acceptable=include_acceptable,
        llm_provider=llm_provider,
    )

    if not proposals:
        typer.secho(
            "No proposals generated (this shouldn't happen with clusters).",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(code=0)

    # Write proposal pack
    out_dir = repo_root / out
    typer.echo(f"Writing proposal pack to {out_dir}...")
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = out_dir / "proposal_report.md"
    proposals_json_path = out_dir / "proposals.json"
    copy_paste_dir = out_dir / "copy_paste_snippets"

    if format_type in ("md", "both"):
        proposals_module.write_proposals_markdown(proposals, report_path)

    if format_type in ("json", "both"):
        proposals_module.write_proposals_json(proposals, proposals_json_path)

    proposals_module.write_copy_paste_snippets(proposals, copy_paste_dir)

    # Update state.json
    write_propose_state(repo_root, out_dir, report_path, proposals_json_path)

    # Print summary
    typer.echo("\n" + "=" * 60)
    typer.secho("Proposed Patch Pack Created", fg=typer.colors.GREEN, bold=True)
    typer.echo("=" * 60)
    typer.echo(f"\n  - Report: {report_path.relative_to(repo_root)}")
    typer.echo(f"  - Proposals JSON: {proposals_json_path.relative_to(repo_root)}")
    typer.echo(
        f"  - Regression Snippets: {out_dir.relative_to(repo_root)}/regression_snippets/"
    )
    typer.echo(f"  - Copy-Paste Snippets: {copy_paste_dir.relative_to(repo_root)}/")

    typer.echo("\nSummary:")
    typer.echo(f"  - Total proposals: {len(proposals)}")

    # Show top 5 proposals
    typer.echo("\nTop 5 Proposals:")
    for proposal in proposals[:5]:
        hint_short = (
            proposal.primary_hint[:60] + "..."
            if len(proposal.primary_hint) > 60
            else proposal.primary_hint
        )
        typer.echo(
            f"  - {proposal.cluster_id}: {proposal.rule_id} ({proposal.count} findings)"
        )
        typer.echo(f"    Hint: {hint_short}")

    typer.echo(f"\nReview {report_path.relative_to(repo_root)} for detailed proposals.")
    typer.echo(
        "Remember: These are suggestions only. Review carefully before applying!"
    )


@app.command()
def start(
    repo_root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """One-command workflow: init (if needed) + doctor + check.

    This is the recommended entry point for human workflows.
    Automatically creates config if missing, verifies tools, runs signals,
    and provides a concise summary with next steps.
    """
    import sys

    repo_root = repo_root.resolve()
    config_path = repo_root / "vibegate.yaml"

    # Create config if missing
    if not config_path.exists():
        is_tty = sys.stdin.isatty()
        create_config = True

        if is_tty:
            response = typer.prompt(
                "No vibegate.yaml found. Create config with recommended defaults?",
                default="Y",
                type=str,
            )
            create_config = response.lower() in ("y", "yes", "")

        if create_config:
            typer.echo("Creating configuration...")
            # Reuse init logic
            try:
                init(repo_root=repo_root, force=False, yes=True)
            except typer.Exit as exc:
                # init may raise Exit, but we continue workflow
                # Configuration may have been partially created
                logger.debug(
                    "Init command exited with code %s, continuing workflow",
                    getattr(exc, "exit_code", None),
                )
        else:
            typer.secho("Configuration required. Exiting.", fg=typer.colors.RED)
            raise typer.Exit(code=2)

    # Run doctor
    typer.echo("\nVerifying tools...")
    try:
        doctor(repo_root)
    except typer.Exit as exc:
        if exc.exit_code != 0:
            typer.secho(
                "\nDoctor check failed. Install missing tools before continuing.",
                fg=typer.colors.RED,
            )
            raise

    # Run check
    typer.echo("\nRunning signals...")
    try:
        config = load_config(repo_root)
    except ConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc

    artifacts, status = run_check(config, repo_root)

    # Load summary from evidence
    summary = load_run_summary(config.outputs.evidence_jsonl)

    # Print concise summary
    typer.echo("\n" + "=" * 60)
    typer.secho("VibeGate Decision", fg=typer.colors.BRIGHT_CYAN, bold=True)
    typer.echo("=" * 60)

    if summary and isinstance(summary.get("counts"), dict):
        counts = summary["counts"]
        total = counts.get("findings_total", 0)
        blocking = counts.get("findings_blocking", 0)
        warnings = counts.get("findings_warning", 0)
        suppressed = counts.get("suppressed_total", 0)
        decision = summary.get("decision") or {}
        comparison = summary.get("comparison") or {}
        counts_delta = (
            comparison.get("counts_delta") if isinstance(comparison, dict) else None
        )

        typer.echo(f"\nSignals surfaced: {total}")
        if suppressed > 0:
            typer.echo(f"  - Suppressed: {suppressed}")
        if blocking > 0:
            typer.secho(f"  - Blocking: {blocking}", fg=typer.colors.RED, bold=True)
        if warnings > 0:
            typer.secho(f"  - Warnings: {warnings}", fg=typer.colors.YELLOW)

        reason = decision.get("reason")
        decision_line = f"\nDecision: {status}"
        if reason:
            decision_line += f" ({reason})"
        typer.secho(
            decision_line,
            fg=typer.colors.GREEN if status == "PASS" else typer.colors.RED,
            bold=True,
        )
        if isinstance(counts_delta, dict) and counts_delta:
            label_map = {
                "findings_blocking": "blocking",
                "findings_warning": "warnings",
                "findings_unsuppressed": "unsuppressed",
                "suppressed_total": "suppressed",
            }
            delta_bits = []
            for key in (
                "findings_blocking",
                "findings_warning",
                "findings_unsuppressed",
                "suppressed_total",
            ):
                if key in counts_delta:
                    label = label_map.get(key, key)
                    delta_bits.append(f"{label}: {_format_delta(counts_delta[key])}")
            if delta_bits:
                typer.echo(f"Delta vs baseline: {', '.join(delta_bits)}")
    else:
        typer.secho(
            f"\nDecision: {status}",
            fg=typer.colors.GREEN if status == "PASS" else typer.colors.RED,
            bold=True,
        )

    # Show where artifacts were written
    state_path = repo_root / ".vibegate" / "state.json"
    if state_path.exists():
        try:
            state_data = json.load(state_path.open("r", encoding="utf-8"))
            evidence_rel = state_data.get("last_run", {}).get("evidence_path")
            report_paths = state_data.get("last_run", {}).get("report_paths", [])

            typer.echo("\nEvidence & artifacts:")
            if evidence_rel:
                typer.echo(f"  - Evidence: {evidence_rel}")
            for report_path in report_paths:
                typer.echo(f"  - Report: {report_path}")
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            # State file malformed or missing - skip artifact display
            # User will still see output from check command
            logger.debug(
                "Could not load artifact paths from state file: %s (skipping display)",
                exc,
            )

    # Suggest next steps
    typer.echo("\nNext steps:")
    if status == "FAIL":
        if sys.stdin.isatty():
            typer.echo("  - Review findings and label signal noise: vibegate triage")
        typer.echo("  - Tune signals based on labels: vibegate tune")
    else:
        typer.echo("  - All signals passed!")

    if status == "FAIL":
        raise typer.Exit(code=1)


@app.command()
def triage(
    repo_root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
) -> None:
    """Interactive labeling workflow for findings.

    Allows you to mark findings as false_positive, true_positive, or acceptable_risk.
    This helps improve check tuning and track finding quality.

    Requires a TTY. For non-interactive labeling, use: vibegate label <fingerprint>
    """
    import sys
    from datetime import datetime, timezone

    repo_root = repo_root.resolve()

    # Check if running in TTY
    if not sys.stdin.isatty():
        typer.secho(
            "Triage is an interactive command and requires a TTY.",
            fg=typer.colors.YELLOW,
        )
        typer.echo("\nFor non-interactive labeling, use:")
        typer.echo("  vibegate label <fingerprint> --false-positive --reason <reason>")
        raise typer.Exit(code=1)

    # Load evidence from state.json or default path
    evidence_path = None
    state_path = repo_root / ".vibegate" / "state.json"
    if state_path.exists():
        try:
            state_data = json.load(state_path.open("r", encoding="utf-8"))
            evidence_rel = state_data.get("last_run", {}).get("evidence_path")
            if evidence_rel:
                evidence_path = repo_root / evidence_rel
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            # State file malformed or missing - will use default evidence path
            # Fallback to default is handled below
            logger.debug(
                "Could not load evidence path from state file: %s (using defaults)", exc
            )

    if evidence_path is None:
        evidence_path = repo_root / "evidence" / "vibegate.jsonl"

    if not evidence_path.exists():
        typer.secho(
            f"Evidence file not found: {evidence_path}",
            fg=typer.colors.RED,
        )
        typer.echo("\nRun 'vibegate check .' first to generate evidence.")
        raise typer.Exit(code=1)

    # Load findings from evidence
    findings_list = []
    with evidence_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                if event.get("event_type") == "finding":
                    findings_list.append(event)
            except json.JSONDecodeError:
                continue

    if not findings_list:
        typer.secho("No findings to triage!", fg=typer.colors.GREEN)
        raise typer.Exit(code=0)

    # Sort findings by severity (desc), confidence (desc), file path, line
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    confidence_order = {"high": 0, "medium": 1, "low": 2}

    def finding_sort_key(finding):
        severity = finding.get("severity", "info")
        confidence = finding.get("confidence", "low")
        location = finding.get("location") or {}
        path = location.get("path", "")
        line = location.get("line", 0)
        return (
            severity_order.get(severity, 99),
            confidence_order.get(confidence, 99),
            path,
            line,
        )

    findings_list = sorted(findings_list, key=finding_sort_key)

    # Load existing labels
    labels_path = repo_root / ".vibegate" / "labels.yaml"
    if labels_path.exists():
        with labels_path.open("r", encoding="utf-8") as f:
            labels_data = yaml.safe_load(f) or {}
    else:
        labels_data = {"version": 1, "labels": []}

    labels_list = labels_data.get("labels", [])
    if not isinstance(labels_list, list):
        labels_list = []

    # Track session stats
    session_stats = {"fp": 0, "tp": 0, "acceptable": 0}

    # Interactive loop
    typer.echo(f"\nFound {len(findings_list)} findings to triage.")
    typer.echo(
        "Commands: f=false_positive, t=true_positive, a=acceptable_risk, s=skip, q=quit\n"
    )

    idx = 0
    while idx < len(findings_list):
        finding = findings_list[idx]
        fingerprint = finding.get("fingerprint", "")
        rule_id = finding.get("rule_id", "")
        severity = finding.get("severity", "")
        confidence = finding.get("confidence", "")
        message = finding.get("message", "")
        location = finding.get("location") or {}
        path = location.get("path", "")
        line = location.get("line", "")

        typer.echo(f"[{idx + 1}/{len(findings_list)}] ", nl=False)
        typer.secho(f"{rule_id}", fg=typer.colors.CYAN, bold=True, nl=False)
        typer.echo(f" ({severity}/{confidence})")
        typer.echo(f"  File: {path}:{line}")
        typer.echo(f"  Message: {message}")
        typer.echo(f"  Fingerprint: {fingerprint[:16]}...")

        action = typer.prompt(
            "\nAction",
            default="s",
            type=str,
        ).lower()

        if action == "q":
            break
        elif action == "s":
            idx += 1
            typer.echo("")
            continue
        elif action in ("f", "t", "a"):
            # Prompt for reason
            reason = typer.prompt("Reason tag", type=str)
            note = typer.prompt("Note (optional)", default="", type=str)

            label_type = {
                "f": "false_positive",
                "t": "true_positive",
                "a": "acceptable_risk",
            }[action]

            # Update or create label
            existing = None
            for entry in labels_list:
                if entry.get("fingerprint") == fingerprint:
                    existing = entry
                    break

            now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

            if existing:
                existing["label"] = label_type
                existing["reason"] = reason
                existing["note"] = note
                existing["created_at"] = now_iso
            else:
                labels_list.append(
                    {
                        "fingerprint": fingerprint,
                        "rule_id": rule_id,
                        "label": label_type,
                        "reason": reason,
                        "note": note,
                        "created_at": now_iso,
                    }
                )

            # Write labels immediately
            labels_data["labels"] = labels_list
            labels_path.parent.mkdir(parents=True, exist_ok=True)
            with labels_path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(
                    labels_data, f, sort_keys=False, default_flow_style=False
                )

            # Update session stats
            if label_type == "false_positive":
                session_stats["fp"] += 1
            elif label_type == "true_positive":
                session_stats["tp"] += 1
            elif label_type == "acceptable_risk":
                session_stats["acceptable"] += 1

            typer.secho(f"Saved: {label_type}", fg=typer.colors.GREEN)
            typer.echo(
                f"Session: FP={session_stats['fp']} TP={session_stats['tp']} Acceptable={session_stats['acceptable']}\n"
            )

            idx += 1
        else:
            typer.echo("Invalid action. Use f/t/a/s/q.\n")

    typer.echo("\nTriage session complete!")
    typer.echo(
        f"Labeled in this session: FP={session_stats['fp']} TP={session_stats['tp']} Acceptable={session_stats['acceptable']}"
    )
    typer.echo(f"Labels saved to: {labels_path}")


@app.command()
def evolve(
    repo_root: Path = typer.Argument(
        Path("."),
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    no_propose: bool = typer.Option(False, "--no-propose", help="Skip propose step"),
) -> None:
    """Full evolution loop: start + triage (optional) + tune + propose.

    This command runs the complete workflow:
    1. Initialize config (if needed), verify tools, and run signals
    2. Optionally triage findings interactively (if TTY)
    3. Generate tuning recommendations based on labels
    4. Generate actionable proposal pack for rule refinement

    Recommended for maintainers evolving signal quality over time.
    """
    import sys

    repo_root = repo_root.resolve()

    # Step 1: Run start (init + doctor + check)
    typer.secho(
        "\n=== Phase 1: Running signals ===", fg=typer.colors.BRIGHT_CYAN, bold=True
    )
    start_failed = False
    try:
        start(repo_root)
    except typer.Exit as exc:
        if exc.exit_code == 1:
            # Signal run failed (blocking findings), but we continue to tune
            start_failed = True
            typer.echo(
                "\nSignals had blocking findings, but continuing to tuning phase..."
            )
        else:
            # Config error or doctor failure - bail out
            raise

    # Step 2: Offer triage if TTY
    if sys.stdin.isatty():
        typer.secho(
            "\n=== Phase 2: Triage (optional) ===",
            fg=typer.colors.BRIGHT_CYAN,
            bold=True,
        )
        response = typer.prompt(
            "Open interactive triage to label findings?",
            default="Y",
            type=str,
        )
        if response.lower() in ("y", "yes", ""):
            try:
                triage(repo_root)
            except typer.Exit as exc:
                # Triage may exit early - continue to tune phase
                # User labels (if any) will still be available
                logger.debug(
                    "Triage command exited with code %s, continuing to tune phase",
                    getattr(exc, "exit_code", None),
                )
    else:
        typer.echo(
            "\nSkipping triage (non-TTY). Use 'vibegate triage .' for interactive labeling."
        )

    # Step 3: Run tune
    typer.secho("\n=== Phase 3: Tuning ===", fg=typer.colors.BRIGHT_CYAN, bold=True)

    # Check if labels exist
    labels_path = repo_root / ".vibegate" / "labels.yaml"
    if not labels_path.exists():
        typer.secho(
            "No labels found. Skipping tuning phase.",
            fg=typer.colors.YELLOW,
        )
        typer.echo(
            "\nLabel some findings first with 'vibegate triage .' or 'vibegate label'"
        )
        if start_failed:
            raise typer.Exit(code=1)
        raise typer.Exit(code=0)

    # Run tune
    try:
        # Load evidence and labels
        from vibegate import tuning as tuning_module

        evidence_path = None
        state_path = repo_root / ".vibegate" / "state.json"
        if state_path.exists():
            try:
                state_data = json.load(state_path.open("r", encoding="utf-8"))
                evidence_rel = state_data.get("last_run", {}).get("evidence_path")
                if evidence_rel:
                    evidence_path = repo_root / evidence_rel
            except (json.JSONDecodeError, KeyError, OSError) as exc:
                # State file malformed or missing - will use default evidence path
                # Fallback to default is handled below
                logger.debug(
                    "Could not load evidence path from state file: %s (using defaults)",
                    exc,
                )

        if evidence_path is None:
            evidence_path = repo_root / "evidence" / "vibegate.jsonl"

        if not evidence_path.exists():
            typer.secho(
                f"Evidence file not found: {evidence_path}",
                fg=typer.colors.RED,
            )
            if start_failed:
                raise typer.Exit(code=1)
            raise typer.Exit(code=2)

        typer.echo("Loading evidence and labels...")
        findings = tuning_module.load_evidence_findings(evidence_path)
        labels_map = tuning_module.load_labels(labels_path)

        if not findings:
            typer.secho("No findings in evidence file.", fg=typer.colors.YELLOW)
            if start_failed:
                raise typer.Exit(code=1)
            raise typer.Exit(code=0)

        labeled, unlabeled = tuning_module.join_findings_with_labels(
            findings, labels_map
        )

        if not labeled:
            typer.secho(
                "No labeled findings found. Label some findings first.",
                fg=typer.colors.YELLOW,
            )
            if start_failed:
                raise typer.Exit(code=1)
            raise typer.Exit(code=0)

        metrics = tuning_module.compute_metrics(labeled, unlabeled)

        if metrics.false_positive_count == 0:
            typer.secho(
                "No false positives to analyze. All labeled findings are true positives.",
                fg=typer.colors.GREEN,
            )
            typer.echo("\nNothing to tune!")
            if start_failed:
                raise typer.Exit(code=1)
            raise typer.Exit(code=0)

        typer.echo("Clustering findings...")
        clusters = tuning_module.cluster_findings(labeled, include_acceptable=False)

        if not clusters:
            typer.secho(
                "No clusters generated.",
                fg=typer.colors.YELLOW,
            )
            if start_failed:
                raise typer.Exit(code=1)
            raise typer.Exit(code=0)

        # Write tuning pack
        out_dir = repo_root / "artifacts" / "tuning"
        typer.echo(f"Writing tuning pack to {out_dir}...")
        report_path, clusters_json_path, examples_dir = tuning_module.write_tuning_pack(
            out_dir, repo_root, metrics, clusters, max_examples=5
        )

        # Update state.json with tune metadata
        from vibegate.runner import write_tune_state

        write_tune_state(
            repo_root, out_dir, report_path, clusters_json_path, examples_dir
        )

        # Print summary
        typer.echo("\n" + "=" * 60)
        typer.secho("Tuning Pack Created", fg=typer.colors.GREEN, bold=True)
        typer.echo("=" * 60)
        typer.echo(f"\n  - Report: {report_path.relative_to(repo_root)}")
        typer.echo(f"  - Clusters JSON: {clusters_json_path.relative_to(repo_root)}")
        typer.echo(f"  - Examples: {examples_dir.relative_to(repo_root)}/")

        typer.echo("\nSummary:")
        typer.echo(f"  - Total findings: {metrics.total_findings}")
        typer.echo(f"  - Labeled: {metrics.labeled_count}")
        typer.echo(f"  - False positives: {metrics.false_positive_count}")
        typer.echo(f"  - Clusters found: {len(clusters)}")

        # Print top N clusters
        typer.echo("\nTop 5 Clusters by FP count:")
        for cluster in clusters[:5]:
            typer.echo(
                f"  - {cluster.cluster_id}: {cluster.rule_id} ({cluster.count} findings)"
            )
            if cluster.action_hints:
                typer.echo(f"    Hint: {cluster.action_hints[0]}")

        typer.echo(
            f"\nReview {report_path.relative_to(repo_root)} for detailed analysis."
        )

        # Step 4: Run propose (unless --no-propose)
        if not no_propose:
            typer.secho(
                "\n=== Phase 4: Proposals ===", fg=typer.colors.BRIGHT_CYAN, bold=True
            )
            typer.echo("Generating actionable proposal pack...")

            from vibegate import proposals as proposals_module
            from vibegate.runner import write_propose_state

            # Generate proposals from the tuning clusters we just created
            proposals = proposals_module.generate_proposals(
                proposals_module.load_tuning_clusters(clusters_json_path),
                repo_root,
                top_n=10,
                include_acceptable=False,
            )

            if proposals:
                # Write proposal pack
                proposals_out = repo_root / "artifacts" / "proposals"
                proposals_out.mkdir(parents=True, exist_ok=True)

                proposals_report_path = proposals_out / "proposal_report.md"
                proposals_json_path = proposals_out / "proposals.json"
                copy_paste_dir = proposals_out / "copy_paste_snippets"

                proposals_module.write_proposals_markdown(
                    proposals, proposals_report_path
                )
                proposals_module.write_proposals_json(proposals, proposals_json_path)
                proposals_module.write_copy_paste_snippets(proposals, copy_paste_dir)

                # Update state.json
                write_propose_state(
                    repo_root, proposals_out, proposals_report_path, proposals_json_path
                )

                # Print summary
                typer.echo("\n" + "=" * 60)
                typer.secho(
                    "Proposed Patch Pack Created", fg=typer.colors.GREEN, bold=True
                )
                typer.echo("=" * 60)
                typer.echo(
                    f"\n  - Report: {proposals_report_path.relative_to(repo_root)}"
                )
                typer.echo(
                    f"  - Proposals JSON: {proposals_json_path.relative_to(repo_root)}"
                )
                typer.echo(
                    f"  - Copy-Paste Snippets: {copy_paste_dir.relative_to(repo_root)}/"
                )

                typer.echo("\nTop 5 Proposals:")
                for proposal in proposals[:5]:
                    hint_short = (
                        proposal.primary_hint[:60] + "..."
                        if len(proposal.primary_hint) > 60
                        else proposal.primary_hint
                    )
                    typer.echo(
                        f"  - {proposal.cluster_id}: {proposal.rule_id} ({proposal.count} findings)"
                    )
                    typer.echo(f"    Hint: {hint_short}")

                typer.echo(
                    f"\nReview {proposals_report_path.relative_to(repo_root)} for actionable proposals."
                )
            else:
                typer.secho("No proposals generated.", fg=typer.colors.YELLOW)

    except typer.Exit:
        if start_failed:
            raise typer.Exit(code=1)
        raise

    if start_failed:
        raise typer.Exit(code=1)


@app.command()
def version() -> None:
    """Print the VibeGate version."""
    typer.echo(__version__)


def _print_outputs(config, artifacts: List) -> None:
    typer.echo("Evidence & artifacts:")
    for artifact in artifacts:
        typer.echo(f"- {artifact.path}")
    typer.echo(f"- {config.outputs.evidence_jsonl}")


def _print_summary(status: str, config: VibeGateConfig) -> None:
    summary = load_run_summary(config.outputs.evidence_jsonl)
    unsuppressed = "unknown"
    if summary and isinstance(summary.get("counts"), dict):
        counts = summary.get("counts", {})
        count = counts.get("findings_unsuppressed")
        if isinstance(count, int):
            unsuppressed = str(count)

    typer.echo("Decision:")
    typer.echo(f"- Status: {status}")
    typer.echo(f"- Unsuppressed signals: {unsuppressed}")
    typer.echo(f"- Evidence report: {config.outputs.report_markdown}")
    typer.echo(f"- Evidence log: {config.outputs.evidence_jsonl}")


def _format_delta(value: int) -> str:
    if value > 0:
        return f"+{value}"
    return str(value)


def _detect_packaging_tool(tool_detection_order: List[str]) -> str:
    for tool in tool_detection_order:
        if tool_exists(tool):
            return tool
    return "pip"


def _required_tools(config: VibeGateConfig) -> Set[str]:
    required: Set[str] = set()
    if config.checks.formatting.enabled or config.checks.lint.enabled:
        required.add("ruff")
    if config.checks.typecheck.enabled:
        required.add("pyright")
    if config.checks.tests.enabled:
        required.add("pytest")
    if config.checks.sast.enabled:
        required.add("bandit")
    if config.checks.secrets.enabled:
        required.add("gitleaks")
    if config.checks.vulnerability.enabled:
        required.add("osv-scanner")
    return required


def _extract_version(raw: str) -> Optional[str]:
    for token in raw.split():
        if token and token[0].isdigit():
            return token.strip()
    return None


def _install_guidance(tool: str, expected: Optional[str]) -> str:
    version = f"=={expected}" if expected else ""
    pipx_tools = {"ruff"}
    pip_tools = {"pyright", "pytest", "bandit"}
    if tool in pipx_tools:
        return f"pipx install {tool}{version}"
    if tool in pip_tools:
        return f"pip install {tool}{version}"
    if tool == "gitleaks":
        return (
            "macOS: brew install gitleaks; other OS: "
            "see https://github.com/gitleaks/gitleaks#installation"
        )
    if tool == "osv-scanner":
        return (
            "macOS: brew install osv-scanner; other OS: "
            "see https://google.github.io/osv-scanner/"
        )
    return "Install via your preferred package manager."


def _suppressions_template() -> str:
    return """# VibeGate suppressions
schema_version: v1alpha1
suppressions: []
  # - fingerprint: "<stable-fingerprint>"
  #   rule_id: "RULE_ID"  # Optional: match a specific rule
  #   justification: "Why this finding is acceptable"
  #   expires_at: "2099-12-31T00:00:00Z"
  #   actor: "your-name-or-team"
"""


def _labels_template() -> str:
    return """# VibeGate labels (false positive feedback)
# Labels are for tracking finding quality and informing future rule evolution.
# They do NOT affect CI/CD behavior (use suppressions.yaml for that).
version: 1
labels: []
  # - fingerprint: "<finding-fingerprint>"
  #   rule_id: "<rule_id>"
  #   label: "false_positive"  # or "true_positive" or "acceptable_risk"
  #   reason: "<short-tag>"
  #   note: "<optional-details>"
  #   created_at: "<iso-timestamp>"
"""


if __name__ == "__main__":
    app()
