from __future__ import annotations

from wolves_python.experiment import Experiment


def test_experiment_get_defaulting() -> None:
    exp = Experiment(
        name="exp",
        value={"a": 1, "b": None, "s": "x"},
        experiment_id="eid",
        group_name="g",
    )
    assert exp.get("a", 0) == 1
    assert exp.get("missing", 7) == 7
    assert exp.get("b", 9) == 9


def test_experiment_get_string() -> None:
    exp = Experiment(name="exp", value={"s": "x", "n": 1}, experiment_id="", group_name=None)
    assert exp.get_string("s", "d") == "x"
    assert exp.get_string("missing", "d") == "d"
    assert exp.get_string("n", "d") == "d"


def test_experiment_get_bool() -> None:
    exp = Experiment(name="exp", value={"b": True, "s": "x"}, experiment_id="", group_name=None)
    assert exp.get_bool("b", False) is True
    assert exp.get_bool("missing", True) is True
    assert exp.get_bool("s", True) is True


def test_experiment_get_float() -> None:
    exp = Experiment(name="exp", value={"f": 1.5, "i": 2, "s": "x"}, experiment_id="", group_name=None)
    assert exp.get_float("f", 0.0) == 1.5
    assert exp.get_float("i", 0.0) == 2.0
    assert exp.get_float("missing", 3.0) == 3.0
    assert exp.get_float("s", 4.0) == 4.0
