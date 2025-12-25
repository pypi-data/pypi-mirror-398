from __future__ import annotations

from typing import cast

from typed_linq_collections.collections.q_frozen_set import QFrozenSet


# Binary operators
def test_union_operator_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = QFrozenSet([1, 2, 3]) | QFrozenSet([3, 4, 5])
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({1, 2, 3, 4, 5})


def test_reverse_union_operator_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = cast(QFrozenSet[int], frozenset({3, 4, 5}) | QFrozenSet([1, 2, 3]))
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({1, 2, 3, 4, 5})


def test_intersection_operator_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = QFrozenSet([1, 2, 3]) & QFrozenSet([2, 3, 4])
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({2, 3})


def test_reverse_intersection_operator_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = cast(QFrozenSet[int], frozenset({2, 3, 4}) & QFrozenSet([1, 2, 3]))
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({2, 3})


def test_difference_operator_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = QFrozenSet([1, 2, 3]) - QFrozenSet([2, 3, 4])
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({1})


def test_reverse_difference_operator_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = cast(QFrozenSet[int], frozenset({2, 3, 4}) - QFrozenSet([1, 2, 3]))
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({4})


def test_symmetric_difference_operator_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = QFrozenSet([1, 2, 3]) ^ QFrozenSet([2, 3, 4])
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({1, 4})


def test_reverse_symmetric_difference_operator_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = cast(QFrozenSet[int], frozenset({2, 3, 4}) ^ QFrozenSet([1, 2, 3]))
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({1, 4})


# Methods
def test_copy_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = QFrozenSet([1, 2, 3]).copy()
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({1, 2, 3})


def test_union_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = QFrozenSet([1, 2, 3]).union([3, 4, 5])
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({1, 2, 3, 4, 5})


def test_intersection_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = QFrozenSet([1, 2, 3]).intersection([2, 3, 4])
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({2, 3})


def test_difference_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = QFrozenSet([1, 2, 3]).difference([2, 3, 4])
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({1})


def test_symmetric_difference_returns_qfrozenset_with_the_correct_values() -> None:
    result: QFrozenSet[int] = QFrozenSet([1, 2, 3]).symmetric_difference([2, 3, 4])
    assert isinstance(result, QFrozenSet)
    assert result == frozenset({1, 4})
