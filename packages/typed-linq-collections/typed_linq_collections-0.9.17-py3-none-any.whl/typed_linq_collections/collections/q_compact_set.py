from __future__ import annotations

from bisect import bisect_left, bisect_right
from itertools import chain
from typing import TYPE_CHECKING, Self, override

from typed_linq_collections.q_iterable import QIterable

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from collections.abc import Set as AbstractSet


class QCompactSet[TItem](QIterable[TItem]):
    """An immutable, memory-efficient set that maintains items sorted by hash.

    QCompactSet provides set-like uniqueness guarantees while using ~75% less
    memory than Python's built-in set or frozenset. It achieves this by storing
    items in a plain list sorted by their hash values, using binary search for
    O(log n) lookups instead of hash tables.

    This collection is immutable - once created, items cannot be added or removed.
    All set operations return new QCompactSet instances.

    Performance characteristics:
    - Construction: O(n log n) - deduplicates and sorts
    - Contains/membership: O(log n) - binary search on hashes
    - Iteration: O(n) - fast, contiguous memory
    - Memory: ~75% less than set/frozenset (just a list of items, no hash table)

    Trade-offs compared to set/frozenset:
    - Much lower memory usage (~8 KB vs ~36 KB for 1000 references)
    - Slower lookups: O(log n) vs O(1)
    - Immutable (like frozenset)
    - Items must be hashable (same requirement as set/frozenset)

    Use QCompactSet when:
    - Memory is the primary constraint
    - You build the collection once and query it many times
    - You can accept O(log n) lookups instead of O(1)
    - You need immutability

    Use set/frozenset when:
    - You need O(1) lookups
    - Memory is not a concern
    - You need mutability (set only)

    Inheritance:
    - Implements QIterable[TItem] for LINQ-style query operations
    """

    __slots__: tuple[str, ...] = ("_items",)

    def __init__(self, iterable: Iterable[TItem] = ()) -> None:
        """Initializes a new QCompactSet with unique elements from the given iterable.

        Duplicate elements in the input iterable are automatically removed, and
        items are stored sorted by their hash values for efficient binary search.

        This operation is O(n log n) where n is the number of unique items.

        Args:
            iterable: An iterable of hashable elements to initialize the set with.
                     Duplicates will be automatically removed.
                     Defaults to an empty sequence.

        Raises:
            TypeError: If any item is not hashable.

        Examples:
            >>> QCompactSet([1, 2, 3])
            QCompactSet([1, 2, 3])
            >>> QCompactSet([1, 2, 2, 3])  # Duplicates removed
            QCompactSet([1, 2, 3])
        """
        # Efficient O(n log n) construction:
        # 1. dict.fromkeys() deduplicates in O(n) using temporary hash table
        # 2. sorted(..., key=hash) sorts in O(n log n)
        # Hash table is garbage collected after construction
        self._items: list[TItem] = sorted(dict.fromkeys(iterable), key=hash)

    @staticmethod
    def create[T](*sources: Iterable[T]) -> QCompactSet[T]:
        """Creates a new QCompactSet by combining elements from multiple iterables.

        This method is useful for combining collections of different subtypes into
        a common base type. Elements from all sources are combined and deduplicated.

        Args:
            *sources: One or more iterables of elements to combine.
                     Duplicates across all sources will be removed.

        Returns:
            A new QCompactSet containing unique elements from all sources.

        Examples:
            >>> QCompactSet.create([1, 2], [2, 3], [3, 4])
            QCompactSet([1, 2, 3, 4])
        """
        if not sources:
            return QCompactSet()
        if len(sources) == 1:
            return QCompactSet(sources[0])
        return QCompactSet(chain(*sources))

    def _find_index(self, item: TItem) -> tuple[int, bool]:
        """Find the index where item is or should be inserted.

        Uses binary search on hash values for O(log n) lookup.

        Args:
            item: The item to find.

        Returns:
            A tuple of (index, found) where:
            - index is where the item is or should be inserted
            - found is True if the exact item exists at that index
        """
        if not self._items:
            return (0, False)

        item_hash = hash(item)
        # Find leftmost position where hash(item) could be
        left = bisect_left(self._items, item_hash, key=hash)
        # Find rightmost position where hash(item) could be
        right = bisect_right(self._items, item_hash, key=hash)

        # Check if item exists in the range [left, right)
        for i in range(left, right):
            if self._items[i] == item:
                return (i, True)

        # Item not found, return insertion point
        return (left, False)

    def copy(self) -> Self:
        """Create a shallow copy of the set.

        Returns:
            A new QCompactSet with the same items.

        Examples:
            >>> cs = QCompactSet([1, 2, 3])
            >>> cs2 = cs.copy()
            >>> cs2 is cs
            False
            >>> list(cs2)
            [1, 2, 3]
        """
        new_set: Self = type(self).__new__(type(self))
        new_set._items = self._items.copy()
        return new_set

    def __contains__(self, item: object) -> bool:
        """Check if an item is in the collection.

        Args:
            item: The item to check for.

        Returns:
            True if the item is in the collection, False otherwise.

        Examples:
            >>> cs = QCompactSet([1, 2, 3])
            >>> 2 in cs
            True
            >>> 5 in cs
            False
        """
        try:
            # Try to hash the item first to ensure it's hashable
            hash(item)
            # If hashable, search for it (cast is safe since we know it's hashable)
            from typing import cast as type_cast
            _, found = self._find_index(type_cast(TItem, item))
            return found
        except TypeError:
            # Item is not hashable, so it can't be in the collection
            return False

    def __len__(self) -> int:
        """Return the number of items in the collection.

        Returns:
            The number of unique items.

        Examples:
            >>> cs = QCompactSet([1, 2, 3])
            >>> len(cs)
            3
        """
        return len(self._items)

    @override
    def __iter__(self) -> Iterator[TItem]:
        """Iterate over items in hash-sorted order.

        Returns:
            An iterator over the items.

        Examples:
            >>> cs = QCompactSet([3, 1, 2])
            >>> list(cs)  # Order depends on hash values
            [...]
        """
        return iter(self._items)

    @override
    def __repr__(self) -> str:
        """Return a string representation of the collection.

        Returns:
            A string showing the collection contents.

        Examples:
            >>> QCompactSet([1, 2, 3])
            QCompactSet([1, 2, 3])
        """
        return f"QCompactSet({list(self._items)!r})"

    @override
    def __eq__(self, other: object) -> bool:
        """Check equality with another collection.

        Two QCompactSets are equal if they contain the same items,
        regardless of order (since order is hash-based).

        Args:
            other: The object to compare with.

        Returns:
            True if both contain the same items.

        Examples:
            >>> QCompactSet([1, 2, 3]) == QCompactSet([3, 2, 1])
            True
            >>> QCompactSet([1, 2]) == QCompactSet([1, 2, 3])
            False
        """
        if isinstance(other, QCompactSet):
            return set(self._items) == set(other._items)  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        return NotImplemented

    def __bool__(self) -> bool:
        """Check if the collection is non-empty.

        Returns:
            False if empty, True otherwise.

        Examples:
            >>> bool(QCompactSet())
            False
            >>> bool(QCompactSet([1]))
            True
        """
        return bool(self._items)

    # Set operations

    def union(self, *others: Iterable[TItem]) -> Self:
        """Return a new set with elements from this set and all others.

        Args:
            *others: One or more iterables to union with.

        Returns:
            A new QCompactSet containing all unique elements.

        Examples:
            >>> cs1 = QCompactSet([1, 2, 3])
            >>> cs2 = QCompactSet([3, 4, 5])
            >>> sorted(cs1.union(cs2))
            [1, 2, 3, 4, 5]
        """
        # Efficient O(n log n): use set for deduplication, then sort
        combined = set(chain(self._items, *others))
        result: Self = type(self).__new__(type(self))
        result._items = sorted(combined, key=hash)
        return result

    def intersection(self, *others: Iterable[TItem]) -> Self:
        """Return a new set with elements common to this set and all others.

        Args:
            *others: One or more iterables to intersect with.

        Returns:
            A new QCompactSet containing only common elements.

        Examples:
            >>> cs1 = QCompactSet([1, 2, 3, 4])
            >>> cs2 = QCompactSet([3, 4, 5])
            >>> sorted(cs1.intersection(cs2))
            [3, 4]
        """
        if not others:
            return self.copy()

        # Convert others to sets for fast lookup
        other_sets = [set(other) for other in others]
        # Filter self._items and keep sorted order
        result: Self = type(self).__new__(type(self))
        result._items = [item for item in self._items
                         if all(item in other_set for other_set in other_sets)]
        return result

    def difference(self, *others: Iterable[TItem]) -> Self:
        """Return a new set with elements in this set but not in others.

        Args:
            *others: One or more iterables to subtract.

        Returns:
            A new QCompactSet with elements not in any of the others.

        Examples:
            >>> cs1 = QCompactSet([1, 2, 3, 4])
            >>> cs2 = QCompactSet([3, 4, 5])
            >>> sorted(cs1.difference(cs2))
            [1, 2]
        """
        if not others:
            return self.copy()

        # Combine all others into one set for fast lookup
        other_items = set(chain(*others))
        result: Self = type(self).__new__(type(self))
        result._items = [item for item in self._items if item not in other_items]
        return result

    def symmetric_difference(self, other: Iterable[TItem]) -> Self:
        """Return a new set with elements in either set but not both.

        Args:
            other: An iterable to compute symmetric difference with.

        Returns:
            A new QCompactSet with elements unique to each set.

        Examples:
            >>> cs1 = QCompactSet([1, 2, 3])
            >>> cs2 = QCompactSet([3, 4, 5])
            >>> sorted(cs1.symmetric_difference(cs2))
            [1, 2, 4, 5]
        """
        # Use set symmetric_difference, then sort
        result_set = set(self._items) ^ set(other)
        result: Self = type(self).__new__(type(self))
        result._items = sorted(result_set, key=hash)
        return result

    def issubset(self, other: Iterable[TItem]) -> bool:
        """Test whether every element in the collection is in other.

        Args:
            other: An iterable to test against.

        Returns:
            True if this collection is a subset of other.

        Examples:
            >>> ul1 = QCompactSet([1, 2])
            >>> ul1.issubset([1, 2, 3, 4])
            True
        """
        other_set = set(other)
        return all(item in other_set for item in self._items)

    def issuperset(self, other: Iterable[TItem]) -> bool:
        """Test whether every element in other is in the collection.

        Args:
            other: An iterable to test against.

        Returns:
            True if this collection is a superset of other.

        Examples:
            >>> ul1 = QCompactSet([1, 2, 3, 4])
            >>> ul1.issuperset([1, 2])
            True
        """
        return all(item in self for item in other)

    def isdisjoint(self, other: Iterable[TItem]) -> bool:
        """Test whether the collection has no elements in common with other.

        Args:
            other: An iterable to test against.

        Returns:
            True if no elements are shared.

        Examples:
            >>> ul1 = QCompactSet([1, 2, 3])
            >>> ul1.isdisjoint([4, 5, 6])
            True
        """
        return all(item not in self for item in other)

    # Set operators

    def __or__(self, other: AbstractSet[TItem] | QCompactSet[TItem]) -> Self:
        """Return the union using the | operator.

        Args:
            other: A set to union with.

        Returns:
            A new QCompactSet with all unique elements.

        Examples:
            >>> ul1 = QCompactSet([1, 2, 3])
            >>> ul2 = QCompactSet([3, 4, 5])
            >>> list(ul1 | ul2)
            [1, 2, 3, 4, 5]
        """
        return self.union(other)

    def __and__(self, other: AbstractSet[TItem] | QCompactSet[TItem]) -> Self:
        """Return the intersection using the & operator.

        Args:
            other: A set to intersect with.

        Returns:
            A new QCompactSet with common elements.

        Examples:
            >>> ul1 = QCompactSet([1, 2, 3, 4])
            >>> ul2 = QCompactSet([3, 4, 5])
            >>> list(ul1 & ul2)
            [3, 4]
        """
        return self.intersection(other)

    def __sub__(self, other: AbstractSet[TItem] | QCompactSet[TItem]) -> Self:
        """Return the difference using the - operator.

        Args:
            other: A set to subtract.

        Returns:
            A new QCompactSet with elements not in other.

        Examples:
            >>> ul1 = QCompactSet([1, 2, 3, 4])
            >>> ul2 = QCompactSet([3, 4, 5])
            >>> list(ul1 - ul2)
            [1, 2]
        """
        return self.difference(other)

    def __xor__(self, other: AbstractSet[TItem] | QCompactSet[TItem]) -> Self:
        """Return the symmetric difference using the ^ operator.

        Args:
            other: A set to compute symmetric difference with.

        Returns:
            A new QCompactSet with elements in either but not both.

        Examples:
            >>> ul1 = QCompactSet([1, 2, 3])
            >>> ul2 = QCompactSet([3, 4, 5])
            >>> list(ul1 ^ ul2)
            [1, 2, 4, 5]
        """
        return self.symmetric_difference(other)

    # QIterable implementation

    @override
    def _optimized_length(self) -> int:
        return len(self._items)

    @override
    def contains(self, value: TItem) -> bool:
        """Determines whether the collection contains the specified element.

        This method provides O(log n) average-case performance for membership testing
        using binary search on hash values.

        Args:
            value: The element to search for.

        Returns:
            True if the element is found, False otherwise.

        Examples:
            >>> cs = QCompactSet([1, 2, 3, 4, 5])
            >>> cs.contains(3)
            True
            >>> cs.contains(10)
            False
        """
        return value in self
