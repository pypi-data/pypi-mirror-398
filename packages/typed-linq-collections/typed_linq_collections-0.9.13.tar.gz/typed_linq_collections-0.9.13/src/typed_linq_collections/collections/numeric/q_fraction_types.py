from __future__ import annotations

import statistics
from abc import ABC
from fractions import Fraction
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

class QFractionIterable(QIterable[Fraction], ABC):
    """An abstract base class for LINQ-style query operations on iterables of Fraction values.

    Extends QIterable with Fraction-specific numeric operations such as sum, min, max,
    and average. All operations handle rational arithmetic and provide
    appropriate default values and error handling for empty collections.

    This class serves as the base for all Fraction collection types including
    QFractionList, QFractionSet, QFractionSequence, and QFractionFrozenSet.
    """
    __slots__: tuple[str, ...] = ()

    def sum(self) -> Fraction:
        """Calculates the sum of all Fraction values in this iterable.

        Returns:
            The sum of all Fraction values. Returns Fraction(0) for empty collections.

        Examples:
            >>> from fractions import Fraction
            >>> query([Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)]).as_fractions().sum()
            Fraction(1, 1)
            >>> query([]).as_fractions().sum()
            Fraction(0, 1)
        """
        return sum(self, Fraction(0))

    def min(self) -> Fraction:
        """Finds the minimum Fraction value in this iterable.

        Returns:
            The smallest Fraction value in the iterable.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> from fractions import Fraction
            >>> query([Fraction(3, 4), Fraction(1, 2), Fraction(5, 6)]).as_fractions().min()
            Fraction(1, 2)
            >>> query([]).as_fractions().min()  # Raises EmptyIterableError

        See Also:
            min_or_default(): Returns Fraction(0) instead of raising for empty collections.
        """
        try:
            return min(self)
        except ValueError:
            raise EmptyIterableError() from None

    def max(self) -> Fraction:
        """Finds the maximum Fraction value in this iterable.

        Returns:
            The largest Fraction value in the iterable.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> from fractions import Fraction
            >>> query([Fraction(3, 4), Fraction(1, 2), Fraction(5, 6)]).as_fractions().max()
            Fraction(5, 6)
            >>> query([]).as_fractions().max()  # Raises EmptyIterableError

        See Also:
            max_or_default(): Returns Fraction(0) instead of raising for empty collections.
        """
        try:
            return max(self)
        except ValueError:
            raise EmptyIterableError() from None

    def min_or_default(self) -> Fraction:
        """Finds the minimum Fraction value in this iterable, or returns Fraction(0) if empty.

        Returns:
            The smallest Fraction value in the iterable, or Fraction(0) if the iterable is empty.

        Examples:
            >>> from fractions import Fraction
            >>> query([Fraction(3, 4), Fraction(1, 2), Fraction(5, 6)]).as_fractions().min_or_default()
            Fraction(1, 2)
            >>> query([]).as_fractions().min_or_default()
            Fraction(0, 1)
        """
        return min(self) if self.any() else Fraction(0)

    def max_or_default(self) -> Fraction:
        """Finds the maximum Fraction value in this iterable, or returns Fraction(0) if empty.

        Returns:
            The largest Fraction value in the iterable, or Fraction(0) if the iterable is empty.

        Examples:
            >>> from fractions import Fraction
            >>> query([Fraction(3, 4), Fraction(1, 2), Fraction(5, 6)]).as_fractions().max_or_default()
            Fraction(5, 6)
            >>> query([]).as_fractions().max_or_default()
            Fraction(0, 1)
        """
        return max(self) if self.any() else Fraction(0)

    def average(self) -> Fraction:
        """Calculates the arithmetic mean of all Fraction values in this iterable.

        Returns:
            The average of all Fraction values as a Fraction.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> from fractions import Fraction
            >>> query([Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)]).as_fractions().average()
            Fraction(1, 3)
            >>> query([Fraction(1, 4), Fraction(3, 4)]).as_fractions().average()
            Fraction(1, 2)
            >>> query([]).as_fractions().average()  # Raises EmptyIterableError

        See Also:
            average_or_default(): Returns Fraction(0) instead of raising for empty collections.
        """
        return statistics.mean(self._assert_not_empty())

    def average_or_default(self) -> Fraction:
        """Calculates the arithmetic mean of all Fraction values, or returns Fraction(0) if empty.

        Returns:
            The average of all Fraction values as a Fraction, or Fraction(0) if the iterable is empty.

        Examples:
            >>> from fractions import Fraction
            >>> query([Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)]).as_fractions().average_or_default()
            Fraction(1, 3)
            >>> query([]).as_fractions().average_or_default()
            Fraction(0, 1)
        """
        return statistics.mean(self) if self.any() else Fraction(0)

    @override
    def _lazy(self, factory: Func[Iterable[Fraction]]) -> QFractionIterable: return QFractionIterableImplementation(factory)

    @override
    def _order_by(self, key_selector: Selector[Fraction, SupportsRichComparison], descending: bool) -> QOrderedIterable[Fraction]:
        return QFractionOrderedIterable(lambda: self, [SortInstruction(key_selector, descending)])

    @staticmethod
    def _selfcast(iterable: QIterable[Fraction]) -> QFractionIterable: return cast(QFractionIterable, iterable)
    @staticmethod
    def _selfcast_ordered(iterable: QOrderedIterable[Fraction]) -> QFractionOrderedIterable: return cast(QFractionOrderedIterable, iterable)

    # region override methods so that typecheckers know that we actually return QFractionIterables now, not QIterable[Fraction]
    # call the base method to eliminate code duplication. The base class will call lazy from just above, so it is already the correct type
    @override
    def where(self, predicate: Predicate[Fraction]) -> QFractionIterable: return self._selfcast(super().where(predicate))
    @override
    def where_not_none(self) -> QFractionIterable: return self._selfcast(super().where_not_none())
    @override
    def distinct(self) -> QFractionIterable: return self._selfcast(super().distinct())
    @override
    def distinct_by[TKey](self, key_selector: Selector[Fraction, TKey]) -> QFractionIterable: return self._selfcast(super().distinct_by(key_selector))
    @override
    def take(self, count: int) -> QFractionIterable: return self._selfcast(super().take(count))
    @override
    def take_while(self, predicate: Predicate[Fraction]) -> QFractionIterable: return self._selfcast(super().take_while(predicate))
    @override
    def take_last(self, count: int) -> QFractionIterable: return self._selfcast(super().take_last(count))
    @override
    def skip(self, count: int) -> QFractionIterable: return self._selfcast(super().skip(count))
    @override
    def skip_last(self, count: int) -> QFractionIterable: return self._selfcast(super().skip_last(count))
    @override
    def reversed(self) -> QFractionIterable: return self._selfcast(super().reversed())

    @override
    def concat(self, *others: Iterable[Fraction]) -> QFractionIterable: return self._selfcast(super().concat(*others))

    @override
    def order_by(self, key_selector: Selector[Fraction, SupportsRichComparison]) -> QFractionOrderedIterable: return self._selfcast_ordered(super().order_by(key_selector))
    @override
    def order_by_descending(self, key_selector: Selector[Fraction, SupportsRichComparison]) -> QFractionOrderedIterable: return self._selfcast_ordered(super().order_by_descending(key_selector))
    # endregion

    @override
    def to_list(self) -> QFractionList: return QFractionList(self)

    @override
    def to_sequence(self) -> QFractionSequence: return QFractionSequence(self)

    @override
    def to_tuple(self) -> tuple[Fraction, ...]: return tuple(self)

    @override
    def to_set(self) -> QFractionSet: return QFractionSet(self)

    @override
    def to_frozenset(self) -> QFractionFrozenSet: return QFractionFrozenSet(self)

