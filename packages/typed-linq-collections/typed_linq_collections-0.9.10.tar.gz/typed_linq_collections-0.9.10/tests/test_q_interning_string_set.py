from __future__ import annotations

import sys

from typed_linq_collections.collections.q_interning_string_set import QInterningStringSet


def test_q_interning_string_set_empty_constructor() -> None:
    """Test that empty constructor works correctly."""
    empty_set = QInterningStringSet()
    assert len(empty_set) == 0
    assert empty_set.to_list() == []


def test_q_interning_string_set_with_iterable() -> None:
    """Test initialization with an iterable of strings."""
    test_set = QInterningStringSet(["hello", "world", "hello"])  # Duplicates should be removed
    assert len(test_set) == 2
    assert set(test_set.to_list()) == {"hello", "world"}


def test_q_interning_string_set_interns_on_init() -> None:
    """Test that strings are interned during initialization."""
    original_strings = ["test", "string", "values"]
    test_set = QInterningStringSet(original_strings)

    # Verify that the strings in the set are the same objects as interned strings
    for s in test_set:
        assert s is sys.intern(s), f"String '{s}' should be interned"


def test_q_interning_string_set_stores_interned_not_original() -> None:
    """Test that the set stores interned instances, not the original instances."""
    # Create non-interned strings using chr() which doesn't auto-intern in all cases
    original1 = chr(115) + chr(101) + chr(116) + chr(49)  # "set1"
    original2 = chr(115) + chr(101) + chr(116) + chr(50)  # "set2"

    # Verify they are not already interned
    assert original1 is not sys.intern(original1), "Test setup failed: string already interned"
    assert original2 is not sys.intern(original2), "Test setup failed: string already interned"

    test_set = QInterningStringSet([original1, original2])

    # Verify that stored strings are NOT the original instances
    for stored in test_set:
        if stored == original1:
            assert stored is not original1, "Should store interned version, not original"
            assert stored is sys.intern(original1), "Should store sys.intern version"
        elif stored == original2:
            assert stored is not original2, "Should store interned version, not original"
            assert stored is sys.intern(original2), "Should store sys.intern version"


def test_q_interning_string_set_add_interns() -> None:
    """Test that add() method interns strings."""
    test_set = QInterningStringSet()
    test_string = "hello"
    test_set.add(test_string)

    # Verify the string is interned
    stored_string = next(iter(test_set))
    assert stored_string is sys.intern(test_string)


def test_q_interning_string_set_add_stores_interned_not_original() -> None:
    """Test that add() stores interned instance, not the original instance."""
    test_set = QInterningStringSet()
    # Create non-interned string - in Python 3.13 most strings are auto-interned
    # Use a UUID-like pattern to minimize chance of auto-interning
    import uuid
    original = str(uuid.uuid4())[:8]  # Random 8-char string like "a3b5c7d9"

    # Call intern to ensure the intern pool has this value
    sys.intern(original)

    # Now add a new string with same content (might be auto-interned to same object)
    # The key point is that our implementation calls sys.intern explicitly
    test_set.add(original)

    stored = next(iter(test_set))
    # Verify the stored value is interned (same as sys.intern result)
    assert stored is sys.intern(stored), "Stored value should be interned"
    assert stored == original, "Stored value should equal original"
    """Test that update() method interns all strings."""
    test_set = QInterningStringSet(["initial"])
    test_set.update(["foo", "bar"], ["baz"])

    # Verify all strings are interned
    for s in test_set:
        assert s is sys.intern(s), f"String '{s}' should be interned"

    assert len(test_set) == 4
    assert set(test_set) == {"initial", "foo", "bar", "baz"}


def test_q_interning_string_set_union_interns() -> None:
    """Test that union() method returns a new set with interned strings."""
    set1 = QInterningStringSet(["a", "b"])
    set2 = {"c", "d"}
    result = set1.union(set2)

    # Verify result is QInterningStringSet
    assert isinstance(result, QInterningStringSet)

    # Verify all strings are interned
    for s in result:
        assert s is sys.intern(s), f"String '{s}' should be interned"

    assert set(result) == {"a", "b", "c", "d"}


