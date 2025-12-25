from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def element_at[TItem](self: Iterable[TItem], index: int) -> TItem:
    if index < 0:
        raise IndexError(f"Index {index} was outside the bounds of the collection.")
    try:
        return next(itertools.islice(self, index, index + 1))
    except StopIteration:
        raise IndexError(f"Index {index} was outside the bounds of the collection.") from None
