from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Selector

def select[T, TResult](self: Iterable[T], selector: Selector[T, TResult]) -> Iterable[TResult]:
    return (selector(item) for item in self)
