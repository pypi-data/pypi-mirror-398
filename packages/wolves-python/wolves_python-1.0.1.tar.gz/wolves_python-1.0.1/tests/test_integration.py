from __future__ import annotations

import os

import pytest

from wolves_python import WolvesClient, WolvesUser

API_KEY = "apikey-011a5eea-c25c-4d51-87f6-3155267fc6cc"


def _skip_unless_enabled() -> None:
    if os.environ.get("WOLVES_RUN_INTEGRATION") != "1":
        pytest.skip("Set WOLVES_RUN_INTEGRATION=1 to run integration tests")


@pytest.mark.integration
def test_integration_initialize_and_get_experiment() -> None:
    _skip_unless_enabled()

    client = WolvesClient(API_KEY)
    user = WolvesUser(user_id="test_user")
    try:
        assert client.initialize(user).wait(timeout=30) is True

        exp = client.get_experiment(user, "rongyu-test-exp")
        group = exp.group_name or ""
        param1 = exp.get_string("test-param1", "")
        param2 = exp.get_float("test-param2", 0.0)

        expected = {
            ("control-group", 1.0),
            ("test-group", 2.0),
            ("other-group", 3.0),
        }
        assert (param1, param2) in expected, f"Unexpected group/value: group={group} param1={param1} param2={param2}"
    finally:
        client.shutdown().wait(timeout=30)


@pytest.mark.integration
def test_integration_exposure_and_event_ingestion_succeeds() -> None:
    _skip_unless_enabled()

    client = WolvesClient(API_KEY)
    user = WolvesUser(user_id="test_user")
    try:
        assert client.initialize(user).wait(timeout=30) is True

        client.get_experiment(user, "rongyu-test-exp")
        client.log_event(user, "sdk-integration-test", value=1, metadata={"ok": "true"})

        client.shutdown().wait(timeout=30)
        assert client._logger._last_flush_success is True  # type: ignore[attr-defined]
    finally:
        # shutdown is idempotent in this SDK (subsequent calls no-op for stopped runtime)
        pass
