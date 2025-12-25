from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, Self, override

from typed_linq_collections.q_iterable import QIterable

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Set as AbstractSet


class QSet[TItem](set[TItem], QIterable[TItem]):
    """A mutable set that extends Python's built-in set with LINQ-style query operations.

    QSet provides all the functionality of Python's standard set while also implementing
    the full QIterable interface for LINQ-style operations. It maintains all the performance
    characteristics and uniqueness constraints of the built-in set, making it a drop-in
    replacement that adds powerful querying capabilities.

    Inheritance:
    - Inherits from set[TItem] for all standard set operations and seamless interoperability with the built-in set
    - Implements QIterable[TItem] for LINQ-style query operations
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[TItem] = ()) -> None:
        """Initializes a new QSet with unique elements from the given iterable.

        Duplicate elements in the input iterable are automatically removed, maintaining
        only unique values as per standard set behavior.

        Args:
            iterable: An iterable of elements to initialize the set with.
                     Duplicates will be automatically removed.
                     Defaults to an empty sequence.

        Examples:
            >>> QSet([1, 2, 3])
            {1, 2, 3}
            >>> QSet([1, 2, 2])
            {1, 2}
        """
        super().__init__(iterable)

    @staticmethod
    def create[T](*sources: Iterable[T]) -> QSet[T]:
        """Creates a new QSet by combining elements from multiple iterables.

        This method is useful for combining collections of different subtypes into
        a common base type. Elements from all sources are combined and deduplicated.

        Args:
            *sources: One or more iterables of elements to combine.
                     Duplicates across all sources will be removed.

        Returns:
            A new QSet containing unique elements from all sources.

        Examples:
            >>> QSet.create([1, 2], [2, 3], [3, 4])
            {1, 2, 3, 4}
            >>> # Combining subtypes into base type
            >>> dogs: QSet[Dog] = QSet([...])
            >>> cats: QSet[Cat] = QSet([...])
            >>> all_animals: QSet[Animal] = QSet.create(dogs, cats)
        """
        if not sources:
            return QSet()
        if len(sources) == 1:
            return QSet(sources[0])
        return QSet(chain(*sources))

    @override
    def _optimized_length(self) -> int: return len(self)

    @override
    def contains(self, value: TItem) -> bool:
        """Determines whether the set contains the specified element.

        This method provides O(1) average-case performance for membership testing,
        leveraging the underlying set's hash table implementation. It's part of the
        QIterable interface and provides a consistent API across all collection types.

        Args:
            value: The element to search for in the set.

        Returns:
            True if the element is found in the set, False otherwise.

        Examples:
            >>> qset = QSet([1, 2, 3, 4, 5])
            >>> qset.contains(3)
            True
            >>> qset.contains(10)
            False
            >>> # Equivalent to using 'in' operator
            >>> 3 in qset
            True
        """
        return value in self

    # Binary operators
    @override
    def __or__(self, other: AbstractSet[TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return type(self)(super().__or__(other))  # type: ignore[arg-type]  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

    def __ror__(self, other: AbstractSet[TItem]) -> Self:
        return type(self)(set.__or__(set(other), self))  # type: ignore[arg-type]  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

    @override
    def __and__(self, other: AbstractSet[TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return type(self)(super().__and__(other))  # type: ignore[arg-type]  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

    def __rand__(self, other: AbstractSet[TItem]) -> Self:
        return type(self)(set.__and__(set(other), self))  # type: ignore[arg-type]  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

    @override
    def __sub__(self, other: AbstractSet[TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return type(self)(super().__sub__(other))  # type: ignore[arg-type]  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

    def __rsub__(self, other: AbstractSet[TItem]) -> Self:
        return type(self)(set.__sub__(set(other), self))  # type: ignore[arg-type]  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

    @override
    def __xor__(self, other: AbstractSet[TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return type(self)(super().__xor__(other))  # type: ignore[arg-type]  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

    def __rxor__(self, other: AbstractSet[TItem]) -> Self:
        return type(self)(set.__xor__(set(other), self))  # type: ignore[arg-type]  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]

    # In-place operators
    @override
    def __ior__(self, other: AbstractSet[TItem]) -> Self:
        super().__ior__(other)
        return self

    @override
    def __iand__(self, other: AbstractSet[TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        super().__iand__(other)
        return self

    @override
    def __isub__(self, other: AbstractSet[TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        super().__isub__(other)
        return self

    @override
    def __ixor__(self, other: AbstractSet[TItem]) -> Self:
        super().__ixor__(other)
        return self

    # Methods
    @override
    def copy(self) -> Self:
        return type(self)(super().copy())

    @override
    def union(self, *others: Iterable[TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return type(self)(super().union(*others))

    @override
    def intersection(self, *others: Iterable[TItem]) -> Self:
        return type(self)(super().intersection(*others))

    @override
    def difference(self, *others: Iterable[TItem]) -> Self:
        return type(self)(super().difference(*others))

    @override
    def symmetric_difference(self, other: Iterable[TItem]) -> Self:
        return type(self)(super().symmetric_difference(other))
