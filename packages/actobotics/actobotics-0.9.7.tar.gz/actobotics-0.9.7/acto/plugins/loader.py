from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata


@dataclass
class PluginInfo:
    name: str
    version: str
    entrypoint: str


class PluginLoader:
    GROUP = "acto.plugins"

    def list_plugins(self) -> list[PluginInfo]:
        plugins: list[PluginInfo] = []
        eps = metadata.entry_points()
        group = eps.select(group=self.GROUP) if hasattr(eps, "select") else eps.get(self.GROUP, [])
        for ep in group:
            try:
                dist = metadata.distribution(ep.dist.name) if ep.dist else None
                version = dist.version if dist else "unknown"
            except Exception:
                version = "unknown"
            plugins.append(PluginInfo(name=ep.name, version=version, entrypoint=f"{ep.module}:{ep.attr}"))
        return plugins
