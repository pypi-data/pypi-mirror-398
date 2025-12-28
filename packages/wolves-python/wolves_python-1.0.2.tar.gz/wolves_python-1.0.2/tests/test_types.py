from __future__ import annotations

from wolves_python.types import (
    ExperimentConfig,
    InitializeResponse,
    WolvesEvent,
    WolvesUser,
    build_ingest_event,
    ms_to_iso8601_utc,
)


def test_wolves_user_to_api_dict_matches_js_shape() -> None:
    user = WolvesUser(
        user_id="u1",
        email="e@example.com",
        ip="127.0.0.1",
        custom={"flag": True, "n": 2, "tags": ["a", "b"], "s": "x"},
    )
    assert user.to_api_dict() == {
        "userID": "u1",
        "email": "e@example.com",
        "ip": "127.0.0.1",
        "custom": {"flag": True, "n": 2, "tags": ["a", "b"], "s": "x"},
    }


def test_wolves_user_to_api_dict_omits_none_fields() -> None:
    user = WolvesUser(email="e@example.com")
    assert user.to_api_dict() == {"email": "e@example.com"}


def test_ms_to_iso8601_utc_matches_toISOString_millis() -> None:
    assert ms_to_iso8601_utc(0) == "1970-01-01T00:00:00.000Z"


def test_build_ingest_event_uses_user_id_field_name() -> None:
    user = WolvesUser(user_id="abc")
    event = WolvesEvent(event_name="purchase", user=user, time_ms=0, value=3, metadata={"k": "v"})
    assert build_ingest_event(event) == {
        "timestamp": "1970-01-01T00:00:00.000Z",
        "event": "purchase",
        "user_id": "abc",
        "user_properties": {"userID": "abc"},
        "value": 3,
        "metadata": {"k": "v"},
    }


def test_initialize_response_and_experiment_config_parsing() -> None:
    payload = {
        "dynamic_configs": {
            "exp": {"value": {"a": 1}, "experiment_id": "eid", "group": "g"},
            "bad1": None,
            2: {"value": {"x": 1}},
        },
        "has_updates": True,
        "time": 123,
    }
    resp = InitializeResponse.from_api_dict(payload)
    assert resp.has_updates is True
    assert resp.time == 123
    assert resp.dynamic_configs["exp"] == ExperimentConfig(value={"a": 1}, experiment_id="eid", group="g")


def test_experiment_config_from_api_dict_invalid_types_defaulted() -> None:
    cfg = ExperimentConfig.from_api_dict({"value": "nope", "experiment_id": 1, "group": True})
    assert cfg.value == {}
    assert cfg.experiment_id is None
    assert cfg.group is None


def test_initialize_response_from_api_dict_invalid_dynamic_configs_defaulted() -> None:
    resp = InitializeResponse.from_api_dict({"dynamic_configs": "nope", "has_updates": 0, "time": "x"})
    assert resp.dynamic_configs == {}
    assert resp.has_updates is False
    assert resp.time == 0
