from __future__ import annotations

from typed_linq_collections.collections.q_list import QList


class QGrouping[TKey, TElement](QList[TElement]):
    """Represents a collection of objects that have a common key."""
    __slots__: tuple[str, ...] = ("key",)

    def __init__(self, values: tuple[TKey, QList[TElement]]) -> None:
        """Initialize a grouping with a key and list of grouped elements.

        Args:
            values: A tuple containing (key, list_of_elements) where the key
                   is the grouping criterion and the list contains all elements
                   that share this key.
        """
        super().__init__(values[1])
        self.key: TKey = values[0]
