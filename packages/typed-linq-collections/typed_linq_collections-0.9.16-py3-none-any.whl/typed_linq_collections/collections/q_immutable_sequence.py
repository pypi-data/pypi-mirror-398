from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, overload, override

# noinspection PyProtectedMember
from typed_linq_collections._private_implementation_details.immutable_sequence import ImmutableSequence
from typed_linq_collections.collections.q_sequence import QSequence

if TYPE_CHECKING:
    from collections.abc import Iterable


class QImmutableSequence[TItem](ImmutableSequence[TItem], QSequence[TItem]):
    """An immutable sequence that provides LINQ-style query operations with guaranteed ordering.

    QImmutableSequence offers the functionality of an ordered, indexed collection that cannot
    be modified after creation. It provides O(1) indexing and maintains element order while
    implementing the full QIterable interface for LINQ-style operations.

    This class is ideal for scenarios requiring immutable data structures with efficient
    indexed access, such as functional programming patterns, caching scenarios, or when
    you need to ensure data integrity across multiple operations.

    Inheritance:
    - Inherits from ImmutableSequence[TItem] for immutable sequence operations
    - Implements QSequence[TItem] for indexed access patterns
    - Implements QIterable[TItem] for LINQ-style query operations

    Key Features:
    - **Immutable**: Cannot be modified after creation, ensuring thread safety
    - **Indexed Access**: Supports efficient O(1) indexing and slicing operations
    - **Ordered**: Maintains insertion order consistently
    - **LINQ Operations**: Full suite of query methods returning new instances
    - **Slicing**: Slice operations return new QImmutableSequence instances
    - **Type Safety**: Maintains generic type information for compile-time safety
    - **Memory Efficient**: Optimized internal storage for immutable access patterns
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[TItem] = ()) -> None:
        """Initializes a new QImmutableSequence with elements from the given iterable.

        The sequence is created once and cannot be modified afterward. All elements
        from the iterable are copied into the internal storage, preserving their order.

        Args:
            iterable: An iterable of elements to initialize the sequence with.
                     Elements will be stored in the order they appear in the iterable.
                     Defaults to an empty sequence.

        Examples:
            >>> QImmutableSequence([1, 2, 3])
            [1, 2, 3]
        """
        super().__init__(list(iterable))

    @staticmethod
    def create[T](*sources: Iterable[T]) -> QImmutableSequence[T]:
        """Creates a new QImmutableSequence by concatenating elements from multiple iterables.

        This method is useful for combining collections of different subtypes into
        a common base type. Elements from all sources are concatenated in order.

        Args:
            *sources: One or more iterables of elements to concatenate.

        Returns:
            A new QImmutableSequence containing all elements from all sources in order.

        Examples:
            >>> QImmutableSequence.create([1, 2], [3, 4], [5, 6])
            [1, 2, 3, 4, 5, 6]
            >>> # Combining subtypes into base type
            >>> dogs = QImmutableSequence([...])
            >>> cats = QImmutableSequence([...])
            >>> all_animals: QImmutableSequence[Animal] = QImmutableSequence.create(dogs, cats)
        """
        if not sources:
            return QImmutableSequence()
        if len(sources) == 1:
            return QImmutableSequence(sources[0])
        return QImmutableSequence(chain(*sources))

    @overload
    def __getitem__(self, index: int) -> TItem: ...
    @overload
    def __getitem__(self, index: slice) -> QImmutableSequence[TItem]: ...

    @override
    def __getitem__(self, index: int | slice) -> TItem | QImmutableSequence[TItem]:
        """Gets an element by index or a slice of elements.

        This method provides efficient indexed access to sequence elements and supports
        slicing operations that return new QImmutableSequence instances.

        Args:
            index: Either an integer index for single element access, or a slice object
                  for range access. Negative indices are supported.

        Returns:
            For integer index: The element at that position.
            For slice: A new QImmutableSequence containing elements from the specified range.

        Raises:
            IndexError: If the integer index is out of bounds.

        Examples:
            >>> seq = QImmutableSequence([10, 20, 30, 40, 50])
            >>> seq[2]  # Single element
            30
            >>> seq[-1]  # Negative indexing supported
            50
            >>> seq[1:4]  # Slice returns new QImmutableSequence
            QImmutableSequence([20, 30, 40])
            >>> seq[1:4].where(lambda x: x > 25).to_list()  # Chain operations
            [30, 40]
        """
        if isinstance(index, slice):
            return QImmutableSequence(super().__getitem__(index))
        return super().__getitem__(index)
