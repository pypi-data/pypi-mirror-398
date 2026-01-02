"""Enhance proposals and findings with LLM-generated explanations and fix prompts."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from vibegate.findings import Finding
from vibegate.llm.ollama import OllamaProvider
from vibegate.llm.providers import CodeContext, LLMResponse

logger = logging.getLogger(__name__)


def create_llm_provider_from_config(llm_config: Any) -> OllamaProvider | None:
    """Create an LLM provider from configuration.

    Args:
        llm_config: LLMConfig from VibeGateConfig

    Returns:
        Initialized provider or None if LLM not enabled
    """
    if llm_config is None or not llm_config.enabled:
        return None

    if llm_config.provider != "ollama":
        logger.warning(f"Unsupported LLM provider: {llm_config.provider}")
        return None

    try:
        provider = OllamaProvider(
            model=llm_config.ollama.model,
            base_url=llm_config.ollama.base_url,
            cache_dir=llm_config.cache_dir,
            temperature=llm_config.ollama.temperature,
        )

        # Check if available
        if not provider.is_available():
            logger.warning(
                f"Ollama provider not available (model: {llm_config.ollama.model})"
            )
            return None

        return provider

    except Exception as e:
        logger.error(f"Failed to create LLM provider: {e}")
        return None


def enhance_finding_with_llm(
    finding: Finding,
    provider: OllamaProvider,
    code_snippet: str | None = None,
    surrounding_lines: list[str] | None = None,
) -> dict[str, str | bool]:
    """Enhance a finding with LLM-generated explanation and fix prompt.

    Args:
        finding: The finding to enhance
        provider: LLM provider instance
        code_snippet: Optional code snippet showing the issue
        surrounding_lines: Optional surrounding code context

    Returns:
        Dictionary with 'explanation', 'fix_prompt', and 'cached' keys
    """
    try:
        # Build code context
        context = None
        if finding.location and finding.location.path:
            context = CodeContext(
                file_path=Path(finding.location.path),
                line_number=finding.location.line,
                code_snippet=code_snippet,
                surrounding_lines=surrounding_lines,
            )

        # Generate LLM response
        response: LLMResponse = provider.process_finding(finding, context)

        return {
            "explanation": response.explanation,
            "fix_prompt": response.fix_prompt,
            "cached": response.cached,
        }

    except Exception as e:
        logger.error(f"Failed to enhance finding with LLM: {e}")
        return {
            "explanation": "",
            "fix_prompt": "",
            "cached": False,
        }


def enhance_cluster_with_llm(
    cluster: Dict[str, Any],
    provider: OllamaProvider,
) -> dict[str, str]:
    """Enhance a tuning cluster with LLM-generated explanation.

    This creates a synthetic "cluster finding" to explain the pattern.

    Args:
        cluster: Cluster data from tuning
        provider: LLM provider instance

    Returns:
        Dictionary with 'explanation' and 'summary' keys
    """
    try:
        # Create a synthetic finding representing the cluster pattern
        from vibegate.findings import Finding

        rule_id = cluster.get("rule_id", "unknown")
        count = cluster.get("count", 0)
        trigger_sig = cluster.get("trigger_signature", "")
        action_hints = cluster.get("action_hints", [])
        top_dirs = cluster.get("top_directories", [])

        # Build message describing the cluster
        message_parts = [
            f"Rule {rule_id} triggered {count} false positives.",
            f"Pattern: {trigger_sig}" if trigger_sig else "",
        ]

        if action_hints:
            message_parts.append(f"Common context: {', '.join(action_hints[:3])}")

        if top_dirs:
            dir_names = []
            for d in top_dirs[:3]:
                if isinstance(d, dict):
                    dir_names.append(d.get("directory", "unknown"))
                elif isinstance(d, tuple) and len(d) >= 1:
                    dir_names.append(d[0])
                else:
                    dir_names.append(str(d))
            dir_summary = ", ".join(dir_names)
            message_parts.append(f"Most affected directories: {dir_summary}")

        message = " ".join([p for p in message_parts if p])

        # Create synthetic finding
        finding = Finding(
            check_id="cluster",
            finding_type="false_positive_pattern",
            rule_id=rule_id,
            severity="info",
            message=message,
            fingerprint=cluster.get("cluster_id", ""),
            tool="tuning",
            remediation_hint=action_hints[0] if action_hints else None,
            location=None,
        )

        # Generate explanation using LLM
        response = provider.explain_finding(finding)

        return {
            "explanation": response,
            "summary": f"Cluster of {count} false positives for rule {rule_id}",
        }

    except Exception as e:
        logger.error(f"Failed to enhance cluster with LLM: {e}")
        return {
            "explanation": "",
            "summary": "Cluster of false positives",
        }


def generate_cluster_fix_prompt(
    cluster: Dict[str, Any],
    rule_refinement_suggestion: str,
    provider: OllamaProvider,
) -> str:
    """Generate a detailed fix prompt for addressing a cluster of false positives.

    Args:
        cluster: Cluster data from tuning
        rule_refinement_suggestion: The rule refinement suggestion
        provider: LLM provider instance

    Returns:
        LLM-generated fix prompt
    """
    try:
        from vibegate.findings import Finding

        rule_id = cluster.get("rule_id", "unknown")
        count = cluster.get("count", 0)
        action_hints = cluster.get("action_hints", [])

        # Build context message for LLM
        context_parts = [
            f"You need to refine the detection rule '{rule_id}' which is producing {count} false positives.",
            f"Suggested refinement: {rule_refinement_suggestion}",
        ]

        if action_hints:
            context_parts.append(
                f"Common patterns in false positives: {', '.join(action_hints[:5])}"
            )

        context_message = "\n".join(context_parts)

        # Create synthetic finding for prompt generation
        finding = Finding(
            check_id="cluster_fix",
            finding_type="rule_refinement",
            rule_id=rule_id,
            severity="info",
            message=context_message,
            fingerprint=cluster.get("cluster_id", ""),
            tool="tuning",
            remediation_hint=rule_refinement_suggestion,
            location=None,
        )

        # Build context
        context = CodeContext(
            file_path=Path(
                "vibegate/checks.py"
            ),  # Placeholder - actual file depends on check type
            line_number=None,
            code_snippet=None,
            surrounding_lines=None,
        )

        # Generate fix prompt
        fix_prompt = provider.generate_fix_prompt(finding, context)

        return fix_prompt

    except Exception as e:
        logger.error(f"Failed to generate cluster fix prompt: {e}")
        return rule_refinement_suggestion  # Fallback to basic suggestion
