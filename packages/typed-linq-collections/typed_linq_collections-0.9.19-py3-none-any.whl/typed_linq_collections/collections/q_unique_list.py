from __future__ import annotations

from bisect import bisect_left, bisect_right
from itertools import chain
from typing import TYPE_CHECKING, Self, override

from typed_linq_collections.q_iterable import QIterable

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator
    from collections.abc import Set as AbstractSet


class QUniqueList[TItem](QIterable[TItem]):
    """A memory-efficient unique collection that maintains items sorted by hash.

    QUniqueList provides set-like uniqueness guarantees while using significantly less
    memory than Python's built-in set. It achieves this by storing items in a plain list
    sorted by their hash values, using binary search for O(log n) lookups instead of
    hash tables.

    Performance characteristics:
    - Contains/membership: O(log n) average case
    - Add: O(n) due to list insertion (binary search + list shift)
    - Remove: O(n) due to list deletion (binary search + list shift)
    - Memory: Minimal - just a list of items (no hash table overhead)

    Trade-offs compared to set:
    - Much lower memory usage (~90% less for object references)
    - Slower insertions/deletions due to list shifting
    - Faster iteration (contiguous memory)
    - Items must be hashable (same requirement as set)

    Use QUniqueList when:
    - Memory is constrained
    - You primarily read/query after building the collection
    - You need to minimize memory overhead

    Use set when:
    - You need O(1) insertions/deletions
    - You frequently modify the collection

    Inheritance:
    - Implements QIterable[TItem] for LINQ-style query operations
    """

    __slots__: tuple[str, ...] = ("_items",)

    def __init__(self, iterable: Iterable[TItem] = ()) -> None:
        """Initializes a new QUniqueList with unique elements from the given iterable.

        Duplicate elements in the input iterable are automatically removed, maintaining
        only unique values. Items are stored sorted by their hash values.

        Args:
            iterable: An iterable of hashable elements to initialize the collection with.
                     Duplicates will be automatically removed.
                     Defaults to an empty sequence.

        Raises:
            TypeError: If any item is not hashable.

        Examples:
            >>> QUniqueList([1, 2, 3])
            QUniqueList([1, 2, 3])
            >>> QUniqueList([1, 2, 2, 3])  # Duplicates removed
            QUniqueList([1, 2, 3])
        """

        self._items: list[TItem] = sorted(set(iterable), key=hash)

    @staticmethod
    def create[T](*sources: Iterable[T]) -> QUniqueList[T]:
        """Creates a new QUniqueList by combining elements from multiple iterables.

        This method is useful for combining collections of different subtypes into
        a common base type. Elements from all sources are combined and deduplicated.

        Args:
            *sources: One or more iterables of elements to combine.
                     Duplicates across all sources will be removed.

        Returns:
            A new QUniqueList containing unique elements from all sources.

        Examples:
            >>> QUniqueList.create([1, 2], [2, 3], [3, 4])
            QUniqueList([1, 2, 3, 4])
        """
        if not sources:
            return QUniqueList()
        if len(sources) == 1:
            return QUniqueList(sources[0])
        return QUniqueList(chain(*sources))

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

    def add(self, item: TItem) -> None:
        """Add an item to the collection if it's not already present.

        If the item already exists (determined by equality), this method does nothing.

        Args:
            item: The hashable item to add.

        Raises:
            TypeError: If the item is not hashable.

        Examples:
            >>> ul = QUniqueList([1, 2, 3])
            >>> ul.add(4)
            >>> ul.add(2)  # Already exists, no effect
            >>> list(ul)
            [1, 2, 3, 4]
        """
        index, found = self._find_index(item)
        if not found:
            self._items.insert(index, item)

    def discard(self, item: TItem) -> None:
        """Remove an item from the collection if it exists.

        If the item is not found, this method does nothing (silent success).
        This provides consistency with set.discard() behavior.

        Args:
            item: The item to remove.

        Examples:
            >>> ul = QUniqueList([1, 2, 3])
            >>> ul.discard(2)
            >>> ul.discard(999)  # No error
            >>> list(ul)
            [1, 3]
        """
        index, found = self._find_index(item)
        if found:
            del self._items[index]

    def remove(self, item: TItem) -> None:
        """Remove an item from the collection.

        Args:
            item: The item to remove.

        Raises:
            ValueError: If the item is not in the collection.

        Examples:
            >>> ul = QUniqueList([1, 2, 3])
            >>> ul.remove(2)
            >>> list(ul)
            [1, 3]
        """
        index, found = self._find_index(item)
        if not found:
            raise ValueError(f"{item!r} not in QUniqueList")
        del self._items[index]

    def remove_where(self, predicate: Callable[[TItem], bool]) -> int:
        """Remove all items matching the predicate.

        Args:
            predicate: A function that returns True for items to remove.

        Returns:
            The number of items removed.

        Examples:
            >>> ul = QUniqueList([1, 2, 3, 4, 5])
            >>> ul.remove_where(lambda x: x % 2 == 0)
            2
            >>> list(ul)
            [1, 3, 5]
        """
        to_remove = [item for item in self._items if predicate(item)]
        for item in to_remove:
            self.discard(item)
        return len(to_remove)

    def update(self, *others: Iterable[TItem]) -> None:
        """Update the collection, adding elements from all others.

        This is an in-place operation that adds all unique elements from the
        provided iterables to this collection. This method provides consistency
        with set.update() behavior.

        Args:
            *others: One or more iterables whose elements will be added.

        Examples:
            >>> ul = QUniqueList([1, 2, 3])
            >>> ul.update([3, 4, 5], [5, 6, 7])
            >>> sorted(ul)
            [1, 2, 3, 4, 5, 6, 7]
        """
        if not others:
            return
        # Combine current items with all others, deduplicate and sort
        self._items = sorted(set(chain(self._items, *others)), key=hash)

    def clear(self) -> None:
        """Remove all items from the collection.

        Examples:
            >>> ul = QUniqueList([1, 2, 3])
            >>> ul.clear()
            >>> len(ul)
            0
        """
        self._items.clear()

    def copy(self) -> Self:
        """Create a shallow copy of the collection.

        Returns:
            A new QUniqueList with the same items.

        Examples:
            >>> ul = QUniqueList([1, 2, 3])
            >>> ul2 = ul.copy()
            >>> ul2.add(4)
            >>> list(ul)
            [1, 2, 3]
            >>> list(ul2)
            [1, 2, 3, 4]
        """
        new_list: Self = type(self).__new__(type(self))
        new_list._items = self._items.copy()
        return new_list

    def __contains__(self, item: object) -> bool:
        """Check if an item is in the collection.

        Args:
            item: The item to check for.

        Returns:
            True if the item is in the collection, False otherwise.

        Examples:
            >>> ul = QUniqueList([1, 2, 3])
            >>> 2 in ul
            True
            >>> 5 in ul
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
            >>> ul = QUniqueList([1, 2, 3])
            >>> len(ul)
            3
        """
        return len(self._items)

    @override
    def __iter__(self) -> Iterator[TItem]:
        """Iterate over items in hash-sorted order.

        Returns:
            An iterator over the items.

        Examples:
            >>> ul = QUniqueList([3, 1, 2])
            >>> list(ul)  # Order depends on hash values
            [...]
        """
        return iter(self._items)

    @override
    def __repr__(self) -> str:
        """Return a string representation of the collection.

        Returns:
            A string showing the collection contents.

        Examples:
            >>> QUniqueList([1, 2, 3])
            QUniqueList([1, 2, 3])
        """
        return f"QUniqueList({list(self._items)!r})"

    @override
    def __eq__(self, other: object) -> bool:
        """Check equality with another collection.

        Two QUniqueLists are equal if they contain the same items,
        regardless of order (since order is hash-based).

        Args:
            other: The object to compare with.

        Returns:
            True if both contain the same items.

        Examples:
            >>> QUniqueList([1, 2, 3]) == QUniqueList([3, 2, 1])
            True
            >>> QUniqueList([1, 2]) == QUniqueList([1, 2, 3])
            False
        """
        if isinstance(other, QUniqueList):
            return set(self._items) == set(other._items)  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
        return NotImplemented

    def __bool__(self) -> bool:
        """Check if the collection is non-empty.

        Returns:
            False if empty, True otherwise.

        Examples:
            >>> bool(QUniqueList())
            False
            >>> bool(QUniqueList([1]))
            True
        """
        return bool(self._items)

    # Set operations

    def union(self, *others: Iterable[TItem]) -> Self:
        """Return a new collection with elements from this collection and all others.

        Args:
            *others: One or more iterables to union with.

        Returns:
            A new QUniqueList containing all unique elements.

        Examples:
            >>> ul1 = QUniqueList([1, 2, 3])
            >>> ul2 = QUniqueList([3, 4, 5])
            >>> list(ul1.union(ul2))
            [1, 2, 3, 4, 5]
        """
        # Combine all iterables and deduplicate in one operation
        result: Self = type(self).__new__(type(self))
        result._items = sorted(set(chain(self._items, *others)), key=hash)
        return result

    def intersection(self, *others: Iterable[TItem]) -> Self:
        """Return a new collection with elements common to this collection and all others.

        Args:
            *others: One or more iterables to intersect with.

        Returns:
            A new QUniqueList containing only common elements.

        Examples:
            >>> ul1 = QUniqueList([1, 2, 3, 4])
            >>> ul2 = QUniqueList([3, 4, 5])
            >>> list(ul1.intersection(ul2))
            [3, 4]
        """
        if not others:
            return self.copy()

        # Convert others to sets for fast lookup
        other_sets = [set(other) for other in others]
        result: Self = type(self).__new__(type(self))
        result._items = []

        for item in self._items:
            if all(item in other_set for other_set in other_sets):
                result._items.append(item)

        return result

    def difference(self, *others: Iterable[TItem]) -> Self:
        """Return a new collection with elements in this collection but not in others.

        Args:
            *others: One or more iterables to subtract.

        Returns:
            A new QUniqueList with elements not in any of the others.

        Examples:
            >>> ul1 = QUniqueList([1, 2, 3, 4])
            >>> ul2 = QUniqueList([3, 4, 5])
            >>> list(ul1.difference(ul2))
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
        """Return a new collection with elements in either collection but not both.

        Args:
            other: An iterable to compute symmetric difference with.

        Returns:
            A new QUniqueList with elements unique to each collection.

        Examples:
            >>> ul1 = QUniqueList([1, 2, 3])
            >>> ul2 = QUniqueList([3, 4, 5])
            >>> list(ul1.symmetric_difference(ul2))
            [1, 2, 4, 5]
        """
        other_set = set(other)
        self_set = set(self._items)

        # Collect items from self not in other and items from other not in self
        unique_items = [item for item in self._items if item not in other_set]
        unique_items.extend(item for item in other_set if item not in self_set)

        result: Self = type(self).__new__(type(self))
        result._items = sorted(unique_items, key=hash)
        return result

    def issubset(self, other: Iterable[TItem]) -> bool:
        """Test whether every element in the collection is in other.

        Args:
            other: An iterable to test against.

        Returns:
            True if this collection is a subset of other.

        Examples:
            >>> ul1 = QUniqueList([1, 2])
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
            >>> ul1 = QUniqueList([1, 2, 3, 4])
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
            >>> ul1 = QUniqueList([1, 2, 3])
            >>> ul1.isdisjoint([4, 5, 6])
            True
        """
        return all(item not in self for item in other)

    # Set operators

    def __or__(self, other: AbstractSet[TItem] | QUniqueList[TItem]) -> Self:
        """Return the union using the | operator.

        Args:
            other: A set to union with.

        Returns:
            A new QUniqueList with all unique elements.

        Examples:
            >>> ul1 = QUniqueList([1, 2, 3])
            >>> ul2 = QUniqueList([3, 4, 5])
            >>> list(ul1 | ul2)
            [1, 2, 3, 4, 5]
        """
        return self.union(other)

    def __and__(self, other: AbstractSet[TItem] | QUniqueList[TItem]) -> Self:
        """Return the intersection using the & operator.

        Args:
            other: A set to intersect with.

        Returns:
            A new QUniqueList with common elements.

        Examples:
            >>> ul1 = QUniqueList([1, 2, 3, 4])
            >>> ul2 = QUniqueList([3, 4, 5])
            >>> list(ul1 & ul2)
            [3, 4]
        """
        return self.intersection(other)

    def __sub__(self, other: AbstractSet[TItem] | QUniqueList[TItem]) -> Self:
        """Return the difference using the - operator.

        Args:
            other: A set to subtract.

        Returns:
            A new QUniqueList with elements not in other.

        Examples:
            >>> ul1 = QUniqueList([1, 2, 3, 4])
            >>> ul2 = QUniqueList([3, 4, 5])
            >>> list(ul1 - ul2)
            [1, 2]
        """
        return self.difference(other)

    def __xor__(self, other: AbstractSet[TItem] | QUniqueList[TItem]) -> Self:
        """Return the symmetric difference using the ^ operator.

        Args:
            other: A set to compute symmetric difference with.

        Returns:
            A new QUniqueList with elements in either but not both.

        Examples:
            >>> ul1 = QUniqueList([1, 2, 3])
            >>> ul2 = QUniqueList([3, 4, 5])
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
            >>> ul = QUniqueList([1, 2, 3, 4, 5])
            >>> ul.contains(3)
            True
            >>> ul.contains(10)
            False
        """
        return value in self
