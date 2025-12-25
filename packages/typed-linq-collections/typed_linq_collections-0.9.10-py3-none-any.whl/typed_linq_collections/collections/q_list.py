from __future__ import annotations

import sys
from itertools import chain
from typing import TYPE_CHECKING, Self, SupportsIndex, cast, overload, override

# noinspection PyProtectedMember
from typed_linq_collections._private_implementation_details.q_lazy_iterable import QLazyIterableImplementation
from typed_linq_collections.collections.q_sequence import QSequence
from typed_linq_collections.q_iterable import QIterable

if TYPE_CHECKING:
    from collections.abc import Iterable

class QList[TItem](list[TItem], QSequence[TItem], QIterable[TItem]):
    """A mutable list that extends Python's built-in list with LINQ-style query operations.

    QList provides all the functionality of Python's standard list while also implementing
    the full QIterable interface for LINQ-style operations. It maintains all the performance
    characteristics and mutability of the built-in list, making it a drop-in replacement
    that adds powerful querying capabilities.

    Inheritance:
    - Inherits from list[TItem] for all standard list operations and seamless interoperability with the built-in list
    - Implements QIterable[TItem] for LINQ-style query operations
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[TItem] = ()) -> None:
        """Initializes a new QList with elements from the given iterable.

        Args:
            iterable: An iterable of elements to initialize the list with.
                     Defaults to an empty sequence.

        Examples:
            >>> QList([1, 2, 3])
            [1, 2, 3]
        """
        super().__init__(iterable)

    @staticmethod
    def create[T](*sources: Iterable[T]) -> QList[T]:
        """Creates a new QList by concatenating elements from multiple iterables.

        This method is useful for combining collections of different subtypes into
        a common base type. Elements from all sources are concatenated in order.

        Args:
            *sources: One or more iterables of elements to concatenate.

        Returns:
            A new QList containing all elements from all sources in order.

        Examples:
            >>> QList.create([1, 2], [3, 4], [5, 6])
            [1, 2, 3, 4, 5, 6]
            >>> # Combining subtypes into base type
            >>> dogs: QList[Dog] = QList([...])
            >>> cats: QList[Cat] = QList([...])
            >>> all_animals: QList[Animal] = QList.create(dogs, cats)
        """
        if not sources:
            return QList()
        if len(sources) == 1:
            return QList(sources[0])
        return QList(chain(*sources))

    def discard(self, value: TItem) -> None:
        """Remove the first occurrence of a value from the list without raising an error.

        If the value is not found, this method does nothing (silent success).
        This provides consistency with set.discard() behavior.

        Args:
            value: The value to remove from the list.

        Examples:
            >>> lst = QList([1, 2, 3, 2])
            >>> lst.discard(2)
            >>> lst
            [1, 3, 2]
            >>> lst.discard(999)  # No error
        """
        if value in self:
            self.remove(value)

    @override
    def _optimized_length(self) -> int: return len(self)

    @override
    def reversed(self) -> QIterable[TItem]: return QLazyIterableImplementation[TItem](lambda: reversed(self))

    @override
    def element_at(self, index: int) -> TItem:
        if index < 0:
            raise IndexError(f"Index {index} was outside the bounds of the collection.")
        return self[index]

    @override
    def index(self, value: TItem, start: SupportsIndex = 0, stop: SupportsIndex = sys.maxsize) -> int:
        return super().index(value, start, stop)

    @override
    def count(self, value: TItem) -> int: return super().count(value)

    @overload
    def __getitem__(self, index: SupportsIndex) -> TItem: ...

    @overload
    def __getitem__(self, index: slice) -> QList[TItem]: ...

    @override
    def __getitem__(self, index: SupportsIndex | slice) -> TItem | QList[TItem]:
        """Gets an element by index or a slice of elements.

        This method extends the standard list indexing behavior to return QList instances
        for slice operations, enabling continued method chaining with LINQ operations.
        Single index access returns the element directly, while slice access returns
        a new QList containing the sliced elements.

        Args:
            index: Either an integer index for single element access, or a slice object
                  for range access.

        Returns:
            For integer index: The element at that position.
            For slice: A new QList containing elements from the specified range.

        Examples:
            >>> qlist = QList([10, 20, 30, 40, 50])
            >>> qlist[2]  # Single element
            30
            >>> qlist[1:4]  # Slice returns QList
            QList([20, 30, 40])
            >>> qlist[1:4].where(lambda x: x > 25).to_list()  # Chain operations
            [30, 40]
        """
        if isinstance(index, slice):
            return QList(super().__getitem__(index))
        return super().__getitem__(index)

    @override
    def __add__(self, other: list[TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return type(self)(super().__add__(other))

    def __radd__(self, other: list[TItem]) -> Self:
        return type(self)(cast(list[TItem], list.__add__(other, self)))  # pyright: ignore[reportUnknownMemberType]

    @override
    def __mul__(self, other: int) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return type(self)(super().__mul__(other))

    @override
    def __rmul__(self, other: int) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return type(self)(cast(list[TItem], list.__mul__(self, other)))  # pyright: ignore[reportUnknownMemberType]

    @override
    def __iadd__(self, other: list[TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        super().__iadd__(other)
        return self

    @override
    def __imul__(self, other: int) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        super().__imul__(other)
        return self

    @override
    def copy(self) -> Self:
        return type(self)(super().copy())
