from __future__ import annotations

import statistics
from abc import ABC
from decimal import Decimal
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

class QDecimalIterable(QIterable[Decimal], ABC):
    """An abstract base class for LINQ-style query operations on iterables of Decimal values.

    Extends QIterable with Decimal-specific numeric operations such as sum, min, max,
    and average. All operations handle precise decimal arithmetic and provide
    appropriate default values and error handling for empty collections.

    This class serves as the base for all Decimal collection types including
    QDecimalList, QDecimalSet, QDecimalSequence, and QDecimalFrozenSet.
    """
    __slots__: tuple[str, ...] = ()

    def sum(self) -> Decimal:
        """Calculates the sum of all Decimal values in this iterable.

        Returns:
            The sum of all Decimal values. Returns Decimal(0) for empty collections.

        Examples:
            >>> from decimal import Decimal
            >>> query([Decimal('1.5'), Decimal('2.5'), Decimal('3.0')]).as_decimals().sum()
            Decimal('7.0')
            >>> query([]).as_decimals().sum()
            Decimal('0')
        """
        return sum(self, Decimal(0))

    def min(self) -> Decimal:
        """Finds the minimum Decimal value in this iterable.

        Returns:
            The smallest Decimal value in the iterable.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> from decimal import Decimal
            >>> query([Decimal('3.5'), Decimal('1.2'), Decimal('4.8')]).as_decimals().min()
            Decimal('1.2')
            >>> query([]).as_decimals().min()  # Raises EmptyIterableError

        See Also:
            min_or_default(): Returns Decimal(0) instead of raising for empty collections.
        """
        try:
            return min(self)
        except ValueError:
            raise EmptyIterableError() from None

    def max(self) -> Decimal:
        """Finds the maximum Decimal value in this iterable.

        Returns:
            The largest Decimal value in the iterable.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> from decimal import Decimal
            >>> query([Decimal('3.5'), Decimal('1.2'), Decimal('4.8')]).as_decimals().max()
            Decimal('4.8')
            >>> query([]).as_decimals().max()  # Raises EmptyIterableError

        See Also:
            max_or_default(): Returns Decimal(0) instead of raising for empty collections.
        """
        try:
            return max(self)
        except ValueError:
            raise EmptyIterableError() from None

    def min_or_default(self) -> Decimal:
        """Finds the minimum Decimal value in this iterable, or returns Decimal(0) if empty.

        Returns:
            The smallest Decimal value in the iterable, or Decimal(0) if the iterable is empty.

        Examples:
            >>> from decimal import Decimal
            >>> query([Decimal('3.5'), Decimal('1.2'), Decimal('4.8')]).as_decimals().min_or_default()
            Decimal('1.2')
            >>> query([]).as_decimals().min_or_default()
            Decimal('0')
        """
        return min(self) if self.any() else Decimal(0)

    def max_or_default(self) -> Decimal:
        """Finds the maximum Decimal value in this iterable, or returns Decimal(0) if empty.

        Returns:
            The largest Decimal value in the iterable, or Decimal(0) if the iterable is empty.

        Examples:
            >>> from decimal import Decimal
            >>> query([Decimal('3.5'), Decimal('1.2'), Decimal('4.8')]).as_decimals().max_or_default()
            Decimal('4.8')
            >>> query([]).as_decimals().max_or_default()
            Decimal('0')
        """
        return max(self) if self.any() else Decimal(0)

    def average(self) -> Decimal:
        """Calculates the arithmetic mean of all Decimal values in this iterable.

        Returns:
            The average of all Decimal values as a Decimal.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> from decimal import Decimal
            >>> query([Decimal('1'), Decimal('2'), Decimal('3')]).as_decimals().average()
            Decimal('2')
            >>> query([Decimal('2.5'), Decimal('7.5')]).as_decimals().average()
            Decimal('5.0')
            >>> query([]).as_decimals().average()  # Raises EmptyIterableError

        See Also:
            average_or_default(): Returns Decimal(0) instead of raising for empty collections.
        """
        return statistics.mean(self._assert_not_empty())

    def average_or_default(self) -> Decimal:
        """Calculates the arithmetic mean of all Decimal values, or returns Decimal(0) if empty.

        Returns:
            The average of all Decimal values as a Decimal, or Decimal(0) if the iterable is empty.

        Examples:
            >>> from decimal import Decimal
            >>> query([Decimal('1'), Decimal('2'), Decimal('3')]).as_decimals().average_or_default()
            Decimal('2')
            >>> query([]).as_decimals().average_or_default()
            Decimal('0')
        """
        return statistics.mean(self) if self.any() else Decimal(0)

    @override
    def _lazy(self, factory: Func[Iterable[Decimal]]) -> QDecimalIterable: return QDecimalIterableImplementation(factory)

    @override
    def _order_by(self, key_selector: Selector[Decimal, SupportsRichComparison], descending: bool) -> QOrderedIterable[Decimal]:
        return QDecimalOrderedIterable(lambda: self, [SortInstruction(key_selector, descending)])

    @staticmethod
    def _selfcast(iterable: QIterable[Decimal]) -> QDecimalIterable: return cast(QDecimalIterable, iterable)
    @staticmethod
    def _selfcast_ordered(iterable: QOrderedIterable[Decimal]) -> QDecimalOrderedIterable: return cast(QDecimalOrderedIterable, iterable)

    # region override methods so that typecheckers know that we actually return QDecimalIterables now, not QIterable[Decimal]
    # call the base method to eliminate code duplication. The base class will call lazy from just above, so it is already the correct type
    @override
    def where(self, predicate: Predicate[Decimal]) -> QDecimalIterable: return self._selfcast(super().where(predicate))
    @override
    def where_not_none(self) -> QDecimalIterable: return self._selfcast(super().where_not_none())
    @override
    def distinct(self) -> QDecimalIterable: return self._selfcast(super().distinct())
    @override
    def distinct_by[TKey](self, key_selector: Selector[Decimal, TKey]) -> QDecimalIterable: return self._selfcast(super().distinct_by(key_selector))
    @override
    def take(self, count: int) -> QDecimalIterable: return self._selfcast(super().take(count))
    @override
    def take_while(self, predicate: Predicate[Decimal]) -> QDecimalIterable: return self._selfcast(super().take_while(predicate))
    @override
    def take_last(self, count: int) -> QDecimalIterable: return self._selfcast(super().take_last(count))
    @override
    def skip(self, count: int) -> QDecimalIterable: return self._selfcast(super().skip(count))
    @override
    def skip_last(self, count: int) -> QDecimalIterable: return self._selfcast(super().skip_last(count))
    @override
    def reversed(self) -> QDecimalIterable: return self._selfcast(super().reversed())

    @override
    def concat(self, *others: Iterable[Decimal]) -> QDecimalIterable: return self._selfcast(super().concat(*others))

    @override
    def order_by(self, key_selector: Selector[Decimal, SupportsRichComparison]) -> QDecimalOrderedIterable: return self._selfcast_ordered(super().order_by(key_selector))
    @override
    def order_by_descending(self, key_selector: Selector[Decimal, SupportsRichComparison]) -> QDecimalOrderedIterable: return self._selfcast_ordered(super().order_by_descending(key_selector))
    # endregion

    @override
    def to_list(self) -> QDecimalList: return QDecimalList(self)

    @override
    def to_sequence(self) -> QDecimalSequence: return QDecimalSequence(self)

    @override
    def to_tuple(self) -> tuple[Decimal, ...]: return tuple(self)

    @override
    def to_set(self) -> QDecimalSet: return QDecimalSet(self)

    @override
    def to_frozenset(self) -> QDecimalFrozenSet: return QDecimalFrozenSet(self)

