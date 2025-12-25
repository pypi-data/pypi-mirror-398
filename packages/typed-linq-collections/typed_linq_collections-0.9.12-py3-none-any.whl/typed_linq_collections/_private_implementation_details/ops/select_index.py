from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

def select_index[T, TResult](self: Iterable[T], selector: Callable[[T, int], TResult]) -> Iterable[TResult]:
    return (selector(item, index) for index, item in enumerate(self))
