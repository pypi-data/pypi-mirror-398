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

class QFloatIterable(QIterable[float], ABC):
    """An abstract base class for LINQ-style query operations on iterables of floats.

    Extends QIterable with float-specific numeric operations such as sum, min, max,
    and average. All operations handle floating-point arithmetic and provide
    appropriate default values and error handling for empty collections.

    This class serves as the base for all float collection types including
    QFloatList, QFloatSet, QFloatSequence, and QFloatFrozenSet.
    """
    __slots__: tuple[str, ...] = ()

    def sum(self) -> float:
        """Calculates the sum of all floats in this iterable.

        Returns:
            The sum of all floats. Returns 0.0 for empty collections.

        Examples:
            >>> query([1.5, 2.5, 3.0]).as_floats().sum()
            7.0
            >>> query([]).as_floats().sum()
            0.0
        """
        return sum(self)

    def min(self) -> float:
        """Finds the minimum float in this iterable.

        Returns:
            The smallest float in the iterable.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> query([3.5, 1.2, 4.8, 2.1]).as_floats().min()
            1.2
            >>> query([]).as_floats().min()  # Raises EmptyIterableError

        See Also:
            min_or_default(): Returns 0.0 instead of raising for empty collections.
        """
        try:
            return min(self)
        except ValueError:
            raise EmptyIterableError() from None

    def max(self) -> float:
        """Finds the maximum float in this iterable.

        Returns:
            The largest float in the iterable.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> query([3.5, 1.2, 4.8, 2.1]).as_floats().max()
            4.8
            >>> query([]).as_floats().max()  # Raises EmptyIterableError

        See Also:
            max_or_default(): Returns 0.0 instead of raising for empty collections.
        """
        try:
            return max(self)
        except ValueError:
            raise EmptyIterableError() from None

    def min_or_default(self) -> float:
        """Finds the minimum float in this iterable, or returns 0.0 if empty.

        Returns:
            The smallest float in the iterable, or 0.0 if the iterable is empty.

        Examples:
            >>> query([3.5, 1.2, 4.8, 2.1]).as_floats().min_or_default()
            1.2
            >>> query([]).as_floats().min_or_default()
            0.0
        """
        return min(self) if self.any() else 0.0

    def max_or_default(self) -> float:
        """Finds the maximum float in this iterable, or returns 0.0 if empty.

        Returns:
            The largest float in the iterable, or 0.0 if the iterable is empty.

        Examples:
            >>> query([3.5, 1.2, 4.8, 2.1]).as_floats().max_or_default()
            4.8
            >>> query([]).as_floats().max_or_default()
            0.0
        """
        return max(self) if self.any() else 0.0

    def average(self) -> float:
        """Calculates the arithmetic mean of all floats in this iterable.

        Returns:
            The average of all floats.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> query([1.0, 2.0, 3.0]).as_floats().average()
            2.0
            >>> query([2.5, 7.5]).as_floats().average()
            5.0
            >>> query([]).as_floats().average()  # Raises EmptyIterableError

        See Also:
            average_or_default(): Returns 0.0 instead of raising for empty collections.
        """
        return statistics.mean(self._assert_not_empty())

    def average_or_default(self) -> float:
        """Calculates the arithmetic mean of all floats, or returns 0.0 if empty.

        Returns:
            The average of all floats, or 0.0 if the iterable is empty.

        Examples:
            >>> query([1.0, 2.0, 3.0]).as_floats().average_or_default()
            2.0
            >>> query([]).as_floats().average_or_default()
            0.0
        """
        return statistics.mean(self) if self.any() else 0.0

    @override
    def _lazy(self, factory: Func[Iterable[float]]) -> QFloatIterable: return QFloatIterableImplementation(factory)

    @override
    def _order_by(self, key_selector: Selector[float, SupportsRichComparison], descending: bool) -> QOrderedIterable[float]:
        return QFloatOrderedIterable(lambda: self, [SortInstruction(key_selector, descending)])

    @staticmethod
    def _selfcast(iterable: QIterable[float]) -> QFloatIterable: return cast(QFloatIterable, iterable)
    @staticmethod
    def _selfcast_ordered(iterable: QOrderedIterable[float]) -> QFloatOrderedIterable: return cast(QFloatOrderedIterable, iterable)

    # region override methods so that typecheckers know that we actually return QFloatIterables now, not QIterable[float]
    # call the base method to eliminate code duplication. The base class will call lazy from just above, so it is already the correct type
    @override
    def where(self, predicate: Predicate[float]) -> QFloatIterable: return self._selfcast(super().where(predicate))
    @override
    def where_not_none(self) -> QFloatIterable: return self._selfcast(super().where_not_none())
    @override
    def distinct(self) -> QFloatIterable: return self._selfcast(super().distinct())
    @override
    def distinct_by[TKey](self, key_selector: Selector[float, TKey]) -> QFloatIterable: return self._selfcast(super().distinct_by(key_selector))
    @override
    def take(self, count: int) -> QFloatIterable: return self._selfcast(super().take(count))
    @override
    def take_while(self, predicate: Predicate[float]) -> QFloatIterable: return self._selfcast(super().take_while(predicate))
    @override
    def take_last(self, count: int) -> QFloatIterable: return self._selfcast(super().take_last(count))
    @override
    def skip(self, count: int) -> QFloatIterable: return self._selfcast(super().skip(count))
    @override
    def skip_last(self, count: int) -> QFloatIterable: return self._selfcast(super().skip_last(count))
    @override
    def reversed(self) -> QFloatIterable: return self._selfcast(super().reversed())

    @override
    def concat(self, *others: Iterable[float]) -> QFloatIterable: return self._selfcast(super().concat(*others))

    @override
    def order_by(self, key_selector: Selector[float, SupportsRichComparison]) -> QFloatOrderedIterable: return self._selfcast_ordered(super().order_by(key_selector))
    @override
    def order_by_descending(self, key_selector: Selector[float, SupportsRichComparison]) -> QFloatOrderedIterable: return self._selfcast_ordered(super().order_by_descending(key_selector))
    # endregion

    @override
    def to_list(self) -> QFloatList: return QFloatList(self)

    @override
    def to_sequence(self) -> QFloatSequence: return QFloatSequence(self)

    @override
    def to_tuple(self) -> tuple[float, ...]: return tuple(self)

    @override
    def to_set(self) -> QFloatSet: return QFloatSet(self)

    @override
    def to_frozenset(self) -> QFloatFrozenSet: return QFloatFrozenSet(self)

