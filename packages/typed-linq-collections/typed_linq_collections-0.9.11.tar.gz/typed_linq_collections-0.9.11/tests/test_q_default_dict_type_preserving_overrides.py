from __future__ import annotations

from typing import cast

from typed_linq_collections.collections.q_default_dict import QDefaultDict


# Merge operators
def test_or_operator_returns_qdefaultdict_with_the_correct_values() -> None:
    qdd: QDefaultDict[int, list[int]] = QDefaultDict(list)
    qdd[1] = [1, 2]
    qdd[2] = [3, 4]
    result: QDefaultDict[int, list[int]] = qdd | {3: [5, 6], 4: [7, 8]}
    assert isinstance(result, QDefaultDict)
    assert result == {1: [1, 2], 2: [3, 4], 3: [5, 6], 4: [7, 8]}


def test_or_operator_overwrites_with_right_side_values() -> None:
    qdd: QDefaultDict[int, list[int]] = QDefaultDict(list)
    qdd[1] = [1, 2]
    qdd[2] = [3, 4]
    result: QDefaultDict[int, list[int]] = qdd | {2: [99], 3: [5, 6]}
    assert isinstance(result, QDefaultDict)
    assert result == {1: [1, 2], 2: [99], 3: [5, 6]}


def test_reverse_or_operator_returns_qdefaultdict_with_the_correct_values() -> None:
    qdd: QDefaultDict[int, list[int]] = QDefaultDict(list)
    qdd[3] = [5, 6]
    qdd[4] = [7, 8]
    result: QDefaultDict[int, list[int]] = cast(QDefaultDict[int, list[int]], {1: [1, 2], 2: [3, 4]} | qdd)
    assert isinstance(result, QDefaultDict)
    assert result == {1: [1, 2], 2: [3, 4], 3: [5, 6], 4: [7, 8]}


def test_reverse_or_operator_overwrites_with_right_side_values() -> None:
    qdd: QDefaultDict[int, list[int]] = QDefaultDict(list)
    qdd[2] = [99]
    qdd[3] = [5, 6]
    result: QDefaultDict[int, list[int]] = cast(QDefaultDict[int, list[int]], {1: [1, 2], 2: [3, 4]} | qdd)
    assert isinstance(result, QDefaultDict)
    assert result == {1: [1, 2], 2: [99], 3: [5, 6]}


# In-place operators
def test_inplace_or_operator_returns_qdefaultdict_with_the_correct_values() -> None:
    qdd: QDefaultDict[int, list[int]] = QDefaultDict(list)
    qdd[1] = [1, 2]
    qdd[2] = [3, 4]
    qdd |= {3: [5, 6], 4: [7, 8]}
    assert isinstance(qdd, QDefaultDict)
    assert qdd == {1: [1, 2], 2: [3, 4], 3: [5, 6], 4: [7, 8]}


def test_inplace_or_operator_overwrites_with_right_side_values() -> None:
    qdd: QDefaultDict[int, list[int]] = QDefaultDict(list)
    qdd[1] = [1, 2]
    qdd[2] = [3, 4]
    qdd |= {2: [99], 3: [5, 6]}
    assert isinstance(qdd, QDefaultDict)
    assert qdd == {1: [1, 2], 2: [99], 3: [5, 6]}


# Methods
def test_copy_returns_qdefaultdict_with_the_correct_values() -> None:
    qdd: QDefaultDict[int, list[int]] = QDefaultDict(list)
    qdd[1] = [1, 2]
    qdd[2] = [3, 4]
    result: QDefaultDict[int, list[int]] = qdd.copy()
    assert isinstance(result, QDefaultDict)
    assert result == {1: [1, 2], 2: [3, 4]}


def test_copy_preserves_default_factory() -> None:
    qdd: QDefaultDict[int, list[int]] = QDefaultDict(list)
    qdd[1] = [1, 2]
    result: QDefaultDict[int, list[int]] = qdd.copy()
    result[2].append(99)  # Should use default factory to create empty list
    assert result[2] == [99]
