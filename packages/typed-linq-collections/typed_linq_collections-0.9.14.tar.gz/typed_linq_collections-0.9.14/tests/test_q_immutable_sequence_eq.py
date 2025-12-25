from __future__ import annotations

from typed_linq_collections.collections.q_immutable_sequence import QImmutableSequence


def test_eq_self() -> None:
    assert QImmutableSequence([1, 2, 3]) == QImmutableSequence([1, 2, 3])
    assert QImmutableSequence([3, 2, 1]) == QImmutableSequence([3, 2, 1])

def test_neq_self_different_lengths() -> None:
    assert QImmutableSequence([1, 2, 3]) != QImmutableSequence([1, 2])
    assert QImmutableSequence([1, 2]) != QImmutableSequence([1, 2, 3])

def test_neq_self_different_elements() -> None:
    assert QImmutableSequence([1, 2, 3]) != QImmutableSequence([1, 2, 4])
    assert QImmutableSequence([1, 2, 3]) != QImmutableSequence([4, 5, 6])

def test_eq_with_list() -> None:
    assert QImmutableSequence([1, 2, 3]) == [1, 2, 3]
    assert QImmutableSequence([3, 2, 1]) == [3, 2, 1]

def test_neq_with_list_different_lengths() -> None:
    assert QImmutableSequence([1, 2, 3]) != [1, 2]
    assert QImmutableSequence([1, 2]) != [1, 2, 3]

def test_neq_with_list_different_elements() -> None:
    assert QImmutableSequence([1, 2, 3]) != [1, 2, 4]
    assert QImmutableSequence([1, 2, 3]) != [4, 5, 6]

def test_neq_if_other_is_not_sequence() -> None:
    assert QImmutableSequence([1, 2, 3]) != "not a sequence"
    assert QImmutableSequence([1, 2, 3]) != 123
    assert QImmutableSequence([1, 2, 3]) != None  # noqa: E711
