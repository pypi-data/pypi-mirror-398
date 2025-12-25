from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Selector


def select_many[T, TSubItem](self: Iterable[T], select_children: Selector[T, Iterable[TSubItem]]) -> Iterable[TSubItem]:
    return (child for parent in self for child in select_children(parent))
