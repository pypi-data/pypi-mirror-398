from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Selector


def where_key_not_in[TItem, TKey](self: Iterable[TItem], keys: Iterable[TKey], key_selector: Selector[TItem, TKey]) -> Iterable[TItem]:
    excluded_keys:set[TKey] = set(keys)
    seen_keys: set[TKey] = set()
    for item in self:
        item_key = key_selector(item)
        if item_key in excluded_keys:
            continue
        if item_key in seen_keys:
            continue
        seen_keys.add(item_key)
        yield item