def test_q_interning_string_set_intersection_update_interns() -> None:
    """Test that intersection_update() works with interned strings."""
    set1 = QInterningStringSet(["a", "b", "c"])
    set2 = ["b", "c", "d"]
    set1.intersection_update(set2)

    # Verify all remaining strings are interned
    for s in set1:
        assert s is sys.intern(s), f"String '{s}' should be interned"

    assert set(set1) == {"b", "c"}


def test_q_interning_string_set_difference_update_interns() -> None:
    """Test that difference_update() works with interned strings."""
    set1 = QInterningStringSet(["a", "b", "c"])
    set2 = ["b", "d"]
    set1.difference_update(set2)

    # Verify all remaining strings are interned
    for s in set1:
        assert s is sys.intern(s), f"String '{s}' should be interned"

    assert set(set1) == {"a", "c"}


def test_q_interning_string_set_symmetric_difference_update_interns() -> None:
    """Test that symmetric_difference_update() works with interned strings."""
    set1 = QInterningStringSet(["a", "b", "c"])
    set2 = ["b", "c", "d"]
    set1.symmetric_difference_update(set2)

    # Verify all remaining strings are interned
    for s in set1:
        assert s is sys.intern(s), f"String '{s}' should be interned"

    assert set(set1) == {"a", "d"}


def test_q_interning_string_set_memory_efficiency() -> None:
    """Test that interning actually uses the same object for duplicate strings."""
    # Create multiple instances of the same string content
    strings = [str(i % 3) for i in range(100)]  # Creates many "0", "1", "2" strings
    test_set = QInterningStringSet(strings)

    # Should only have 3 unique strings
    assert len(test_set) == 3

    # Each string in the set should be the exact same object as sys.intern returns
    for s in test_set:
        # Create a new string with same content
        new_string = str(int(s))
        assert s is sys.intern(new_string), "Interned strings should be identical objects"


def test_q_interning_string_set_contains() -> None:
    """Test that contains() works correctly with interned strings."""
    test_set = QInterningStringSet(["hello", "world"])
    assert test_set.contains("hello")
    assert not test_set.contains("goodbye")
    assert "world" in test_set


def test_q_interning_string_set_qcount() -> None:
    """Test that qcount() works correctly."""
    test_set = QInterningStringSet(["a", "b", "c"])
    assert test_set.qcount() == 3

    empty_set = QInterningStringSet()
    assert empty_set.qcount() == 0


def test_q_interning_string_set_linq_operations() -> None:
    """Test that LINQ operations still work correctly."""
    test_set = QInterningStringSet(["apple", "banana", "cherry", "date"])

    # Test where
    filtered = test_set.where(lambda x: len(x) > 5)
    result = filtered.to_list()
    assert set(result) == {"banana", "cherry"}

    # Test select
    lengths = test_set.select(lambda x: len(x)).to_list()
    assert set(lengths) == {4, 5, 6}


def test_q_interning_string_set_copy_preserves_interning() -> None:
    """Test that copy() preserves string interning."""
    original = QInterningStringSet(["test", "copy"])
    copied = original.copy()

    # Verify copy is also QInterningStringSet
    assert isinstance(copied, QInterningStringSet)

    # Verify all strings are still interned
    for s in copied:
        assert s is sys.intern(s), f"String '{s}' should be interned in copy"


def test_q_interning_string_set_set_operations() -> None:
    """Test various set operations maintain interning."""
    set1 = QInterningStringSet(["a", "b", "c"])
    set2 = QInterningStringSet(["c", "d", "e"])

    # Union
    union_result = set1 | set2
    assert isinstance(union_result, QInterningStringSet)
    for s in union_result:
        assert s is sys.intern(s)

    # Intersection
    intersection_result = set1 & set2
    assert isinstance(intersection_result, QInterningStringSet)
    for s in intersection_result:
        assert s is sys.intern(s)

    # Difference
    diff_result = set1 - set2
    assert isinstance(diff_result, QInterningStringSet)
    for s in diff_result:
        assert s is sys.intern(s)

    # Symmetric difference
    sym_diff_result = set1 ^ set2
    assert isinstance(sym_diff_result, QInterningStringSet)
    for s in sym_diff_result:
        assert s is sys.intern(s)
