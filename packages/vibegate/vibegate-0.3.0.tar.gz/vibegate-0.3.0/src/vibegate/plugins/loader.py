from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
import logging
from typing import Any, Dict, Iterable, Sequence

from vibegate.config import PluginGroupConfig


@dataclass(frozen=True)
class LoadedPlugin:
    name: str
    plugin: Any
    config: Dict[str, Any]


def _entry_points_for_group(group: str) -> Sequence[metadata.EntryPoint]:
    entry_points = metadata.entry_points()
    if hasattr(entry_points, "select"):
        return list(entry_points.select(group=group))
    if isinstance(entry_points, dict):
        return list(entry_points.get(group, []))
    return [entry_point for entry_point in entry_points if entry_point.group == group]


def _configured_names(config: PluginGroupConfig) -> set[str]:
    return set(config.enabled) | set(config.config.keys())


def _desired_names(config: PluginGroupConfig, available: Iterable[str]) -> list[str]:
    disabled = set(config.disabled)
    if config.enabled:
        return [name for name in config.enabled if name not in disabled]
    return [name for name in sorted(available) if name not in disabled]


def load_plugins(
    group: str,
    config: PluginGroupConfig,
    logger: logging.Logger,
) -> list[LoadedPlugin]:
    entry_points = _entry_points_for_group(group)
    entry_point_map = {entry_point.name: entry_point for entry_point in entry_points}

    for name in sorted(_configured_names(config)):
        if name not in entry_point_map:
            logger.warning(
                "Configured plugin '%s' for group '%s' cannot be loaded (entry point not found).",
                name,
                group,
            )

    loaded: list[LoadedPlugin] = []
    for name in _desired_names(config, entry_point_map.keys()):
        entry_point = entry_point_map.get(name)
        if entry_point is None:
            logger.warning(
                "Configured plugin '%s' for group '%s' cannot be loaded (entry point not found).",
                name,
                group,
            )
            continue
        try:
            plugin = entry_point.load()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to load plugin '%s' from group '%s': %s",
                name,
                group,
                exc,
            )
            continue
        loaded.append(
            LoadedPlugin(
                name=name,
                plugin=plugin,
                config=dict(config.config.get(name, {})),
            )
        )
    return loaded
