from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class FindingLocation:
    path: str | None = None
    line: int | None = None
    col: int | None = None
    end_line: int | None = None
    end_col: int | None = None

    def to_payload(self) -> Dict[str, Any] | None:
        if not self.path:
            return None
        payload: Dict[str, Any] = {"path": self.path}
        if self.line is not None:
            payload["line"] = self.line
        if self.col is not None:
            payload["col"] = self.col
        if self.end_line is not None:
            payload["end_line"] = self.end_line
        if self.end_col is not None:
            payload["end_col"] = self.end_col
        return payload


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

    def event_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "check_id": self.check_id,
            "finding_type": self.finding_type,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "fingerprint": self.fingerprint,
            "confidence": self.confidence,
            "rule_version": self.rule_version,
        }
        if self.tool:
            payload["tool"] = self.tool
        if self.remediation_hint:
            payload["remediation_hint"] = self.remediation_hint
        if self.location:
            location_payload = self.location.to_payload()
            if location_payload:
                payload["location"] = location_payload
        if self.trigger_explanation:
            payload["trigger_explanation"] = self.trigger_explanation
        if self.ast_node_type:
            payload["ast_node_type"] = self.ast_node_type
        if self.in_type_annotation is not None:
            payload["in_type_annotation"] = self.in_type_annotation
        return payload
