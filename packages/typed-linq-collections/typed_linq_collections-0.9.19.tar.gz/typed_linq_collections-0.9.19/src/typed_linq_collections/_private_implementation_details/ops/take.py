from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

# noinspection PyPep8Naming
from typed_linq_collections._private_implementation_details.q_zero_overhead_collection_contructors import ZeroImportOverheadConstructors as C

if TYPE_CHECKING:
    from collections.abc import Iterable


def take[TItem](self: Iterable[TItem], count: int) -> Iterable[TItem]:
    if count <= 0: return C.empty_iterable()
    return itertools.islice(self, count)
