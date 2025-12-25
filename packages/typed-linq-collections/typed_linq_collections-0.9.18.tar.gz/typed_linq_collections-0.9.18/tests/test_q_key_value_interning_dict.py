from __future__ import annotations

import sys

from typed_linq_collections.collections.string_interning.q_key_value_interning_dict import QKeyValueInterningDict


def test_q_key_value_interning_dict_empty_constructor() -> None:
    """Test creating an empty QKeyValueInterningDict."""
    empty_dict: QKeyValueInterningDict = QKeyValueInterningDict()
    assert len(empty_dict) == 0
    assert list(empty_dict.keys()) == []


def test_q_key_value_interning_dict_with_iterable() -> None:
    """Test creating a QKeyValueInterningDict with an iterable."""
    test_dict: QKeyValueInterningDict = QKeyValueInterningDict([("a", "one"), ("b", "two"), ("c", "three")])

    assert len(test_dict) == 3
    assert test_dict["a"] == "one"
    assert test_dict["b"] == "two"
    assert test_dict["c"] == "three"


def test_q_key_value_interning_dict_interns_keys_on_init() -> None:
    """Test that keys are interned during initialization."""
    original_keys = ["key1", "key2", "key3"]
    test_dict: QKeyValueInterningDict = QKeyValueInterningDict([(k, "value") for k in original_keys])

    # Verify that the keys in the dict are the same objects as interned strings
    for key in test_dict:
        assert key is sys.intern(key), f"Key '{key}' should be interned"


def test_q_key_value_interning_dict_interns_values_on_init() -> None:
    """Test that values are interned during initialization."""
    original_values = ["value1", "value2", "value3"]
    test_dict: QKeyValueInterningDict = QKeyValueInterningDict([(f"key{i}", v) for i, v in enumerate(original_values)])

    # Verify that the values in the dict are the same objects as interned strings
    for value in test_dict.values():
        assert value is sys.intern(value), f"Value '{value}' should be interned"


def test_q_key_value_interning_dict_stores_interned_not_original_keys() -> None:
    """Test that the dict stores interned key instances, not the original instances."""
    # Create non-interned strings using chr() which doesn't auto-intern
    non_interned_key = chr(107) + chr(101) + chr(121) + chr(49)  # "key1"
    assert non_interned_key is not sys.intern(non_interned_key), "Key should not be pre-interned"

    test_dict: QKeyValueInterningDict = QKeyValueInterningDict([(non_interned_key, "value")])

    stored_key = next(iter(test_dict.keys()))
    assert stored_key is not non_interned_key, "Should store interned version, not original"
    assert stored_key is sys.intern(non_interned_key), "Stored key should be interned"


def test_q_key_value_interning_dict_stores_interned_not_original_values() -> None:
    """Test that the dict stores interned value instances, not the original instances."""
    # Create non-interned strings using chr() which doesn't auto-intern
    non_interned_value = chr(118) + chr(97) + chr(108) + chr(49)  # "val1"
    assert non_interned_value is not sys.intern(non_interned_value), "Value should not be pre-interned"

    test_dict: QKeyValueInterningDict = QKeyValueInterningDict([("key", non_interned_value)])

    stored_value = test_dict["key"]
    assert stored_value is not non_interned_value, "Should store interned version, not original"
    assert stored_value is sys.intern(non_interned_value), "Stored value should be interned"


def test_q_key_value_interning_dict_setitem_interns_key() -> None:
    """Test that __setitem__ interns the key."""
    test_dict: QKeyValueInterningDict = QKeyValueInterningDict()
    non_interned_key = "test_" + "key_" + "789"

    test_dict[non_interned_key] = "value"

    stored_key = next(iter(test_dict.keys()))
    assert stored_key is sys.intern(non_interned_key), "Key should be interned on setitem"


def test_q_key_value_interning_dict_setitem_interns_value() -> None:
    """Test that __setitem__ interns the value."""
    test_dict: QKeyValueInterningDict = QKeyValueInterningDict()
    non_interned_value = "test_" + "value_" + "abc"

    test_dict["key"] = non_interned_value

    stored_value = test_dict["key"]
    assert stored_value is sys.intern(non_interned_value), "Value should be interned on setitem"


