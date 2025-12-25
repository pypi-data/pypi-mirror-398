from __future__ import annotations

from typing import TYPE_CHECKING

# noinspection PyPep8Naming
from typed_linq_collections._private_implementation_details.q_zero_overhead_collection_contructors import ZeroImportOverheadConstructors as C

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Selector
    from typed_linq_collections.collections.q_list import QList

def group_join[TOuter, TInner, TKey, TResult](
        self: Iterable[TOuter],
        other: Iterable[TInner],
        self_key: Selector[TOuter, TKey],
        group_key: Selector[TInner, TKey],
        select: Callable[[TOuter, QList[TInner]], TResult]
) -> Iterable[TResult]:
    groups_by_key: dict[TKey, QList[TInner]] = {}
    for other_item in other:
        key = group_key(other_item)
        if key not in groups_by_key:
            groups_by_key[key] = C.list()
        groups_by_key[key].append(other_item)

    for self_item in self:
        self_key_value = self_key(self_item)
        yield select(self_item, groups_by_key.get(self_key_value, C.list()))
