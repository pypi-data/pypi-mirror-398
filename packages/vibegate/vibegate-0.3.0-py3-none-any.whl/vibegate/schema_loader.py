from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from importlib import resources


class SchemaError(RuntimeError):
    pass


def load_schema(filename: str, repo_root: Path | None = None) -> dict[str, Any]:
    candidates = []
    if repo_root is not None:
        candidates.append(repo_root / "schema" / filename)
    candidates.append(Path.cwd() / "schema" / filename)

    for candidate in candidates:
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))

    try:
        with (
            resources.files("vibegate.schemas")
            .joinpath(filename)
            .open("r", encoding="utf-8") as handle
        ):
            return json.load(handle)
    except FileNotFoundError as exc:
        raise SchemaError(f"Schema {filename} not found.") from exc
