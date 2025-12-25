from __future__ import annotations

import pytest

from typed_linq_collections.collections.q_dict import QDict


def test_q_dict_empty_constructor() -> None:
    empty_dict: QDict[str, int] = QDict()
    assert len(empty_dict) == 0
    assert empty_dict.to_list() == []


def test_q_dict_with_iterable() -> None:
    test_dict = QDict([("a", 1), ("b", 2), ("c", 3)])
    assert len(test_dict) == 3
    assert set(test_dict.to_list()) == {"a", "b", "c"}


def test_q_dict_qcount() -> None:
    test_dict = QDict([("a", 1), ("b", 2), ("c", 3)])
    assert test_dict.qcount() == 3

    empty_dict: QDict[str, int] = QDict()
    assert empty_dict.qcount() == 0


def test_q_dict_remove() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1, "b": 2, "c": 3})
    test_dict.remove("b")
    assert len(test_dict) == 2
    assert "b" not in test_dict
    assert test_dict == {"a": 1, "c": 3}


def test_q_dict_remove_raises_on_missing() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1})
    with pytest.raises(KeyError):
        test_dict.remove("missing")


def test_q_dict_discard() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1, "b": 2, "c": 3})
    test_dict.discard("b")
    assert len(test_dict) == 2
    assert "b" not in test_dict
    assert test_dict == {"a": 1, "c": 3}


def test_q_dict_discard_silent_on_missing() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1})
    test_dict.discard("missing")  # Should not raise
    assert len(test_dict) == 1
    assert test_dict == {"a": 1}


def test_q_dict_get_or_add_existing_key() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1, "b": 2})
    result = test_dict.get_or_add("a", 99)
    assert result == 1  # Returns existing value
    assert test_dict == {"a": 1, "b": 2}  # Dict unchanged


def test_q_dict_get_or_add_new_key() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1})
    result = test_dict.get_or_add("b", 2)
    assert result == 2  # Returns new value
    assert test_dict == {"a": 1, "b": 2}  # Key added to dict


def test_q_dict_get_or_add_multiple() -> None:
    test_dict: QDict[str, int] = QDict()
    val1 = test_dict.get_or_add("x", 10)
    val2 = test_dict.get_or_add("y", 20)
    val3 = test_dict.get_or_add("x", 99)  # Already exists
    assert val1 == 10
    assert val2 == 20
    assert val3 == 10  # Returns original value, not 99
    assert test_dict == {"x": 10, "y": 20}
