from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List
import time
from uuid import uuid4

from jsonschema import Draft202012Validator

from vibegate.artifacts import sha256_path
from vibegate.config import VibeGateConfig
from vibegate.schema_loader import load_schema
from vibegate import __version__


@dataclass(frozen=True)
class EvidenceRun:
    run_id: str
    started_at: str
    started_at_monotonic: float


@dataclass(frozen=True)
class RepoMetadata:
    root: str
    vcs: str
    commit: str
    dirty: bool


@dataclass(frozen=True)
class ContractMetadata:
    path: str
    sha256: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _validator(repo_root: Path) -> Draft202012Validator:
    schema = load_schema("vibegate-events.schema.json", repo_root=repo_root)
    return Draft202012Validator(schema)


def _validate_event(event: dict[str, Any], validator: Draft202012Validator) -> None:
    errors = sorted(validator.iter_errors(event), key=lambda err: err.path)
    if errors:
        messages = [
            f"{'.'.join(map(str, err.path)) or '<root>'}: {err.message}"
            for err in errors
        ]
        raise ValueError(
            "Evidence event schema validation failed:\n" + "\n".join(messages)
        )


def _repo_metadata(repo_root: Path) -> RepoMetadata:
    if (repo_root / ".git").exists():
        try:
            commit = (
                subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root)
                .decode("utf-8")
                .strip()
            )
            dirty = bool(
                subprocess.check_output(
                    ["git", "status", "--porcelain"], cwd=repo_root
                ).strip()
            )
            return RepoMetadata(
                root=str(repo_root), vcs="git", commit=commit, dirty=dirty
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return RepoMetadata(root=str(repo_root), vcs="none", commit="", dirty=False)
    return RepoMetadata(root=str(repo_root), vcs="none", commit="", dirty=False)


def _contract_metadata(config: VibeGateConfig) -> ContractMetadata:
    contract_path = config.contract_path or Path("vibegate.yaml")
    sha = sha256_path(contract_path) if contract_path.exists() else ""
    return ContractMetadata(path=str(contract_path), sha256=sha)


def _mode() -> str:
    return "ci" if os.environ.get("CI") else "local"


class EvidenceWriter:
    def __init__(self, config: VibeGateConfig, repo_root: Path) -> None:
        self.config = config
        self.repo_root = repo_root
        self.validator = _validator(repo_root)
        self.repo = _repo_metadata(repo_root)
        self.contract = _contract_metadata(config)
        self.run_id = uuid4().hex[:8]
        self.seq = 1
        self.started_at = utc_now()
        self.evidence_path = config.outputs.evidence_jsonl
        self.evidence_path.parent.mkdir(parents=True, exist_ok=True)

    def _base_event(self, event_type: str) -> dict[str, Any]:
        return {
            "schema_version": self.config.schema_version,
            "event_type": event_type,
            "run_id": self.run_id,
            "seq": self.seq,
            "ts": utc_now(),
            "repo": {
                "root": self.repo.root,
                "vcs": self.repo.vcs,
                "commit": self.repo.commit,
                "dirty": self.repo.dirty,
            },
            "contract": {
                "path": self.contract.path,
                "sha256": self.contract.sha256,
            },
        }

    def _write(self, event: dict[str, Any]) -> None:
        _validate_event(event, self.validator)
        with self.evidence_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")
        self.seq += 1

    def start_run(
        self, selected_packaging: dict[str, Any], toolchain: Iterable[dict[str, str]]
    ) -> EvidenceRun:
        event = self._base_event("run_start")
        event.update(
            {
                "vibegate": {"version": __version__, "mode": _mode()},
                "selected_packaging": selected_packaging,
                "toolchain": list(toolchain),
            }
        )
        self._write(event)
        return EvidenceRun(
            run_id=self.run_id,
            started_at=self.started_at,
            started_at_monotonic=time.monotonic(),
        )

    def tool_exec(
        self,
        check_id: str,
        tool: str,
        tool_version: str,
        argv: List[str],
        cwd: str,
        duration_ms: int,
        exit_code: int,
        artifacts: List[dict[str, str]] | None = None,
    ) -> None:
        event = self._base_event("tool_exec")
        event.update(
            {
                "check_id": check_id,
                "tool": tool,
                "tool_version": tool_version,
                "command": {
                    "argv": argv,
                    "cwd": cwd,
                    "env_allowlist": dict(self.config.determinism.env),
                },
                "duration_ms": duration_ms,
                "exit_code": exit_code,
                "artifacts": artifacts or [],
            }
        )
        self._write(event)

    def check_start(self, check_id: str, check_key: str, enabled: bool) -> None:
        event = self._base_event("check_start")
        event.update(
            {
                "check_id": check_id,
                "check_key": check_key,
                "enabled": enabled,
            }
        )
        self._write(event)

    def check_end(
        self,
        check_id: str,
        check_key: str,
        status: str,
        duration_ms: int,
        exit_code: int | None,
        skipped_reason: str | None,
        findings_count: int,
    ) -> None:
        event = self._base_event("check_end")
        event.update(
            {
                "check_id": check_id,
                "check_key": check_key,
                "status": status,
                "duration_ms": duration_ms,
                "exit_code": exit_code,
                "skipped_reason": skipped_reason,
                "findings_count": findings_count,
            }
        )
        self._write(event)

    def finding(self, payload: dict[str, Any]) -> None:
        event = self._base_event("finding")
        event.update(payload)
        self._write(event)

    def suppression_applied(self, payload: dict[str, Any]) -> None:
        event = self._base_event("suppression_applied")
        event.update(payload)
        self._write(event)

    def run_summary(
        self,
        result: str,
        duration_ms: int,
        counts: dict[str, int],
        skipped_checks: list[dict[str, str]],
        decision: dict[str, Any] | None = None,
        comparison: dict[str, Any] | None = None,
    ) -> None:
        event = self._base_event("run_summary")
        payload: dict[str, Any] = {
            "result": result,
            "duration_ms": duration_ms,
            "counts": counts,
            "skipped_checks": skipped_checks,
        }
        if decision:
            payload["decision"] = decision
        if comparison:
            payload["comparison"] = comparison
        event.update(payload)
        self._write(event)


def load_run_summary(evidence_path: Path) -> dict[str, Any] | None:
    if not evidence_path.exists():
        return None
    try:
        with evidence_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if payload.get("event_type") == "run_summary":
                    return payload
    except OSError:
        return None
    return None


def artifacts_to_records(paths: Iterable[Path]) -> List[dict[str, str]]:
    records = []
    for path in paths:
        if path.exists():
            records.append({"path": str(path), "sha256": sha256_path(path)})
    return records
