from __future__ import annotations

from typing import TYPE_CHECKING

# noinspection PyPep8Naming
from typed_linq_collections._private_implementation_details.q_zero_overhead_collection_contructors import ZeroImportOverheadConstructors as C
from typed_linq_collections.q_errors import ArgumentError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections.collections.q_list import QList

def chunk[TItem](self: Iterable[TItem], size: int) -> Iterable[QList[TItem]]:
    if size <= 0:
        raise ArgumentError("Chunk size must be greater than 0")

    iterator = iter(self)
    while True:
        chunk_items: QList[TItem] = C.list()
        for _ in range(size):
            try:
                chunk_items.append(next(iterator))
            except StopIteration:
                if chunk_items:
                    yield chunk_items
                return
        yield chunk_items
