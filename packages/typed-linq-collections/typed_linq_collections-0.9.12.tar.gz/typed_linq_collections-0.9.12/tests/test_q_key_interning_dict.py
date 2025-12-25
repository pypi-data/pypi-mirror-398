from __future__ import annotations

import sys

from typed_linq_collections.collections.q_key_interning_dict import QKeyInterningDict


def test_q_key_interning_dict_empty_constructor() -> None:
    """Test that empty constructor works correctly."""
    empty_dict: QKeyInterningDict[int] = QKeyInterningDict()
    assert len(empty_dict) == 0
    assert empty_dict.to_list() == []


def test_q_key_interning_dict_with_iterable() -> None:
    """Test initialization with an iterable of key-value tuples."""
    test_dict: QKeyInterningDict[int] = QKeyInterningDict([("a", 1), ("b", 2), ("c", 3)])
    assert len(test_dict) == 3
    assert set(test_dict.to_list()) == {"a", "b", "c"}
    assert test_dict["a"] == 1
    assert test_dict["b"] == 2
    assert test_dict["c"] == 3


def test_q_key_interning_dict_interns_on_init() -> None:
    """Test that keys are interned during initialization."""
    original_keys: list[str] = ["name", "age", "city"]
    test_dict: QKeyInterningDict[int] = QKeyInterningDict([(k, i) for i, k in enumerate(original_keys)])

    # Verify that the keys in the dict are the same objects as interned strings
    for key in test_dict:
        assert key is sys.intern(key), f"Key '{key}' should be interned"


def test_q_key_interning_dict_stores_interned_not_original_keys() -> None:
    """Test that the dict stores interned key instances, not the original instances."""
    # Create non-interned strings using chr() which doesn't auto-intern
    original_key1: str = chr(107) + chr(101) + chr(121) + chr(49)  # "key1"
    original_key2: str = chr(107) + chr(101) + chr(121) + chr(50)  # "key2"

    # Verify they are not already interned
    assert original_key1 is not sys.intern(original_key1), "Test setup failed: key already interned"
    assert original_key2 is not sys.intern(original_key2), "Test setup failed: key already interned"

    test_dict: QKeyInterningDict[str] = QKeyInterningDict([(original_key1, "value1"), (original_key2, "value2")])

    # Verify that stored keys are NOT the original instances
    for stored_key in test_dict:
        if stored_key == original_key1:
            assert stored_key is not original_key1, "Should store interned version, not original"
            assert stored_key is sys.intern(original_key1), "Should store sys.intern version"
        elif stored_key == original_key2:
            assert stored_key is not original_key2, "Should store interned version, not original"
            assert stored_key is sys.intern(original_key2), "Should store sys.intern version"


def test_q_key_interning_dict_setitem_interns() -> None:
    """Test that __setitem__ method interns keys."""
    test_dict: QKeyInterningDict[str] = QKeyInterningDict()
    test_key: str = "hello"
    test_dict[test_key] = "world"

    # Verify the key is interned
    stored_key: str = next(iter(test_dict))
    assert stored_key is sys.intern(test_key)


def test_q_key_interning_dict_setitem_stores_interned_not_original() -> None:
    """Test that __setitem__ stores interned key instance, not the original instance."""
    test_dict: QKeyInterningDict[str] = QKeyInterningDict()
    # Create non-interned string using chr() which doesn't auto-intern in all cases
    original_key: str = chr(100) + chr(105) + chr(99) + chr(116) + chr(49)  # "dict1"

    # Verify it's not already interned
    assert original_key is not sys.intern(original_key), "Test setup failed: key already interned"

    test_dict[original_key] = "test_value"

    stored_key: str = next(iter(test_dict))
    assert stored_key is not original_key, "Should store interned version, not original"
    assert stored_key is sys.intern(original_key), "Should store sys.intern version"


def test_q_key_interning_dict_getitem_with_interned_key() -> None:
    """Test that __getitem__ works with interned keys."""
    test_dict: QKeyInterningDict[str] = QKeyInterningDict([("key1", "value1"), ("key2", "value2")])

    # Access with a new string object
    assert test_dict["key1"] == "value1"
    assert test_dict["key2"] == "value2"


