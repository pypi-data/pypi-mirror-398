from __future__ import annotations

from typing import override

from typed_linq_collections.collections.q_unique_list import QUniqueList


def test_empty_constructor() -> None:
    empty = QUniqueList[str]()
    assert len(empty) == 0
    assert list(empty) == []


def test_with_iterable() -> None:
    ul = QUniqueList([1, 2, 3, 2])  # Duplicates should be removed
    assert len(ul) == 3
    assert set(ul) == {1, 2, 3}


def test_constructor_with_many_duplicates() -> None:
    # Test constructor optimization with lots of duplicates
    ul = QUniqueList([1, 1, 1, 2, 2, 2, 3, 3, 3])
    assert len(ul) == 3
    assert set(ul) == {1, 2, 3}


def test_constructor_maintains_hash_order() -> None:
    # Verify that constructor sorts by hash
    ul = QUniqueList([3, 1, 4, 1, 5, 9, 2, 6])
    hashes = [hash(item) for item in ul]
    assert hashes == sorted(hashes)


def test_constructor_empty_iterable() -> None:
    ul = QUniqueList[object]([])
    assert len(ul) == 0
    assert list(ul) == []


def test_add() -> None:
    ul = QUniqueList[int]()
    ul.add(1)
    ul.add(2)
    ul.add(1)  # Duplicate, should not add
    assert len(ul) == 2
    assert set(ul) == {1, 2}


def test_contains() -> None:
    ul = QUniqueList([1, 2, 3])
    assert 2 in ul
    assert 4 not in ul
    assert ul.contains(2)
    assert not ul.contains(4)


def test_remove() -> None:
    ul = QUniqueList([1, 2, 3])
    ul.remove(2)
    assert 2 not in ul
    assert len(ul) == 2


def test_remove_raises_on_missing() -> None:
    ul = QUniqueList([1, 2, 3])
    try:
        ul.remove(999)
        raise AssertionError("Should raise ValueError")
    except ValueError as e:
        assert "999" in str(e)


def test_discard() -> None:
    ul = QUniqueList([1, 2, 3])
    ul.discard(2)
    assert 2 not in ul
    ul.discard(999)  # Should not raise
    assert len(ul) == 2


def test_remove_where() -> None:
    ul = QUniqueList([1, 2, 3, 4, 5])
    removed = ul.remove_where(lambda x: x % 2 == 0)
    assert removed == 2
    assert set(ul) == {1, 3, 5}


def test_remove_where_none_match() -> None:
    ul = QUniqueList([1, 2, 3])
    removed = ul.remove_where(lambda x: x > 10)
    assert removed == 0
    assert set(ul) == {1, 2, 3}


def test_update_single_iterable() -> None:
    ul = QUniqueList([1, 2, 3])
    ul.update([3, 4, 5])
    assert set(ul) == {1, 2, 3, 4, 5}
    assert len(ul) == 5


def test_update_multiple_iterables() -> None:
    ul = QUniqueList([1, 2, 3])
    ul.update([3, 4, 5], [5, 6, 7])
    assert set(ul) == {1, 2, 3, 4, 5, 6, 7}
    assert len(ul) == 7


def test_update_with_duplicates() -> None:
    ul = QUniqueList([1, 2])
    ul.update([2, 2, 3, 3, 4])
    assert set(ul) == {1, 2, 3, 4}
    assert len(ul) == 4


def test_update_empty() -> None:
    ul = QUniqueList([1, 2, 3])
    ul.update()
    assert set(ul) == {1, 2, 3}  # No change


def test_update_on_empty_list() -> None:
    ul = QUniqueList[int]()
    ul.update([1, 2, 3])
    assert set(ul) == {1, 2, 3}


def test_update_maintains_hash_order() -> None:
    ul = QUniqueList([1, 2, 3])
    ul.update([4, 5, 6])
    # Verify items are still sorted by hash
    hashes = [hash(item) for item in ul]
    assert hashes == sorted(hashes)


