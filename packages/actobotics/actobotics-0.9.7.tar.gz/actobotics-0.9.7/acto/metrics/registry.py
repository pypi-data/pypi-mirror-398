from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MetricsRegistry:
    counters: dict[str, int] = field(default_factory=dict)

    def inc(self, name: str, amount: int = 1) -> None:
        self.counters[name] = int(self.counters.get(name, 0) + amount)

    def render_prometheus(self) -> str:
        lines = []
        for k, v in sorted(self.counters.items()):
            metric = k.replace("-", "_").replace(".", "_")
            lines.append(f"# TYPE {metric} counter")
            lines.append(f"{metric} {v}")
        return "\n".join(lines) + "\n"
