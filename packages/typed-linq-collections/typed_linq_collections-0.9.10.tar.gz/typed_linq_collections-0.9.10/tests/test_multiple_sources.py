"""Tests for multiple sources functionality using static from_() methods."""
from __future__ import annotations

from typed_linq_collections.collections.q_frozen_set import QFrozenSet
from typed_linq_collections.collections.q_immutable_sequence import QImmutableSequence
from typed_linq_collections.collections.q_list import QList
from typed_linq_collections.collections.q_set import QSet
from typed_linq_collections.q_iterable import query, query_from


# Test classes for type variance scenarios
class Animal:
    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Animal) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


class Dog(Animal):
    pass


class Cat(Animal):
    pass


# QSet tests
def test_q_set_from_multiple_sources() -> None:
    result: QSet[int] = QSet.create([1, 2], [3, 4], [5, 6])
    assert len(result) == 6
    assert set(result) == {1, 2, 3, 4, 5, 6}


def test_q_set_from_multiple_sources_with_duplicates() -> None:
    result: QSet[int] = QSet.create([1, 2], [2, 3], [3, 4])
    assert len(result) == 4
    assert set(result) == {1, 2, 3, 4}


def test_q_set_from_single_source() -> None:
    result: QSet[int] = QSet.create([1, 2, 3])
    assert len(result) == 3
    assert set(result) == {1, 2, 3}


def test_q_set_from_empty() -> None:
    result: QSet[int] = QSet.create()
    assert len(result) == 0


def test_q_set_from_with_heterogeneous_subtypes() -> None:
    dogs: QSet[Dog] = QSet([Dog("Buddy"), Dog("Max")])
    cats: QSet[Cat] = QSet([Cat("Whiskers"), Cat("Mittens")])

    # Combine into base type
    all_animals: QSet[Animal] = QSet.create(dogs, cats)

    assert len(all_animals) == 4
    names = {animal.name for animal in all_animals}
    assert names == {"Buddy", "Max", "Whiskers", "Mittens"}


def test_q_set_constructor_does_not_iterate_strings() -> None:
    # This is the critical test - strings should be treated as single elements
    # when passed to constructor, not iterated
    result: QSet[str] = QSet(["hello", "world"])
    assert len(result) == 2
    assert set(result) == {"hello", "world"}


# QList tests
def test_q_list_from_multiple_sources() -> None:
    result: QList[int] = QList.create([1, 2], [3, 4], [5, 6])
    assert len(result) == 6
    assert result.to_list() == [1, 2, 3, 4, 5, 6]


def test_q_list_from_multiple_sources_preserves_order() -> None:
    result: QList[int] = QList.create([1, 2], [3, 4], [5, 6])
    assert result[0] == 1
    assert result[3] == 4
    assert result[5] == 6


def test_q_list_from_multiple_sources_preserves_duplicates() -> None:
    result: QList[int] = QList.create([1, 2], [2, 3], [3, 4])
    assert len(result) == 6
    assert result.to_list() == [1, 2, 2, 3, 3, 4]


def test_q_list_from_single_source() -> None:
    result: QList[int] = QList.create([1, 2, 3])
    assert len(result) == 3
    assert result.to_list() == [1, 2, 3]


def test_q_list_from_empty() -> None:
    result: QList[int] = QList.create()
    assert len(result) == 0


def test_q_list_from_with_heterogeneous_subtypes() -> None:
    dogs: QList[Dog] = QList([Dog("Buddy"), Dog("Max")])
    cats: QList[Cat] = QList([Cat("Whiskers"), Cat("Mittens")])
    more_dogs: QList[Dog] = QList([Dog("Rex")])

    # Combine into base type
    all_animals: QList[Animal] = QList.create(dogs, cats, more_dogs)

    assert len(all_animals) == 5
    assert all_animals[0].name == "Buddy"
    assert all_animals[2].name == "Whiskers"
    assert all_animals[4].name == "Rex"


def test_q_list_constructor_does_not_iterate_strings() -> None:
    result: QList[str] = QList(["hello", "world"])
    assert len(result) == 2
    assert result.to_list() == ["hello", "world"]


# QFrozenSet tests
def test_q_frozen_set_from_multiple_sources() -> None:
    result: QFrozenSet[int] = QFrozenSet.create([1, 2], [3, 4], [5, 6])
    assert len(result) == 6
    assert set(result) == {1, 2, 3, 4, 5, 6}


def test_q_frozen_set_from_multiple_sources_with_duplicates() -> None:
    result: QFrozenSet[int] = QFrozenSet.create([1, 2], [2, 3], [3, 4])
    assert len(result) == 4
    assert set(result) == {1, 2, 3, 4}


