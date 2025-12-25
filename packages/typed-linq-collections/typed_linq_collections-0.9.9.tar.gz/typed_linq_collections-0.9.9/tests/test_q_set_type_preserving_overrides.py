from __future__ import annotations

from typing import cast

from typed_linq_collections.collections.q_set import QSet


# Binary operators
def test_union_operator_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = QSet([1, 2, 3]) | QSet([3, 4, 5])
    assert isinstance(result, QSet)
    assert result == {1, 2, 3, 4, 5}


def test_reverse_union_operator_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = cast(QSet[int], {3, 4, 5} | QSet([1, 2, 3]))
    assert isinstance(result, QSet)
    assert result == {1, 2, 3, 4, 5}


def test_intersection_operator_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = QSet([1, 2, 3]) & QSet([2, 3, 4])
    assert isinstance(result, QSet)
    assert result == {2, 3}


def test_reverse_intersection_operator_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = cast(QSet[int], {2, 3, 4} & QSet([1, 2, 3]))
    assert isinstance(result, QSet)
    assert result == {2, 3}


def test_difference_operator_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = QSet([1, 2, 3]) - QSet([2, 3, 4])
    assert isinstance(result, QSet)
    assert result == {1}


def test_reverse_difference_operator_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = cast(QSet[int], {2, 3, 4} - QSet([1, 2, 3]))
    assert isinstance(result, QSet)
    assert result == {4}


def test_symmetric_difference_operator_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = QSet([1, 2, 3]) ^ QSet([2, 3, 4])
    assert isinstance(result, QSet)
    assert result == {1, 4}


def test_reverse_symmetric_difference_operator_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = cast(QSet[int], {2, 3, 4} ^ QSet([1, 2, 3]))
    assert isinstance(result, QSet)
    assert result == {1, 4}


# In-place operators
def test_inplace_union_operator_returns_qset_with_the_correct_values() -> None:
    qs: QSet[int] = QSet([1, 2, 3])
    qs |= QSet([3, 4, 5])
    assert isinstance(qs, QSet)
    assert qs == {1, 2, 3, 4, 5}


def test_inplace_intersection_operator_returns_qset_with_the_correct_values() -> None:
    qs: QSet[int] = QSet([1, 2, 3])
    qs &= QSet([2, 3, 4])
    assert isinstance(qs, QSet)
    assert qs == {2, 3}


def test_inplace_difference_operator_returns_qset_with_the_correct_values() -> None:
    qs: QSet[int] = QSet([1, 2, 3])
    qs -= QSet([2, 3, 4])
    assert isinstance(qs, QSet)
    assert qs == {1}


def test_inplace_symmetric_difference_operator_returns_qset_with_the_correct_values() -> None:
    qs: QSet[int] = QSet([1, 2, 3])
    qs ^= QSet([2, 3, 4])
    assert isinstance(qs, QSet)
    assert qs == {1, 4}


# Methods
def test_copy_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = QSet([1, 2, 3]).copy()
    assert isinstance(result, QSet)
    assert result == {1, 2, 3}


def test_union_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = QSet([1, 2, 3]).union([3, 4, 5])
    assert isinstance(result, QSet)
    assert result == {1, 2, 3, 4, 5}


def test_intersection_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = QSet([1, 2, 3]).intersection([2, 3, 4])
    assert isinstance(result, QSet)
    assert result == {2, 3}


def test_difference_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = QSet([1, 2, 3]).difference([2, 3, 4])
    assert isinstance(result, QSet)
    assert result == {1}


def test_symmetric_difference_returns_qset_with_the_correct_values() -> None:
    result: QSet[int] = QSet([1, 2, 3]).symmetric_difference([2, 3, 4])
    assert isinstance(result, QSet)
    assert result == {1, 4}
