from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Experiment:
    name: str
    value: Mapping[str, Any]
    experiment_id: str
    group_name: str | None

    def get(self, key: str, default: T) -> T:
        val = self.value.get(key)
        if val is None:
            return default
        return val  # type: ignore[return-value]

    def get_string(self, key: str, default: str) -> str:
        val = self.value.get(key)
        if val is None:
            return default
        return val if isinstance(val, str) else default

    def get_bool(self, key: str, default: bool) -> bool:
        val = self.value.get(key)
        if val is None:
            return default
        return val if isinstance(val, bool) else default

    def get_float(self, key: str, default: float) -> float:
        val = self.value.get(key)
        if val is None:
            return default
        if isinstance(val, (int, float)):
            return float(val)
        return default

