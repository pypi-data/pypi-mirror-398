from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

def skip_last[TItem](self: Iterable[TItem], count: int) -> Iterable[TItem]:
    if count <= 0:
        yield from self
    else:
        iterator = iter(self)
        buffer_into_the_past_of_the_iteration_count_items_long = deque[TItem](maxlen=count)

        try:
            for _ in range(count):
                buffer_into_the_past_of_the_iteration_count_items_long.append(next(iterator))  # fill the sliding window with the first count items without yielding them, we don't yet know if we are allowed to yield any of them
        except StopIteration:  # there are less items in the collection than we are supposed to skip, return no items
            return

        for item in iterator:  # start normal iteration of the items after the sliding window that we have created
            yield buffer_into_the_past_of_the_iteration_count_items_long[0]  # yield the oldest item in the sliding window, the one that we iterated through count items ago so we know we are allowed to yield it
            buffer_into_the_past_of_the_iteration_count_items_long.append(item)  # push the item we just iterated through into the sliding window pushing the yielded item out of the window
