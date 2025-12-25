from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typed_linq_collections._private_implementation_details.type_aliases import Predicate
    from typed_linq_collections.q_iterable import QIterable


def qcount[TItem](self: QIterable[TItem], predicate: Predicate[TItem] | None = None) -> int:
    if predicate is not None:
        self = self.where(predicate)

    return self._optimized_length()  # pyright: ignore [reportPrivateUsage]
