from __future__ import annotations

import statistics
from abc import ABC
from typing import TYPE_CHECKING, cast, override

# noinspection PyProtectedMember
from typed_linq_collections._private_implementation_details.q_lazy_iterable import QLazyIterableImplementation

# noinspection PyProtectedMember
from typed_linq_collections._private_implementation_details.sort_instruction import SortInstruction
from typed_linq_collections.collections.q_frozen_set import QFrozenSet
from typed_linq_collections.collections.q_immutable_sequence import QImmutableSequence
from typed_linq_collections.collections.q_list import QList
from typed_linq_collections.collections.q_set import QSet
from typed_linq_collections.q_errors import EmptyIterableError
from typed_linq_collections.q_iterable import QIterable
from typed_linq_collections.q_ordered_iterable import QOrderedIterable

if TYPE_CHECKING:
    from collections.abc import Iterable

    from _typeshed import SupportsRichComparison

    # noinspection PyProtectedMember
    from typed_linq_collections._private_implementation_details.type_aliases import Func, Predicate, Selector

class QIntIterable(QIterable[int], ABC):
    """An abstract base class for LINQ-style query operations on iterables of integers.

    Extends QIterable with integer-specific numeric operations such as sum, min, max,
    and average. All operations are optimized for integer arithmetic and provide
    appropriate default values and error handling for empty collections.

    This class serves as the base for all integer collection types including
    QIntList, QIntSet, QIntSequence, and QIntFrozenSet.
    """
    __slots__: tuple[str, ...] = ()

    def sum(self) -> int:
        """Calculates the sum of all integers in this iterable.

        Returns:
            The sum of all integers. Returns 0 for empty collections.

        Examples:
            >>> query([1, 2, 3, 4]).as_ints().sum()
            10
            >>> query([]).as_ints().sum()
            0
        """
        return sum(self)

    def min(self) -> int:
        """Finds the minimum integer in this iterable.

        Returns:
            The smallest integer in the iterable.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> query([3, 1, 4, 2]).as_ints().min()
            1
            >>> query([]).as_ints().min()  # Raises EmptyIterableError

        See Also:
            min_or_default(): Returns 0 instead of raising for empty collections.
        """
        try:
            return min(self)
        except ValueError:
            raise EmptyIterableError() from None

    def max(self) -> int:
        """Finds the maximum integer in this iterable.

        Returns:
            The largest integer in the iterable.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> query([3, 1, 4, 2]).as_ints().max()
            4
            >>> query([]).as_ints().max()  # Raises EmptyIterableError

        See Also:
            max_or_default(): Returns 0 instead of raising for empty collections.
        """
        try:
            return max(self)
        except ValueError:
            raise EmptyIterableError() from None

    def min_or_default(self) -> int:
        """Finds the minimum integer in this iterable, or returns 0 if empty.

        Returns:
            The smallest integer in the iterable, or 0 if the iterable is empty.

        Examples:
            >>> query([3, 1, 4, 2]).as_ints().min_or_default()
            1
            >>> query([]).as_ints().min_or_default()
            0
        """
        return min(self) if self.any() else 0

    def max_or_default(self) -> int:
        """Finds the maximum integer in this iterable, or returns 0 if empty.

        Returns:
            The largest integer in the iterable, or 0 if the iterable is empty.

        Examples:
            >>> query([3, 1, 4, 2]).as_ints().max_or_default()
            4
            >>> query([]).as_ints().max_or_default()
            0
        """
        return max(self) if self.any() else 0

    def average(self) -> float:
        """Calculates the arithmetic mean of all integers in this iterable.

        Returns:
            The average of all integers as a float.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> query([1, 2, 3]).as_ints().average()
            2.0
            >>> query([2, 4]).as_ints().average()
            3.0
            >>> query([]).as_ints().average()  # Raises EmptyIterableError

        See Also:
            average_or_default(): Returns 0.0 instead of raising for empty collections.
        """
        return statistics.mean(self._assert_not_empty())

    def average_or_default(self) -> float:
        """Calculates the arithmetic mean of all integers, or returns 0.0 if empty.

        Returns:
            The average of all integers as a float, or 0.0 if the iterable is empty.

        Examples:
            >>> query([1, 2, 3]).as_ints().average_or_default()
            2.0
            >>> query([]).as_ints().average_or_default()
            0.0
        """
        return statistics.mean(self) if self.any() else 0.0

    @override
    def _lazy(self, factory: Func[Iterable[int]]) -> QIntIterable: return QIntIterableImplementation(factory)

    @override
    def _order_by(self, key_selector: Selector[int, SupportsRichComparison], descending: bool) -> QOrderedIterable[int]:
        return QIntOrderedIterable(lambda: self, [SortInstruction(key_selector, descending)])

    @staticmethod
    def _selfcast(iterable: QIterable[int]) -> QIntIterable: return cast(QIntIterable, iterable)
    @staticmethod
    def _selfcast_ordered(iterable: QOrderedIterable[int]) -> QIntOrderedIterable: return cast(QIntOrderedIterable, iterable)

    # region override methods so that typecheckers know that we actually return QIntIterables now, not QIterable[int]
    # call the base method to eliminate code duplication. The base class will call lazy from just above, so it is already the correct type
    @override
    def where(self, predicate: Predicate[int]) -> QIntIterable: return self._selfcast(super().where(predicate))
    @override
    def where_not_none(self) -> QIntIterable: return self._selfcast(super().where_not_none())
    @override
    def distinct(self) -> QIntIterable: return self._selfcast(super().distinct())
    @override
    def distinct_by[TKey](self, key_selector: Selector[int, TKey]) -> QIntIterable: return self._selfcast(super().distinct_by(key_selector))
    @override
    def take(self, count: int) -> QIntIterable: return self._selfcast(super().take(count))
    @override
    def take_while(self, predicate: Predicate[int]) -> QIntIterable: return self._selfcast(super().take_while(predicate))
    @override
    def take_last(self, count: int) -> QIntIterable: return self._selfcast(super().take_last(count))
    @override
    def skip(self, count: int) -> QIntIterable: return self._selfcast(super().skip(count))
    @override
    def skip_last(self, count: int) -> QIntIterable: return self._selfcast(super().skip_last(count))
    @override
    def reversed(self) -> QIntIterable: return self._selfcast(super().reversed())

    @override
    def concat(self, *others: Iterable[int]) -> QIntIterable: return self._selfcast(super().concat(*others))

    @override
    def order_by(self, key_selector: Selector[int, SupportsRichComparison]) -> QIntOrderedIterable: return self._selfcast_ordered(super().order_by(key_selector))
    @override
    def order_by_descending(self, key_selector: Selector[int, SupportsRichComparison]) -> QIntOrderedIterable: return self._selfcast_ordered(super().order_by_descending(key_selector))
    # endregion

    @override
    def to_list(self) -> QIntList: return QIntList(self)

    @override
    def to_sequence(self) -> QIntSequence: return QIntSequence(self)

    @override
    def to_tuple(self) -> tuple[int, ...]: return tuple(self)

    @override
    def to_set(self) -> QIntSet: return QIntSet(self)

    @override
    def to_frozenset(self) -> QIntFrozenSet: return QIntFrozenSet(self)

