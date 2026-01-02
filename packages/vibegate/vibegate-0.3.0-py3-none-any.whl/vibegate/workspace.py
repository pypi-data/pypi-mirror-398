from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable, List, Sequence

DEFAULT_EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "env",
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".tox",
    ".eggs",
    "site-packages",
}

DEFAULT_EXCLUDE_GLOBS = [
    ".venv/**",
    "venv/**",
    "env/**",
    ".git/**",
    "__pycache__/**",
    ".pytest_cache/**",
    ".mypy_cache/**",
    ".ruff_cache/**",
    "node_modules/**",
    "dist/**",
    "build/**",
    ".tox/**",
    ".eggs/**",
    "site-packages/**",
    "*.egg-info/**",
]


def _is_default_excluded(rel_path: Path) -> bool:
    for part in rel_path.parts:
        if part in DEFAULT_EXCLUDE_DIRS or part.endswith(".egg-info"):
            return True
    return any(rel_path.match(pattern) for pattern in DEFAULT_EXCLUDE_GLOBS)


def _walk_files(repo_root: Path) -> List[Path]:
    files: list[Path] = []
    for root, dirs, filenames in os.walk(repo_root, topdown=True):
        rel_root = Path(root).relative_to(repo_root)
        dirs[:] = [name for name in dirs if not _is_default_excluded(rel_root / name)]
        for name in filenames:
            rel_path = (rel_root / name) if rel_root.parts else Path(name)
            if _is_default_excluded(rel_path):
                continue
            files.append(Path(root) / name)
    return files


def collect_workspace_files(repo_root: Path) -> List[Path]:
    git_dir = repo_root / ".git"
    files: list[Path] = []
    if git_dir.exists():
        try:
            result = subprocess.run(
                ["git", "ls-files", "-z"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.SubprocessError):
            files = _walk_files(repo_root)
        else:
            for entry in result.stdout.split("\x00"):
                if not entry:
                    continue
                files.append(repo_root / entry)
    else:
        files = _walk_files(repo_root)

    filtered = []
    for path in files:
        if not path.is_file():
            continue
        rel_path = path.relative_to(repo_root)
        if _is_default_excluded(rel_path):
            continue
        filtered.append(path)
    return sorted(filtered, key=lambda item: item.as_posix())


def filter_workspace_files(
    workspace_files: Sequence[Path],
    repo_root: Path,
    include_globs: Iterable[str],
    exclude_globs: Iterable[str],
) -> List[Path]:
    import fnmatch

    include = list(include_globs)
    exclude = list(exclude_globs)
    filtered: list[Path] = []
    for path in workspace_files:
        rel = path.relative_to(repo_root).as_posix()
        if include and not any(fnmatch.fnmatch(rel, pattern) for pattern in include):
            continue
        if exclude and any(fnmatch.fnmatch(rel, pattern) for pattern in exclude):
            continue
        filtered.append(path)
    return sorted(filtered, key=lambda item: item.as_posix())