class QFractionIterableImplementation(QLazyIterableImplementation[Fraction], QFractionIterable):
    """Internal implementation of QFractionIterable that defers execution until iteration.

    This class provides the concrete implementation for lazy Fraction iterables,
    combining lazy evaluation from QLazyIterableImplementation with Fraction-specific
    numeric operations from QFractionIterable.
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, factory: Func[Iterable[Fraction]]) -> None:
        """Initialize with a factory function that produces Fraction iterables.

        Args:
            factory: A function that returns an iterable of Fractions when called.
        """
        super().__init__(factory)

class QFractionOrderedIterable(QOrderedIterable[Fraction], QFractionIterable):
    """An ordered iterable of Fractions that supports multi-level sorting and numeric operations.

    Combines the multi-level sorting capabilities of QOrderedIterable with the
    Fraction-specific numeric operations from QFractionIterable. This allows for complex
    sorting scenarios while maintaining access to methods like sum, min, max, and average
    with exact rational arithmetic.
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, factory: Func[Iterable[Fraction]], sorting_instructions: list[SortInstruction[Fraction]]) -> None:
        """Initialize with a factory and sorting instructions for Fractions.

        Args:
            factory: A function that produces the source iterable of Fractions.
            sorting_instructions: A list of sorting instructions defining the sort order.
        """
        super().__init__(factory, sorting_instructions)

