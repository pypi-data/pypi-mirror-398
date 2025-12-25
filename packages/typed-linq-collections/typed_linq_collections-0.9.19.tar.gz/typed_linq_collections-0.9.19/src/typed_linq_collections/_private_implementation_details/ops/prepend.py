from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

def prepend[TItem](self: Iterable[TItem], item: TItem) -> Iterable[TItem]:
    yield item
    yield from self