from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import Iterable, List, Literal, cast


Action = Literal["block", "warn", "allow"]
Selector = Literal["severity", "check", "rule"]


@dataclass(frozen=True)
class SemanticRule:
    action: Action
    selector: Selector
    value: str
    confidences: List[str] | None = None


class SemanticPolicyError(ValueError):
    pass


def parse_semantic_rules(statements: Iterable[str]) -> List[SemanticRule]:
    rules: List[SemanticRule] = []
    for raw in statements:
        if not isinstance(raw, str) or not raw.strip():
            raise SemanticPolicyError(
                "Semantic policy entries must be non-empty strings."
            )
        tokens = shlex.split(raw)
        if len(tokens) < 3:
            raise SemanticPolicyError(
                f"Semantic policy must be 'action selector value': {raw}"
            )
        action_raw = tokens[0].lower()
        selector_raw = tokens[1].lower()
        if action_raw not in {"block", "warn", "allow"}:
            raise SemanticPolicyError(f"Unknown semantic action: {tokens[0]}")
        if selector_raw not in {"severity", "check", "rule"}:
            raise SemanticPolicyError(f"Unknown semantic selector: {tokens[1]}")

        # Type-safe after validation
        action = cast(Action, action_raw)
        selector = cast(Selector, selector_raw)
        tail = tokens[2:]
        if selector == "severity":
            severity = tail[0].lower()
            confidences: List[str] | None = None
            if len(tail) > 1:
                if tail[1].lower() != "confidence":
                    raise SemanticPolicyError(
                        f"Expected 'confidence' keyword in: {raw}"
                    )
                if len(tail) < 3:
                    raise SemanticPolicyError(f"Confidence list required in: {raw}")
                raw_list = " ".join(tail[2:])
                parts = []
                for chunk in raw_list.split(","):
                    parts.extend(chunk.split())
                confidences = [part.lower() for part in parts if part.strip()]
                if not confidences:
                    raise SemanticPolicyError(f"Confidence list required in: {raw}")
            rules.append(
                SemanticRule(
                    action=action,
                    selector=selector,
                    value=severity,
                    confidences=confidences,
                )
            )
            continue

        raw_list = " ".join(tail)
        values = []
        for chunk in raw_list.split(","):
            chunk = chunk.strip()
            if chunk:
                values.append(chunk)
        if not values:
            raise SemanticPolicyError(f"Missing selector value in: {raw}")
        for value in values:
            rules.append(SemanticRule(action=action, selector=selector, value=value))

    return rules