class QFractionList(QList[Fraction], QFractionIterable):
    """A mutable list of Fraction values with LINQ-style query operations and numeric methods.

    Combines the functionality of a standard list with Fraction-specific operations
    like sum, min, max, and average. Elements can be added, removed, and modified
    while maintaining access to all LINQ-style query methods and exact rational arithmetic.

    Args:
        iterable: An optional iterable of Fraction values to initialize the list.
                 Defaults to an empty list.

    Examples:
        >>> from fractions import Fraction
        >>> fraction_list = QFractionList([Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)])
        >>> fraction_list.sum()
        Fraction(1, 1)
        >>> fraction_list.where(lambda x: x > Fraction(1, 4)).to_list()
        [Fraction(1, 2), Fraction(1, 3)]
        >>> fraction_list.append(Fraction(1, 4))
        >>> fraction_list.average()
        Fraction(5, 16)
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[Fraction] = ()) -> None:
        super().__init__(iterable)

    @override
    def reversed(self) -> QFractionIterable: return QFractionIterable.reversed(self)

class QFractionSet(QSet[Fraction], QFractionIterable):
    """A mutable set of unique Fraction values with LINQ-style query operations and numeric methods.

    Maintains a collection of unique Fraction values while providing Fraction-specific operations
    like sum, min, max, and average. Duplicate values are automatically excluded,
    and all standard set operations are available alongside LINQ query methods.

    Args:
        iterable: An optional iterable of Fraction values to initialize the set.
                 Duplicates will be automatically removed. Defaults to an empty set.

    Examples:
        >>> from fractions import Fraction
        >>> fraction_set = QFractionSet([Fraction(1, 2), Fraction(2, 4), Fraction(1, 3)])  # 1/2 == 2/4
        >>> len(fraction_set)  # Duplicates removed
        2
        >>> fraction_set.sum()
        Fraction(5, 6)
        >>> fraction_set.where(lambda x: x > Fraction(1, 4)).to_list()
        [Fraction(1, 2), Fraction(1, 3)]  # Order may vary
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[Fraction] = ()) -> None:
        super().__init__(iterable)

class QFractionFrozenSet(QFrozenSet[Fraction], QFractionIterable):
    """An immutable set of unique Fraction values with LINQ-style query operations and numeric methods.

    An immutable, hashable collection of unique Fraction values that provides Fraction-specific
    operations like sum, min, max, and average. Once created, the set cannot be modified,
    making it suitable for use as dictionary keys or in other sets.

    Args:
        iterable: An optional iterable of Fraction values to initialize the frozen set.
                 Duplicates will be automatically removed. Defaults to an empty set.

    Examples:
        >>> from fractions import Fraction
        >>> fraction_frozenset = QFractionFrozenSet([Fraction(1, 2), Fraction(2, 4), Fraction(1, 3)])
        >>> len(fraction_frozenset)  # Duplicates removed (1/2 == 2/4)
        2
        >>> fraction_frozenset.sum()
        Fraction(5, 6)
        >>> fraction_frozenset.where(lambda x: x > Fraction(1, 4)).to_list()
        [Fraction(1, 2), Fraction(1, 3)]  # Order may vary
        >>> hash(fraction_frozenset)  # Hashable since immutable
        1234567890  # Example hash value
    """
    __slots__: tuple[str, ...] = ()

    def __new__(cls, iterable: Iterable[Fraction] = ()) -> QFractionFrozenSet:
        return super().__new__(cls, iterable)  # pyright: ignore [reportReturnType]

class QFractionSequence(QImmutableSequence[Fraction], QFractionIterable):
    """An immutable sequence of Fraction values with LINQ-style query operations and numeric methods.

    An immutable, ordered collection of Fraction values that provides Fraction-specific operations
    like sum, min, max, and average. Elements maintain their insertion order and can be
    accessed by index, but the sequence cannot be modified after creation.

    Args:
        iterable: An optional iterable of Fraction values to initialize the sequence.
                 Order is preserved and duplicates are allowed. Defaults to an empty sequence.

    Examples:
        >>> from fractions import Fraction
        >>> fraction_sequence = QFractionSequence([Fraction(3, 4), Fraction(1, 2), Fraction(5, 6)])
        >>> fraction_sequence[1]  # Access by index
        Fraction(1, 2)
        >>> fraction_sequence.sum()
        Fraction(25, 12)
        >>> fraction_sequence.where(lambda x: x > Fraction(1, 2)).to_list()
        [Fraction(3, 4), Fraction(5, 6)]
        >>> fraction_sequence.reversed().to_list()
        [Fraction(5, 6), Fraction(1, 2), Fraction(3, 4)]
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[Fraction] = ()) -> None:
        super().__init__(iterable)

    @override
    def reversed(self) -> QFractionIterable: return QFractionIterable.reversed(self)
