from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

def where_not_none[TItem](self: Iterable[TItem]) -> Iterable[TItem]:
    return (item for item in self if item is not None)
