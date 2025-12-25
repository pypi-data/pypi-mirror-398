from __future__ import annotations

from typing import cast

from typed_linq_collections.collections.q_list import QList


# Concatenation operators
def test_add_operator_returns_qlist_with_the_correct_values() -> None:
    result: QList[int] = QList([1, 2, 3]) + [4, 5]
    assert isinstance(result, QList)
    assert result == [1, 2, 3, 4, 5]


def test_reverse_add_operator_returns_qlist_with_the_correct_values() -> None:
    result: QList[int] = cast(QList[int], [1, 2] + QList([3, 4, 5]))
    assert isinstance(result, QList)
    assert result == [1, 2, 3, 4, 5]


# Repetition operators
def test_mul_operator_returns_qlist_with_the_correct_values() -> None:
    result: QList[int] = QList([1, 2]) * 3
    assert isinstance(result, QList)
    assert result == [1, 2, 1, 2, 1, 2]


def test_reverse_mul_operator_returns_qlist_with_the_correct_values() -> None:
    result: QList[int] = 3 * QList([1, 2])
    assert isinstance(result, QList)
    assert result == [1, 2, 1, 2, 1, 2]


# In-place operators
def test_inplace_add_operator_returns_qlist_with_the_correct_values() -> None:
    ql: QList[int] = QList([1, 2, 3])
    ql += [4, 5]
    assert isinstance(ql, QList)
    assert ql == [1, 2, 3, 4, 5]


def test_inplace_mul_operator_returns_qlist_with_the_correct_values() -> None:
    ql: QList[int] = QList([1, 2])
    ql *= 3
    assert isinstance(ql, QList)
    assert ql == [1, 2, 1, 2, 1, 2]


# Methods
def test_copy_returns_qlist_with_the_correct_values() -> None:
    result: QList[int] = QList([1, 2, 3]).copy()
    assert isinstance(result, QList)
    assert result == [1, 2, 3]