def test_clear() -> None:
    ul = QUniqueList([1, 2, 3])
    ul.clear()
    assert len(ul) == 0
    assert list(ul) == []


def test_copy() -> None:
    ul1 = QUniqueList([1, 2, 3])
    ul2 = ul1.copy()
    ul2.add(4)
    assert len(ul1) == 3
    assert len(ul2) == 4


def test_equality() -> None:
    ul1 = QUniqueList([1, 2, 3])
    ul2 = QUniqueList([3, 2, 1])  # Different order, same items
    ul3 = QUniqueList([1, 2])
    assert ul1 == ul2
    assert ul1 != ul3


def test_bool() -> None:
    empty = QUniqueList[int]()
    non_empty = QUniqueList([1])
    assert not bool(empty)
    assert bool(non_empty)


def test_repr() -> None:
    ul = QUniqueList([1, 2, 3])
    repr_str = repr(ul)
    assert "QUniqueList" in repr_str
    assert "1" in repr_str


def test_union() -> None:
    ul1 = QUniqueList([1, 2, 3])
    ul2 = QUniqueList([3, 4, 5])
    result = ul1.union(ul2)
    assert set(result) == {1, 2, 3, 4, 5}


def test_union_multiple() -> None:
    ul1 = QUniqueList([1, 2])
    ul2 = QUniqueList([2, 3])
    ul3 = QUniqueList([3, 4])
    result = ul1.union(ul2, ul3)
    assert set(result) == {1, 2, 3, 4}


def test_union_with_duplicates() -> None:
    ul1 = QUniqueList([1, 2, 3])
    ul2 = [2, 2, 3, 3, 4, 4]
    result = ul1.union(ul2)
    assert set(result) == {1, 2, 3, 4}


def test_union_maintains_hash_order() -> None:
    ul1 = QUniqueList([1, 2, 3])
    ul2 = QUniqueList([4, 5, 6])
    result = ul1.union(ul2)
    hashes = [hash(item) for item in result]
    assert hashes == sorted(hashes)


def test_union_empty() -> None:
    ul1 = QUniqueList([1, 2, 3])
    result = ul1.union()
    assert set(result) == {1, 2, 3}
    assert result is not ul1  # Should be a new instance


def test_intersection() -> None:
    ul1 = QUniqueList([1, 2, 3, 4])
    ul2 = QUniqueList([3, 4, 5])
    result = ul1.intersection(ul2)
    assert set(result) == {3, 4}


def test_intersection_multiple() -> None:
    ul1 = QUniqueList([1, 2, 3, 4])
    ul2 = QUniqueList([2, 3, 4, 5])
    ul3 = QUniqueList([3, 4, 5, 6])
    result = ul1.intersection(ul2, ul3)
    assert set(result) == {3, 4}


def test_difference() -> None:
    ul1 = QUniqueList([1, 2, 3, 4])
    ul2 = QUniqueList([3, 4, 5])
    result = ul1.difference(ul2)
    assert set(result) == {1, 2}


def test_difference_multiple() -> None:
    ul1 = QUniqueList([1, 2, 3, 4, 5])
    ul2 = QUniqueList([2, 3])
    ul3 = QUniqueList([4])
    result = ul1.difference(ul2, ul3)
    assert set(result) == {1, 5}


def test_symmetric_difference() -> None:
    ul1 = QUniqueList([1, 2, 3])
    ul2 = QUniqueList([3, 4, 5])
    result = ul1.symmetric_difference(ul2)
    assert set(result) == {1, 2, 4, 5}


def test_symmetric_difference_maintains_hash_order() -> None:
    ul1 = QUniqueList([1, 2, 3])
    ul2 = QUniqueList([3, 4, 5])
    result = ul1.symmetric_difference(ul2)
    hashes = [hash(item) for item in result]
    assert hashes == sorted(hashes)


