from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

def skip[TItem](self: Iterable[TItem],
                count: int) -> Iterable[TItem]:
    if count <= 0: return self
    return itertools.islice(self, count, None)