def test_q_key_interning_dict_delitem_interns() -> None:
    """Test that __delitem__ works with interned keys."""
    test_dict: QKeyInterningDict[str] = QKeyInterningDict([("key1", "value1"), ("key2", "value2")])
    del test_dict["key1"]

    assert "key1" not in test_dict
    assert "key2" in test_dict
    assert len(test_dict) == 1


def test_q_key_interning_dict_contains() -> None:
    """Test that __contains__ works correctly with interned keys."""
    test_dict: QKeyInterningDict[int] = QKeyInterningDict([("hello", 1), ("world", 2)])

    assert "hello" in test_dict
    assert "world" in test_dict
    assert "goodbye" not in test_dict

    # Test with non-string key (should not crash)
    assert 123 not in test_dict


def test_q_key_interning_dict_get() -> None:
    """Test that get() method works with interned keys."""
    test_dict: QKeyInterningDict[int] = QKeyInterningDict([("a", 1), ("b", 2)])

    assert test_dict.get("a") == 1
    assert test_dict.get("b") == 2
    assert test_dict.get("c") is None
    assert test_dict.get("c", 99) == 99


def test_q_key_interning_dict_setdefault() -> None:
    """Test that setdefault() method interns keys."""
    test_dict: QKeyInterningDict[int] = QKeyInterningDict()

    result: int | None = test_dict.setdefault("key1", 10)
    assert result == 10
    assert test_dict["key1"] == 10

    # Verify key is interned
    assert next(iter(test_dict)) is sys.intern("key1")

    # Test with existing key
    result = test_dict.setdefault("key1", 20)
    assert result == 10  # Should return existing value


def test_q_key_interning_dict_pop() -> None:
    """Test that pop() method works with interned keys."""
    test_dict: QKeyInterningDict[int] = QKeyInterningDict([("a", 1), ("b", 2), ("c", 3)])

    value: int = test_dict.pop("b")
    assert value == 2
    assert "b" not in test_dict
    assert len(test_dict) == 2

    # Pop with default
    value = test_dict.pop("missing", 99)
    assert value == 99


def test_q_key_interning_dict_update_with_dict() -> None:
    """Test that update() method interns keys when updating with a dict."""
    test_dict: QKeyInterningDict[int] = QKeyInterningDict([("a", 1)])
    test_dict.update({"b": 2, "c": 3})

    # Verify all keys are interned
    for key in test_dict:
        assert key is sys.intern(key), f"Key '{key}' should be interned"

    assert len(test_dict) == 3
    assert test_dict["a"] == 1
    assert test_dict["b"] == 2
    assert test_dict["c"] == 3


def test_q_key_interning_dict_update_with_iterable() -> None:
    """Test that update() method interns keys when updating with an iterable."""
    test_dict: QKeyInterningDict[int] = QKeyInterningDict([("a", 1)])
    test_dict.update([("b", 2), ("c", 3)])

    # Verify all keys are interned
    for key in test_dict:
        assert key is sys.intern(key), f"Key '{key}' should be interned"

    assert len(test_dict) == 3
    assert test_dict["a"] == 1
    assert test_dict["b"] == 2
    assert test_dict["c"] == 3


def test_q_key_interning_dict_update_with_kwargs() -> None:
    """Test that update() method interns keys when updating with keyword arguments."""
    test_dict: QKeyInterningDict[int] = QKeyInterningDict([("a", 1)])
    test_dict.update(b=2, c=3)

    # Verify all keys are interned
    for key in test_dict:
        assert key is sys.intern(key), f"Key '{key}' should be interned"

    assert len(test_dict) == 3
    assert test_dict["a"] == 1
    assert test_dict["b"] == 2
    assert test_dict["c"] == 3


def test_q_key_interning_dict_fromkeys() -> None:
    """Test that fromkeys() class method interns keys."""
    test_dict: QKeyInterningDict[int] = QKeyInterningDict.fromkeys(["a", "b", "c"], 0)

    # Verify all keys are interned
    for key in test_dict:
        assert key is sys.intern(key), f"Key '{key}' should be interned"

    assert len(test_dict) == 3
    assert all(test_dict[k] == 0 for k in test_dict)


