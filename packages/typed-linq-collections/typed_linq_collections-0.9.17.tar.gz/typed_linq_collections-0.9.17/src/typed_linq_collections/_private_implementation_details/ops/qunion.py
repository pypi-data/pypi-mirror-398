from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

def qunion[TItem](self: Iterable[TItem], other: Iterable[TItem]) -> Iterable[TItem]:
    seen: set[TItem] = set()
    for item in self:
        if item not in seen:
            seen.add(item)
            yield item

    for item in other:
        if item not in seen:
            seen.add(item)
            yield item