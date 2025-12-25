from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def concat[T](self: Iterable[T], *others: Iterable[T]) -> Iterable[T]:
    return itertools.chain(self, *others)
