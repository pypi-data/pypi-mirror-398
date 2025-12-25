from __future__ import annotations

from typing import TYPE_CHECKING, Self, override

from typed_linq_collections.collections.q_set import QSet

if TYPE_CHECKING:
    from collections.abc import Iterable


class QInterningStringSet(QSet[str]):
    """A specialized QSet that automatically interns all string values before storing them.

    String interning is a method of storing only one copy of each distinct string value.
    This can save memory when the same strings are used repeatedly, and can make string
    comparisons faster (since interned strings can be compared by identity rather than value).

    All strings added to this set are automatically interned using Python's sys.intern()
    function. This applies to strings added via any method: initialization, add, update,
    union, etc.

    Inheritance:
    - Inherits from QSet[str], providing all set operations with automatic string interning
    - Maintains all LINQ-style query operations from QIterable

    Examples:
        >>> qset = QInterningStringSet(["hello", "world"])
        >>> # All stored strings are interned
        >>> "hello" in qset  # Uses interned comparison
        True
        >>> qset.add("python")
        >>> # "python" is automatically interned before storage
    """
    __slots__: tuple[str, ...] = ()

    @override
    def __init__(self, iterable: Iterable[str] = ()) -> None:
        """Initializes a new QInterningStringSet with interned strings from the given iterable.

        All strings in the input iterable are automatically interned before being added
        to the set. Duplicates are removed as per standard set behavior.

        Args:
            iterable: An iterable of strings to initialize the set with.
                     All strings will be interned automatically.
                     Defaults to an empty sequence.
        """
        super().__init__(self._intern_iterable(iterable))

    @staticmethod
    def _intern_iterable(iterable: Iterable[str]) -> Iterable[str]:
        """Interns all strings in the given iterable.

        Args:
            iterable: An iterable of strings to intern.

        Returns:
            An iterable of interned strings.
        """
        import sys
        return (sys.intern(s) for s in iterable)

    @override
    def add(self, element: str) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Adds an interned version of the string to the set.

        Args:
            element: The string to intern and add to the set.
        """
        import sys
        super().add(sys.intern(element))

    @override
    def update(self, *others: Iterable[str]) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Updates the set by adding interned versions of strings from the given iterables.

        Args:
            *others: One or more iterables of strings to intern and add to the set.
        """
        for other in others:
            super().update(self._intern_iterable(other))

    @override
    def union(self, *others: Iterable[str]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Returns a new set with interned strings from this set and all others.

        Args:
            *others: One or more iterables of strings to include in the union.

        Returns:
            A new QInterningStringSet containing the union of all sets.
        """
        result = self.copy()
        result.update(*others)
        return result

    @override
    def intersection_update(self, *others: Iterable[str]) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Updates the set, keeping only interned strings found in all iterables.

        Args:
            *others: One or more iterables of strings to intersect with.
        """
        interned_others = [set(self._intern_iterable(other)) for other in others]
        super().intersection_update(*interned_others)

    @override
    def difference_update(self, *others: Iterable[str]) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Removes interned versions of strings found in the given iterables.

        Args:
            *others: One or more iterables of strings to remove.
        """
        for other in others:
            super().difference_update(self._intern_iterable(other))

    @override
    def symmetric_difference_update(self, other: Iterable[str]) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Updates the set to contain only strings in either set, but not both.

        Args:
            other: An iterable of strings to perform symmetric difference with.
        """
        super().symmetric_difference_update(self._intern_iterable(other))
