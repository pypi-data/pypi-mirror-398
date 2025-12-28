from __future__ import annotations

import asyncio
import concurrent.futures
import json
import time
from typing import Any
from unittest.mock import patch

from wolves_python.future import WolvesFuture
from wolves_python.types import ExperimentConfig, InitializeResponse, WolvesEvent, WolvesUser


class FakeNetwork:
    def __init__(self, _sdk_key: str, api: str) -> None:
        self.api = api
        self.closed = False
        self.fetch_calls: list[WolvesUser] = []
        self.next_config: InitializeResponse | None = None

    async def fetch_config(self, user: WolvesUser, since_time: int | None = None, **_: Any) -> InitializeResponse | None:
        self.fetch_calls.append(user)
        await asyncio.sleep(0)
        return self.next_config

    async def aclose(self) -> None:
        self.closed = True


class RecordingLogger:
    def __init__(self, _network: object, _runtime: object, **_: Any) -> None:
        self.events: list[WolvesEvent] = []
        self.stopped = False

    def enqueue(self, event: WolvesEvent) -> None:
        self.events.append(event)

    def stop(self) -> WolvesFuture[None]:
        self.stopped = True
        fut: concurrent.futures.Future[None] = concurrent.futures.Future()
        fut.set_result(None)
        return WolvesFuture(fut)


def test_initialize_success_and_get_experiment_logs_exposure() -> None:
    with patch("wolves_python.client.Network", FakeNetwork), patch("wolves_python.client.EventLogger", RecordingLogger):
        from wolves_python.client import WolvesClient

        client = WolvesClient("k", api="https://unit.test/api")
        user = WolvesUser(user_id="u")
        try:
            client._network.next_config = InitializeResponse(  # type: ignore[attr-defined]
                dynamic_configs={
                    "exp": ExperimentConfig(value={"k": "v"}, experiment_id="eid", group="g")
                },
                has_updates=True,
                time=1,
            )
            assert client.initialize(user).wait(timeout=2) is True

            exp = client.get_experiment(user, "exp")
            assert exp.experiment_id == "eid"
            assert exp.group_name == "g"
            assert exp.get_string("k", "d") == "v"

            events = client._logger.events  # type: ignore[attr-defined]
            exposure = next(e for e in events if e.event_name == "exposure")
            assert exposure.metadata is not None
            assert exposure.metadata["experiment_name"] == "exp"
            assert exposure.metadata["experiment_id"] == "eid"
            assert exposure.metadata["group"] == "g"
            assert json.loads(exposure.metadata["value"]) == {"k": "v"}
        finally:
            client.shutdown().wait(timeout=5)


def test_initialize_failure_returns_false() -> None:
    with patch("wolves_python.client.Network", FakeNetwork), patch("wolves_python.client.EventLogger", RecordingLogger):
        from wolves_python.client import WolvesClient

        client = WolvesClient("k", api="https://unit.test/api")
        try:
            client._network.next_config = None  # type: ignore[attr-defined]
            assert client.initialize(WolvesUser(user_id="u")).wait(timeout=2) is False
        finally:
            client.shutdown().wait(timeout=5)


def test_get_experiment_before_initialize_triggers_background_fetch() -> None:
    with patch("wolves_python.client.Network", FakeNetwork), patch("wolves_python.client.EventLogger", RecordingLogger):
        from wolves_python.client import WolvesClient

        client = WolvesClient("k", api="https://unit.test/api")
        user = WolvesUser(user_id="u")
        try:
            client._network.next_config = InitializeResponse(  # type: ignore[attr-defined]
                dynamic_configs={
                    "exp": ExperimentConfig(value={"k": "v"}, experiment_id="eid", group="g")
                },
                has_updates=True,
                time=1,
            )

            exp1 = client.get_experiment(user, "exp")
            assert exp1.get_string("k", "d") in {"d", "v"}

            for _ in range(200):
                if client._network.fetch_calls:  # type: ignore[attr-defined]
                    break
                time.sleep(0.01)
            assert client._network.fetch_calls  # type: ignore[attr-defined]

            for _ in range(200):
                exp2 = client.get_experiment(user, "exp")
                if exp2.get_string("k", "d") == "v":
                    break
                time.sleep(0.01)
            assert exp2.get_string("k", "d") == "v"
        finally:
            client.shutdown().wait(timeout=5)


