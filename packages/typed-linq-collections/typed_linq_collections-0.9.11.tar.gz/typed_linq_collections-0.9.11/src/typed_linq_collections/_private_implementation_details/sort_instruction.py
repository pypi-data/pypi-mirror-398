from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from _typeshed import SupportsRichComparison

    from typed_linq_collections._private_implementation_details.type_aliases import Selector


class SortInstruction[TItem]:
    """Represents a single sorting instruction with key selector and direction.

    Used internally to store sorting criteria for multi-level sorting operations
    in QOrderedIterable. Each instruction contains a key selector function and
    a boolean indicating whether the sort should be descending.
    """
    __slots__: tuple[str, ...] = ("key_selector", "descending")

    def __init__(self, key_selector: Selector[TItem, SupportsRichComparison], descending: bool) -> None:
        """Initialize a new sort instruction.

        Args:
            key_selector: Function to extract sort key from elements.
            descending: True for descending order, False for ascending.
        """
        self.key_selector: Selector[TItem, SupportsRichComparison] = key_selector
        self.descending: bool = descending
