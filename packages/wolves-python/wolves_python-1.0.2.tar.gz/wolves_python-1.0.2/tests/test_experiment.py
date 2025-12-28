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


def test_experiment_get_integer() -> None:
    exp = Experiment(
        name="exp",
        value={"i": 42, "f": 3.0, "f2": 3.5, "b": True, "s": "x"},
        experiment_id="",
        group_name=None,
    )
    assert exp.get_integer("i", 0) == 42
    assert exp.get_integer("f", 0) == 3  # float with integer value
    assert exp.get_integer("f2", 0) == 0  # float with non-integer value returns default
    assert exp.get_integer("b", 0) == 0  # bool is not treated as int
    assert exp.get_integer("missing", 99) == 99
    assert exp.get_integer("s", 0) == 0


def test_experiment_get_array_json() -> None:
    exp = Experiment(
        name="exp",
        value={"arr": [1, 2, 3], "nested": [{"a": 1}, {"b": 2}], "s": "x", "d": {"k": "v"}},
        experiment_id="",
        group_name=None,
    )
    assert exp.get_array_json("arr", "[]") == "[1, 2, 3]"
    assert exp.get_array_json("nested", "[]") == '[{"a": 1}, {"b": 2}]'
    assert exp.get_array_json("missing", "[]") == "[]"
    assert exp.get_array_json("s", "[]") == "[]"  # string is not an array
    assert exp.get_array_json("d", "[]") == "[]"  # dict is not an array


def test_experiment_get_object_json() -> None:
    exp = Experiment(
        name="exp",
        value={"obj": {"a": 1, "b": "x"}, "arr": [1, 2], "s": "x"},
        experiment_id="",
        group_name=None,
    )
    assert exp.get_object_json("obj", "{}") == '{"a": 1, "b": "x"}'
    assert exp.get_object_json("missing", "{}") == "{}"
    assert exp.get_object_json("arr", "{}") == "{}"  # array is not an object
    assert exp.get_object_json("s", "{}") == "{}"  # string is not an object
