from __future__ import annotations

import threading

from .types import ExperimentConfig, InitializeResponse


class Store:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._values: InitializeResponse | None = None

    def set_values(self, values: InitializeResponse) -> None:
        with self._lock:
            self._values = values

    def get_experiment(self, name: str) -> ExperimentConfig | None:
        with self._lock:
            if not self._values:
                return None
            return self._values.dynamic_configs.get(name)

    def get_values(self) -> InitializeResponse | None:
        with self._lock:
            return self._values

    def get_last_update_time(self) -> int | None:
        with self._lock:
            return self._values.time if self._values else None
