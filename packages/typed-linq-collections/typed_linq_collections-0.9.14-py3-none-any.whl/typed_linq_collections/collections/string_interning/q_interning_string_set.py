from __future__ import annotations

from typing import TYPE_CHECKING, Self, override

from typed_linq_collections.collections.q_set import QSet

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


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
    __slots__: tuple[str, ...] = ("_intern_func",)

    @override
    def __init__(self, iterable: Iterable[str] = (), *, intern_func: Callable[[str], str] | None = None) -> None:
        """Initializes a new QInterningStringSet with interned strings from the given iterable.

        All strings in the input iterable are automatically interned before being added
        to the set. Duplicates are removed as per standard set behavior.

        Args:
            iterable: An iterable of strings to initialize the set with.
                     All strings will be interned automatically.
                     Defaults to an empty sequence.
            intern_func: A custom function to use for interning strings. If None, uses the
                        default interning function (configurable via set_default_intern_func).
                        Defaults to None.
        """
        from typed_linq_collections.collections import string_interning
        self._intern_func: Callable[[str], str] = intern_func if intern_func is not None else string_interning.default_intern_func
        super().__init__(self._intern_iterable(iterable))

    def _intern_iterable(self, iterable: Iterable[str]) -> Iterable[str]:
        """Interns all strings in the given iterable.

        Args:
            iterable: An iterable of strings to intern.

        Returns:
            An iterable of interned strings.
        """
        return (self._intern_func(s) for s in iterable)

    @override
    def copy(self) -> Self:
        """Creates a shallow copy of the set, preserving the intern function.

        Returns:
            A new QInterningStringSet with the same elements and intern function.
        """
        result = type(self)(intern_func=self._intern_func)
        result.update(super().copy())
        return result

    @override
    def add(self, element: str) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Adds an interned version of the string to the set.

        Args:
            element: The string to intern and add to the set.
        """
        super().add(self._intern_func(element))

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
    def intersection(self, *others: Iterable[str]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Returns a new set with strings common to this set and all others.

        Args:
            *others: One or more iterables of strings to intersect with.

        Returns:
            A new QInterningStringSet containing the intersection of all sets.
        """
        result = self.copy()
        result.intersection_update(*others)
        return result

    @override
    def difference(self, *others: Iterable[str]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Returns a new set with strings in this set but not in others.

        Args:
            *others: One or more iterables of strings to exclude.

        Returns:
            A new QInterningStringSet containing the difference.
        """
        result = self.copy()
        result.difference_update(*others)
        return result

    @override
    def symmetric_difference(self, other: Iterable[str]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Returns a new set with strings in either set but not both.

        Args:
            other: An iterable of strings to perform symmetric difference with.

        Returns:
            A new QInterningStringSet containing the symmetric difference.
        """
        result = self.copy()
        result.symmetric_difference_update(other)
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
