from __future__ import annotations

from typing import cast

from typed_linq_collections.collections.q_dict import QDict


# Merge operators
def test_or_operator_returns_qdict_with_the_correct_values() -> None:
    result: QDict[int, str] = cast(QDict[int, str], QDict([(1, "a"), (2, "b")]) | {3: "c", 4: "d"})
    assert isinstance(result, QDict)
    assert result == {1: "a", 2: "b", 3: "c", 4: "d"}


def test_or_operator_overwrites_with_right_side_values() -> None:
    result: QDict[int, str] = cast(QDict[int, str], QDict([(1, "a"), (2, "b")]) | {2: "B", 3: "c"})
    assert isinstance(result, QDict)
    assert result == {1: "a", 2: "B", 3: "c"}


def test_reverse_or_operator_returns_qdict_with_the_correct_values() -> None:
    result: QDict[int, str] = cast(QDict[int, str], {1: "a", 2: "b"} | QDict([(3, "c"), (4, "d")]))
    assert isinstance(result, QDict)
    assert result == {1: "a", 2: "b", 3: "c", 4: "d"}


def test_reverse_or_operator_overwrites_with_right_side_values() -> None:
    result: QDict[int, str] = cast(QDict[int, str], {1: "a", 2: "b"} | QDict([(2, "B"), (3, "c")]))
    assert isinstance(result, QDict)
    assert result == {1: "a", 2: "B", 3: "c"}


# In-place operators
def test_inplace_or_operator_returns_qdict_with_the_correct_values() -> None:
    qd: QDict[int, str] = QDict([(1, "a"), (2, "b")])
    qd |= {3: "c", 4: "d"}
    assert isinstance(qd, QDict)
    assert qd == {1: "a", 2: "b", 3: "c", 4: "d"}


def test_inplace_or_operator_overwrites_with_right_side_values() -> None:
    qd: QDict[int, str] = QDict([(1, "a"), (2, "b")])
    qd |= {2: "B", 3: "c"}
    assert isinstance(qd, QDict)
    assert qd == {1: "a", 2: "B", 3: "c"}


# Methods
def test_copy_returns_qdict_with_the_correct_values() -> None:
    result: QDict[int, str] = cast(QDict[int, str], QDict([(1, "a"), (2, "b")]).copy())
    assert isinstance(result, QDict)
    assert result == {1: "a", 2: "b"}