class QIntIterableImplementation(QLazyIterableImplementation[int], QIntIterable):
    """Internal implementation of QIntIterable that defers execution until iteration.

    This class provides the concrete implementation for lazy integer iterables,
    combining lazy evaluation from QLazyIterableImplementation with integer-specific
    numeric operations from QIntIterable.
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, factory: Func[Iterable[int]]) -> None:
        """Initialize with a factory function that produces integer iterables.

        Args:
            factory: A function that returns an iterable of integers when called.
        """
        super().__init__(factory)

class QIntOrderedIterable(QOrderedIterable[int], QIntIterable):
    """An ordered iterable of integers that supports multi-level sorting and numeric operations.

    Combines the multi-level sorting capabilities of QOrderedIterable with the
    integer-specific numeric operations from QIntIterable. This allows for complex
    sorting scenarios while maintaining access to methods like sum, min, max, and average.
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, factory: Func[Iterable[int]], sorting_instructions: list[SortInstruction[int]]) -> None:
        """Initialize with a factory and sorting instructions for integers.

        Args:
            factory: A function that produces the source iterable of integers.
            sorting_instructions: A list of sorting instructions defining the sort order.
        """
        super().__init__(factory, sorting_instructions)

class QIntList(QList[int], QIntIterable):
    """A mutable list of integers with LINQ-style query operations and numeric methods.

    Combines the functionality of a standard list with integer-specific operations
    like sum, min, max, and average. Elements can be added, removed, and modified
    while maintaining access to all LINQ-style query methods.

    Args:
        iterable: An optional iterable of integers to initialize the list.
                 Defaults to an empty list.

    Examples:
        >>> int_list = QIntList([1, 2, 3, 4])
        >>> int_list.sum()
        10
        >>> int_list.where(lambda x: x > 2).to_list()
        [3, 4]
        >>> int_list.append(5)
        >>> int_list.average()
        3.0
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[int] = ()) -> None:
        super().__init__(iterable)

    @override
    def reversed(self) -> QIntIterable: return QIntIterable.reversed(self)

class QIntSet(QSet[int], QIntIterable):
    """A mutable set of unique integers with LINQ-style query operations and numeric methods.

    Maintains a collection of unique integers while providing integer-specific operations
    like sum, min, max, and average. Duplicate values are automatically excluded,
    and all standard set operations are available alongside LINQ query methods.

    Args:
        iterable: An optional iterable of integers to initialize the set.
                 Duplicates will be automatically removed. Defaults to an empty set.

    Examples:
        >>> int_set = QIntSet([1, 2, 2, 3, 3, 4])
        >>> len(int_set)  # Duplicates removed
        4
        >>> int_set.sum()
        10
        >>> int_set.where(lambda x: x > 2).to_list()
        [3, 4]  # Order may vary
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[int] = ()) -> None:
        super().__init__(iterable)