class QFloatIterableImplementation(QLazyIterableImplementation[float], QFloatIterable):
    """Internal implementation of QFloatIterable that defers execution until iteration.

    This class provides the concrete implementation for lazy float iterables,
    combining lazy evaluation from QLazyIterableImplementation with float-specific
    numeric operations from QFloatIterable.
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, factory: Func[Iterable[float]]) -> None:
        """Initialize with a factory function that produces float iterables.

        Args:
            factory: A function that returns an iterable of floats when called.
        """
        super().__init__(factory)

class QFloatOrderedIterable(QOrderedIterable[float], QFloatIterable):
    """An ordered iterable of floats that supports multi-level sorting and numeric operations.

    Combines the multi-level sorting capabilities of QOrderedIterable with the
    float-specific numeric operations from QFloatIterable. This allows for complex
    sorting scenarios while maintaining access to methods like sum, min, max, and average.
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, factory: Func[Iterable[float]], sorting_instructions: list[SortInstruction[float]]) -> None:
        """Initialize with a factory and sorting instructions for floats.

        Args:
            factory: A function that produces the source iterable of floats.
            sorting_instructions: A list of sorting instructions defining the sort order.
        """
        super().__init__(factory, sorting_instructions)

class QFloatList(QList[float], QFloatIterable):
    """A mutable list of floats with LINQ-style query operations and numeric methods.

    Combines the functionality of a standard list with float-specific operations
    like sum, min, max, and average. Elements can be added, removed, and modified
    while maintaining access to all LINQ-style query methods.

    Args:
        iterable: An optional iterable of floats to initialize the list.
                 Defaults to an empty list.

    Examples:
        >>> float_list = QFloatList([1.5, 2.5, 3.0, 4.5])
        >>> float_list.sum()
        11.5
        >>> float_list.where(lambda x: x > 2.0).to_list()
        [2.5, 3.0, 4.5]
        >>> float_list.append(5.5)
        >>> float_list.average()
        3.4
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[float] = ()) -> None:
        super().__init__(iterable)

    @override
    def reversed(self) -> QFloatIterable: return QFloatIterable.reversed(self)

class QFloatSet(QSet[float], QFloatIterable):
    """A mutable set of unique floats with LINQ-style query operations and numeric methods.

    Maintains a collection of unique floats while providing float-specific operations
    like sum, min, max, and average. Duplicate values are automatically excluded,
    and all standard set operations are available alongside LINQ query methods.

    Args:
        iterable: An optional iterable of floats to initialize the set.
                 Duplicates will be automatically removed. Defaults to an empty set.

    Examples:
        >>> float_set = QFloatSet([1.5, 2.5, 2.5, 3.0, 3.0, 4.5])
        >>> len(float_set)  # Duplicates removed
        4
        >>> float_set.sum()
        11.5
        >>> float_set.where(lambda x: x > 2.0).to_list()
        [2.5, 3.0, 4.5]  # Order may vary
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[float] = ()) -> None:
        super().__init__(iterable)

