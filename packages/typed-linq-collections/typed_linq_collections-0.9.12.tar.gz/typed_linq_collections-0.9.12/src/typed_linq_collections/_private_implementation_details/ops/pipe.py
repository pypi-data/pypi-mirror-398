from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typed_linq_collections._private_implementation_details.type_aliases import Selector
    from typed_linq_collections.q_iterable import QIterable

def pipe[TItem, TReturn](self: QIterable[TItem],
                         action: Selector[QIterable[TItem], TReturn]) -> TReturn:
    return action(self)
