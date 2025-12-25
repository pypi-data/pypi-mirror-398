from __future__ import annotations

from abc import ABC
from collections.abc import Callable, Iterable
from itertools import chain
from typing import TYPE_CHECKING, Never, Self, overload

# noinspection PyProtectedMember
from typed_linq_collections._private_implementation_details import ops

# noinspection PyPep8Naming,PyProtectedMember
from typed_linq_collections._private_implementation_details.q_zero_overhead_collection_contructors import ZeroImportOverheadConstructors as C

# noinspection PyProtectedMember
from typed_linq_collections._private_implementation_details.sort_instruction import SortInstruction
from typed_linq_collections.q_errors import EmptyIterableError

if TYPE_CHECKING:
    from decimal import Decimal
    from fractions import Fraction

    from _typeshed import SupportsRichComparison

    # noinspection PyProtectedMember
    from typed_linq_collections._private_implementation_details.type_aliases import Action1, Func, Predicate, Selector
    from typed_linq_collections.collections.numeric.q_decimal_types import QDecimalIterable
    from typed_linq_collections.collections.numeric.q_float_types import QFloatIterable
    from typed_linq_collections.collections.numeric.q_fraction_types import QFractionIterable
    from typed_linq_collections.collections.numeric.q_int_types import QIntIterable
    from typed_linq_collections.collections.q_dict import QDict
    from typed_linq_collections.collections.q_frozen_set import QFrozenSet
    from typed_linq_collections.collections.q_key_value_pair import KeyValuePair
    from typed_linq_collections.collections.q_list import QList
    from typed_linq_collections.collections.q_sequence import QSequence
    from typed_linq_collections.collections.q_set import QSet
    from typed_linq_collections.q_cast import QCast
    from typed_linq_collections.q_grouping import QGrouping
    from typed_linq_collections.q_ordered_iterable import QOrderedIterable

def query[TItem](value: Iterable[TItem]) -> QIterable[TItem]:
    """Creates a QIterable from any iterable for LINQ-style operations.

    This is the main entry point for the typed-linq-collections library. It wraps
    any iterable (list, tuple, set, generator, etc.) in a QIterable that provides
    a rich set of LINQ-style operations for querying and transforming data.

    The resulting QIterable is lazy. Operations are chained together
    and only executed when the result is materialized (e.g., via to_list(), any(),
    count(), etc.).

    Args:
        value: Any iterable object (list, tuple, set, generator, range, etc.)
               to wrap in a QIterable for LINQ-style operations.

    Returns:
        A QIterable[TItem] that provides LINQ-style methods for querying and
        transforming the data.

    Examples:
        >>> query([1, 2, 3, 4, 5]).where(lambda x: x > 2).to_list()
        [3, 4, 5]

        >>> query("hello").where(lambda c: c != 'l').to_list()
        ['h', 'e', 'o']

        >>> query(range(10)).where(lambda x: x % 2 == 0).select(lambda x: x ** 2).take(3).to_list()
        [0, 4, 16]

        >>> people = [("Alice", 25), ("Bob", 30), ("Charlie", 35)]
        >>> query(people).where(lambda p: p[1] >= 30).select(lambda p: p[0]).to_list()
        ['Bob', 'Charlie']
    """
    return C.caching_iterable(value)


def query_from[TItem](*sources: Iterable[TItem]) -> QIterable[TItem]:
    """Creates a QIterable by combining multiple iterables.

    This function is useful for combining collections of different subtypes into
    a common base type. Elements from all sources are concatenated in order.

    Args:
        *sources: One or more iterable objects to combine.

    Returns:
        A QIterable[TItem] containing all elements from all sources.

    Examples:
        >>> query_from([1, 2], [3, 4], [5, 6]).to_list()
        [1, 2, 3, 4, 5, 6]

        >>> # Combining subtypes into base type
        >>> dogs: QSet[Dog] = QSet([...])
        >>> cats: QSet[Cat] = QSet([...])
        >>> all_animals: QIterable[Animal] = query_from(dogs, cats)
    """
    if not sources:
        return C.caching_iterable(())  # type: ignore
    if len(sources) == 1:
        return C.caching_iterable(sources[0])
    return C.caching_iterable(chain(*sources))

