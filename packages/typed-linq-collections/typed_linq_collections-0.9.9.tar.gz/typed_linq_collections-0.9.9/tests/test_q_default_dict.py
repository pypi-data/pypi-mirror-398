from __future__ import annotations

from typed_linq_collections.collections.q_default_dict import QDefaultDict


def test_q_default_dict_constructor() -> None:
    test_dict: QDefaultDict[str, int] = QDefaultDict(lambda: 0)
    test_dict["a"] = 1
    test_dict["b"] = 2
    assert len(test_dict) == 2
    assert set(test_dict.to_list()) == {"a", "b"}


def test_q_default_dict_default_value() -> None:
    test_dict: QDefaultDict[str, str] = QDefaultDict(lambda: "default")
    test_dict["existing"] = "value"
    assert test_dict["existing"] == "value"
    assert test_dict["missing"] == "default"  # This will create the key
    assert len(test_dict) == 2


def test_q_default_dict_qcount() -> None:
    test_dict: QDefaultDict[str, int] = QDefaultDict(lambda: 0)
    test_dict["a"] = 1
    test_dict["b"] = 2
    test_dict["c"] = 3
    assert test_dict.qcount() == 3

    empty_dict: QDefaultDict[str, int] = QDefaultDict(lambda: 0)
    assert empty_dict.qcount() == 0