class QDecimalIterableImplementation(QLazyIterableImplementation[Decimal], QDecimalIterable):
    """Internal implementation of QDecimalIterable that defers execution until iteration.

    This class provides the concrete implementation for lazy Decimal iterables,
    combining lazy evaluation from QLazyIterableImplementation with Decimal-specific
    numeric operations from QDecimalIterable.
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, factory: Func[Iterable[Decimal]]) -> None:
        """Initialize with a factory function that produces Decimal iterables.

        Args:
            factory: A function that returns an iterable of Decimals when called.
        """
        super().__init__(factory)

class QDecimalOrderedIterable(QOrderedIterable[Decimal], QDecimalIterable):
    """An ordered iterable of Decimals that supports multi-level sorting and numeric operations.

    Combines the multi-level sorting capabilities of QOrderedIterable with the
    Decimal-specific numeric operations from QDecimalIterable. This allows for complex
    sorting scenarios while maintaining access to methods like sum, min, max, and average
    with precise decimal arithmetic.
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, factory: Func[Iterable[Decimal]], sorting_instructions: list[SortInstruction[Decimal]]) -> None:
        """Initialize with a factory and sorting instructions for Decimals.

        Args:
            factory: A function that produces the source iterable of Decimals.
            sorting_instructions: A list of sorting instructions defining the sort order.
        """
        super().__init__(factory, sorting_instructions)

