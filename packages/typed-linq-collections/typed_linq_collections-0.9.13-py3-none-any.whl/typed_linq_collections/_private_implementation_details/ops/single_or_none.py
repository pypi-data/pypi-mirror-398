from __future__ import annotations

from typing import TYPE_CHECKING

from typed_linq_collections._private_implementation_details import ops
from typed_linq_collections.q_errors import InvalidOperationError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Predicate

def single_or_none[TItem](self: Iterable[TItem],
                          predicate: Predicate[TItem] | None = None) -> TItem | None:
    if predicate is not None:
        self = ops.where(self, predicate)
    iterator = iter(self)
    try:
        first_element = next(iterator)
    except StopIteration:
        return None

    try:
        next(iterator)  # Check if there's a second element
        raise InvalidOperationError("Sequence contains more than one element")
    except StopIteration:
        return first_element
