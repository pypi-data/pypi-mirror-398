from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from typed_linq_collections.collections.string_interning.q_interning_list import QInterningList

if TYPE_CHECKING:
    from collections.abc import Generator


def test_q_interning_list_empty_constructor() -> None:
    """Test creating an empty QInterningList."""
    empty_list: QInterningList = QInterningList()
    assert len(empty_list) == 0
    assert list(empty_list) == []


def test_q_interning_list_with_iterable() -> None:
    """Test creating a QInterningList with an iterable."""
    test_list: QInterningList = QInterningList(["one", "two", "three"])

    assert len(test_list) == 3
    assert test_list[0] == "one"
    assert test_list[1] == "two"
    assert test_list[2] == "three"


def test_q_interning_list_interns_on_init() -> None:
    """Test that values are interned during initialization."""
    original_values = ["value1", "value2", "value3"]
    test_list: QInterningList = QInterningList(original_values)

    # Verify that the values in the list are the same objects as interned strings
    for value in test_list:
        assert value is sys.intern(value), f"Value '{value}' should be interned"


def test_q_interning_list_modifies_source_list_in_place() -> None:
    """Test that when initialized with a list, it modifies the source list in-place."""
    # Create non-interned strings using chr() which doesn't auto-intern
    non_interned_str1 = chr(118) + chr(97) + chr(108) + chr(49)  # "val1"
    non_interned_str2 = chr(118) + chr(97) + chr(108) + chr(50)  # "val2"

    # Verify they're not interned
    assert non_interned_str1 is not sys.intern(non_interned_str1), "Test setup failed"
    assert non_interned_str2 is not sys.intern(non_interned_str2), "Test setup failed"

    source_list = [non_interned_str1, non_interned_str2]
    original_str1 = source_list[0]
    original_str2 = source_list[1]

    QInterningList(source_list)

    # Verify source list was modified in-place
    assert source_list[0] is not original_str1, "Source list should be modified"
    assert source_list[1] is not original_str2, "Source list should be modified"
    assert source_list[0] is sys.intern(non_interned_str1), "Source list should contain interned strings"
    assert source_list[1] is sys.intern(non_interned_str2), "Source list should contain interned strings"


def test_q_interning_list_does_not_modify_non_list_iterables() -> None:
    """Test that non-list iterables are not modified."""
    # Create a tuple (immutable)
    source_tuple = ("a", "b", "c")
    test_list = QInterningList(source_tuple)

    # Verify the list was created and values are interned
    assert len(test_list) == 3
    for value in test_list:
        assert value is sys.intern(value)


def test_q_interning_list_append_interns() -> None:
    """Test that append interns the value."""
    test_list = QInterningList()
    non_interned_str = chr(116) + chr(101) + chr(115) + chr(116)  # "test"

    test_list.append(non_interned_str)

    assert test_list[0] is sys.intern(non_interned_str), "Appended value should be interned"


def test_q_interning_list_insert_interns() -> None:
    """Test that insert interns the value."""
    test_list = QInterningList(["a", "c"])
    non_interned_str = chr(98) + chr(98)  # "bb"

    test_list.insert(1, non_interned_str)

    assert test_list[1] is sys.intern(non_interned_str), "Inserted value should be interned"


def test_q_interning_list_extend_interns() -> None:
    """Test that extend interns all values."""
    test_list = QInterningList(["a"])
    non_interned_str1 = chr(98) + chr(98)  # "bb"
    non_interned_str2 = chr(99) + chr(99)  # "cc"

    test_list.extend([non_interned_str1, non_interned_str2])

    assert test_list[1] is sys.intern(non_interned_str1), "Extended value should be interned"
    assert test_list[2] is sys.intern(non_interned_str2), "Extended value should be interned"


def test_q_interning_list_setitem_interns() -> None:
    """Test that __setitem__ interns the value."""
    test_list = QInterningList(["a", "b", "c"])
    non_interned_str = chr(120) + chr(120)  # "xx"

    test_list[1] = non_interned_str

    assert test_list[1] is sys.intern(non_interned_str), "Set value should be interned"