def test_get_experiment_for_test_uses_group_and_store_experiment_id() -> None:
    with patch("wolves_python.client.Network", FakeNetwork), patch("wolves_python.client.EventLogger", RecordingLogger):
        from wolves_python.client import WolvesClient

        client = WolvesClient("k", api="https://unit.test/api")
        user = WolvesUser(user_id="u")
        try:
            client._network.next_config = InitializeResponse(  # type: ignore[attr-defined]
                dynamic_configs={"exp": ExperimentConfig(value={"k": "v"}, experiment_id="eid", group="g")},
                has_updates=True,
                time=1,
            )
            assert client.initialize(user).wait(timeout=2) is True

            exp = client.get_experiment_for_test("exp", "g2")
            assert exp.experiment_id == "eid"
            assert exp.group_name == "g2"
            assert exp.get_string("k", "d") == "d"

            exposure = next(e for e in client._logger.events if e.event_name == "exposure")  # type: ignore[attr-defined]
            assert exposure.metadata is not None
            assert exposure.metadata["group"] == "g2"
            assert exposure.metadata["experiment_id"] == "eid"
        finally:
            client.shutdown().wait(timeout=5)


def test_get_experiment_background_fetch_none_config_is_safe() -> None:
    with patch("wolves_python.client.Network", FakeNetwork), patch("wolves_python.client.EventLogger", RecordingLogger):
        from wolves_python.client import WolvesClient

        client = WolvesClient("k", api="https://unit.test/api")
        user = WolvesUser(user_id="u")
        try:
            client._network.next_config = None  # type: ignore[attr-defined]
            exp = client.get_experiment(user, "exp")
            assert exp.get_string("k", "d") == "d"

            for _ in range(200):
                if client._network.fetch_calls:  # type: ignore[attr-defined]
                    break
                time.sleep(0.01)
            assert client._network.fetch_calls  # type: ignore[attr-defined]

            exp2 = client.get_experiment(user, "exp")
            assert exp2.get_string("k", "d") == "d"
        finally:
            client.shutdown().wait(timeout=5)


def test_get_experiment_for_test_uses_default_user_when_uninitialized() -> None:
    with patch("wolves_python.client.Network", FakeNetwork), patch("wolves_python.client.EventLogger", RecordingLogger):
        from wolves_python.client import WolvesClient

        client = WolvesClient("k", api="https://unit.test/api")
        try:
            client.get_experiment_for_test("exp", "g")
            exposure = next(e for e in client._logger.events if e.event_name == "exposure")  # type: ignore[attr-defined]
            assert exposure.user == WolvesUser()
        finally:
            client.shutdown().wait(timeout=5)


def test_log_event_enqueues_event() -> None:
    with patch("wolves_python.client.Network", FakeNetwork), patch("wolves_python.client.EventLogger", RecordingLogger):
        from wolves_python.client import WolvesClient

        client = WolvesClient("k", api="https://unit.test/api")
        user = WolvesUser(user_id="u")
        try:
            client.log_event(user, "purchase", value=3, metadata={"k": "v"})
            evt = next(e for e in client._logger.events if e.event_name == "purchase")  # type: ignore[attr-defined]
            assert evt.value == 3
            assert evt.metadata == {"k": "v"}
            assert evt.user == user
        finally:
            client.shutdown().wait(timeout=5)


def test_shutdown_stops_logger_and_closes_network() -> None:
    with patch("wolves_python.client.Network", FakeNetwork), patch("wolves_python.client.EventLogger", RecordingLogger):
        from wolves_python.client import WolvesClient

        client = WolvesClient("k", api="https://unit.test/api")
        client.shutdown().wait(timeout=5)
        assert client._logger.stopped is True  # type: ignore[attr-defined]
        assert client._network.closed is True  # type: ignore[attr-defined]
