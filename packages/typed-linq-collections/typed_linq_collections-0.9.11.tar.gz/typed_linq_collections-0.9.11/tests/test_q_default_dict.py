from __future__ import annotations

import pytest

from typed_linq_collections.collections.q_default_dict import QDefaultDict


def test_q_default_dict_constructor() -> None:
    test_dict: QDefaultDict[str, int] = QDefaultDict(lambda: 0)
    test_dict["a"] = 1
    test_dict["b"] = 2
    assert len(test_dict) == 2
    assert set(test_dict.to_list()) == {"a", "b"}


def test_q_default_dict_default_value() -> None:
    test_dict: QDefaultDict[str, str] = QDefaultDict(lambda: "default")
    test_dict["existing"] = "value"
    assert test_dict["existing"] == "value"
    assert test_dict["missing"] == "default"  # This will create the key
    assert len(test_dict) == 2


def test_q_default_dict_qcount() -> None:
    test_dict: QDefaultDict[str, int] = QDefaultDict(lambda: 0)
    test_dict["a"] = 1
    test_dict["b"] = 2
    test_dict["c"] = 3
    assert test_dict.qcount() == 3

    empty_dict: QDefaultDict[str, int] = QDefaultDict(lambda: 0)
    assert empty_dict.qcount() == 0


def test_q_default_dict_remove() -> None:
    test_dict: QDefaultDict[str, int] = QDefaultDict(int)
    test_dict["a"] = 1
    test_dict["b"] = 2
    test_dict["c"] = 3
    test_dict.remove("b")
    assert len(test_dict) == 2
    assert "b" not in test_dict
    assert set(test_dict.keys()) == {"a", "c"}


def test_q_default_dict_remove_raises_on_missing() -> None:
    test_dict: QDefaultDict[str, int] = QDefaultDict(int)
    test_dict["a"] = 1
    with pytest.raises(KeyError):
        test_dict.remove("missing")


def test_q_default_dict_discard() -> None:
    test_dict: QDefaultDict[str, int] = QDefaultDict(int)
    test_dict["a"] = 1
    test_dict["b"] = 2
    test_dict["c"] = 3
    test_dict.discard("b")
    assert len(test_dict) == 2
    assert "b" not in test_dict
    assert set(test_dict.keys()) == {"a", "c"}


def test_q_default_dict_discard_silent_on_missing() -> None:
    test_dict: QDefaultDict[str, int] = QDefaultDict(int)
    test_dict["a"] = 1
    test_dict.discard("missing")  # Should not raise
    assert len(test_dict) == 1
    assert set(test_dict.keys()) == {"a"}


def test_q_default_dict_get_or_add_existing_key() -> None:
    test_dict: QDefaultDict[str, int] = QDefaultDict(int)
    test_dict["a"] = 1
    test_dict["b"] = 2
    result = test_dict.get_or_add("a", 99)
    assert result == 1  # Returns existing value
    assert set(test_dict.keys()) == {"a", "b"}  # Dict unchanged


def test_q_default_dict_get_or_add_new_key() -> None:
    test_dict: QDefaultDict[str, int] = QDefaultDict(int)
    test_dict["a"] = 1
    result = test_dict.get_or_add("b", 2)
    assert result == 2  # Returns new value
    assert set(test_dict.keys()) == {"a", "b"}  # Key added to dict


def test_q_default_dict_get_or_add_multiple() -> None:
    test_dict: QDefaultDict[str, int] = QDefaultDict(int)
    val1 = test_dict.get_or_add("x", 10)
    val2 = test_dict.get_or_add("y", 20)
    val3 = test_dict.get_or_add("x", 99)  # Already exists
    assert val1 == 10
    assert val2 == 20
    assert val3 == 10  # Returns original value, not 99
    assert test_dict == {"x": 10, "y": 20}
