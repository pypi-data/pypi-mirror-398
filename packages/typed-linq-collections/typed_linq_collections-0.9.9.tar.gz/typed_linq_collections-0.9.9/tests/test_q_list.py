from __future__ import annotations

import pytest

from typed_linq_collections.collections.q_list import QList


def test_q_list_empty_constructor() -> None:
    empty_list = QList[str]()
    assert len(empty_list) == 0
    assert empty_list.to_list() == []


def test_q_list_with_iterable() -> None:
    test_list = QList([1, 2, 3])
    assert len(test_list) == 3
    assert test_list.to_list() == [1, 2, 3]


def test_q_list_element_at() -> None:
    test_list = QList([1, 2, 3])
    assert test_list.element_at(0) == 1
    assert test_list.element_at(1) == 2
    assert test_list.element_at(2) == 3


def test_q_list_indexing() -> None:
    test_list = QList([1, 2, 3, 4, 5])
    assert test_list[1] == 2

    # Test slice returning QList
    sliced = test_list[1:4]
    assert isinstance(sliced, QList)
    assert sliced.to_list() == [2, 3, 4]


def test_q_list_index_basic() -> None:
    test_list = QList([1, 2, 3, 2, 4])
    assert test_list.index(2) == 1  # First occurrence


def test_q_list_index_with_start() -> None:
    test_list = QList([1, 2, 3, 2, 4])
    assert test_list.index(2, 2) == 3  # Start from index 2


def test_q_list_index_with_stop() -> None:
    test_list = QList([1, 2, 3, 2, 4])
    assert test_list.index(2, 0, 3) == 1  # Stop at index 3


def test_q_list_index_with_start_and_stop() -> None:
    test_list = QList([1, 2, 3, 2, 4])
    assert test_list.index(2, 2, 4) == 3  # Start 2, stop 4


def test_q_list_index_not_found() -> None:
    test_list = QList([1, 2, 3])
    with pytest.raises(ValueError, match="is not in list"):
        test_list.index(4)


def test_q_list_index_empty_list() -> None:
    test_list = QList[int]([])
    with pytest.raises(ValueError, match="is not in list"):
        test_list.index(1)


def test_q_list_index_single_element() -> None:
    test_list = QList([5])
    assert test_list.index(5) == 0
