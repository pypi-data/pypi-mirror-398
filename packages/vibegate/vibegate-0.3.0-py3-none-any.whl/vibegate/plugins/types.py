from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class FindingLocation:
    path: str | None = None
    line: int | None = None
    col: int | None = None
    end_line: int | None = None
    end_col: int | None = None


@dataclass(frozen=True)
class Finding:
    check_id: str
    finding_type: str
    rule_id: str
    severity: str
    message: str
    fingerprint: str
    confidence: str = "high"
    rule_version: str = "1"
    tool: str | None = None
    remediation_hint: str | None = None
    location: FindingLocation | None = None
    trigger_explanation: str | None = None
    ast_node_type: str | None = None
    in_type_annotation: bool | None = None


@dataclass(frozen=True)
class Remediation:
    title: str
    description: str | None = None
    commands: Sequence[str] = field(default_factory=tuple)
    file_targets: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class FixpackTask:
    task_id: str
    task_type: str
    order: int
    title: str
    description: str | None = None
    file_targets: Sequence[str] = field(default_factory=tuple)
    references: Sequence[str] = field(default_factory=tuple)
    depends_on: Sequence[str] = field(default_factory=tuple)
    acceptance_criteria: Sequence[str] = field(default_factory=tuple)
    verification_commands: Sequence[str] = field(default_factory=tuple)
    ai_prompt_hint: str | None = None
