from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class WolvesUser:
    user_id: str | None = None
    email: str | None = None
    ip: str | None = None
    custom: Mapping[str, str | int | bool | list[str]] = field(default_factory=dict)

    def to_api_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.user_id is not None:
            payload["userID"] = self.user_id
        if self.email is not None:
            payload["email"] = self.email
        if self.ip is not None:
            payload["ip"] = self.ip
        if self.custom:
            payload["custom"] = dict(self.custom)
        return payload


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    value: Mapping[str, Any]
    experiment_id: str | None = None
    group: str | None = None

    @staticmethod
    def from_api_dict(payload: Mapping[str, Any]) -> ExperimentConfig:
        raw_value = payload.get("value") or {}
        value: Mapping[str, Any] = raw_value if isinstance(raw_value, Mapping) else {}

        experiment_id = payload.get("experiment_id")
        if not isinstance(experiment_id, str):
            experiment_id = None

        group = payload.get("group")
        if not isinstance(group, str):
            group = None

        return ExperimentConfig(value=value, experiment_id=experiment_id, group=group)


@dataclass(frozen=True, slots=True)
class InitializeResponse:
    dynamic_configs: Mapping[str, ExperimentConfig]
    has_updates: bool
    time: int

    @staticmethod
    def from_api_dict(payload: Mapping[str, Any]) -> InitializeResponse:
        raw_dynamic_configs = payload.get("dynamic_configs") or {}
        if not isinstance(raw_dynamic_configs, Mapping):
            raw_dynamic_configs = {}

        dynamic_configs: dict[str, ExperimentConfig] = {}
        for name, cfg in raw_dynamic_configs.items():
            if not isinstance(name, str) or not isinstance(cfg, Mapping):
                continue
            dynamic_configs[name] = ExperimentConfig.from_api_dict(cfg)

        has_updates = bool(payload.get("has_updates"))

        raw_time = payload.get("time")
        time = int(raw_time) if isinstance(raw_time, (int, float)) else 0

        return InitializeResponse(dynamic_configs=dynamic_configs, has_updates=has_updates, time=time)


@dataclass(frozen=True, slots=True)
class WolvesEvent:
    event_name: str
    user: WolvesUser | None
    time_ms: int
    value: str | float | int | None = None
    metadata: Mapping[str, str] | None = None


def ms_to_iso8601_utc(time_ms: int) -> str:
    dt = datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build_ingest_event(event: WolvesEvent) -> dict[str, Any]:
    user_properties: dict[str, Any] = event.user.to_api_dict() if event.user else {}
    user_id = event.user.user_id if event.user and event.user.user_id else ""

    payload: dict[str, Any] = {
        "timestamp": ms_to_iso8601_utc(event.time_ms),
        "event": event.event_name,
        "user_id": user_id,
        "user_properties": user_properties,
    }

    if event.value is not None:
        payload["value"] = event.value
    if event.metadata is not None:
        payload["metadata"] = dict(event.metadata)

    return payload
