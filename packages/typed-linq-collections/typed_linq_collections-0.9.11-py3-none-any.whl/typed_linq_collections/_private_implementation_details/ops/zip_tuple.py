from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

def zip_tuple[T, T2](first: Iterable[T],
                     second: Iterable[T2]) -> Iterable[tuple[T, T2]]:
    return builtins.zip(first, second, strict=False)

def zip_tuple2[T, T2, T3](first: Iterable[T],
                          second: Iterable[T2],
                          third: Iterable[T3]) -> Iterable[tuple[T, T2, T3]]:
    return builtins.zip(first, second, third, strict=False)

def zip_tuple3[T, T2, T3, T4](first: Iterable[T],
                              second: Iterable[T2],
                              third: Iterable[T3],
                              fourth: Iterable[T4]) -> Iterable[tuple[T, T2, T3, T4]]:
    return builtins.zip(first, second, third, fourth, strict=False)
