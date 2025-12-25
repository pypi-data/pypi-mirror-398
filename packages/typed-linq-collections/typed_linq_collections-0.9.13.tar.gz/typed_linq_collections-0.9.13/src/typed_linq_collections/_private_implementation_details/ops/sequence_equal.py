from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

def sequence_equal[TItem](self: Iterable[TItem], other: Iterable[TItem]) -> bool:
    self_iterator = iter(self)
    other_iterator = iter(other)

    while True:
        try:
            self_current_element = next(self_iterator)
        except StopIteration:
            try:
                next(other_iterator)
                return False  # self shorter than other  # noqa: TRY300
            except StopIteration:
                return True

        try:
            other_current_element = next(other_iterator)
        except StopIteration:
            return False  # Other shorter than self

        if self_current_element != other_current_element:
            return False
