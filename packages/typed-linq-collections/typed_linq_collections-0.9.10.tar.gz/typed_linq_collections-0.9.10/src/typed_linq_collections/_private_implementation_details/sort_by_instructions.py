from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.sort_instruction import SortInstruction


def sort_by_instructions[TItem](self: Iterable[TItem], sort_instructions: list[SortInstruction[TItem]]) -> Iterable[TItem]:
    items = list(self)
    for instruction in sort_instructions:  # the official documentation recommends multiple sort passes. Unless proven to perform badly in the common usage scenarios by actual performance testing, let's keep it simple: https://docs.python.org/3/howto/sorting.html
        items.sort(key=instruction.key_selector, reverse=instruction.descending)

    yield from items
