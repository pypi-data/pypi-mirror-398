from __future__ import annotations

from typing import TYPE_CHECKING

# noinspection PyPep8Naming
from typed_linq_collections._private_implementation_details.q_zero_overhead_collection_contructors import ZeroImportOverheadConstructors as C

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Selector
    from typed_linq_collections.collections.q_dict import QDict
    from typed_linq_collections.collections.q_key_value_pair import KeyValuePair
    from typed_linq_collections.q_iterable import QIterable

def qcount_by[TItem, TKey](self: Iterable[TItem], key_selector: Selector[TItem, TKey]) -> QIterable[KeyValuePair[TKey, int]]:
    counts: QDict[TKey, int] = C.dict()

    for item in self:
        key = key_selector(item)
        counts[key] = counts.get(key, 0) + 1

    return counts.qitems()