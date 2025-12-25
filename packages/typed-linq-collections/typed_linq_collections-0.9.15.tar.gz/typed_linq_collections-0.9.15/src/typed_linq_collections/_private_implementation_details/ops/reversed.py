from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def reversed[TItem](self: Iterable[TItem]) -> Iterable[TItem]:
    return builtins.reversed(list(self))
