from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

def contains[T](self: Iterable[T], item: T) -> bool:
    return item in self