def test_q_key_value_interning_dict_update_interns_keys_and_values() -> None:
    """Test that update interns both keys and values."""
    test_dict: QKeyValueInterningDict = QKeyValueInterningDict()
    non_interned_key = "update_" + "key_" + "xyz"
    non_interned_value = "update_" + "value_" + "def"

    test_dict.update([(non_interned_key, non_interned_value)])

    stored_key = next(iter(test_dict.keys()))
    stored_value = test_dict[stored_key]
    assert stored_key is sys.intern(non_interned_key), "Key should be interned on update"
    assert stored_value is sys.intern(non_interned_value), "Value should be interned on update"


def test_q_key_value_interning_dict_setdefault_interns_key_and_value() -> None:
    """Test that setdefault interns both key and default value."""
    test_dict: QKeyValueInterningDict = QKeyValueInterningDict()
    non_interned_key = "setdef_" + "key_" + "pqr"
    non_interned_value = "setdef_" + "value_" + "stu"

    result = test_dict.setdefault(non_interned_key, non_interned_value)

    assert result is sys.intern(non_interned_value), "Returned value should be interned"
    stored_key = next(iter(test_dict.keys()))
    stored_value = test_dict[stored_key]
    assert stored_key is sys.intern(non_interned_key), "Key should be interned on setdefault"
    assert stored_value is sys.intern(non_interned_value), "Value should be interned on setdefault"


def test_q_key_value_interning_dict_fromkeys_interns_keys_and_value() -> None:
    """Test that fromkeys interns both keys and the value."""
    non_interned_keys = ["from_" + "key_" + str(i) for i in range(3)]
    non_interned_value = "from_" + "value_" + "vwx"

    test_dict = QKeyValueInterningDict.fromkeys(non_interned_keys, non_interned_value)

    for key in test_dict:
        assert key is sys.intern(key), f"Key '{key}' should be interned"
        assert test_dict[key] is sys.intern(non_interned_value), "Value should be interned"


def test_q_key_value_interning_dict_copy_preserves_interning() -> None:
    """Test that copy creates a new dict that also interns keys and values."""
    original = QKeyValueInterningDict([("key1", "value1"), ("key2", "value2")])
    copied = original.copy()

    # Add a new non-interned key-value pair to the copy
    non_interned_key = "copy_" + "key_" + "mno"
    non_interned_value = "copy_" + "value_" + "ghi"
    copied[non_interned_key] = non_interned_value

    # Verify the new key and value are interned in the copy
    assert non_interned_key in copied
    stored_value = copied[non_interned_key]
    assert stored_value is sys.intern(non_interned_value), "Value should be interned in copied dict"


def test_q_key_value_interning_dict_custom_intern_func() -> None:
    """Test that a custom intern function is used for both keys and values."""
    def custom_intern(s: str) -> str: return s.upper()

    test_dict = QKeyValueInterningDict([("key", "value")], intern_func=custom_intern)
    test_dict["hello"] = "world"

    assert "KEY" in test_dict
    assert "HELLO" in test_dict
    assert test_dict["KEY"] == "VALUE"
    assert test_dict["HELLO"] == "WORLD"


def test_q_key_value_interning_dict_custom_intern_func_preserved_in_copy() -> None:
    """Test that copy preserves the custom intern function."""
    def custom_intern(s: str) -> str: return s.upper()

    original = QKeyValueInterningDict([("key", "value")], intern_func=custom_intern)
    copied = original.copy()
    copied["hello"] = "world"

    assert "HELLO" in copied
    assert copied["HELLO"] == "WORLD"


def test_q_key_value_interning_dict_custom_intern_func_in_fromkeys() -> None:
    """Test that fromkeys uses the custom intern function."""
    def custom_intern(s: str) -> str: return s.upper()

    test_dict = QKeyValueInterningDict.fromkeys(["a", "b", "c"], "value", intern_func=custom_intern)

    assert "A" in test_dict
    assert "B" in test_dict
    assert "C" in test_dict
    assert test_dict["A"] == "VALUE"
