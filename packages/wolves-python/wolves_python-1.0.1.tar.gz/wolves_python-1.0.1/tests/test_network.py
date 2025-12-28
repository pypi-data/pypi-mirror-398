from __future__ import annotations

import asyncio
import json

import httpx
import respx

from wolves_python.metadata import WolvesMetadataProvider
from wolves_python.network import Network
from wolves_python.types import WolvesEvent, WolvesUser


@respx.mock
def test_fetch_config_retries_on_retryable_status() -> None:
    api = "https://unit.test/api"
    route = respx.post(f"{api}/events/initialize").mock(
        side_effect=[
            httpx.Response(503, text="nope"),
            httpx.Response(
                200,
                json={"dynamic_configs": {}, "has_updates": True, "time": 10},
            ),
        ]
    )

    network = Network("sdk-key", api=api)
    try:
        resp = asyncio.run(network.fetch_config(WolvesUser(user_id="u1"), retries=1, backoff=0))
        assert resp is not None
        assert resp.time == 10
        assert route.call_count == 2
    finally:
        asyncio.run(network.aclose())


@respx.mock
def test_fetch_config_includes_since_time_when_provided() -> None:
    api = "https://unit.test/api"
    captured: dict | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={"dynamic_configs": {}, "has_updates": True, "time": 10})

    respx.post(f"{api}/events/initialize").mock(side_effect=handler)

    network = Network("sdk-key", api=api)
    try:
        resp = asyncio.run(network.fetch_config(WolvesUser(user_id="u1"), since_time=5, retries=0, backoff=0))
        assert resp is not None
    finally:
        asyncio.run(network.aclose())

    assert captured == {"user": {"userID": "u1"}, "sinceTime": 5}


@respx.mock
def test_fetch_config_returns_none_on_nonretryable_status() -> None:
    api = "https://unit.test/api"
    route = respx.post(f"{api}/events/initialize").mock(return_value=httpx.Response(401, text="nope"))

    network = Network("sdk-key", api=api)
    try:
        resp = asyncio.run(network.fetch_config(WolvesUser(user_id="u1"), retries=0, backoff=0))
        assert resp is None
        assert route.call_count == 1
    finally:
        asyncio.run(network.aclose())


@respx.mock
def test_fetch_config_returns_none_on_invalid_json_shape() -> None:
    api = "https://unit.test/api"
    respx.post(f"{api}/events/initialize").mock(return_value=httpx.Response(200, json=["not-a-dict"]))

    network = Network("sdk-key", api=api)
    try:
        resp = asyncio.run(network.fetch_config(WolvesUser(user_id="u1"), retries=0, backoff=0))
        assert resp is None
    finally:
        asyncio.run(network.aclose())


@respx.mock
def test_fetch_config_retries_on_exception_then_succeeds() -> None:
    api = "https://unit.test/api"
    route = respx.post(f"{api}/events/initialize").mock(
        side_effect=[
            httpx.ReadTimeout("boom"),
            httpx.Response(200, json={"dynamic_configs": {}, "has_updates": True, "time": 10}),
        ]
    )

    network = Network("sdk-key", api=api)
    try:
        resp = asyncio.run(network.fetch_config(WolvesUser(user_id="u1"), retries=1, backoff=0))
        assert resp is not None
        assert route.call_count == 2
    finally:
        asyncio.run(network.aclose())


@respx.mock
def test_fetch_config_negative_retries_skips_loop_returns_none() -> None:
    api = "https://unit.test/api"
    network = Network("sdk-key", api=api)
    try:
        resp = asyncio.run(network.fetch_config(WolvesUser(user_id="u1"), retries=-1, backoff=0))
        assert resp is None
    finally:
        asyncio.run(network.aclose())


@respx.mock
def test_send_events_builds_payload_and_attaches_metadata() -> None:
    api = "https://unit.test/api"
    captured: dict | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200)

    respx.post(f"{api}/events/ingest/batch").mock(side_effect=handler)

    WolvesMetadataProvider.add({"unit_test": "1"})

    network = Network("sdk-key", api=api)
    try:
        event = WolvesEvent(
            event_name="purchase",
            user=WolvesUser(user_id="abc"),
            time_ms=0,
            value=3,
            metadata={"k": "v"},
        )
        asyncio.run(network.send_events([event], retries=0, backoff=0))
    finally:
        asyncio.run(network.aclose())

    assert captured is not None
    assert captured["events"] == [
        {
            "timestamp": "1970-01-01T00:00:00.000Z",
            "event": "purchase",
            "user_id": "abc",
            "user_properties": {"userID": "abc"},
            "value": 3,
            "metadata": {"k": "v"},
        }
    ]
    assert captured["wolvesMetadata"]["sdk_type"] == "wolves-python"
    assert captured["wolvesMetadata"]["unit_test"] == "1"


@respx.mock
def test_send_events_retries_then_succeeds() -> None:
    api = "https://unit.test/api"
    route = respx.post(f"{api}/events/ingest/batch").mock(
        side_effect=[
            httpx.Response(500, text="fail"),
            httpx.Response(200),
        ]
    )

    network = Network("sdk-key", api=api)
    try:
        event = WolvesEvent(event_name="e", user=WolvesUser(user_id="u"), time_ms=0)
        asyncio.run(network.send_events([event], retries=1, backoff=0))
        assert route.call_count == 2
    finally:
        asyncio.run(network.aclose())


@respx.mock
def test_send_events_raises_on_terminal_failure() -> None:
    api = "https://unit.test/api"
    respx.post(f"{api}/events/ingest/batch").mock(return_value=httpx.Response(400, text="bad"))

    network = Network("sdk-key", api=api)
    try:
        event = WolvesEvent(event_name="e", user=WolvesUser(user_id="u"), time_ms=0)
        try:
            asyncio.run(network.send_events([event], retries=0, backoff=0))
            assert False, "Expected RuntimeError"
        except RuntimeError:
            pass
    finally:
        asyncio.run(network.aclose())


@respx.mock
def test_send_events_retries_on_exception_then_succeeds() -> None:
    api = "https://unit.test/api"
    route = respx.post(f"{api}/events/ingest/batch").mock(side_effect=[httpx.ReadTimeout("t"), httpx.Response(200)])

    network = Network("sdk-key", api=api)
    try:
        event = WolvesEvent(event_name="e", user=WolvesUser(user_id="u"), time_ms=0)
        asyncio.run(network.send_events([event], retries=1, backoff=0))
        assert route.call_count == 2
    finally:
        asyncio.run(network.aclose())


def test_send_events_negative_retries_raises_value_error() -> None:
    api = "https://unit.test/api"
    network = Network("sdk-key", api=api)
    try:
        event = WolvesEvent(event_name="e", user=WolvesUser(user_id="u"), time_ms=0)
        try:
            asyncio.run(network.send_events([event], retries=-1, backoff=0))
            assert False, "Expected ValueError"
        except ValueError:
            pass
    finally:
        asyncio.run(network.aclose())
