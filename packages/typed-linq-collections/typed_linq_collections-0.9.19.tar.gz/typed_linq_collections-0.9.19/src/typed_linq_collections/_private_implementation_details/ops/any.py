from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typed_linq_collections._private_implementation_details.type_aliases import Predicate
    from typed_linq_collections.q_iterable import QIterable


def any[TItem](self: QIterable[TItem], predicate: Predicate[TItem] | None = None) -> bool:
    if predicate is not None:
        self = self.where(predicate)

    iterator = iter(self)
    try:
        next(iterator)
        return True  # noqa: TRY300
    except StopIteration:
        return False
