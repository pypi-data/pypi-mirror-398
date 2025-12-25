from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

_empty_iterator = iter(())
def take_last[TItem](self: Iterable[TItem], count: int) -> Iterable[TItem]:
    if count <= 0: return _empty_iterator
    buffer = deque[TItem](maxlen=count)
    for item in self:
        buffer.append(item)

    return buffer
