"""Plugin interfaces and types for VibeGate."""

from vibegate.plugins.api import CheckPlugin, EmitterPlugin, EvidenceHook, PluginContext
from vibegate.plugins.types import Finding, FindingLocation, FixpackTask, Remediation

__all__ = [
    "CheckPlugin",
    "EmitterPlugin",
    "EvidenceHook",
    "PluginContext",
    "Finding",
    "FindingLocation",
    "FixpackTask",
    "Remediation",
]
