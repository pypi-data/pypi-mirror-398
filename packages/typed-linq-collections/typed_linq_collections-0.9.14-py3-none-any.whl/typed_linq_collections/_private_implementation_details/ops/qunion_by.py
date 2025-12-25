from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Selector

def qunion_by[TItem, TKey](self: Iterable[TItem], other: Iterable[TItem], key_selector: Selector[TItem, TKey]) -> Iterable[TItem]:
    seen_keys: set[TKey] = set()

    # First, yield distinct items from self based on key
    for item in self:
        item_key = key_selector(item)
        if item_key not in seen_keys:
            seen_keys.add(item_key)
            yield item

    # Then, yield items from other that have keys not seen in self
    for item in other:
        item_key = key_selector(item)
        if item_key not in seen_keys:
            seen_keys.add(item_key)
            yield item
