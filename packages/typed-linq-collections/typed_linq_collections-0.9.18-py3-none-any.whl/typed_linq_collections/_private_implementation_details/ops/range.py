from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    pass

def range(start_or_stop_before: int, stop_before: int | None = None, step: int = 1, /) -> Iterable[int]:
    return (builtins.range(start_or_stop_before)
            if stop_before is None
            else builtins.range(start_or_stop_before, stop_before, step))