class QFloatFrozenSet(QFrozenSet[float], QFloatIterable):
    """An immutable set of unique floats with LINQ-style query operations and numeric methods.

    An immutable, hashable collection of unique floats that provides float-specific
    operations like sum, min, max, and average. Once created, the set cannot be modified,
    making it suitable for use as dictionary keys or in other sets.

    Args:
        iterable: An optional iterable of floats to initialize the frozen set.
                 Duplicates will be automatically removed. Defaults to an empty set.

    Examples:
        >>> float_frozenset = QFloatFrozenSet([1.5, 2.5, 2.5, 3.0, 3.0, 4.5])
        >>> len(float_frozenset)  # Duplicates removed
        4
        >>> float_frozenset.sum()
        11.5
        >>> float_frozenset.where(lambda x: x > 2.0).to_list()
        [2.5, 3.0, 4.5]  # Order may vary
        >>> hash(float_frozenset)  # Hashable since immutable
        1234567890  # Example hash value
    """
    __slots__: tuple[str, ...] = ()

    def __new__(cls, iterable: Iterable[float] = ()) -> QFloatFrozenSet:
        return super().__new__(cls, iterable)  # pyright: ignore [reportReturnType]

class QFloatSequence(QImmutableSequence[float], QFloatIterable):
    """An immutable sequence of floats with LINQ-style query operations and numeric methods.

    An immutable, ordered collection of floats that provides float-specific operations
    like sum, min, max, and average. Elements maintain their insertion order and can be
    accessed by index, but the sequence cannot be modified after creation.

    Args:
        iterable: An optional iterable of floats to initialize the sequence.
                 Order is preserved and duplicates are allowed. Defaults to an empty sequence.

    Examples:
        >>> float_sequence = QFloatSequence([3.5, 1.2, 4.8, 1.2, 5.9])
        >>> float_sequence[2]  # Access by index
        4.8
        >>> float_sequence.sum()
        16.6
        >>> float_sequence.where(lambda x: x > 2.0).to_list()
        [3.5, 4.8, 5.9]
        >>> float_sequence.reversed().to_list()
        [5.9, 1.2, 4.8, 1.2, 3.5]
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[float] = ()) -> None:
        super().__init__(iterable)

    @override
    def reversed(self) -> QFloatIterable: return QFloatIterable.reversed(self)
