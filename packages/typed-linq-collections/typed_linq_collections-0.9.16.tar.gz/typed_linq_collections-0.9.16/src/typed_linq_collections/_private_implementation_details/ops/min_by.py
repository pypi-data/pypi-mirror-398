from __future__ import annotations

from typing import TYPE_CHECKING

from typed_linq_collections.q_errors import EmptyIterableError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from _typeshed import SupportsRichComparison

    from typed_linq_collections._private_implementation_details.type_aliases import Selector


def min_by[TItem, TKey: SupportsRichComparison](self: Iterable[TItem], key_selector: Selector[TItem, TKey]) -> TItem:
    iterator = iter(self)
    try:
        best_item = next(iterator)
        best_key = key_selector(best_item)
    except StopIteration:
        raise EmptyIterableError() from None

    for item in iterator:
        key = key_selector(item)
        if key < best_key:  # pyright: ignore [reportOperatorIssue]
            best_key = key
            best_item = item
    return best_item