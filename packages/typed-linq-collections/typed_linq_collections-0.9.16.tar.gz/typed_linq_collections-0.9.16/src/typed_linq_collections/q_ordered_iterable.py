from __future__ import annotations

from typing import TYPE_CHECKING, override

# noinspection PyProtectedMember
import typed_linq_collections._private_implementation_details.ops as ops

# noinspection PyProtectedMember
from typed_linq_collections._private_implementation_details.sort_instruction import SortInstruction
from typed_linq_collections.q_iterable import QIterable

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from _typeshed import SupportsRichComparison

    # noinspection PyProtectedMember
    from typed_linq_collections._private_implementation_details.type_aliases import Func, Selector


class QOrderedIterable[TItem](QIterable[TItem]):
    """An iterable that maintains multiple levels of sorting operations.

    QOrderedIterable allows chaining multiple sorting criteria using then_by() and
    then_by_descending() methods. This enables complex multi-level sorting where
    elements are first sorted by the primary key, then by secondary keys for elements
    with equal primary keys, and so on.

    The sorting is performed lazily - the actual sorting occurs only when the
    iterable is enumerated.
    """
    __slots__: tuple[str, ...] = ("sorting_instructions", "_factory")

    def __init__(self, factory: Func[Iterable[TItem]], sorting_instructions: list[SortInstruction[TItem]]) -> None:
        """Initialize a new QOrderedIterable.

        Args:
            factory: A function that produces the source iterable.
            sorting_instructions: A list of sorting instructions defining the sort order.
        """
        self.sorting_instructions: list[SortInstruction[TItem]] = sorting_instructions
        self._factory: Func[Iterable[TItem]] = factory

    def then_by(self, key_selector: Selector[TItem, SupportsRichComparison]) -> QOrderedIterable[TItem]:
        """Add a secondary ascending sort criterion.

        Elements that are equal according to previous sorting criteria will be
        further sorted by this key selector in ascending order.

        Args:
            key_selector: A function that extracts the sort key from each element.

        Returns:
            A new QOrderedIterable with the additional sort criterion.

        Examples:
            >>> people = [("Alice", 25), ("Bob", 30), ("Alice", 20)]
            >>> result = (query(people)
            ...           .order_by(lambda p: p[0])  # Sort by name first
            ...           .then_by(lambda p: p[1])   # Then by age
            ...           .to_list())
            [('Alice', 20), ('Alice', 25), ('Bob', 30)]
        """
        return QOrderedIterable(self._factory, self.sorting_instructions + [SortInstruction(key_selector, descending=False)])

    def then_by_descending(self, key_selector: Selector[TItem, SupportsRichComparison]) -> QOrderedIterable[TItem]:
        """Add a secondary descending sort criterion.

        Elements that are equal according to previous sorting criteria will be
        further sorted by this key selector in descending order.

        Args:
            key_selector: A function that extracts the sort key from each element.

        Returns:
            A new QOrderedIterable with the additional sort criterion.

        Examples:
            >>> people = [("Alice", 25), ("Bob", 30), ("Alice", 20)]
            >>> result = (query(people)
            ...           .order_by(lambda p: p[0])              # Sort by name first (ascending)
            ...           .then_by_descending(lambda p: p[1])    # Then by age (descending)
            ...           .to_list())
            [('Alice', 25), ('Alice', 20), ('Bob', 30)]
        """
        return QOrderedIterable(self._factory, self.sorting_instructions + [SortInstruction(key_selector, descending=True)])

    @override
    def __iter__(self) -> Iterator[TItem]: yield from ops.sort_by_instructions(self._factory(), self.sorting_instructions)
