from __future__ import annotations

from typed_linq_collections.collections.q_compact_set import QCompactSet
from typed_linq_collections.q_iterable import query


def test_to_compact_set_basic() -> None:
    result = query([1, 2, 3]).to_compact_set()
    assert len(result) == 3
    assert set(result) == {1, 2, 3}


def test_to_compact_set_with_duplicates() -> None:
    result = query([1, 2, 2, 3, 3, 3]).to_compact_set()
    assert len(result) == 3
    assert set(result) == {1, 2, 3}


def test_to_compact_set_empty() -> None:
    result: QCompactSet[int] = query([0]).where(lambda x: False).to_compact_set()
    assert len(result) == 0


def test_to_compact_set_from_where() -> None:
    result = query([1, 2, 3, 4, 5]).where(lambda x: x > 2).to_compact_set()
    assert set(result) == {3, 4, 5}


def test_to_compact_set_from_select() -> None:
    result = query([1, 2, 3]).select(lambda x: x % 2).to_compact_set()
    assert set(result) == {0, 1}  # [1, 0, 1] -> {0, 1}
