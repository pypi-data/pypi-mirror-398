from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def element_at_or_none[TItem](self: Iterable[TItem],
                              index: int) -> TItem | None:
    if index < 0:
        return None
    return next(itertools.islice(self, index, index + 1), None)
