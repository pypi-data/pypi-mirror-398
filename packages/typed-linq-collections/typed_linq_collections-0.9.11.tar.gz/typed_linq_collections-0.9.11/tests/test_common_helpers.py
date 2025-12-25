from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from typing import cast

import pytest

from typed_linq_collections.collections.q_frozen_set import QFrozenSet
from typed_linq_collections.collections.q_immutable_sequence import QImmutableSequence
from typed_linq_collections.collections.q_list import QList
from typed_linq_collections.collections.q_set import QSet
from typed_linq_collections.q_iterable import QIterable, query


@contextmanager
def sane_asserting() -> Iterator[None]:
    try:
        yield
    except AssertionError as e:
        print(f"""
Failure message: {str(e).split("\n")[0]}
""")
        raise

def create_sequences[T](iterable: Iterable[T] | Callable[[], Iterable[T]], skip_sets: bool = False) -> list[tuple[str, QIterable[T]]]:
    factory: Callable[[], Iterable[T]] = (iterable
                                          if not isinstance(iterable, Iterable)
                                          else lambda: cast(Iterable[T], iterable))  # pyright: ignore[reportUnnecessaryCast] while basedpyright understands it is not needed, pyright does not

    values = [
        ("query", query(factory())),
        ("QList", QList(factory())),
        ("QImmutableSequence", QImmutableSequence(list(factory()))),
    ]
    if not skip_sets:
        values += [("QSet", QSet(factory())),
                   ("QFRozenSet", QFrozenSet(factory()))]
    return values

def where_test[TIn, TOut](input: Iterable[TIn],
                          predicate: Callable[[TIn], bool],
                          output: list[TOut],
                          skip_sets: bool = False) -> None:
    for name, sequence in create_sequences(input, skip_sets):
        result = sequence.where(predicate)
        assert result.to_list() == output, name

def select_test[TIn, TOut](input: Iterable[TIn],
                           select: Callable[[TIn], TOut],
                           output: list[TOut],
                           skip_sets: bool = False) -> None:
    for name, sequence in create_sequences(input, skip_sets):
        result = sequence.select(select)
        assert result.to_list() == output, name

def lists_value_test[TIn, TOut](input: list[TIn] | Callable[[], Iterable[TIn]],
                                operation: Callable[[QIterable[TIn]], TOut],
                                output: TOut) -> None:
    value_test_including_unordered_collections(input, operation, output, skip_sets=True)

def value_test_including_unordered_collections[TIn, TOut](input: list[TIn] | Callable[[], Iterable[TIn]],
                                                          operation: Callable[[QIterable[TIn]], TOut],
                                                          output: TOut,
                                                          skip_sets: bool = False) -> None:
    for _name, sequence in create_sequences(input, skip_sets):
        with sane_asserting():
            result = operation(sequence)
            assert result == output, f"Test failed for {_name}"

def throws_test[TIn, TOut](input: Iterable[TIn],
                           operation: Callable[[QIterable[TIn]], TOut],
                           exception: type[Exception] = Exception,
                           skip_sets: bool = False) -> None:
    for name, sequence in create_sequences(input, skip_sets):
        with pytest.raises(exception):  # noqa: PT012
            operation(sequence)
            raise AssertionError(f"{name}: Expected {exception} to be raised")

class CallCounter:
    def __init__(self) -> None:
        self.call_count: int = 0

    def increment(self) -> None:
        self.call_count += 1

def test_throws_test_fails_when_no_exception_is_raised() -> None:
    with pytest.raises(AssertionError):
        throws_test([1, 2, 3], lambda x: x.to_list(), exception=ValueError)

def test_sane_asserting_re_raises_assertion_error() -> None:
    with pytest.raises(AssertionError), sane_asserting():
        assert False, "This is a test failure"  # noqa: B011, PT015
