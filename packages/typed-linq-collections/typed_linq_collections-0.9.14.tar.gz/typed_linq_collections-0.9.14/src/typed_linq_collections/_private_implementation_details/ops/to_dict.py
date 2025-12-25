from __future__ import annotations

from typing import TYPE_CHECKING

# noinspection PyPep8Naming
from typed_linq_collections._private_implementation_details.q_zero_overhead_collection_contructors import ZeroImportOverheadConstructors as C

if TYPE_CHECKING:
    from typed_linq_collections._private_implementation_details.type_aliases import Selector
    from typed_linq_collections.collections.q_dict import QDict
    from typed_linq_collections.q_iterable import QIterable


def to_dict[T, TKey, TValue](self: QIterable[T], key_selector: Selector[T, TKey], value_selector: Selector[T, TValue], allow_duplicates: bool = False) -> QDict[TKey, TValue]:
    if allow_duplicates:
        # Python dict behavior: last value wins
        return C.dict((key_selector(item), value_selector(item)) for item in self)

    # .NET behavior: raise exception on duplicates
    result_pairs: list[tuple[TKey, TValue]] = []
    seen_keys: set[TKey] = set()
    for item in self:
        key = key_selector(item)
        if key in seen_keys:
            raise ValueError(f"An element with the same key already exists: {key}")
        seen_keys.add(key)
        result_pairs.append((key, value_selector(item)))
    return C.dict(result_pairs)
