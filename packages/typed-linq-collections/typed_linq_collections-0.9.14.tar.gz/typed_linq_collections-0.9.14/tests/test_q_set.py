from __future__ import annotations

from typed_linq_collections.collections.q_set import QSet


def test_q_set_empty_constructor() -> None:
    empty_set = QSet[str]()
    assert len(empty_set) == 0
    assert empty_set.to_list() == []


def test_q_set_with_iterable() -> None:
    test_set = QSet([1, 2, 3, 2])  # Duplicates should be removed
    assert len(test_set) == 3
    assert set(test_set.to_list()) == {1, 2, 3}


def test_q_set_contains() -> None:
    test_set = QSet([1, 2, 3])
    assert test_set.contains(2)
    assert not test_set.contains(4)


def test_q_set_qcount() -> None:
    test_set = QSet([1, 2, 3])
    assert test_set.qcount() == 3

    empty_set = QSet[str]()
    assert empty_set.qcount() == 0


def test_q_set_remove_where() -> None:
    test_set: QSet[int] = QSet({1, 2, 3, 4, 5})
    removed = test_set.remove_where(lambda x: x > 3)
    assert removed == 2
    assert test_set == {1, 2, 3}


def test_q_set_remove_where_even_numbers() -> None:
    test_set: QSet[int] = QSet({1, 2, 3, 4, 5, 6})
    removed = test_set.remove_where(lambda x: x % 2 == 0)
    assert removed == 3
    assert test_set == {1, 3, 5}


def test_q_set_remove_where_none_match() -> None:
    test_set: QSet[int] = QSet({1, 2, 3})
    removed = test_set.remove_where(lambda x: x > 10)
    assert removed == 0
    assert test_set == {1, 2, 3}