class QDecimalList(QList[Decimal], QDecimalIterable):
    """A mutable list of Decimal values with LINQ-style query operations and numeric methods.

    Combines the functionality of a standard list with Decimal-specific operations
    like sum, min, max, and average. Elements can be added, removed, and modified
    while maintaining access to all LINQ-style query methods and precise decimal arithmetic.

    Args:
        iterable: An optional iterable of Decimal values to initialize the list.
                 Defaults to an empty list.

    Examples:
        >>> from decimal import Decimal
        >>> decimal_list = QDecimalList([Decimal('1.5'), Decimal('2.5'), Decimal('3.0')])
        >>> decimal_list.sum()
        Decimal('7.0')
        >>> decimal_list.where(lambda x: x > Decimal('2')).to_list()
        [Decimal('2.5'), Decimal('3.0')]
        >>> decimal_list.append(Decimal('4.5'))
        >>> decimal_list.average()
        Decimal('2.875')
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[Decimal] = ()) -> None:
        super().__init__(iterable)

    @override
    def reversed(self) -> QDecimalIterable: return QDecimalIterable.reversed(self)

class QDecimalSet(QSet[Decimal], QDecimalIterable):
    """A mutable set of unique Decimal values with LINQ-style query operations and numeric methods.

    Maintains a collection of unique Decimal values while providing Decimal-specific operations
    like sum, min, max, and average. Duplicate values are automatically excluded,
    and all standard set operations are available alongside LINQ query methods.

    Args:
        iterable: An optional iterable of Decimal values to initialize the set.
                 Duplicates will be automatically removed. Defaults to an empty set.

    Examples:
        >>> from decimal import Decimal
        >>> decimal_set = QDecimalSet([Decimal('1.5'), Decimal('2.5'), Decimal('2.5'), Decimal('3.0')])
        >>> len(decimal_set)  # Duplicates removed
        3
        >>> decimal_set.sum()
        Decimal('7.0')
        >>> decimal_set.where(lambda x: x > Decimal('2')).to_list()
        [Decimal('2.5'), Decimal('3.0')]  # Order may vary
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[Decimal] = ()) -> None:
        super().__init__(iterable)

class QDecimalFrozenSet(QFrozenSet[Decimal], QDecimalIterable):
    """An immutable set of unique Decimal values with LINQ-style query operations and numeric methods.

    An immutable, hashable collection of unique Decimal values that provides Decimal-specific
    operations like sum, min, max, and average. Once created, the set cannot be modified,
    making it suitable for use as dictionary keys or in other sets.

    Args:
        iterable: An optional iterable of Decimal values to initialize the frozen set.
                 Duplicates will be automatically removed. Defaults to an empty set.

    Examples:
        >>> from decimal import Decimal
        >>> decimal_frozenset = QDecimalFrozenSet([Decimal('1.5'), Decimal('2.5'), Decimal('2.5')])
        >>> len(decimal_frozenset)  # Duplicates removed
        2
        >>> decimal_frozenset.sum()
        Decimal('4.0')
        >>> decimal_frozenset.where(lambda x: x > Decimal('2')).to_list()
        [Decimal('2.5')]  # Order may vary
        >>> hash(decimal_frozenset)  # Hashable since immutable
        1234567890  # Example hash value
    """
    __slots__: tuple[str, ...] = ()

    def __new__(cls, iterable: Iterable[Decimal] = ()) -> QDecimalFrozenSet:
        return super().__new__(cls, iterable)  # pyright: ignore [reportReturnType]

class QDecimalSequence(QImmutableSequence[Decimal], QDecimalIterable):
    """An immutable sequence of Decimal values with LINQ-style query operations and numeric methods.

    An immutable, ordered collection of Decimal values that provides Decimal-specific operations
    like sum, min, max, and average. Elements maintain their insertion order and can be
    accessed by index, but the sequence cannot be modified after creation.

    Args:
        iterable: An optional iterable of Decimal values to initialize the sequence.
                 Order is preserved and duplicates are allowed. Defaults to an empty sequence.

    Examples:
        >>> from decimal import Decimal
        >>> decimal_sequence = QDecimalSequence([Decimal('3.5'), Decimal('1.2'), Decimal('4.8')])
        >>> decimal_sequence[1]  # Access by index
        Decimal('1.2')
        >>> decimal_sequence.sum()
        Decimal('9.5')
        >>> decimal_sequence.where(lambda x: x > Decimal('2')).to_list()
        [Decimal('3.5'), Decimal('4.8')]
        >>> decimal_sequence.reversed().to_list()
        [Decimal('4.8'), Decimal('1.2'), Decimal('3.5')]
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, iterable: Iterable[Decimal] = ()) -> None:
        super().__init__(iterable)

    @override
    def reversed(self) -> QDecimalIterable: return QDecimalIterable.reversed(self)