class QIntFrozenSet(QFrozenSet[int], QIntIterable):
    """An immutable set of unique integers with LINQ-style query operations and numeric methods.

    An immutable, hashable collection of unique integers that provides integer-specific
    operations like sum, min, max, and average. Once created, the set cannot be modified,
    making it suitable for use as dictionary keys or in other sets.

    Args:
        iterable: An optional iterable of integers to initialize the frozen set.
                 Duplicates will be automatically removed. Defaults to an empty set.

    Examples:
        >>> int_frozenset = QIntFrozenSet([1, 2, 2, 3, 3, 4])
        >>> len(int_frozenset)  # Duplicates removed
        4
        >>> int_frozenset.sum()
        10
        >>> int_frozenset.where(lambda x: x > 2).to_list()
        [3, 4]  # Order may vary
        >>> hash(int_frozenset)  # Hashable since immutable
        1234567890  # Example hash value
    """
    __slots__: tuple[str, ...] = ()

    def __new__(cls, iterable: Iterable[int] = ()) -> QIntFrozenSet:
        return super().__new__(cls, iterable)  # pyright: ignore [reportReturnType]

class QIntSequence(QImmutableSequence[int], QIntIterable):
    """An immutable sequence of integers with LINQ-style query operations and numeric methods.

    An immutable, ordered collection of integers that provides integer-specific operations
    like sum, min, max, and average. Elements maintain their insertion order and can be
    accessed by index, but the sequence cannot be modified after creation.

    Args:
        iterable: An optional iterable of integers to initialize the sequence.
                 Order is preserved and duplicates are allowed. Defaults to an empty sequence.

    Examples:
        >>> int_sequence = QIntSequence([3, 1, 4, 1, 5])
        >>> int_sequence[2]  # Access by index
        4
        >>> int_sequence.sum()
        14
        >>> int_sequence.where(lambda x: x > 2).to_list()
        [3, 4, 5]
        >>> int_sequence.reversed().to_list()
        [5, 1, 4, 1, 3]
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[int] = ()) -> None:
        super().__init__(iterable)

    @override
    def reversed(self) -> QIntIterable: return QIntIterable.reversed(self)
