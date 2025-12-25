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


def test_q_dict_qvalues() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1, "b": 2, "c": 3})
    values = test_dict.qvalues()
    assert values.to_list() == [1, 2, 3]


def test_q_dict_qvalues_with_where() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1, "b": 2, "c": 3, "d": 4})
    result = test_dict.qvalues().where(lambda x: x > 2).to_list()
    assert result == [3, 4]


def test_q_dict_qvalues_empty() -> None:
    test_dict: QDict[str, int] = QDict()
    values = test_dict.qvalues()
    assert values.to_list() == []


def test_q_dict_get_or_add_with_factory() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1})
    result = test_dict.get_or_add("b", lambda: 2)
    assert result == 2
    assert test_dict == {"a": 1, "b": 2}


def test_q_dict_get_or_add_factory_not_called_when_key_exists() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1})
    call_count = 0

    def factory() -> int:
        nonlocal call_count
        call_count += 1
        return 99

    result = test_dict.get_or_add("a", factory)  # Key exists, shouldn't call factory
    assert result == 1
    assert call_count == 0  # Factory never called
    assert test_dict == {"a": 1}


def test_q_dict_get_or_add_factory_called_when_key_missing() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1})
    call_count = 0

    def factory() -> int:
        nonlocal call_count
        call_count += 1
        return 42

    result = test_dict.get_or_add("b", factory)  # Key missing, should call factory
    assert result == 42
    assert call_count == 1  # Factory called exactly once
    assert test_dict == {"a": 1, "b": 42}

def test_q_dict_get_value_or_default_existing_key() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1, "b": 2})
    result = test_dict.get_value_or_default("a", 99)
    assert result == 1
    assert test_dict == {"a": 1, "b": 2}  # Dict unchanged


def test_q_dict_get_value_or_default_missing_key() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1})
    result = test_dict.get_value_or_default("b", 2)
    assert result == 2
    assert test_dict == {"a": 1}  # Dict unchanged, key not added


def test_q_dict_get_value_or_default_with_factory() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1})
    result = test_dict.get_value_or_default("b", lambda: 42)
    assert result == 42
    assert test_dict == {"a": 1}  # Dict unchanged


def test_q_dict_get_value_or_default_factory_not_called_when_key_exists() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1})
    call_count = 0

    def factory() -> int:
        nonlocal call_count
        call_count += 1
        return 99

    result = test_dict.get_value_or_default("a", factory)
    assert result == 1
    assert call_count == 0  # Factory never called
    assert test_dict == {"a": 1}

def test_q_dict_remove_where_by_value() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1, "b": 2, "c": 3})
    removed = test_dict.remove_where(lambda kv: kv.value > 1)
    assert removed == 2
    assert test_dict == {"a": 1}


def test_q_dict_remove_where_by_key() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1, "b": 2, "c": 3})
    removed = test_dict.remove_where(lambda kv: kv.key.startswith("b"))
    assert removed == 1
    assert test_dict == {"a": 1, "c": 3}


def test_q_dict_remove_where_none_match() -> None:
    test_dict: QDict[str, int] = QDict({"a": 1, "b": 2})
    removed = test_dict.remove_where(lambda kv: kv.value > 10)
    assert removed == 0
    assert test_dict == {"a": 1, "b": 2}