class QIterable[T](Iterable[T], ABC):
    """An abstract base class for LINQ-style query operations on iterables.

    QIterable provides a rich set of methods for querying, filtering, transforming,
    and aggregating data in a functional programming style, similar to .NET's LINQ

    Inheritance:
    Concrete implementations which inherit from QIterable and the builtin versions and interoperate seamlessly with them include:
    - QList, QSet, QFrozenSet - collection wrappers
    - QSequence - immutable sequence
    - QIntIterable, QFloatIterable - numeric specializations
    - QOrderedIterable - for multi-level sorting
    - QGrouping - for grouped data

    Key Features:
    - **Lazy Evaluation**: Operations are chained and only executed when results are materialized
    - **Method Chaining**: Fluent interface allows chaining operations like .where().select().take()
    - **Type Safety**: Full generic type support with proper type inference in modern Python
    - **Rich API**: 80+ methods covering filtering, mapping, grouping, joining, sorting, and aggregation
    - **Interoperability**: Works with any Python iterable and converts to standard collections
    """
    __slots__: tuple[str, ...] = ()

    @property
    def cast(self) -> QCast[T]:
        """Provides casting operations for elements in this iterable.

        This property returns a QCast object that performs type casting without
        value conversion. For actual value conversion (like string to int), use select()
        with the target type constructor. The cast operations are for accessing type-specific methods with autocomplete,
        not for transforming values.

        Returns:
            A QCast[T] object that provides type casting methods for the iterable elements.

        Examples:
            >>> # Type casting (no conversion) - elements remain unchanged
            >>> query([1, 2, 3]).cast.to(int).to_list()  # Still [1, 2, 3] as ints
            [1, 2, 3]
            >>> # Checked casting validates types but doesn't convert
            >>> query([1, 2, 3]).cast.checked.to(int).to_list()  # Validates all are ints
            [1, 2, 3]
            >>> # For actual conversion, use select() instead:
            >>> query(["1", "2", "3"]).select(int).to_list()  # Converts strings to ints
            [1, 2, 3]
            >>> # Accessing type-specific methods after casting
            >>> query([1, 2, 3]).cast.int().sum()  # Access numeric operations
            6
        """
        return C.cast(self)

    def _lazy(self, factory: Func[Iterable[T]]) -> QIterable[T]: return C.lazy_iterable(factory)

    # region  static factory methods
    @staticmethod
    def empty() -> QIterable[Never]:
        """Creates an empty iterable with no elements.

        This factory method returns a singleton empty iterable that contains no elements.
        The same immutable instance is returned on each call. The returned type
        uses Never to indicate it contains no elements of any type.

        Returns:
            An empty QIterable that contains no elements.

        Examples:
            >>> empty_query = QIterable.empty()
            >>> empty_query.to_list()
            []
            >>> empty_query.any()
            False
            >>> empty_query.qcount()
            0

            # Useful for providing empty defaults
            >>> def get_items(condition: bool) -> QIterable[int]:
            ...     return QIterable.range(5) if condition else QIterable.empty()
        """
        return C.empty_iterable()

    @staticmethod
    @overload
    def range(stop_before: int, /) -> QIntIterable:
        """Generates a sequence of integers from 0 to stop_before-1.

        This overload creates a sequence starting from 0 and incrementing by 1
        until reaching (but not including) the stop_before value.

        Args:
            stop_before: The exclusive upper bound. The sequence will contain
                        integers from 0 up to (but not including) this value.

        Returns:
            A QIntIterable containing integers [0, 1, 2, ..., stop_before-1].

        Examples:
            >>> QIterable.range(5).to_list()
            [0, 1, 2, 3, 4]
            >>> QIterable.range(0).to_list()
            []
            >>> QIterable.range(1).to_list()
            [0]
        """

    @staticmethod
    @overload
    def range(start: int, stop_before: int, step: int = 1, /) -> QIntIterable:
        """Generates a sequence of integers from start to stop_before-1 with specified step.

        This overload creates a sequence starting from the start value and incrementing
        by the step value until reaching (but not including) the stop_before value.
        The step can be positive or negative for ascending or descending sequences.

        Args:
            start: The inclusive lower bound where the sequence begins.
            stop_before: The exclusive upper bound where the sequence ends.
            step: The increment between successive numbers. Defaults to 1.
                 Can be negative for descending sequences. Must not be zero.

        Returns:
            A QIntIterable containing integers from start to stop_before-1 with
            the specified step increment.

        Raises:
            ValueError: If step is zero.

        Examples:
            >>> QIterable.range(2, 6).to_list()
            [2, 3, 4, 5]
            >>> QIterable.range(0, 10, 2).to_list()
            [0, 2, 4, 6, 8]
            >>> QIterable.range(5, 0, -1).to_list()
            [5, 4, 3, 2, 1]
            >>> QIterable.range(3, 3, 1).to_list()
            []
        """

    @staticmethod
    def range(start_or_stop_before: int, stop_before: int | None = None, step: int = 1, /) -> QIntIterable:
        """Generates a sequence of integers within a specified range.

        This method supports multiple calling patterns:
        - range(stop) creates numbers from 0 to stop-1
        - range(start, stop) creates numbers from start to stop-1
        - range(start, stop, step) creates numbers from start to stop-1 with given step

        Args:
            start_or_stop_before: When called with one argument, this is the exclusive upper bound starting from 0.
                                 When called with multiple arguments, this is the inclusive lower bound.
            stop_before: The exclusive upper bound. If None, start_or_stop_before is treated as the stop value.
            step: The increment between successive numbers. Can be negative for descending sequences.

        Returns:
            A QIntIterable containing the generated sequence of integers.

        Raises:
            ValueError: If step is zero.

        Examples:
            >>> QIterable.range(5).to_list()
            [0, 1, 2, 3, 4]
            >>> QIterable.range(2, 6).to_list()
            [2, 3, 4, 5]
            >>> QIterable.range(0, 10, 2).to_list()
            [0, 2, 4, 6, 8]
            >>> QIterable.range(5, 0, -1).to_list()
            [5, 4, 3, 2, 1]
            >>> QIterable.range(3, 3).to_list()
            []
        """
        return C.int_iterable(lambda: ops.range(start_or_stop_before, stop_before, step))

    @staticmethod
    def repeat[TElement](element: TElement, count: int) -> QIterable[TElement]:
        """Generates a sequence that contains the same element repeated a specified number of times.

        This method creates an iterable where the given element appears exactly count times.
        The element can be of any type, including None, and each occurrence is the same
        object reference (not a copy).

        Args:
            element: The element to repeat. Can be any type including None.
            count: The number of times to repeat the element. Must be non-negative.

        Returns:
            A new QIterable containing the element repeated count times.

        Raises:
            ArgumentError: If count is negative.

        Examples:
            >>> QIterable.repeat("hello", 3).to_list()
            ['hello', 'hello', 'hello']
            >>> QIterable.repeat(42, 0).to_list()
            []
            >>> QIterable.repeat(None, 2).to_list()
            [None, None]
            >>> # Useful for initialization
            >>> QIterable.repeat([], 3).to_list()  # Note: same list object repeated
            [[], [], []]
        """
        return C.lazy_iterable(lambda: ops.repeat(element, count))

    # endregion

    # region operations on the whole collection, not the items
    def qappend(self, item: T) -> QIterable[T]:
        """Appends a single item to the end of the iterable.

        Args:
            item: The item to append to the end of the iterable.

        Returns:
            A new QIterable with the item appended to the end.

        Examples:
            >>> query([1, 2, 3]).qappend(4).to_list()
            [1, 2, 3, 4]
            >>> query([]).qappend(42).to_list()
            [42]
        """
        return self._lazy(lambda: ops.append(self, item))

    def prepend(self, item: T) -> QIterable[T]:
        """Prepends a single item to the beginning of the iterable.

        Args:
            item: The item to prepend to the beginning of the iterable.

        Returns:
            A new QIterable with the item prepended to the beginning.

        Examples:
            >>> query([2, 3, 4]).prepend(1).to_list()
            [1, 2, 3, 4]
            >>> query(["world"]).prepend("hello").to_list()
            ['hello', 'world']
        """
        return self._lazy(lambda: ops.prepend(self, item))

    def concat(self, *others: Iterable[T]) -> QIterable[T]:
        """Concatenates one or more iterables to the end of this iterable.

        Args:
            *others: One or more iterables to concatenate to the end of this iterable.

        Returns:
            A new QIterable containing all elements from this iterable followed by all elements from the other iterables in order.

        Examples:
            >>> query([1, 2]).concat([3, 4]).to_list()
            [1, 2, 3, 4]
            >>> query([1, 2]).concat([3, 4], [5, 6]).to_list()
            [1, 2, 3, 4, 5, 6]
        """
        return self._lazy(lambda: ops.concat(self, *others))
    # endregion

    # region functional programming helpers
    def pipe[TReturn](self, action: Selector[QIterable[T], TReturn]) -> TReturn:
        """Pipes this iterable through a function and returns the result.

        This is useful for functional composition, allowing you to pass the iterable
        to another function without breaking the method chain.

        Args:
            action: A function that takes this QIterable and returns a result of type TReturn.

        Returns:
            The result of applying the action function to this iterable.

        Examples:
            >>> # Pipe to built-in functions that work with iterables
            >>> query(["apple", "banana", "cherry"]).pipe(max)
            'cherry'

            >>> # Pipe to external library functions
            >>> import statistics
            >>> query([1, 2, 3, 4, 5]).pipe(statistics.stdev)
            1.5811388300841898
        """
        return ops.pipe(self, action)

    def for_each(self, action: Action1[T]) -> Self:
        """Executes the specified action on each element in the iterable.

        This method iterates through all elements and performs the given action for side effects,
        then returns self to allow method chaining.

        Args:
            action: A function to execute on each element. The function takes an element and returns nothing.

        Returns:
            This same QIterable instance to allow method chaining.

        Examples:
            >>> results = []
            >>> query([1, 2, 3]).for_each(lambda x: results.append(x * 2)).to_list()
            [1, 2, 3]  # Original elements returned
            >>> results
            [2, 4, 6]  # Side effects occurred
        """
        for item in self: action(item)
        return self
    # endregion

    def as_iterable(self) -> QIterable[T]:
        """Returns this iterable as a QIterable[T].

        This method provides a way to explicitly convert any QIterable subclass back to
        the base QIterable type. The primary purpose is to get a variable of a type that is
        immutable and will cause type checker errors if you try to call mutating methods.

        Returns:
            This same QIterable instance.

        Examples:
            >>> q_list = QList([1, 2, 3])
            >>> an_iterable = q_list.as_iterable()
            >>> an_iterable is q_list # trying to invoke add on base_query will cause a type checker error
        """
        return self

    # region typed convertions to access type specific functionality type checkers will only allow calls if the instance is the correct type

    def as_ints(self: QIterable[int]) -> QIntIterable:
        """Converts this iterable to a QIntIterable for access to integer-specific operations.

        This method provides a type-safe conversion that allows access to numeric operations
        specific to integers such as sum, average, min, max, etc. The type checker ensures
        this method can only be called on iterables that contain integers.

        Returns:
            A QIntIterable containing the same integer elements with access to numeric operations.

        Examples:
            >>> int_query = query(["1", "2", "3"]).select(int).as_ints()
            >>> int_query.sum()  # Now has access to sum() method
            6
            >>> int_query.average()  # And average() method
            2

        Note:
            This method can only be called when the iterable contains int elements.
            Use select(int) first if you need to convert elements to integers.
            Do use a competent type checker, like Pyright
        """
        return ops.as_ints(self)

    def as_floats(self: QIterable[float]) -> QFloatIterable:
        """Converts this iterable to a QFloatIterable for access to float-specific operations.

        This method provides a type-safe conversion that allows access to numeric operations
        specific to floats such as sum, average, min, max, etc. The type checker ensures
        this method can only be called on iterables that contain floats.

        Returns:
            A QFloatIterable containing the same float elements with access to numeric operations.

        Examples:
            >>> float_query = query([1.0, 2.5, 3.7]).as_floats()
            >>> float_query.sum()  # Now has access to sum() method
            7.2
            >>> float_query.average()  # And average() method
            2.4

        Note:
            This method can only be called when the iterable contains float elements.
            Use select(float) first if you need to convert elements to floats.
        """
        return ops.as_floats(self)

    def as_fractions(self: QIterable[Fraction]) -> QFractionIterable:
        """Converts this iterable to a QFractionIterable for access to fraction-specific operations.

        This method provides a type-safe conversion that allows access to numeric operations
        specific to fractions such as sum, average, min, max, etc. The type checker ensures
        this method can only be called on iterables that contain Fraction objects.

        Returns:
            A QFractionIterable containing the same Fraction elements with access to numeric operations.

        Examples:
            >>> from fractions import Fraction
            >>> frac_query = query([Fraction(1, 2), Fraction(1, 3)]).as_fractions()
            >>> frac_query.sum()  # Now has access to sum() method
            Fraction(5, 6)
            >>> frac_query.average()  # And average() method
            Fraction(5, 12)

        Note:
            This method can only be called when the iterable contains Fraction elements.
        """
        return ops.as_fractions(self)

    def as_decimals(self: QIterable[Decimal]) -> QDecimalIterable:
        """Converts this iterable to a QDecimalIterable for access to decimal-specific operations.

        This method provides a type-safe conversion that allows access to numeric operations
        specific to decimals such as sum, average, min, max, etc. The type checker ensures
        this method can only be called on iterables that contain Decimal objects.

        Returns:
            A QDecimalIterable containing the same Decimal elements with access to numeric operations.

        Examples:
            >>> from decimal import Decimal
            >>> dec_query = query([Decimal('1.2'), Decimal('2.3')]).as_decimals()
            >>> dec_query.sum()  # Now has access to sum() method
            Decimal('3.5')
            >>> dec_query.average()  # And average() method
            Decimal('1.75')

        Note:
            This method can only be called when the iterable contains Decimal elements.
        """
        return ops.as_decimals(self)

    # endregion

    # region set operations
    def qexcept(self, other: Iterable[T]) -> QIterable[T]:
        """Returns distinct elements from this iterable that are not present in the other iterable.

        This is the set difference operation that removes all elements from this iterable
        that are also present in the other iterable. The result contains only distinct
        elements, preserving the original order from this iterable.

        Args:
            other: An iterable containing elements to exclude from this iterable.

        Returns:
            A new QIterable containing distinct elements from this iterable that are
            not present in the other iterable, in their original order.

        Examples:
            >>> query([1, 2, 3, 4, 5]).qexcept([3, 4, 6, 7]).to_list()
            [1, 2, 5]
            >>> query([1, 2, 2, 3, 3]).qexcept([3]).to_list()
            [1, 2]  # Duplicates are removed from result
            >>> query([1, 2, 3]).qexcept([]).to_list()
            [1, 2, 3]  # Empty other returns distinct elements from this
        """
        return self._lazy(lambda: ops.qexcept(self, other))

    def qexcept_by[TKey](self, keys: Iterable[TKey], key_selector: Selector[T, TKey]) -> QIterable[T]:
        """Excludes elements whose keys are present in the keys iterable (alias for where_key_not_in).

        This method is an alias for where_key_not_in, provided for consistency with other
        set operations and familiarity for those used to the .NET LINQ API. It filters out
        elements by applying the key_selector and excluding those whose keys match any key
        in the provided keys iterable.

        Args:
            keys: An iterable of keys to exclude elements by.
            key_selector: A function that takes an element and returns a key for comparison.

        Returns:
            A new QIterable containing elements whose keys are not in the keys iterable,
            with duplicates removed by key (keeping first occurrence).

        Examples:
            >>> items = [(1, "apple"), (2, "banana"), (3, "cherry")]
            >>> query(items).qexcept_by([1, 3], lambda x: x[0]).to_list()
            [(2, 'banana')]
            >>> query(["apple", "apricot", "banana"]).qexcept_by(["a"], lambda x: x[0]).to_list()
            ['banana']

        Note:
            Consider using the more descriptive where_key_not_in method instead for better code clarity.
        """
        return self.where_key_not_in(keys, key_selector)

    def where_key_not_in[TKey](self, keys: Iterable[TKey], key_selector: Selector[T, TKey]) -> QIterable[T]:
        """Filters elements to exclude those whose keys are present in the keys iterable.

        This method applies the key_selector to each element to extract a key, then excludes
        elements whose keys are found in the provided keys iterable. The result contains
        only distinct elements by key, keeping the first occurrence of each key.

        Args:
            keys: An iterable of keys to exclude elements by.
            key_selector: A function that takes an element and returns a key for comparison.

        Returns:
            A new QIterable containing elements whose keys are not in the keys iterable,
            with duplicates removed by key (keeping first occurrence).

        Examples:
            >>> items = [(1, "a"), (2, "b"), (3, "c"), (4, "d")]
            >>> query(items).where_key_not_in([2, 4], lambda x: x[0]).to_list()
            [(1, 'a'), (3, 'c')]
            >>> query(["apple", "apricot", "banana"]).where_key_not_in(["b"], lambda x: x[0]).to_list()
            ['apple']  # 'apricot' removed as duplicate key 'a'
        """
        return self._lazy(lambda: ops.where_key_not_in(self, keys, key_selector))

    def qunion(self, other: Iterable[T]) -> QIterable[T]:
        """Combines distinct elements from this iterable and another iterable.

        This is the set union operation that combines elements from both iterables,
        removing duplicates. The result preserves the order from the first iterable
        followed by new elements from the second iterable.

        Args:
            other: An iterable to union with this iterable.

        Returns:
            A new QIterable containing all distinct elements from both iterables,
            with elements from this iterable appearing first, followed by new
            elements from the other iterable.

        Examples:
            >>> query([1, 2, 3]).qunion([3, 4, 5]).to_list()
            [1, 2, 3, 4, 5]
            >>> query([1, 2, 2]).qunion([2, 3, 3]).to_list()
            [1, 2, 3]  # Duplicates removed within and between sequences
            >>> query([]).qunion([1, 2, 2]).to_list()
            [1, 2]  # Empty first returns distinct elements from second
        """
        return self._lazy(lambda: ops.qunion(self, other))

    def qunion_by[TKey](self, other: Iterable[T], key_selector: Selector[T, TKey]) -> QIterable[T]:
        """Combines elements from this iterable and another, removing duplicates by key.

        Uses the key_selector to determine uniqueness. Elements with duplicate keys
        are excluded, keeping only the first occurrence. The result preserves the
        order from this iterable followed by new elements from the other iterable.

        Args:
            other: An iterable to union with this iterable.
            key_selector: A function that takes an element and returns a key for uniqueness comparison.

        Returns:
            A new QIterable containing elements from both iterables with unique keys,
            preserving order and keeping first occurrence of each key.

        Examples:
            >>> items1 = [(1, "apple"), (2, "banana")]
            >>> items2 = [(1, "avocado"), (3, "cherry")]
            >>> query(items1).qunion_by(items2, lambda x: x[0]).to_list()
            [(1, 'apple'), (2, 'banana'), (3, 'cherry')]  # (1, 'avocado') excluded
            >>> query([1, 2, 2]).qunion_by([2, 3], lambda x: x).to_list()
            [1, 2, 3]  # Duplicates within sequences also removed
        """
        return self._lazy(lambda: ops.qunion_by(self, other, key_selector))

    def qintersect(self, other: Iterable[T]) -> QIterable[T]:
        """Returns distinct common elements between this iterable and another iterable.

        This is the set intersection operation that returns only elements that exist
        in both iterables. The result preserves the order from this iterable and
        contains only distinct elements.

        Args:
            other: An iterable to intersect with this iterable.

        Returns:
            A new QIterable containing distinct elements that appear in both iterables,
            in the order they appear in this iterable.

        Examples:
            >>> query([1, 2, 3, 4]).qintersect([2, 3, 5, 6]).to_list()
            [2, 3]
            >>> query([1, 2, 2, 3]).qintersect([2, 3, 3]).to_list()
            [2, 3]  # Duplicates removed from result
            >>> query([1, 2, 3]).qintersect([4, 5, 6]).to_list()
            []  # No common elements
        """
        return self._lazy(lambda: ops.qintersect(self, other))

    def qintersect_by[TKey](self, keys: Iterable[TKey], key_selector: Selector[T, TKey]) -> QIterable[T]:
        """Includes only elements whose keys are present in the keys iterable (alias for where_key_in).

        This method is an alias for where_key_in, provided for consistency with other
        set operations and familiarity for those used to the .NET LINQ API. It filters
        elements by applying the key_selector and including only those whose keys match
        any key in the provided keys iterable.

        Args:
            keys: An iterable of keys to include elements by.
            key_selector: A function that takes an element and returns a key for comparison.

        Returns:
            A new QIterable containing elements whose keys are in the keys iterable,
            with duplicates removed by key (keeping first occurrence).

        Examples:
            >>> items = [(1, "apple"), (2, "banana"), (3, "cherry")]
            >>> query(items).qintersect_by([1, 3], lambda x: x[0]).to_list()
            [(1, 'apple'), (3, 'cherry')]
            >>> query(["apple", "apricot", "banana"]).qintersect_by(["a"], lambda x: x[0]).to_list()
            ['apple']

        Note:
            Consider using the more descriptive where_key_in method instead for better code clarity.
        """
        return self.where_key_in(keys, key_selector)

    def where_key_in[TKey](self, keys: Iterable[TKey], key_selector: Selector[T, TKey]) -> QIterable[T]:
        """Filters elements to include only those whose keys are present in the keys iterable.

        This method applies the key_selector to each element to extract a key, then includes
        only elements whose keys are found in the provided keys iterable. The result contains
        only distinct elements by key, keeping the first occurrence of each key.

        Args:
            keys: An iterable of keys to include elements by.
            key_selector: A function that takes an element and returns a key for comparison.

        Returns:
            A new QIterable containing elements whose keys are in the keys iterable,
            with duplicates removed by key (keeping first occurrence).

        Examples:
            >>> items = [(1, "a"), (2, "b"), (3, "c"), (4, "d")]
            >>> query(items).where_key_in([2, 4], lambda x: x[0]).to_list()
            [(2, 'b'), (4, 'd')]
            >>> query(["apple", "apricot", "banana"]).where_key_in(["a"], lambda x: x[0]).to_list()
            ['apple']  # Only first element with key 'a'
        """
        return self._lazy(lambda: ops.where_key_in(self, keys, key_selector))

    def contains(self, value: T) -> bool:
        """Determines whether the iterable contains the specified value.

        Uses equality comparison to check if the value exists in the iterable.

        Args:
            value: The value to search for in the iterable.

        Returns:
            True if the value is found in the iterable, False otherwise.

        Examples:
            >>> query([1, 2, 3, 4]).contains(3)
            True
            >>> query([1, 2, 3, 4]).contains(5)
            False
        """
        return ops.contains(self, value)

    # endregion

    # region filtering
    def where(self, predicate: Predicate[T]) -> QIterable[T]:
        """Filters the iterable to include only elements that satisfy the predicate.

        Args:
            predicate: A function that takes an element and returns True if it should be included, False otherwise.

        Returns:
            A new QIterable containing only elements for which the predicate returns True.

        Examples:
            >>> query([1, 2, 3, 4, 5]).where(lambda x: x > 3).to_list()
            [4, 5]
        """
        return self._lazy(lambda: ops.where(self, predicate))

    def where_not_none(self) -> QIterable[T]:
        """Filters the iterable to exclude None values.

        Returns:
            A new QIterable containing only non-None elements.

        Examples:
            >>> query([1, None, 2, None, 3]).where_not_none().to_list()
            [1, 2, 3]
        """
        return self._lazy(lambda: ops.where_not_none(self))

    def distinct(self) -> QIterable[T]:
        """Returns distinct elements from the iterable, removing duplicates.

        Elements are compared using equality. The first occurrence of each element is retained,
        preserving the original order.

        Returns:
            A new QIterable containing only unique elements in their original order.

        Examples:
            >>> query([1, 2, 2, 3, 3]).distinct().to_list()
            [1, 2, 3]
        """
        return self._lazy(lambda: ops.distinct(self))

    def distinct_by[TKey](self, key_selector: Selector[T, TKey]) -> QIterable[T]:
        """Returns distinct elements based on a key selector function.

        Elements are compared by the key returned from the key_selector function. The first element
        for each unique key is retained, preserving the original order.

        Args:
            key_selector: A function that takes an element and returns a key used to determine uniqueness.

        Returns:
            A new QIterable containing the first element for each unique key in their original order.

        Examples:
            >>> query(["apple", "apricot", "banana"]).distinct_by(lambda x: x[0]).to_list()
            ['apple', 'banana']
        """
        return self._lazy(lambda: ops.distinct_by(self, key_selector))

    def take(self, count: int) -> QIterable[T]:
        """Returns the specified number of elements from the start of the iterable.

        Args:
            count: The number of elements to return. If count is 0 or negative, an empty iterable is returned.
                   If count exceeds the number of elements, all elements are returned.

        Returns:
            A new QIterable containing up to count elements from the start of this iterable.

        Examples:
            >>> query([1, 2, 3, 4, 5]).take(3).to_list()
            [1, 2, 3]
            >>> query([1, 2, 3]).take(10).to_list()
            [1, 2, 3]
            >>> query([1, 2, 3]).take(0).to_list()
            []
        """
        return self._lazy(lambda: ops.take(self, count))

    def take_while(self, predicate: Predicate[T]) -> QIterable[T]:
        """Returns elements from the start of the iterable as long as the predicate is true.

        Args:
            predicate: A function that takes an element and returns True to continue taking elements,
                      False to stop.

        Returns:
            A new QIterable containing elements from the start until the predicate returns False.

        Examples:
            >>> query([1, 2, 3, 4, 5]).take_while(lambda x: x < 4).to_list()
            [1, 2, 3]
            >>> query([1, 2, 3]).take_while(lambda x: x > 0).to_list()
            [1, 2, 3]
            >>> query([5, 1, 2]).take_while(lambda x: x < 3).to_list()
            []  # First element (5) fails predicate
        """
        return self._lazy(lambda: ops.take_while(self, predicate))

    def take_last(self, count: int) -> QIterable[T]:
        """Returns the specified number of elements from the end of the iterable.

        Args:
            count: The number of elements to return from the end. If count is 0 or negative,
                  an empty iterable is returned. If count exceeds the number of elements,
                  all elements are returned.

        Returns:
            A new QIterable containing up to count elements from the end of this iterable.

        Examples:
            >>> query([1, 2, 3, 4, 5]).take_last(3).to_list()
            [3, 4, 5]
            >>> query([1, 2, 3]).take_last(10).to_list()
            [1, 2, 3]
            >>> query([1, 2, 3]).take_last(0).to_list()
            []
        """
        return self._lazy(lambda: ops.take_last(self, count))

    def skip(self, count: int) -> QIterable[T]:
        """Skips the specified number of elements from the start and returns the remaining elements.

        Args:
            count: The number of elements to skip from the start. If count is 0 or negative,
                  all elements are returned. If count exceeds the number of elements,
                  an empty iterable is returned.

        Returns:
            A new QIterable containing all elements after skipping the specified count from the start.

        Examples:
            >>> query([1, 2, 3, 4, 5]).skip(2).to_list()
            [3, 4, 5]
            >>> query([1, 2, 3]).skip(0).to_list()
            [1, 2, 3]
            >>> query([1, 2, 3]).skip(10).to_list()
            []
        """
        return self._lazy(lambda: ops.skip(self, count))

    def skip_while(self, predicate: Predicate[T]) -> QIterable[T]:
        """Skips elements from the start as long as the predicate is true, then returns the rest.

        Continues skipping elements until the predicate returns False, then includes that element
        and all subsequent elements regardless of whether they would match the predicate.

        Args:
            predicate: A function that takes an element and returns True to continue skipping,
                      False to stop skipping and include this and all remaining elements.

        Returns:
            A new QIterable containing elements starting from the first element where the predicate
            returns False, plus all subsequent elements.

        Examples:
            >>> query([1, 2, 3, 4, 5]).skip_while(lambda x: x < 3).to_list()
            [3, 4, 5]
            >>> query([1, 2, 3]).skip_while(lambda x: False).to_list()
            [1, 2, 3]  # No elements skipped
            >>> query([1, 2, 3]).skip_while(lambda x: True).to_list()
            []  # All elements skipped
        """
        return self._lazy(lambda: ops.skip_while(self, predicate))

    def skip_last(self, count: int) -> QIterable[T]:
        """Skips the specified number of elements from the end and returns the remaining elements.

        Args:
            count: The number of elements to skip from the end. If count is 0 or negative,
                  all elements are returned. If count exceeds the number of elements,
                  an empty iterable is returned.

        Returns:
            A new QIterable containing all elements except the last count elements.

        Examples:
            >>> query([1, 2, 3, 4, 5]).skip_last(2).to_list()
            [1, 2, 3]
            >>> query([1, 2, 3]).skip_last(0).to_list()
            [1, 2, 3]
            >>> query([1, 2, 3]).skip_last(10).to_list()
            []
        """
        return self._lazy(lambda: ops.skip_last(self, count))

    def of_type[TResult](self, target_type: type[TResult]) -> QIterable[TResult]:
        """Filters elements to only include those that are instances of the specified type.

        Uses isinstance() to check if each element is an instance of the target type,
        which includes subclasses. The returned iterable is properly typed to TResult.

        Args:
            target_type: The type to filter by. Only elements that are instances of this type
                        (including subclasses) will be included.

        Returns:
            A new QIterable[TResult] containing only elements that are instances of target_type.

        Examples:
            >>> query([1, "hello", 2.5, "world", 42]).of_type(str).to_list()
            ['hello', 'world']
            >>> query([1, "hello", 2.5, True]).of_type(int).to_list()
            [1, True]  # bool is a subclass of int in Python
            >>> query([1, 2, 3]).of_type(float).to_list()
            []  # No floats present
        """
        return C.lazy_iterable(lambda: ops.of_type(self, target_type))

    # endregion

    # region value queries
    def qcount_by[TKey](self, key_selector: Selector[T, TKey]) -> QIterable[KeyValuePair[TKey, int]]:
        """Groups elements by a key and returns the count of elements for each key.

        The order of keys in the result corresponds to the order of their first occurrence
        in the original iterable.

        Args:
            key_selector: A function that takes an element and returns a key to group by.

        Returns:
            A new QIterable of KeyValuePair objects where each key is paired with the count
            of elements that produced that key.

        Examples:
            >>> query([1, 2, 2, 3, 3, 3]).qcount_by(lambda x: x).select(lambda kv: (kv.key, kv.value)).to_list()
            [(1, 1), (2, 2), (3, 3)]
            >>> query(["apple", "apricot", "banana"]).qcount_by(lambda x: x[0]).select(lambda kv: (kv.key, kv.value)).to_list()
            [('a', 2), ('b', 1)]
            >>> query([]).qcount_by(lambda x: x).to_list()
            []
        """
        return ops.qcount_by(self, key_selector)

    def qcount(self, predicate: Predicate[T] | None = None) -> int:
        """Returns the count of elements in the iterable, optionally filtered by a predicate.

        Args:
            predicate: Optional function that takes an element and returns True to include it
                      in the count. If None, counts all elements.

        Returns:
            The number of elements that satisfy the predicate, or the total number of elements
            if no predicate is provided.

        Examples:
            >>> query([1, 2, 3, 4, 5]).qcount()
            5
            >>> query([1, 2, 3, 4, 5]).qcount(lambda x: x > 3)
            2
            >>> query([]).qcount()
            0
            >>> query(["a", 1, "b", 2]).qcount(lambda x: isinstance(x, str))
            2
        """
        return ops.qcount(self, predicate)

    def none(self, predicate: Predicate[T] | None = None) -> bool:
        """Determines whether no elements satisfy a condition or if the iterable is empty.

        This is the logical opposite of any(). Returns True if no elements match the predicate
        or if the iterable is empty.

        Args:
            predicate: Optional function that takes an element and returns True if it matches
                      a condition. If None, checks if the iterable is empty.

        Returns:
            True if no elements satisfy the predicate or if the iterable is empty,
            False otherwise.

        Examples:
            >>> query([]).none()
            True  # Empty iterable
            >>> query([1, 2, 3]).none()
            False  # Has elements
            >>> query([1, 3, 5]).none(lambda x: x % 2 == 0)
            True  # No even numbers
            >>> query([1, 2, 3]).none(lambda x: x > 0)
            False  # All are positive
        """
        return not ops.any(self, predicate)

    def any(self, predicate: Predicate[T] | None = None) -> bool:
        """Determines whether any elements satisfy a condition or if the iterable contains elements.

        Args:
            predicate: Optional function that takes an element and returns True if it matches
                      a condition. If None, checks if the iterable contains any elements.

        Returns:
            True if any element satisfies the predicate or if the iterable contains elements
            (when predicate is None), False otherwise.

        Examples:
            >>> query([1, 2, 3]).any()
            True  # Has elements
            >>> query([]).any()
            False  # Empty iterable
            >>> query([1, 2, 3, 4]).any(lambda x: x % 2 == 0)
            True  # Has even numbers (2, 4)
            >>> query([1, 3, 5]).any(lambda x: x % 2 == 0)
            False  # No even numbers
        """
        return ops.any(self, predicate)

    def all(self, predicate: Predicate[T]) -> bool:
        """Determines whether all elements satisfy the specified predicate.

        Returns True if all elements satisfy the predicate or if the iterable is empty.

        Args:
            predicate: A function that takes an element and returns True if it satisfies
                      the condition, False otherwise.

        Returns:
            True if all elements satisfy the predicate or if the iterable is empty,
            False if any element fails the predicate.

        Examples:
            >>> query([2, 4, 6, 8]).all(lambda x: x % 2 == 0)
            True  # All are even
            >>> query([1, 2, 3, 4]).all(lambda x: x > 0)
            True  # All are positive
            >>> query([1, 2, 3]).all(lambda x: x > 2)
            False  # Not all are greater than 2
            >>> query([]).all(lambda x: False)
            True  # Empty iterable always returns True
        """
        return ops.all(self, predicate)

    def sequence_equal(self, other: Iterable[T]) -> bool:
        """Determines whether two iterables are equal by comparing elements in sequence.

        Elements are compared using equality (==) in their respective positions.

        Args:
            other: The iterable to compare with this iterable.

        Returns:
            True if both iterables have the same length and all corresponding elements
            are equal, False otherwise.

        Examples:
            >>> query([1, 2, 3]).sequence_equal([1, 2, 3])
            True
            >>> query([1, 2, 3]).sequence_equal([3, 2, 1])
            False  # Different order
            >>> query([1, 2]).sequence_equal([1, 2, 3])
            False  # Different lengths
            >>> query([]).sequence_equal([])
            True  # Both empty
            >>> query([1, None, 3]).sequence_equal([1, None, 3])
            True  # None values compared positionally
        """
        return ops.sequence_equal(self, other)

    # endregion

    # region aggregation methods
    @overload
    def aggregate(self, func: Callable[[T, T], T]) -> T:
        """Applies an accumulator function over the sequence using the first element as seed.

        This overload uses the first element of the sequence as the initial accumulator
        value and applies the function to subsequent elements. The function combines
        two elements of the same type to produce a result of the same type.

        Args:
            func: A function that takes two elements of type T and returns a combined
                 result of type T. Called as func(accumulator, current_element).

        Returns:
            The final accumulated value after applying the function to all elements.

        Raises:
            EmptyIterableError: If the sequence contains no elements.

        Examples:
            >>> # Sum all numbers
            >>> query([1, 2, 3, 4]).aggregate(lambda acc, x: acc + x)
            10
            >>> # Find maximum
            >>> query([3, 7, 2, 9, 1]).aggregate(lambda acc, x: max(acc, x))
            9
            >>> # Concatenate strings
            >>> query(["Hello", " ", "World"]).aggregate(lambda acc, x: acc + x)
            'Hello World'
        """

    @overload
    def aggregate[TAccumulate](self, func: Callable[[TAccumulate, T], TAccumulate], seed: TAccumulate) -> TAccumulate:
        """Applies an accumulator function over the sequence with an initial seed value.

        This overload uses the provided seed as the initial accumulator value and applies
        the function to each element in the sequence. The accumulator and element types
        can be different, with the function producing a result of the accumulator type.

        Args:
            func: A function that takes an accumulator of type TAccumulate and an element
                 of type T, returning an updated accumulator of type TAccumulate.
            seed: The initial accumulator value of type TAccumulate.

        Returns:
            The final accumulated value of type TAccumulate after applying the function
            to all elements.

        Examples:
            >>> # Sum with initial value (works with empty sequences)
            >>> query([1, 2, 3]).aggregate(lambda acc, x: acc + x, 0)
            6
            >>> # Build a string from numbers
            >>> query([1, 2, 3]).aggregate(lambda acc, x: acc + str(x), "Numbers: ")
            'Numbers: 123'
            >>> # Count elements
            >>> query(["a", "b", "c"]).aggregate(lambda count, _: count + 1, 0)
            3
        """

    @overload
    def aggregate[TAccumulate, TResult](self, func: Callable[[TAccumulate, T], TAccumulate], seed: TAccumulate, select: Selector[TAccumulate, TResult]) -> TResult:
        """Applies an accumulator function with seed and transforms the final result.

        This overload uses the provided seed as the initial accumulator value, applies
        the function to each element, and then transforms the final accumulated result
        using the select function. This allows for complex aggregation scenarios where
        the final result type differs from both the element and accumulator types.

        Args:
            func: A function that takes an accumulator of type TAccumulate and an element
                 of type T, returning an updated accumulator of type TAccumulate.
            seed: The initial accumulator value of type TAccumulate.
            select: A function that transforms the final accumulator value of type
                   TAccumulate into the result of type TResult.

        Returns:
            The final result of type TResult after accumulation and transformation.

        Examples:
            >>> # Calculate average by accumulating sum and count, then dividing
            >>> query([1, 2, 3, 4]).aggregate(
            ...     lambda acc, x: (acc[0] + x, acc[1] + 1),
            ...     (0, 0),
            ...     lambda acc: acc[0] / acc[1] if acc[1] > 0 else 0
            ... )
            2.5
            >>> # Build formatted result
            >>> query([1, 2, 3]).aggregate(
            ...     lambda acc, x: acc + x,
            ...     0,
            ...     lambda total: f"Sum is: {total}"
            ... )
            'Sum is: 6'
        """
        ...

    def aggregate[TAccumulate, TResult](self, func: Callable[[T, T], T] | Callable[[TAccumulate, T], TAccumulate],
                                        seed: TAccumulate | None = None,
                                        select: Selector[TAccumulate, TResult] | None = None) -> T | TAccumulate | TResult:
        """Applies an accumulator function over the sequence.

        This method supports three forms:
        1. aggregate(func) - Applies func to each element with no seed value
        2. aggregate(func, seed) - Uses seed as initial accumulator value
        3. aggregate(func, seed, select) - Uses seed and applies select to final result

        Args:
            func: An accumulator function. For form 1, takes (accumulator, current_element) -> accumulator.
                 For forms 2 and 3, takes (accumulator, current_element) -> accumulator.
            seed: Optional initial accumulator value. If None, first element is used as seed.
            select: Optional function to transform the final accumulator value.

        Returns:
            The final accumulated value, optionally transformed by select function.

        Raises:
            EmptyIterableError: If no seed is provided and the iterable is empty.

        Examples:
            >>> # Sum without seed (requires non-empty sequence)
            >>> query([1, 2, 3, 4]).aggregate(lambda acc, x: acc + x)
            10
            >>> # Sum with seed (works with empty sequence)
            >>> query([1, 2, 3]).aggregate(lambda acc, x: acc + x, 0)
            6
            >>> # Build and transform result
            >>> query([1, 2, 3]).aggregate(lambda acc, x: acc + x, 0, lambda result: f"Sum: {result}")
            'Sum: 6'
        """
        return ops.aggregate(self, func, seed, select)

    # endregion

    # region sorting
    def _order_by(self, key_selector: Selector[T, SupportsRichComparison], descending: bool) -> QOrderedIterable[T]:
        return C.ordered_iterable(lambda: self, [SortInstruction(key_selector, descending)])

    def order_by(self, key_selector: Selector[T, SupportsRichComparison]) -> QOrderedIterable[T]:
        """Sorts the elements in ascending order according to a key selector function.

        Creates a QOrderedIterable that sorts elements when enumerated. The sort is stable,
        preserving the relative order of equal elements. The returned QOrderedIterable
        supports additional then_by operations for multi-level sorting.

        Args:
            key_selector: A function that takes an element and returns a key for comparison.
                         The key must support comparison operations (at minimum __lt__).

        Returns:
            A QOrderedIterable that will sort elements in ascending order by the specified key
            when enumerated.

        Examples:
            >>> query([3, 1, 4, 1, 5]).order_by(lambda x: x).to_list()
            [1, 1, 3, 4, 5]
            >>> query(["apple", "pie", "a"]).order_by(lambda x: len(x)).to_list()
            ['a', 'pie', 'apple']
            >>> # Multi-level sorting
            >>> query([(1, 'b'), (2, 'a'), (1, 'a')]).order_by(lambda x: x[0]).then_by(lambda x: x[1]).to_list()
            [(1, 'a'), (2, 'a'), (1, 'b')]
        """
        return self._order_by(key_selector, False)

    def order_by_descending(self, key_selector: Selector[T, SupportsRichComparison]) -> QOrderedIterable[T]:
        """Sorts the elements in descending order according to a key selector function.

        Creates a QOrderedIterable that sorts elements when enumerated. The sort is stable,
        preserving the relative order of equal elements. The returned QOrderedIterable
        supports additional then_by operations for multi-level sorting.

        Args:
            key_selector: A function that takes an element and returns a key for comparison.
                         The key must support comparison operations (at minimum __lt__).

        Returns:
            A QOrderedIterable that will sort elements in descending order by the specified key
            when enumerated.

        Examples:
            >>> query([3, 1, 4, 1, 5]).order_by_descending(lambda x: x).to_list()
            [5, 4, 3, 1, 1]
            >>> query(["apple", "pie", "a"]).order_by_descending(lambda x: len(x)).to_list()
            ['apple', 'pie', 'a']
            >>> # Multi-level sorting (first desc, then asc)
            >>> items = [(2, 'b'), (1, 'a'), (2, 'a')]
            >>> query(items).order_by_descending(lambda x: x[0]).then_by(lambda x: x[1]).to_list()
            [(2, 'a'), (1, 'a'), (2, 'b')]
        """
        return self._order_by(key_selector, True)

    def reversed(self) -> QIterable[T]:
        """Returns a new iterable with elements in reverse order.

        Returns:
            A new QIterable containing the same elements in reverse order.

        Examples:
            >>> query([1, 2, 3, 4, 5]).reversed().to_list()
            [5, 4, 3, 2, 1]
            >>> query(["hello", "world"]).reversed().to_list()
            ['world', 'hello']
            >>> query([]).reversed().to_list()
            []
        """
        return self._lazy(lambda: ops.reversed(self))

    # endregion

    # region mapping/transformation methods
    def select[TReturn](self, selector: Selector[T, TReturn]) -> QIterable[TReturn]:
        """Projects each element into a new form using a selector function.

        This is the fundamental transformation method that applies a function to each element
        to produce a new sequence.

        Args:
            selector: A function that takes an element of type T and returns a value of type TReturn.

        Returns:
            A new QIterable[TReturn] containing the transformed elements.

        Examples:
            >>> query([1, 2, 3]).select(lambda x: x * 2).to_list()
            [2, 4, 6]
            >>> query(["hello", "world"]).select(lambda s: len(s)).to_list()
            [5, 5]
            >>> query([1, 2, 3]).select(lambda x: f"Item: {x}").to_list()
            ['Item: 1', 'Item: 2', 'Item: 3']
            >>> # Type transformation
            >>> query(["1", "2", "3"]).select(int).to_list()
            [1, 2, 3]
        """
        return C.lazy_iterable(lambda: ops.select(self, selector))

    def select_index[TReturn](self, selector: Callable[[T, int], TReturn]) -> QIterable[TReturn]:
        """Projects each element into a new form using element value and its index.

        Similar to select(), but the selector function receives both the element and its
        zero-based index position in the sequence. This is useful when the transformation
        depends on the element's position.

        Args:
            selector: A function that takes an element of type T and its zero-based index,
                     and returns a value of type TReturn.

        Returns:
            A new QIterable[TReturn] containing the transformed elements.

        Examples:
            >>> query(["a", "b", "c"]).select_index(lambda x, i: f"{i}: {x}").to_list()
            ['0: a', '1: b', '2: c']
            >>> query([10, 20, 30]).select_index(lambda x, i: x + i).to_list()
            [10, 21, 32]  # 10+0, 20+1, 30+2
            >>> # Create index-value pairs
            >>> query(["apple", "banana"]).select_index(lambda x, i: (i, x)).to_list()
            [(0, 'apple'), (1, 'banana')]
        """
        return C.lazy_iterable(lambda: ops.select_index(self, selector))

    def select_many[TInner](self, selector: Selector[T, Iterable[TInner]]) -> QIterable[TInner]:
        """Projects each element to an iterable and flattens the resulting sequences into one sequence.

        This method is useful for flattening nested collections or expanding each element into
        multiple elements. It applies the selector to each element to get an iterable, then
        concatenates all the resulting iterables into a single flat sequence.

        Args:
            selector: A function that takes an element and returns an iterable of TInner elements.

        Returns:
            A new QIterable[TInner] containing all elements from all the iterables returned
            by the selector, concatenated in order.

        Examples:
            >>> query([[1, 2], [3, 4]]).select_many(lambda x: x).to_list()
            [1, 2, 3, 4]
            >>> query(["hello", "world"]).select_many(lambda s: s).to_list()
            ['h', 'e', 'l', 'l', 'o', 'w', 'o', 'r', 'l', 'd']
        """
        return C.lazy_iterable(lambda: ops.select_many(self, selector))

    def join[TInner, TKey, TResult](self, other: Iterable[TInner], self_key: Selector[T, TKey], other_key: Selector[TInner, TKey], select: Callable[[T, TInner], TResult]) -> QIterable[TResult]:
        """Correlates elements of two sequences based on matching keys and returns the results.

        This method performs an inner join between this iterable and another iterable based on
        key equality. For each element in this iterable, it finds all elements in the other
        iterable that have matching keys and applies the result selector to each pair.

        Args:
            other: The iterable to join with this iterable.
            self_key: A function to extract the key from elements of this iterable.
            other_key: A function to extract the key from elements of the other iterable.
            select: A function that takes an element from this iterable and a matching element
                   from the other iterable, and returns the result.

        Returns:
            A new QIterable[TResult] containing the results of the join operation for all
            matching pairs.

        Examples:
            >>> people = [(1, "Alice"), (2, "Bob")]
            >>> orders = [(101, 1, 100.0), (102, 2, 200.0), (103, 1, 150.0)]
            >>> query(people).join(orders, lambda p: p[0], lambda o: o[1], lambda p, o: f"{p[1]}: ${o[2]}").to_list()
            ['Alice: $100.0', 'Alice: $150.0', 'Bob: $200.0']
        """
        return C.lazy_iterable(lambda: ops.join(self, other, self_key, other_key, select))

    def group_join[TInner, TKey, TResult](self, other: Iterable[TInner], self_key: Selector[T, TKey], group_key: Selector[TInner, TKey], select: Callable[[T, QList[TInner]], TResult]) -> QIterable[TResult]:
        """Correlates elements based on key equality and groups the results.

        This method performs a grouped join where each element from this iterable is paired
        with a group (QList) of all matching elements from the other iterable. Unlike join(),
        this ensures each element from the outer sequence appears exactly once in the result,
        even if it has no matches (in which case it gets an empty group).

        Args:
            other: The iterable to join with this iterable.
            self_key: A function to extract the key from elements of this iterable.
            group_key: A function to extract the key from elements of the other iterable.
            select: A function that takes an element from this iterable and a QList of all
                   matching elements from the other iterable, and returns the result.

        Returns:
            A new QIterable[TResult] containing one result for each element in this iterable,
            paired with its group of matching elements from the other iterable.

        Examples:
            >>> people = [(1, "Alice"), (2, "Bob"), (3, "Charlie")]
            >>> orders = [(101, 1, 100.0), (102, 1, 150.0), (103, 2, 200.0)]
            >>> query(people).group_join(orders, lambda p: p[0], lambda o: o[1], lambda p, orders: f"{p[1]}: {len(orders)} orders").to_list()
            ['Alice: 2 orders', 'Bob: 1 orders', 'Charlie: 0 orders']
        """
        return C.lazy_iterable(lambda: ops.group_join(self, other, self_key, group_key, select))

    def qindex(self) -> QIterable[tuple[int, T]]:
        """Returns an iterable of tuples containing the zero-based index and value of each element.

        This method pairs each element with its position in the sequence, creating tuples of
        (index, element). The index starts at 0 for the first element and increments by 1
        for each subsequent element.

        Returns:
            A new QIterable[tuple[int, T]] where each tuple contains the zero-based index
            and the corresponding element.

        Examples:
            >>> query(["a", "b", "c"]).qindex().to_list()
            [(0, 'a'), (1, 'b'), (2, 'c')]
            >>> query([10, 20, 30]).qindex().to_list()
            [(0, 10), (1, 20), (2, 30)]
            >>> query([]).qindex().to_list()
            []
            >>> # Useful for filtering by position
            >>> query(["a", "b", "c", "d"]).qindex().where(lambda t: t[0] % 2 == 0).select(lambda t: t[1]).to_list()
            ['a', 'c']
        """
        return C.lazy_iterable(lambda: ops.qindex(self))

    def zip[T2, TResult](self, second: Iterable[T2], select: Callable[[T, T2], TResult]) -> QIterable[TResult]:
        """Combines corresponding elements from this iterable and another using a selector function.

        This method pairs up elements from two iterables based on their position and applies
        the selector function to each pair. The resulting sequence has the length of the
        shorter input sequence - iteration stops when either sequence is exhausted.

        Args:
            second: The iterable to combine with this iterable.
            select: A function that takes an element from this iterable and the corresponding
                   element from the second iterable, and returns the combined result.

        Returns:
            A new QIterable[TResult] containing the results of applying the selector to
            corresponding pairs of elements.

        Examples:
            >>> query([1, 2, 3]).zip([10, 20, 30], lambda x, y: x + y).to_list()
            [11, 22, 33]
            >>> query(["a", "b"]).zip([1, 2, 3], lambda s, n: f"{s}{n}").to_list()
            ['a1', 'b2']
            >>> query([1, 2, 3]).zip([], lambda x, y: (x, y)).to_list()
            []
        """
        return C.lazy_iterable(lambda: ops.zip(self, second, select))

    def zip2[T2, T3, TResult](self, second: Iterable[T2], third: Iterable[T3], select: Callable[[T, T2, T3], TResult]) -> QIterable[TResult]:
        """Combines corresponding elements from three iterables using a selector function.

        This method pairs up elements from three iterables based on their position and applies
        the selector function to each triple. The resulting sequence has the length of the
        shortest input sequence - iteration stops when any sequence is exhausted.

        Args:
            second: The second iterable to combine.
            third: The third iterable to combine.
            select: A function that takes corresponding elements from all three iterables
                   and returns the combined result.

        Returns:
            A new QIterable[TResult] containing the results of applying the selector to
            corresponding triples of elements.

        Examples:
            >>> query([1, 2]).zip2([10, 20], [100, 200], lambda x, y, z: x + y + z).to_list()
            [111, 222]
            >>> query(["a", "b"]).zip2([1, 2], ["x", "y"], lambda s, n, c: f"{s}{n}{c}").to_list()
            ['a1x', 'b2y']
        """
        return C.lazy_iterable(lambda: ops.zip2(self, second, third, select))

    def zip3[T2, T3, T4, TResult](self, second: Iterable[T2], third: Iterable[T3], fourth: Iterable[T4], select: Callable[[T, T2, T3, T4], TResult]) -> QIterable[TResult]:
        """Combines corresponding elements from four iterables using a selector function.

        This method pairs up elements from four iterables based on their position and applies
        the selector function to each quadruple. The resulting sequence has the length of the
        shortest input sequence - iteration stops when any sequence is exhausted.

        Args:
            second: The second iterable to combine.
            third: The third iterable to combine.
            fourth: The fourth iterable to combine.
            select: A function that takes corresponding elements from all four iterables
                   and returns the combined result.

        Returns:
            A new QIterable[TResult] containing the results of applying the selector to
            corresponding quadruples of elements.

        Examples:
            >>> query([1, 2]).zip3([10, 20], [100, 200], [1000, 2000], lambda w, x, y, z: w + x + y + z).to_list()
            [1111, 2222]
        """
        return C.lazy_iterable(lambda: ops.zip3(self, second, third, fourth, select))

    def zip_tuple[T2](self, second: Iterable[T2]) -> QIterable[tuple[T, T2]]:
        """Combines corresponding elements from this iterable and another into tuples.

        This is a convenience method that combines two iterables into tuples without requiring
        a selector function. It's equivalent to zip(second, lambda x, y: (x, y)). The resulting
        sequence has the length of the shorter input sequence.

        Args:
            second: The iterable to combine with this iterable.

        Returns:
            A new QIterable[tuple[T, T2]] containing tuples of corresponding elements.

        Examples:
            >>> query([1, 2, 3]).zip_tuple(["a", "b", "c"]).to_list()
            [(1, 'a'), (2, 'b'), (3, 'c')]
            >>> query([1, 2]).zip_tuple([10, 20, 30]).to_list()
            [(1, 10), (2, 20)]
            >>> query([]).zip_tuple([1, 2, 3]).to_list()
            []
        """
        return C.lazy_iterable(lambda: ops.zip_tuple(self, second))

    def zip_tuple2[T2, T3](self, second: Iterable[T2], third: Iterable[T3]) -> QIterable[tuple[T, T2, T3]]:
        """Combines corresponding elements from three iterables into 3-tuples.

        This is a convenience method that combines three iterables into tuples without requiring
        a selector function. It's equivalent to zip2(second, third, lambda x, y, z: (x, y, z)).
        The resulting sequence has the length of the shortest input sequence.

        Args:
            second: The second iterable to combine.
            third: The third iterable to combine.

        Returns:
            A new QIterable[tuple[T, T2, T3]] containing 3-tuples of corresponding elements.

        Examples:
            >>> query([1, 2]).zip_tuple2(["a", "b"], [10, 20]).to_list()
            [(1, 'a', 10), (2, 'b', 20)]
        """
        return C.lazy_iterable(lambda: ops.zip_tuple2(self, second, third))

    def zip_tuple3[T2, T3, T4](self, second: Iterable[T2], third: Iterable[T3], fourth: Iterable[T4]) -> QIterable[tuple[T, T2, T3, T4]]:
        """Combines corresponding elements from four iterables into 4-tuples.

        This is a convenience method that combines four iterables into tuples without requiring
        a selector function. It's equivalent to zip3(second, third, fourth, lambda w, x, y, z: (w, x, y, z)).
        The resulting sequence has the length of the shortest input sequence.

        Args:
            second: The second iterable to combine.
            third: The third iterable to combine.
            fourth: The fourth iterable to combine.

        Returns:
            A new QIterable[tuple[T, T2, T3, T4]] containing 4-tuples of corresponding elements.

        Examples:
            >>> query([1]).zip_tuple3(["a"], [10], [100]).to_list()
            [(1, 'a', 10, 100)]
        """
        return C.lazy_iterable(lambda: ops.zip_tuple3(self, second, third, fourth))

    def to_dict[TKey, TValue](self, key_selector: Selector[T, TKey], value_selector: Selector[T, TValue], allow_duplicates: bool = False) -> QDict[TKey, TValue]:
        """Creates a dictionary from the iterable using key and value selector functions.

        This method transforms the elements into key-value pairs by applying the selectors,
        then creates a QDict from the results. By default, duplicate keys will raise a
        ValueError so that the caller is not surprised by the surprising behavior of the last value winning which can create nasty bugs.
         Set allow_duplicates=True to use Python dict behavior where the last value overwrites previous ones.

        Args:
            key_selector: A function that takes an element and returns the key for the dictionary entry.
            value_selector: A function that takes an element and returns the value for the dictionary entry.
            allow_duplicates: If False (default), raises ValueError on duplicate keys to match .NET behavior.
                            If True, uses Python dict behavior where last value wins.

        Returns:
            A new QDict containing the key-value pairs created from the elements.

        Raises:
            ValueError: If duplicate keys are encountered and allow_duplicates=False.

        Examples:
            >>> people = [("Alice", 25), ("Bob", 30), ("Charlie", 35)]
            >>> query(people).to_dict(lambda p: p[0], lambda p: p[1])
            # Results in QDict: {"Alice": 25, "Bob": 30, "Charlie": 35}
            >>>
            >>> # Duplicate keys raise ValueError by default
            >>> try:
            ...     query([("same", 1), ("same", 2)]).to_dict(lambda p: p[0], lambda p: p[1])
            ... except ValueError:
            ...     print("Duplicate key error")
            >>>
            >>> # Allow duplicates (Python dict behavior)
            >>> query([("same", 1), ("same", 2)]).to_dict(lambda p: p[0], lambda p: p[1], allow_duplicates=True)
            # Results in QDict: {"same": 2}  # Last value wins
        """
        return ops.to_dict(self, key_selector, value_selector, allow_duplicates)

    def chunk(self, size: int) -> QIterable[QList[T]]:
        """Splits the elements into chunks of the specified size.

        This method groups consecutive elements from the iterable into sublists of the
        specified size. The last chunk may contain fewer elements if the total number
        of elements is not evenly divisible by the chunk size.

        Args:
            size: The maximum size of each chunk. Must be positive.

        Returns:
            A new QIterable where each element is a QList containing up to 'size'
            consecutive elements from the original iterable.

        Raises:
            ArgumentError: If size is less than or equal to zero.

        Examples:
            >>> query([1, 2, 3, 4, 5, 6, 7]).chunk(3).to_list()
            [[1, 2, 3], [4, 5, 6], [7]]
            >>> query(["a", "b", "c", "d"]).chunk(2).to_list()
            [['a', 'b'], ['c', 'd']]
            >>> query([1, 2, 3]).chunk(5).to_list()
            [[1, 2, 3]]  # Single chunk smaller than size
            >>> query([]).chunk(3).to_list()
            []  # Empty input produces empty output
        """
        return C.lazy_iterable(lambda: ops.chunk(self, size))

    @overload
    def group_by[TKey](self, key: Selector[T, TKey]) -> QIterable[QGrouping[TKey, T]]:
        """Groups elements by a key selector function, preserving original elements.

        This overload groups elements based on the key produced by the key selector,
        keeping the original elements in each group. Each group contains the key
        and all original elements that produced that key.

        Args:
            key: A function that takes an element of type T and returns a grouping
                key of type TKey. Elements producing the same key are grouped together.

        Returns:
            A QIterable of QGrouping[TKey, T] objects, where each grouping contains
            a key and all original elements that produced that key. Groups appear in
            the order their keys are first encountered.

        Examples:
            >>> # Group strings by their first character
            >>> groups = query(["apple", "apricot", "banana", "cherry"]).group_by(lambda s: s[0])
            >>> [(g.key, g.to_list()) for g in groups]
            [('a', ['apple', 'apricot']), ('b', ['banana']), ('c', ['cherry'])]

            >>> # Group numbers by even/odd
            >>> groups = query([1, 2, 3, 4, 5, 6]).group_by(lambda x: x % 2 == 0)
            >>> [(g.key, g.to_list()) for g in groups]
            [(False, [1, 3, 5]), (True, [2, 4, 6])]
        """

    @overload
    def group_by[TKey, TSelected](self, key: Selector[T, TKey], select: Selector[T, TSelected]) -> QIterable[QGrouping[TKey, TSelected]]:
        """Groups elements by key and transforms each element before grouping.

        This overload groups elements based on the key produced by the key selector,
        but transforms each element using the select function before placing it in
        the group. This allows you to group by one property while storing a different
        representation of each element in the groups.

        Args:
            key: A function that takes an element of type T and returns a grouping
                key of type TKey. Elements producing the same key are grouped together.
            select: A function that transforms each element of type T into type TSelected
                   before adding it to the group.

        Returns:
            A QIterable of QGrouping[TKey, TSelected] objects, where each grouping
            contains a key and all transformed elements that produced that key.
            Groups appear in the order their keys are first encountered.

        Examples:
            >>> # Group words by length, keeping only uppercase versions
            >>> groups = query(["cat", "dog", "bird", "fish"]).group_by(len, str.upper)
            >>> [(g.key, g.to_list()) for g in groups]
            [(3, ['CAT', 'DOG']), (4, ['BIRD', 'FISH'])]
        """

    def group_by[TKey, TSelected](self, key: Selector[T, TKey], select: Selector[T, TSelected] | None = None) -> QIterable[QGrouping[TKey, T]] | QIterable[QGrouping[TKey, TSelected]]:
        """Groups elements by a key selector function and optionally transforms the grouped elements.

        This method groups elements that produce the same key when the key selector is applied.
        Each group is represented as a QGrouping object that contains the key and all elements
        that produced that key. If an element selector is provided, elements are transformed
        before being grouped.

        Args:
            key: A function that takes an element and returns a key to group by.
            select: Optional function to transform elements before grouping. If None,
                   elements are grouped as-is.

        Returns:
            A QIterable of QGrouping objects, where each grouping contains a key and
            all elements (or transformed elements) that produced that key. Groups appear
            in the order their keys are first encountered.

        Examples:
            >>> # Group strings by first character
            >>> query(["apple", "apricot", "banana"]).group_by(lambda s: s[0]).to_list()
            # Returns groupings: [('a', ['apple', 'apricot']), ('b', ['banana'])]

            >>> # Group and transform elements
            >>> query(["apple", "apricot", "banana"]).group_by(lambda s: s[0], len).to_list()
            # Returns groupings: [('a', [5, 7]), ('b', [6])]

            >>> # Empty iterable returns no groups
            >>> query([]).group_by(lambda x: x).to_list()
            []
        """
        return ops.group_by_q(self, key, select)
    # endregion

    # region single item selecting methods
    def first(self, predicate: Predicate[T] | None = None) -> T:
        """Returns the first element in the iterable, optionally filtered by a predicate.

        This method returns the first element that satisfies the optional predicate.
        If no predicate is provided, it returns the first element in the sequence.
        The method will raise an exception if no matching element is found.

        Args:
            predicate: Optional function that takes an element and returns True if it
                      matches the desired condition. If None, returns the first element.

        Returns:
            The first element that matches the predicate, or the first element if no
            predicate is provided.

        Raises:
            EmptyIterableError: If the iterable is empty or no element matches the predicate.

        Examples:
            >>> query([1, 2, 3, 4]).first()
            1
            >>> query([1, 2, 3, 4]).first(lambda x: x > 2)
            3
            >>> query(["apple", "banana", "cherry"]).first(lambda s: len(s) > 5)
            'banana'
        """
        return ops.first(self, predicate)

    def first_or_none(self, predicate: Predicate[T] | None = None) -> T | None:
        """Returns the first element in the iterable, or None if no element is found.

        This method is similar to first() but returns None instead of raising an exception
        when no matching element is found.

        Args:
            predicate: Optional function that takes an element and returns True if it
                      matches the desired condition. If None, returns the first element.

        Returns:
            The first element that matches the predicate, the first element if no
            predicate is provided, or None if no matching element exists.

        Examples:
            >>> query([1, 2, 3]).first_or_none()
            1
            >>> query([]).first_or_none()
            None
            >>> query([1, 2, 3]).first_or_none(lambda x: x > 5)
            None
            >>> query([1, 2, 3]).first_or_none(lambda x: x > 2)
            3
        """
        return ops.first_or_none(self, predicate)

    def single(self, predicate: Predicate[T] | None = None) -> T:
        """Returns the single element in the iterable, ensuring exactly one element exists.

        This method enforces that exactly one element exists in the sequence (optionally
        matching a predicate). It raises an exception if the sequence is empty or contains
        more than one element, making it useful for scenarios where you expect exactly
        one result.

        Args:
            predicate: Optional function that takes an element and returns True if it
                      matches the desired condition. If None, operates on all elements.

        Returns:
            The single element in the sequence, or the single element matching the predicate.

        Raises:
            EmptyIterableError: If no elements exist or no elements match the predicate.
            MultipleElementsError: If more than one element exists or matches the predicate.

        Examples:
            >>> query([42]).single()
            42
            >>> query([1, 2, 3]).single(lambda x: x == 2)
            2
            >>> query([]).single()  # Raises EmptyIterableError
            >>> query([1, 2]).single()  # Raises MultipleElementsError
        """
        return ops.single(self, predicate)

    def single_or_none(self, predicate: Predicate[T] | None = None) -> T | None:
        """Returns the single element in the iterable, or None if no element exists.

        This method is similar to single() but returns None instead of raising an exception
        when the sequence contains no elements. Like single(), it raises an
        exception if multiple elements exist.

        Args:
            predicate: Optional function that takes an element and returns True if it
                      matches the desired condition. If None, operates on all elements.

        Returns:
            The single element in the sequence, the single element matching the predicate,
            or None if no elements exist.

        Raises:
            InvalidOperationError: If more than one element exists or matches the predicate.

        Examples:
            >>> query([42]).single_or_none()
            42
            >>> query([]).single_or_none()
            None
            >>> query([1, 2, 3]).single_or_none(lambda x: x == 2)
            2
            >>> query([1, 2, 3]).single_or_none(lambda x: x == 4)
            None
            >>> query([1, 2]).single_or_none()  # Raises InvalidOperationError
            >>> query([1, 2, 3]).single_or_none(lambda x: x > 1)  # Raises InvalidOperationError
        """
        return ops.single_or_none(self, predicate)

    def last(self, predicate: Predicate[T] | None = None) -> T:
        """Returns the last element in the iterable, optionally filtered by a predicate.

        This method returns the last element that satisfies the optional predicate.
        If no predicate is provided, it returns the last element in the sequence.
        The method will raise an exception if no matching element is found.

        Args:
            predicate: Optional function that takes an element and returns True if it
                      matches the desired condition. If None, returns the last element.

        Returns:
            The last element that matches the predicate, or the last element if no
            predicate is provided.

        Raises:
            EmptyIterableError: If the iterable is empty or no element matches the predicate.

        Examples:
            >>> query([1, 2, 3, 4]).last()
            4
            >>> query([1, 2, 3, 4]).last(lambda x: x < 3)
            2
            >>> query(["apple", "banana", "cherry"]).last(lambda s: "a" in s)
            'banana'
        """
        return ops.last(self, predicate)

    def last_or_none(self, predicate: Predicate[T] | None = None) -> T | None:
        """Returns the last element in the iterable, or None if no element is found.

        This method is similar to last() but returns None instead of raising an exception
        when no matching element is found.

        Args:
            predicate: Optional function that takes an element and returns True if it
                      matches the desired condition. If None, returns the last element.

        Returns:
            The last element that matches the predicate, the last element if no
            predicate is provided, or None if no matching element exists.

        Examples:
            >>> query([1, 2, 3]).last_or_none()
            3
            >>> query([]).last_or_none()
            None
            >>> query([1, 2, 3]).last_or_none(lambda x: x > 5)
            None
            >>> query([1, 2, 3]).last_or_none(lambda x: x < 3)
            2
        """
        return ops.last_or_none(self, predicate)

    def element_at(self, index: int) -> T:
        """Returns the element at the specified zero-based index position.

        This method provides indexed access to elements in the iterable, similar to
        list indexing but works with any QIterable. The index must be within the
        bounds of the sequence, otherwise an exception is raised.

        Args:
            index: The zero-based index of the element to retrieve. Must be non-negative
                  and less than the length of the iterable.

        Returns:
            The element at the specified index position.

        Raises:
            IndexError: If the index is negative or greater than or equal to the number
                       of elements in the iterable.

        Examples:
            >>> query(["a", "b", "c"]).element_at(0)
            'a'
            >>> query(["a", "b", "c"]).element_at(2)
            'c'
            >>> query([10, 20, 30]).element_at(1)
            20
            >>> query([1, 2, 3]).element_at(5)  # Raises IndexError
        """
        return ops.element_at(self, index)

    def element_at_or_none(self, index: int) -> T | None:
        """Returns the element at the specified index, or None if the index is out of bounds.

        This method is similar to element_at() but returns None instead of raising an
        exception when the index is out of bounds.

        Args:
            index: The zero-based index of the element to retrieve. Can be any integer value.

        Returns:
            The element at the specified index position, or None if the index is negative
            or greater than or equal to the number of elements in the iterable.

        Examples:
            >>> query(["a", "b", "c"]).element_at_or_none(1)
            'b'
            >>> query(["a", "b", "c"]).element_at_or_none(5)
            None
            >>> query(["a", "b", "c"]).element_at_or_none(-1)
            None
            >>> query([]).element_at_or_none(0)
            None
        """
        return ops.element_at_or_none(self, index)

    def min_by[TKey: SupportsRichComparison](self, key_selector: Selector[T, TKey]) -> T:
        """Returns the element with the minimum key value as determined by the key selector.

        This method finds the element that produces the smallest key when the key_selector
        is applied. The key must support comparison operations. If multiple elements
        produce the same minimum key, the first one encountered is returned.

        Args:
            key_selector: A function that takes an element and returns a comparable key.
                         The key must support comparison operations (at minimum __lt__).

        Returns:
            The element that produces the minimum key value.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> query([3, 1, 4, 1, 5]).min_by(lambda x: x)
            1
            >>> query(["apple", "pie", "a"]).min_by(lambda s: len(s))
            'a'
            >>> people = [("Alice", 25), ("Bob", 30), ("Charlie", 20)]
            >>> query(people).min_by(lambda p: p[1])
            ('Charlie', 20)
        """
        return ops.min_by(self, key_selector)

    def max_by[TKey: SupportsRichComparison](self, key_selector: Selector[T, TKey]) -> T:
        """Returns the element with the maximum key value as determined by the key selector.

        This method finds the element that produces the largest key when the key_selector
        is applied. The key must support comparison operations. If multiple elements
        produce the same maximum key, the first one encountered is returned.

        Args:
            key_selector: A function that takes an element and returns a comparable key.
                         The key must support comparison operations (at minimum __lt__).

        Returns:
            The element that produces the maximum key value.

        Raises:
            EmptyIterableError: If the iterable is empty.

        Examples:
            >>> query([3, 1, 4, 1, 5]).max_by(lambda x: x)
            5
            >>> query(["apple", "pie", "a"]).max_by(lambda s: len(s))
            'apple'
            >>> people = [("Alice", 25), ("Bob", 30), ("Charlie", 20)]
            >>> query(people).max_by(lambda p: p[1])
            ('Bob', 30)
        """
        return ops.max_by(self, key_selector)

    # endregion

    # region methods subclasses may want to override for perfarmonce reasons

    def _optimized_length(self) -> int:
        """Returns the number of elements in this iterable using a basic counting approach.

        This is a default implementation that counts elements by iterating through
        the entire sequence. Subclasses may override this method to provide more
        efficient length calculation when the collection type supports it (e.g.,
        using len() for lists or sets).

        Returns:
            The number of elements in this iterable.

        Examples:
            >>> # Internal usage - subclasses may override for better performance
            >>> query([1, 2, 3])._optimized_length()
            3
            >>> query([])._optimized_length()
            0

        Note:
            This is an internal method used for performance optimization.
            Subclasses should override this when they can provide O(1) length
            computation instead of the default O(n) iteration.
        """
        return sum(1 for _ in self)

    def _assert_not_empty(self) -> Self:
        """Validates that this iterable contains at least one element.

        This is a helper method used internally to ensure that operations requiring
        non-empty sequences can safely proceed. It checks if the iterable has any
        elements and raises an exception if it's empty, otherwise returns self
        for method chaining.

        Returns:
            This same iterable instance if it contains at least one element.

        Raises:
            EmptyIterableError: If the iterable contains no elements.

        Examples:
            >>> # Internal usage - validates non-empty before proceeding
            >>> query([1, 2, 3])._assert_not_empty().first()
            1
            >>> query([])._assert_not_empty()  # Raises EmptyIterableError

        Note:
            This is an internal validation method used by operations that require
            non-empty sequences, such as first(), last(), min(), max(), etc.
        """
        if not self.any(): raise EmptyIterableError()
        return self

    # region factory methods
    # note: we do not "optimize" by returning self in any subclass because the contract is to create a new independent copy
    def to_list(self) -> QList[T]:
        """Converts this iterable to a QList containing all elements.

        This method creates a new QList instance containing all elements from this
        iterable. QList is a subtype of the builtin list and intoperates seamlessly with it,
        while also suppplying all the query operators from QIterable.

        Returns:
            A new QList[T] containing all elements from this iterable in the same order,
            providing all the query operators from QIterable.

        Examples:
            >>> query([1, 2, 3]).where(lambda x: x > 1).to_list()
            [2, 3]
            >>> query(["a", "b", "c"]).select(str.upper).to_list()
            ['A', 'B', 'C']
            >>> query([]).to_list()
            []
            >>> # Materializes lazy operations
            >>> lazy_query = query(range(1000)).where(lambda x: x % 2 == 0)
            >>> result = lazy_query.to_list()  # Now evaluated and stored
        """
        return C.list(self)

    def to_set(self) -> QSet[T]:
        """Converts this iterable to a QSet containing all unique elements.

        This method creates a new QSet instance containing all distinct elements
        from this iterable. Duplicate elements are automatically removed.
        QSet is a subtype of the builtin set and interoperates seamlessly with it,
        while also suppplying all the query operators from QIterable

        Returns:
            A new QSet[T] containing all unique elements from this iterable,
            providing all the query operators from QIterable.

        Examples:
            >>> query([1, 2, 2, 3, 3]).to_set()
            {1, 2, 3}
            >>> query(["apple", "banana", "apple"]).to_set()
            {'apple', 'banana'}
            >>> query([]).to_set()
            set()
            >>> # Removes duplicates during conversion
            >>> query([1, 1, 1, 1]).to_set()
            {1}
        """
        return C.set(self)

    def to_frozenset(self) -> QFrozenSet[T]:
        """Converts this iterable to a QFrozenSet containing all unique elements.

        This method creates a new QFrozenSet instance containing all distinct
        elements from this iterable. Like to_set(), duplicates are automatically
        removed, but the resulting collection is immutable. QfrozenSet is a subtype
        of the builtin frozenset and interoperates seamlessly with it,
        while also supplying all the query operators from QIterable.

        Returns:
            A new QFrozenSet[T] containing all unique elements from this iterable,
            providing all the query operators from QIterable.

        Examples:
            >>> query([1, 2, 2, 3]).to_frozenset()
            frozenset({1, 2, 3})
            >>> query(["x", "y", "x"]).to_frozenset()
            frozenset({'x', 'y'})
            >>> query([]).to_frozenset()
            frozenset()
            >>> # Immutable set with LINQ methods
            >>> fs = query([1, 2, 3, 2]).to_frozenset()
            >>> fs.where(lambda x: x > 1).to_list()
            [2, 3]
        """
        return C.frozen_set(self)

    def to_sequence(self) -> QSequence[T]:
        """Converts this iterable to a QSequence containing all elements.

        This method creates a new immutable QSequence instance containing all elements from
        this iterable. QSequence provides all the query operators from QIterable.

        Returns:
            A new QSequence[T] containing all elements from this iterable in the same order,
            providing all the query operators from QIterable.

        Examples:
            >>> query([1, 2, 3]).to_sequence()
            [1, 2, 3]  # Immutable sequence
            >>> query("hello").to_sequence()
            ['h', 'e', 'l', 'l', 'o']
            >>> query([]).to_sequence()
            []
            >>> # Preserves order in immutable collection
            >>> seq = query([3, 1, 2]).to_sequence()
            >>> seq.order_by(lambda x: x).to_list()
            [1, 2, 3]
        """
        return C.sequence(self)

    def to_tuple(self) -> tuple[T, ...]:
        """Converts this iterable to a tuple containing all elements.

        This method creates a new immutable tuple instance containing all elements from
        this iterable. The tuple is a standard Python built-in tuple.

        Returns:
            A new tuple[T, ...] containing all elements from this iterable in the same order.

        Examples:
            >>> query([1, 2, 3]).where(lambda x: x > 1).to_tuple()
            (2, 3)
            >>> query("abc").to_tuple()
            ('a', 'b', 'c')
            >>> query([]).to_tuple()
            ()
            >>> # Materializes lazy operations into immutable tuple
            >>> lazy_query = query(range(5)).where(lambda x: x % 2 == 0)
            >>> result = lazy_query.to_tuple()  # Now evaluated and stored
            >>> result
            (0, 2, 4)
        """
        return tuple(self)

    def to_built_in_list(self) -> list[T]:
        """Converts this iterable to a standard Python list containing all elements.

        This method creates a new Python built-in list instance containing all
        elements from this iterable.

        Returns:
            A new Python list[T] containing all elements from this iterable in the same order.

        Examples:
            >>> query([1, 2, 3]).where(lambda x: x > 1).to_built_in_list()
            [2, 3]
            >>> query("abc").to_built_in_list()
            ['a', 'b', 'c']
            >>> query([]).to_built_in_list()
            []
            >>> # Standard Python list for interoperability
            >>> result = query([1, 2, 3]).select(lambda x: x * 2).to_built_in_list()
            >>> len(result)  # Standard Python operations work
            3
        """
        return list(self)

    # endregion
