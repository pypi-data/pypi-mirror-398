from __future__ import annotations

from typing import TYPE_CHECKING

from typed_linq_collections._private_implementation_details import ops
from typed_linq_collections.q_errors import EmptyIterableError, InvalidOperationError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Predicate

def single[TItem](self: Iterable[TItem],
                  predicate: Predicate[TItem] | None = None) -> TItem:
    if predicate is not None:
        self = ops.where(self, predicate)
    iterator = iter(self)
    try:
        first_element = next(iterator)
    except StopIteration:
        raise EmptyIterableError() from None

    try:
        next(iterator)
        raise InvalidOperationError("Sequence contains more than one element")
    except StopIteration:
        return first_element
