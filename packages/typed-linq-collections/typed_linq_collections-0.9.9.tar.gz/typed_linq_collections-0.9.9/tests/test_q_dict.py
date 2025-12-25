from __future__ import annotations

from typed_linq_collections.collections.q_dict import QDict


def test_q_dict_empty_constructor() -> None:
    empty_dict: QDict[str, int] = QDict()
    assert len(empty_dict) == 0
    assert empty_dict.to_list() == []


def test_q_dict_with_iterable() -> None:
    test_dict = QDict([("a", 1), ("b", 2), ("c", 3)])
    assert len(test_dict) == 3
    assert set(test_dict.to_list()) == {"a", "b", "c"}


def test_q_dict_qcount() -> None:
    test_dict = QDict([("a", 1), ("b", 2), ("c", 3)])
    assert test_dict.qcount() == 3

    empty_dict: QDict[str, int] = QDict()
    assert empty_dict.qcount() == 0