def test_symmetric_difference_no_overlap() -> None:
    ul1 = QUniqueList([1, 2, 3])
    ul2 = QUniqueList([4, 5, 6])
    result = ul1.symmetric_difference(ul2)
    assert set(result) == {1, 2, 3, 4, 5, 6}


def test_symmetric_difference_complete_overlap() -> None:
    ul1 = QUniqueList([1, 2, 3])
    ul2 = QUniqueList([1, 2, 3])
    result = ul1.symmetric_difference(ul2)
    assert len(result) == 0


def test_issubset() -> None:
    ul1 = QUniqueList([1, 2])
    ul2 = [1, 2, 3, 4]
    assert ul1.issubset(ul2)
    assert not ul1.issubset([1])


def test_issuperset() -> None:
    ul1 = QUniqueList([1, 2, 3, 4])
    ul2 = [1, 2]
    assert ul1.issuperset(ul2)
    assert not ul1.issuperset([1, 2, 5])


def test_isdisjoint() -> None:
    ul1 = QUniqueList([1, 2, 3])
    ul2 = [4, 5, 6]
    ul3 = [3, 4, 5]
    assert ul1.isdisjoint(ul2)
    assert not ul1.isdisjoint(ul3)


def test_or_operator() -> None:
    ul1 = QUniqueList([1, 2, 3])
    ul2 = QUniqueList([3, 4, 5])
    result = ul1 | ul2
    assert set(result) == {1, 2, 3, 4, 5}


def test_and_operator() -> None:
    ul1 = QUniqueList([1, 2, 3, 4])
    ul2 = QUniqueList([3, 4, 5])
    result = ul1 & ul2
    assert set(result) == {3, 4}


def test_sub_operator() -> None:
    ul1 = QUniqueList([1, 2, 3, 4])
    ul2 = QUniqueList([3, 4, 5])
    result = ul1 - ul2
    assert set(result) == {1, 2}


def test_xor_operator() -> None:
    ul1 = QUniqueList([1, 2, 3])
    ul2 = QUniqueList([3, 4, 5])
    result = ul1 ^ ul2
    assert set(result) == {1, 2, 4, 5}


def test_create_single_source() -> None:
    result = QUniqueList.create([1, 2, 3])
    assert set(result) == {1, 2, 3}


def test_create_multiple_sources() -> None:
    result = QUniqueList.create([1, 2], [2, 3], [3, 4])
    assert set(result) == {1, 2, 3, 4}


def test_create_empty() -> None:
    result: QUniqueList[int] = QUniqueList.create()
    assert len(result) == 0


def test_qcount() -> None:
    ul = QUniqueList([1, 2, 3])
    assert ul.qcount() == 3
    empty = QUniqueList[str]()
    assert empty.qcount() == 0


def test_with_strings() -> None:
    ul = QUniqueList(["apple", "banana", "apple", "cherry"])
    assert len(ul) == 3
    assert "apple" in ul
    assert "banana" in ul
    assert "cherry" in ul


def test_with_custom_objects() -> None:
    class Person:
        def __init__(self, name: str, age: int) -> None:
            self.name: str = name
            self.age: int = age

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

    ul = QUniqueList([p1, p2, p3])
    assert len(ul) == 2  # p3 should be deduplicated


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

    ul = QUniqueList([obj1, obj2, obj3])
    assert len(ul) == 2  # obj3 should be deduplicated with obj1


def test_unhashable_item_contains() -> None:
    ul = QUniqueList([1, 2, 3])
    # Testing with unhashable type should return False, not raise
    assert [] not in ul


def test_linq_operations() -> None:
    ul = QUniqueList([1, 2, 3, 4, 5])
    # Test some LINQ operations from QIterable
    result = ul.where(lambda x: x > 2).to_list()
    assert set(result) == {3, 4, 5}

    squared = ul.select(lambda x: x * x).to_list()
    assert set(squared) == {1, 4, 9, 16, 25}
