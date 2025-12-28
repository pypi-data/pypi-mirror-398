from __future__ import annotations

from wolves_python.store import Store
from wolves_python.types import ExperimentConfig, InitializeResponse


def test_store_missing_returns_none() -> None:
    store = Store()
    assert store.get_experiment("nope") is None
    assert store.get_last_update_time() is None
    assert store.get_values() is None


def test_store_set_and_get_experiment_and_time() -> None:
    store = Store()
    values = InitializeResponse(
        dynamic_configs={"exp": ExperimentConfig(value={"k": "v"}, experiment_id="eid", group="g")},
        has_updates=True,
        time=456,
    )
    store.set_values(values)

    cfg = store.get_experiment("exp")
    assert cfg is not None
    assert cfg.value["k"] == "v"
    assert cfg.experiment_id == "eid"
    assert cfg.group == "g"
    assert store.get_last_update_time() == 456
    assert store.get_values() == values
