from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def qexcept[TItem](self: Iterable[TItem], other: Iterable[TItem]) -> Iterable[TItem]:
    other_set = set(other)
    seen: set[TItem] = set()
    for item in self:
        if item not in other_set and item not in seen:
            seen.add(item)
            yield item