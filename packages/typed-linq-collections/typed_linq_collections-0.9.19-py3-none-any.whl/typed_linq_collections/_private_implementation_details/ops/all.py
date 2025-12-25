from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from typed_linq_collections._private_implementation_details import ops

if TYPE_CHECKING:
    from typed_linq_collections._private_implementation_details.type_aliases import Predicate
    from typed_linq_collections.q_iterable import QIterable


def all[TItem](self: QIterable[TItem], predicate: Predicate[TItem]) -> bool:
    return builtins.all(ops.select(self, predicate))
