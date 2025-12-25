from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

def qindex[TItem](self: Iterable[TItem]) -> Iterable[tuple[int, TItem]]: return enumerate(self)
