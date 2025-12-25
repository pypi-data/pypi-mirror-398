from __future__ import annotations

from typed_linq_collections.collections.q_immutable_sequence import QImmutableSequence


def test_q_immutable_sequence_empty_constructor() -> None:
    empty_seq = QImmutableSequence[str]()
    assert len(empty_seq) == 0
    assert empty_seq.to_list() == []


def test_q_immutable_sequence_with_iterable() -> None:
    test_seq = QImmutableSequence([1, 2, 3])
    assert len(test_seq) == 3
    assert test_seq.to_list() == [1, 2, 3]


def test_q_immutable_sequence_indexing() -> None:
    test_seq = QImmutableSequence([1, 2, 3, 4, 5])
    assert test_seq[1] == 2

    # Test slice returning QImmutableSequence
    sliced = test_seq[1:4]
    assert isinstance(sliced, QImmutableSequence)
    assert sliced.to_list() == [2, 3, 4]


def test_q_immutable_sequence_element_at() -> None:
    test_seq = QImmutableSequence([1, 2, 3])
    assert test_seq.element_at(0) == 1
    assert test_seq.element_at(1) == 2
    assert test_seq.element_at(2) == 3


def test_q_immutable_sequence_repr() -> None:
    empty_seq = QImmutableSequence[str]()
    assert repr(empty_seq) == "QImmutableSequence([])"

    test_seq = QImmutableSequence([1, 2, 3])
    assert repr(test_seq) == "QImmutableSequence([1, 2, 3])"
