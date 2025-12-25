from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

def zip[T, T2, TOut](first: Iterable[T],
                     second: Iterable[T2],
                     select: Callable[[T, T2], TOut]) -> Iterable[TOut]:
    for (first_item, second_item) in builtins.zip(first, second, strict=False):
        yield select(first_item, second_item)

def zip2[T, T2, T3, TOut](first: Iterable[T],
                          second: Iterable[T2],
                          third: Iterable[T3],
                          select: Callable[[T, T2, T3], TOut]) -> Iterable[TOut]:
    for first_item, second_item, third_item in builtins.zip(first, second, third, strict=False):
        yield select(first_item, second_item, third_item)

def zip3[T, T2, T3, T4, TOut](first: Iterable[T],
                              second: Iterable[T2],
                              third: Iterable[T3],
                              fourth: Iterable[T4],
                              select: Callable[[T, T2, T3, T4], TOut]) -> Iterable[TOut]:
    for first_item, second_item, third_item, fourth_item in builtins.zip(first, second, third, fourth, strict=False):
        yield select(first_item, second_item, third_item, fourth_item)
