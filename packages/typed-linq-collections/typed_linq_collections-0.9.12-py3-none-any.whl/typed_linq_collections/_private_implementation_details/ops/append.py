from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

def append[TItem](self: Iterable[TItem], item: TItem) -> Iterable[TItem]:
    yield from self
    yield item