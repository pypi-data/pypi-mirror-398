"""Prompt templates for LLM-based finding explanations and fix generation."""

from __future__ import annotations

from vibegate.findings import Finding
from vibegate.llm.providers import CodeContext


def build_explanation_prompt(finding: Finding) -> str:
    """Build a prompt for explaining a finding in user-friendly language.

    Args:
        finding: The finding to explain

    Returns:
        Prompt string for the LLM
    """
    prompt = f"""You are a helpful coding assistant explaining code quality issues in a friendly, approachable way.

Explain this code issue to a developer:

Check Type: {finding.check_id}
Issue Type: {finding.finding_type}
Rule: {finding.rule_id or "N/A"}
Severity: {finding.severity}
Message: {finding.message}
Tool: {finding.tool}
"""

    if finding.location:
        prompt += f"Location: {finding.location.path}"
        if finding.location.line:
            prompt += f" (line {finding.location.line})"
        prompt += "\n"

    if finding.remediation_hint:
        prompt += f"Hint: {finding.remediation_hint}\n"

    prompt += """
Your explanation should:
1. Use plain English (avoid jargon where possible)
2. Use a friendly, conversational tone
3. Include a real-world analogy or metaphor to make it relatable
4. Explain WHY this matters (not just what it is)
5. Be concise (2-4 sentences)
6. Make it feel approachable and not intimidating

Example style: "You imported 'List' from typing but never used it. This is like buying groceries you don't cook with - it clutters your code and makes it harder to see what your module really needs."

Now explain the issue above:"""

    return prompt


def build_fix_prompt(finding: Finding, context: CodeContext | None) -> str:
    """Build a prompt for generating a fix for a vibe coding assistant.

    Args:
        finding: The finding to fix
        context: Code context including file path, snippets, etc.

    Returns:
        Detailed fix prompt string for the LLM
    """
    prompt = f"""You are a coding assistant generating precise fix instructions for another AI coding tool.

Generate a detailed, step-by-step fix prompt for this code issue:

Check Type: {finding.check_id}
Issue Type: {finding.finding_type}
Rule: {finding.rule_id or "N/A"}
Severity: {finding.severity}
Message: {finding.message}
Tool: {finding.tool}
"""

    if context:
        prompt += f"\nFile: {context.file_path}"
        if context.line_number:
            prompt += f"\nLine: {context.line_number}"

        if context.code_snippet:
            prompt += f"\n\nCurrent code:\n```python\n{context.code_snippet}\n```"

        if context.surrounding_lines:
            prompt += "\n\nSurrounding context:\n```python\n"
            prompt += "\n".join(context.surrounding_lines)
            prompt += "\n```"
    elif finding.location:
        prompt += f"\nFile: {finding.location.path}"
        if finding.location.line:
            prompt += f"\nLine: {finding.location.line}"

    if finding.remediation_hint:
        prompt += f"\n\nRemediation hint: {finding.remediation_hint}"

    prompt += """

Generate a fix prompt that includes:
1. Exact file path and line number
2. Clear description of what needs to change
3. Specific action items (be explicit - show before/after if helpful)
4. Verification steps to run after the fix
5. Any important context about VibeGate's determinism and quality standards

Format the output as a clear, actionable prompt that can be copy-pasted directly to an AI coding assistant like Claude Code or GitHub Copilot.

Example format:
"In src/auth/models.py at line 3, remove the unused import.

Current code (line 3):
from typing import List, Dict, Optional

Change it to:
from typing import Dict, Optional

After this change:
1. Run: pyright src/auth/models.py (should pass)
2. Run: pytest tests/test_auth.py (should pass)
3. Verify no other files import these through this module"

Now generate the fix prompt:"""

    return prompt


def build_combined_prompt(finding: Finding, context: CodeContext | None) -> str:
    """Build a combined prompt for both explanation and fix generation.

    This is more efficient than making two separate LLM calls.

    Args:
        finding: The finding to process
        context: Code context

    Returns:
        Prompt that requests both explanation and fix
    """
    prompt = f"""You are a helpful coding assistant. Analyze this code quality issue and provide both a friendly explanation AND a detailed fix prompt.

Issue Details:
Check Type: {finding.check_id}
Issue Type: {finding.finding_type}
Rule: {finding.rule_id or "N/A"}
Severity: {finding.severity}
Message: {finding.message}
Tool: {finding.tool}
"""

    if context:
        prompt += f"\nFile: {context.file_path}"
        if context.line_number:
            prompt += f"\nLine: {context.line_number}"

        if context.code_snippet:
            prompt += f"\n\nCurrent code:\n```python\n{context.code_snippet}\n```"
    elif finding.location:
        prompt += f"\nFile: {finding.location.path}"
        if finding.location.line:
            prompt += f"\nLine: {finding.location.line}"

    if finding.remediation_hint:
        prompt += f"\n\nRemediation hint: {finding.remediation_hint}"

    prompt += """

Please provide TWO sections in your response:

## EXPLANATION
A friendly, 2-4 sentence explanation for developers. Use plain English, include a relatable analogy, and explain why this matters. Make it approachable and not intimidating.

## FIX PROMPT
A detailed, step-by-step fix instruction that can be copy-pasted to an AI coding assistant. Include:
- Exact file path and line number
- What needs to change (show before/after if helpful)
- Verification steps to run after the fix
- Any important context

Format your response exactly as shown above with the two section headers."""

    return prompt
