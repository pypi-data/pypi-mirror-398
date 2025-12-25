from __future__ import annotations

from typing import override

from typed_linq_collections.collections.q_compact_set import QCompactSet


def test_empty_constructor() -> None:
    empty = QCompactSet[str]()
    assert len(empty) == 0
    assert list(empty) == []


def test_with_iterable() -> None:
    cs = QCompactSet([1, 2, 3, 2])  # Duplicates should be removed
    assert len(cs) == 3
    assert set(cs) == {1, 2, 3}


def test_contains() -> None:
    cs = QCompactSet([1, 2, 3])
    assert 2 in cs
    assert 4 not in cs
    assert cs.contains(2)
    assert not cs.contains(4)


def test_copy() -> None:
    cs1 = QCompactSet([1, 2, 3])
    cs2 = cs1.copy()
    assert cs2 is not cs1
    assert len(cs1) == 3
    assert len(cs2) == 3
    assert cs1 == cs2


def test_equality() -> None:
    cs1 = QCompactSet([1, 2, 3])
    cs2 = QCompactSet([3, 2, 1])  # Different order, same items
    cs3 = QCompactSet([1, 2])
    assert cs1 == cs2
    assert cs1 != cs3


def test_bool() -> None:
    empty = QCompactSet[int]()
    non_empty = QCompactSet([1])
    assert not bool(empty)
    assert bool(non_empty)


def test_repr() -> None:
    cs = QCompactSet([1, 2, 3])
    repr_str = repr(cs)
    assert "QCompactSet" in repr_str
    assert "1" in repr_str


def test_union() -> None:
    cs1 = QCompactSet([1, 2, 3])
    cs2 = QCompactSet([3, 4, 5])
    result = cs1.union(cs2)
    assert set(result) == {1, 2, 3, 4, 5}


def test_union_multiple() -> None:
    cs1 = QCompactSet([1, 2])
    cs2 = QCompactSet([2, 3])
    cs3 = QCompactSet([3, 4])
    result = cs1.union(cs2, cs3)
    assert set(result) == {1, 2, 3, 4}


def test_intersection() -> None:
    cs1 = QCompactSet([1, 2, 3, 4])
    cs2 = QCompactSet([3, 4, 5])
    result = cs1.intersection(cs2)
    assert set(result) == {3, 4}


def test_intersection_multiple() -> None:
    cs1 = QCompactSet([1, 2, 3, 4])
    cs2 = QCompactSet([2, 3, 4, 5])
    cs3 = QCompactSet([3, 4, 5, 6])
    result = cs1.intersection(cs2, cs3)
    assert set(result) == {3, 4}


def test_difference() -> None:
    cs1 = QCompactSet([1, 2, 3, 4])
    cs2 = QCompactSet([3, 4, 5])
    result = cs1.difference(cs2)
    assert set(result) == {1, 2}


def test_difference_multiple() -> None:
    cs1 = QCompactSet([1, 2, 3, 4, 5])
    cs2 = QCompactSet([2, 3])
    cs3 = QCompactSet([4])
    result = cs1.difference(cs2, cs3)
    assert set(result) == {1, 5}


def test_symmetric_difference() -> None:
    cs1 = QCompactSet([1, 2, 3])
    cs2 = QCompactSet([3, 4, 5])
    result = cs1.symmetric_difference(cs2)
    assert set(result) == {1, 2, 4, 5}


def test_issubset() -> None:
    cs1 = QCompactSet([1, 2])
    cs2 = [1, 2, 3, 4]
    assert cs1.issubset(cs2)
    assert not cs1.issubset([1])


def test_issuperset() -> None:
    cs1 = QCompactSet([1, 2, 3, 4])
    cs2 = [1, 2]
    assert cs1.issuperset(cs2)
    assert not cs1.issuperset([1, 2, 5])


def test_isdisjoint() -> None:
    cs1 = QCompactSet([1, 2, 3])
    cs2 = [4, 5, 6]
    cs3 = [3, 4, 5]
    assert cs1.isdisjoint(cs2)
    assert not cs1.isdisjoint(cs3)


def test_or_operator() -> None:
    cs1 = QCompactSet([1, 2, 3])
    cs2 = QCompactSet([3, 4, 5])
    result = cs1 | cs2
    assert set(result) == {1, 2, 3, 4, 5}


def test_and_operator() -> None:
    cs1 = QCompactSet([1, 2, 3, 4])
    cs2 = QCompactSet([3, 4, 5])
    result = cs1 & cs2
    assert set(result) == {3, 4}


def test_sub_operator() -> None:
    cs1 = QCompactSet([1, 2, 3, 4])
    cs2 = QCompactSet([3, 4, 5])
    result = cs1 - cs2
    assert set(result) == {1, 2}


def test_xor_operator() -> None:
    cs1 = QCompactSet([1, 2, 3])
    cs2 = QCompactSet([3, 4, 5])
    result = cs1 ^ cs2
    assert set(result) == {1, 2, 4, 5}


def test_create_single_source() -> None:
    result = QCompactSet.create([1, 2, 3])
    assert set(result) == {1, 2, 3}


def test_create_multiple_sources() -> None:
    result = QCompactSet.create([1, 2], [2, 3], [3, 4])
    assert set(result) == {1, 2, 3, 4}


def test_create_empty() -> None:
    result: QCompactSet[int] = QCompactSet.create()
    assert len(result) == 0


def test_qcount() -> None:
    cs = QCompactSet([1, 2, 3])
    assert cs.qcount() == 3
    empty = QCompactSet[str]()
    assert empty.qcount() == 0


def test_with_strings() -> None:
    cs = QCompactSet(["apple", "banana", "apple", "cherry"])
    assert len(cs) == 3
    assert "apple" in cs
    assert "banana" in cs
    assert "cherry" in cs


def test_with_custom_objects() -> None:
    class Person:
        name: str
        age: int

        def __init__(self, name: str, age: int) -> None:
            self.name = name
            self.age = age

        @override
        def __eq__(self, other: object) -> bool:
            if isinstance(other, Person):
                return self.name == other.name and self.age == other.age
            return False

        @override
        def __hash__(self) -> int:
            return hash((self.name, self.age))

    p1 = Person("Alice", 30)
    p2 = Person("Bob", 25)
    p3 = Person("Alice", 30)  # Duplicate of p1

    cs = QCompactSet([p1, p2, p3])
    assert len(cs) == 2  # p3 should be deduplicated


def test_hash_collision_handling() -> None:
    # Create objects with the same hash but different values
    class CollidingObject:
        value: int

        def __init__(self, value: int) -> None:
            self.value = value

        @override
        def __eq__(self, other: object) -> bool:
            if isinstance(other, CollidingObject):
                return self.value == other.value
            return False

        @override
        def __hash__(self) -> int:
            return 42  # Always return same hash

    obj1 = CollidingObject(1)
    obj2 = CollidingObject(2)
    obj3 = CollidingObject(1)  # Equal to obj1

    cs = QCompactSet([obj1, obj2, obj3])
    assert len(cs) == 2  # obj3 should be deduplicated with obj1


def test_unhashable_item_contains() -> None:
    cs = QCompactSet([1, 2, 3])
    # Testing with unhashable type should return False, not raise
    assert [] not in cs


def test_linq_operations() -> None:
    cs = QCompactSet([1, 2, 3, 4, 5])
    # Test some LINQ operations from QIterable
    result = cs.where(lambda x: x > 2).to_list()
    assert set(result) == {3, 4, 5}

    squared = cs.select(lambda x: x * x).to_list()
    assert set(squared) == {1, 4, 9, 16, 25}
