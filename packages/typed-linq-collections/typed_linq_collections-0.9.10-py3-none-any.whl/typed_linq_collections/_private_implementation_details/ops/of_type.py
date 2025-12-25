from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections.q_iterable import QIterable


class _TypeTester:
    def __init__(self, type_: type) -> None:
        self.type_:type = type_
    def __call__(self, value: object) -> bool:
        return isinstance(value, self.type_)


def of_type[TItem, TResult](self: QIterable[TItem], type_: type[TResult]) -> Iterable[TResult]:
    return self.where(_TypeTester(type_)).cast.to(type_)
