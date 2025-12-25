from __future__ import annotations

from typing import TYPE_CHECKING

from typed_linq_collections._private_implementation_details import ops
from typed_linq_collections.q_errors import EmptyIterableError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Predicate

def first[TItem](self: Iterable[TItem],
                 predicate: Predicate[TItem] | None = None) -> TItem:
    if predicate is not None:
        self = ops.where(self, predicate)
    try:
        return next(iter(self))
    except StopIteration:
        raise EmptyIterableError() from None
