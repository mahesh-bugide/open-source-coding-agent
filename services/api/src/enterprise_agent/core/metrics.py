from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass(slots=True)
class MetricsStore:
    counters: Counter[str] = field(default_factory=Counter)
    totals: Counter[str] = field(default_factory=Counter)

    def inc(self, key: str, value: int = 1) -> None:
        self.counters[key] += value

    def add(self, key: str, value: int) -> None:
        self.totals[key] += value

    def snapshot(self) -> dict:
        return {
            "counters": dict(self.counters),
            "totals": dict(self.totals),
        }