def test_q_key_interning_dict_memory_efficiency() -> None:
    """Test that interning actually uses the same object for duplicate keys."""
    # Create multiple dictionaries with the same keys
    dict1: QKeyInterningDict[int] = QKeyInterningDict([("key1", 1), ("key2", 2)])
    _dict2: QKeyInterningDict[int] = QKeyInterningDict([("key1", 10), ("key2", 20)])

    # Keys should be the exact same objects across dictionaries
    for key in dict1:
        # Create a new string with same content
        new_string: str = str(key)
        assert key is sys.intern(new_string), "Keys should be interned"


def test_q_key_interning_dict_qcount() -> None:
    """Test that qcount() works correctly."""
    test_dict: QKeyInterningDict[int] = QKeyInterningDict([("a", 1), ("b", 2), ("c", 3)])
    assert test_dict.qcount() == 3

    empty_dict: QKeyInterningDict[int] = QKeyInterningDict()
    assert empty_dict.qcount() == 0


def test_q_key_interning_dict_linq_operations() -> None:
    """Test that LINQ operations still work correctly on keys."""
    test_dict: QKeyInterningDict[int] = QKeyInterningDict([("apple", 1), ("banana", 2), ("cherry", 3), ("date", 4)])

    # Test where on keys
    filtered = test_dict.where(lambda key: len(key) > 5)
    result: list[str] = filtered.to_list()
    assert set(result) == {"banana", "cherry"}

    # Test select on keys
    lengths: list[int] = test_dict.select(lambda key: len(key)).to_list()
    assert set(lengths) == {4, 5, 6}


def test_q_key_interning_dict_qitems() -> None:
    """Test that qitems() works correctly and maintains interned keys."""
    test_dict: QKeyInterningDict[int] = QKeyInterningDict([("a", 1), ("b", 2), ("c", 3)])

    items = test_dict.qitems().to_list()
    assert len(items) == 3

    # Verify keys in KeyValuePairs are interned
    for item in items:
        assert item.key is sys.intern(item.key), f"Key '{item.key}' in KeyValuePair should be interned"


def test_q_key_interning_dict_copy() -> None:
    """Test that copy() preserves key interning."""
    original: QKeyInterningDict[int] = QKeyInterningDict([("test", 1), ("copy", 2)])
    copied: QKeyInterningDict[int] = original.copy()

    # Verify copy is also QKeyInterningDict
    assert isinstance(copied, QKeyInterningDict)

    # Verify all keys are still interned
    for key in copied:
        assert key is sys.intern(key), f"Key '{key}' should be interned in copy"


def test_q_key_interning_dict_or_operator() -> None:
    """Test that | operator maintains interning."""
    dict1: QKeyInterningDict[int] = QKeyInterningDict([("a", 1), ("b", 2)])
    dict2: QKeyInterningDict[int] = QKeyInterningDict([("c", 3), ("d", 4)])

    result: QKeyInterningDict[int] = dict1 | dict2

    # Verify result is QKeyInterningDict
    assert isinstance(result, QKeyInterningDict)

    # Verify all keys are interned
    for key in result:
        assert key is sys.intern(key), f"Key '{key}' should be interned"

    assert len(result) == 4


def test_q_key_interning_dict_ior_operator() -> None:
    """Test that |= operator maintains interning."""
    dict1: QKeyInterningDict[int] = QKeyInterningDict([("a", 1), ("b", 2)])
    dict2: dict[str, int] = {"c": 3, "d": 4}

    dict1 |= dict2

    # Verify all keys are interned
    for key in dict1:
        assert key is sys.intern(key), f"Key '{key}' should be interned"

    assert len(dict1) == 4
    assert dict1["c"] == 3
    assert dict1["d"] == 4


def test_q_key_interning_dict_with_different_value_types() -> None:
    """Test that the dict works with various value types."""
    # Test with string values
    str_dict: QKeyInterningDict[str] = QKeyInterningDict([("name", "Alice"), ("city", "NYC")])
    assert str_dict["name"] == "Alice"

    # Test with list values
    list_dict: QKeyInterningDict[list[int]] = QKeyInterningDict([("nums", [1, 2, 3])])
    assert list_dict["nums"] == [1, 2, 3]

    # Test with mixed types
    mixed_dict: QKeyInterningDict[int | str] = QKeyInterningDict()
    mixed_dict["count"] = 42
    mixed_dict["name"] = "test"
    assert mixed_dict["count"] == 42
    assert mixed_dict["name"] == "test"

    # All keys should still be interned
    for key in mixed_dict:
        assert key is sys.intern(key)
