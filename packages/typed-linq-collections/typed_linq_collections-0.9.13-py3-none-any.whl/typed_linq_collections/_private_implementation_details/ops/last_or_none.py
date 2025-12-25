from __future__ import annotations

from typing import TYPE_CHECKING, cast

from typed_linq_collections._private_implementation_details import ops

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Predicate

def last_or_none[TItem](self: Iterable[TItem], predicate: Predicate[TItem] | None = None) -> TItem | None:
    if predicate is not None:
        self = ops.where(self, predicate)

    sentinel = object()
    last_item: TItem | object = sentinel
    for item in self:
        last_item = item

    if last_item is sentinel:
        return None

    return cast(TItem, last_item)
