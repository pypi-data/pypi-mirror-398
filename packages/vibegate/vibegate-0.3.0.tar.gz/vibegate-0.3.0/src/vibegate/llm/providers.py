"""LLM provider interface for VibeGate."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from vibegate.findings import Finding


@dataclass
class CodeContext:
    """Context information for generating fix prompts."""

    file_path: Path
    line_number: int | None
    code_snippet: str | None
    surrounding_lines: list[str] | None


@dataclass
class LLMResponse:
    """Response from LLM provider."""

    explanation: str
    fix_prompt: str
    model_used: str
    cached: bool = False


class LLMProvider(Protocol):
    """Protocol for LLM providers that can explain findings and generate fix prompts."""

    def explain_finding(self, finding: Finding) -> str:
        """Generate a user-friendly explanation of a finding.

        Args:
            finding: The finding to explain

        Returns:
            A plain-English explanation of what the issue is and why it matters
        """
        ...

    def generate_fix_prompt(self, finding: Finding, context: CodeContext) -> str:
        """Generate a detailed fix prompt for AI coding assistants.

        Args:
            finding: The finding to generate a fix for
            context: Code context including file path, snippet, etc.

        Returns:
            A detailed, actionable prompt for fixing the issue
        """
        ...

    def process_finding(
        self, finding: Finding, context: CodeContext | None = None
    ) -> LLMResponse:
        """Process a finding and generate both explanation and fix prompt.

        Args:
            finding: The finding to process
            context: Optional code context for better fix prompts

        Returns:
            LLMResponse with explanation and fix prompt
        """
        ...

    def is_available(self) -> bool:
        """Check if the LLM provider is available and ready to use.

        Returns:
            True if provider is ready, False otherwise
        """
        ...

    def get_model_info(self) -> dict[str, str]:
        """Get information about the current model.

        Returns:
            Dictionary with model name, version, and other metadata
        """
        ...
