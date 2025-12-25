from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Selector


def distinct_by[TItem, TKey](self: Iterable[TItem], key_selector: Selector[TItem, TKey]) -> Iterable[TItem]:
    seen: dict[TKey, TItem] = {}
    for item in self:
        key = key_selector(item)
        if key not in seen:
            seen[key] = item
            yield item