def test_q_frozen_set_from_single_source() -> None:
    result: QFrozenSet[int] = QFrozenSet.create([1, 2, 3])
    assert len(result) == 3
    assert set(result) == {1, 2, 3}


def test_q_frozen_set_from_empty() -> None:
    result: QFrozenSet[int] = QFrozenSet.create()
    assert len(result) == 0


def test_q_frozen_set_from_with_heterogeneous_subtypes() -> None:
    dogs: QFrozenSet[Dog] = QFrozenSet([Dog("Buddy"), Dog("Max")])
    cats: QFrozenSet[Cat] = QFrozenSet([Cat("Whiskers"), Cat("Mittens")])

    # Combine into base type
    all_animals: QFrozenSet[Animal] = QFrozenSet.create(dogs, cats)

    assert len(all_animals) == 4
    names = {animal.name for animal in all_animals}
    assert names == {"Buddy", "Max", "Whiskers", "Mittens"}


# QImmutableSequence tests
def test_q_immutable_sequence_from_multiple_sources() -> None:
    result: QImmutableSequence[int] = QImmutableSequence.create([1, 2], [3, 4], [5, 6])
    assert len(result) == 6
    assert list(result) == [1, 2, 3, 4, 5, 6]


def test_q_immutable_sequence_from_multiple_sources_preserves_order() -> None:
    result: QImmutableSequence[int] = QImmutableSequence.create([1, 2], [3, 4], [5, 6])
    assert result[0] == 1
    assert result[3] == 4
    assert result[5] == 6


def test_q_immutable_sequence_from_single_source() -> None:
    result: QImmutableSequence[int] = QImmutableSequence.create([1, 2, 3])
    assert len(result) == 3
    assert list(result) == [1, 2, 3]


def test_q_immutable_sequence_from_empty() -> None:
    result: QImmutableSequence[int] = QImmutableSequence.create()
    assert len(result) == 0


def test_q_immutable_sequence_from_with_heterogeneous_subtypes() -> None:
    dogs: QImmutableSequence[Dog] = QImmutableSequence([Dog("Buddy"), Dog("Max")])
    cats: QImmutableSequence[Cat] = QImmutableSequence([Cat("Whiskers"), Cat("Mittens")])

    # Combine into base type
    all_animals: QImmutableSequence[Animal] = QImmutableSequence.create(dogs, cats)

    assert len(all_animals) == 4
    assert all_animals[0].name == "Buddy"
    assert all_animals[2].name == "Whiskers"


# query_from() function tests
def test_query_from_multiple_sources() -> None:
    result = query_from([1, 2], [3, 4], [5, 6])
    assert result.to_list() == [1, 2, 3, 4, 5, 6]


def test_query_from_multiple_sources_preserves_order() -> None:
    result = query_from([1, 2], [3, 4], [5, 6])
    items = result.to_list()
    assert items[0] == 1
    assert items[3] == 4
    assert items[5] == 6


def test_query_from_multiple_sources_preserves_duplicates() -> None:
    result = query_from([1, 2], [2, 3], [3, 4])
    assert result.to_list() == [1, 2, 2, 3, 3, 4]


def test_query_from_single_source() -> None:
    result = query_from([1, 2, 3])
    assert result.to_list() == [1, 2, 3]


def test_query_from_empty() -> None:
    result = query_from()
    assert result.to_list() == []


def test_query_from_with_heterogeneous_subtypes() -> None:
    dogs: QSet[Dog] = QSet([Dog("Buddy"), Dog("Max")])
    cats: QSet[Cat] = QSet([Cat("Whiskers"), Cat("Mittens")])

    # Combine into base type query
    all_animals = query_from(dogs, cats)

    count = all_animals.qcount()
    assert count == 4


def test_query_constructor_does_not_iterate_strings() -> None:
    # Ensure query() doesn't change behavior
    result = query("hello")
    assert result.to_list() == ["h", "e", "l", "l", "o"]


# Mixed collection types
def test_mixed_collection_types_in_q_list_from() -> None:
    # QList.create() can accept different collection types
    set_data = {1, 2, 3}
    list_data = [4, 5, 6]
    tuple_data = (7, 8, 9)

    result: QList[int] = QList.create(set_data, list_data, tuple_data)
    assert len(result) == 9


def test_mixed_collection_types_in_q_set_from() -> None:
    # QSet.create() can accept different collection types
    set_data = {1, 2, 3}
    list_data = [2, 3, 4]
    tuple_data = (3, 4, 5)

    result: QSet[int] = QSet.create(set_data, list_data, tuple_data)
    assert len(result) == 5
    assert set(result) == {1, 2, 3, 4, 5}