def test_q_interning_list_setitem_slice_interns() -> None:
    """Test that __setitem__ with slice interns all values."""
    test_list = QInterningList(["a", "b", "c", "d"])
    non_interned_str1 = chr(120) + chr(120)  # "xx"
    non_interned_str2 = chr(121) + chr(121)  # "yy"

    test_list[1:3] = [non_interned_str1, non_interned_str2]

    assert test_list[1] is sys.intern(non_interned_str1), "Slice set value should be interned"
    assert test_list[2] is sys.intern(non_interned_str2), "Slice set value should be interned"


def test_q_interning_list_iadd_interns() -> None:
    """Test that += operator interns values."""
    test_list = QInterningList(["a"])
    non_interned_str = chr(98) + chr(98)  # "bb"

    test_list += [non_interned_str]

    assert test_list[1] is sys.intern(non_interned_str), "+= value should be interned"


def test_q_interning_list_copy_preserves_interning() -> None:
    """Test that copy creates a new list that also interns values."""
    original = QInterningList(["a", "b"])
    copied = original.copy()

    # Add a new non-interned value to the copy
    non_interned_str = chr(99) + chr(99)  # "cc"
    copied.append(non_interned_str)

    # Verify the new value is interned in the copy
    assert copied[2] is sys.intern(non_interned_str), "Value should be interned in copied list"
    # Verify original is unchanged
    assert len(original) == 2


def test_q_interning_list_add_preserves_interning() -> None:
    """Test that + operator creates a new list with interning."""
    list1 = QInterningList(["a", "b"])
    non_interned_str = chr(99) + chr(99)  # "cc"

    result = list1 + [non_interned_str]

    assert isinstance(result, QInterningList)
    assert result[2] is sys.intern(non_interned_str), "+ value should be interned"


def test_q_interning_list_mul_preserves_interning() -> None:
    """Test that * operator preserves interning."""
    test_list = QInterningList(["a", "b"])

    result = test_list * 2

    assert isinstance(result, QInterningList)
    assert len(result) == 4
    for value in result:
        assert value is sys.intern(value), "Multiplied values should be interned"


def test_q_interning_list_rmul_preserves_interning() -> None:
    """Test that reverse * operator preserves interning."""
    test_list = QInterningList(["a", "b"])

    result = 2 * test_list

    assert isinstance(result, QInterningList)
    assert len(result) == 4
    for value in result:
        assert value is sys.intern(value), "Multiplied values should be interned"


def test_q_interning_list_custom_intern_func() -> None:
    """Test that a custom intern function is used."""
    def custom_intern(s: str) -> str: return s.upper()

    test_list = QInterningList(["hello", "world"], intern_func=custom_intern)

    assert test_list[0] == "HELLO"
    assert test_list[1] == "WORLD"


def test_q_interning_list_custom_intern_func_preserved_in_copy() -> None:
    """Test that copy preserves the custom intern function."""
    def custom_intern(s: str) -> str: return s.upper()

    original = QInterningList(["hello"], intern_func=custom_intern)
    copied = original.copy()
    copied.append("world")

    assert copied[1] == "WORLD"


def test_q_interning_list_custom_intern_func_modifies_source_list() -> None:
    """Test that custom intern function is used when modifying source list."""
    def custom_intern(s: str) -> str: return s.upper()

    source_list = ["hello", "world"]
    QInterningList(source_list, intern_func=custom_intern)

    # Verify source list was modified with custom intern function
    assert source_list[0] == "HELLO"
    assert source_list[1] == "WORLD"


def test_q_interning_list_from_generator() -> None:
    """Test creating QInterningList from a generator."""
    def string_generator() -> Generator[str]:
        yield "a"
        yield "b"
        yield "c"

    test_list = QInterningList(string_generator())

    assert len(test_list) == 3
    for value in test_list:
        assert value is sys.intern(value)


def test_q_interning_list_preserves_order() -> None:
    """Test that the list preserves insertion order."""
    test_list = QInterningList(["z", "a", "m", "b"])

    assert test_list == ["z", "a", "m", "b"]


def test_q_interning_list_allows_duplicates() -> None:
    """Test that the list allows duplicate values."""
    test_list = QInterningList(["a", "b", "a", "c", "a"])

    assert len(test_list) == 5
    assert test_list.count("a") == 3
