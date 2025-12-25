from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Selector

def join[TOuter, TInner, TKey, TResult](
        first: Iterable[TOuter],
        second: Iterable[TInner],
        first_key: Selector[TOuter, TKey],
        second_key: Selector[TInner, TKey],
        select: Callable[[TOuter, TInner], TResult]
) -> Iterable[TResult]:
    inner_lookup: dict[TKey, list[TInner]] = {}
    for inner_item in second:
        key = second_key(inner_item)
        if key not in inner_lookup:
            inner_lookup[key] = []
        inner_lookup[key].append(inner_item)

    # For each outer element, find matching inner elements and yield results
    for outer_item in first:
        outer_key = first_key(outer_item)
        if outer_key in inner_lookup:
            for inner_item in inner_lookup[outer_key]:
                yield select(outer_item, inner_item)
