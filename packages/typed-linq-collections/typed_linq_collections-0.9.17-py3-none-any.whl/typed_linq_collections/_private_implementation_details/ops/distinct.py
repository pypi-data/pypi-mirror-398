from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def distinct[TItem](self: Iterable[TItem]) -> Iterable[TItem]:
    return dict.fromkeys(self)  # highly optimized and guaranteed to keep ordering
