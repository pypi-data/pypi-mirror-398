from __future__ import annotations

from typing import TYPE_CHECKING, SupportsIndex, override

from typed_linq_collections.collections.q_list import QList

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


class QInterningList(QList[str]):
    """A specialized QList that automatically interns all string values before storing them.

    String interning is a method of storing only one copy of each distinct string value.
    This can save memory when the same strings are used repeatedly, and can make string
    comparisons faster (since interned strings can be compared by identity rather than value).

    When initialized with a list (not just any iterable), this class will modify the source
    list in-place to replace its values with interned versions. This provides maximum memory
    savings by ensuring that even the source list uses interned strings.

    All strings added to this list are automatically interned using Python's sys.intern()
    function or a custom interning function. This applies to strings added via any method:
    initialization, append, insert, extend, etc.

    Inheritance:
    - Inherits from QList[str], providing all list operations with automatic string interning
    - Maintains all LINQ-style query operations from QIterable

    Examples:
        >>> qlist = QInterningList(["hello", "world"])
        >>> # All stored strings are interned
        >>> "hello" in qlist  # Uses interned comparison
        True
        >>> qlist.append("python")
        >>> # "python" is automatically interned before storage
        >>>
        >>> # In-place interning of source list
        >>> source = ["a", "b", "c"]
        >>> qlist = QInterningList(source)
        >>> # source list now contains interned strings
    """
    __slots__: tuple[str, ...] = ("_intern_func",)

    @override
    def __init__(self, iterable: Iterable[str] = (), *, intern_func: Callable[[str], str] | None = None) -> None:
        """Initializes a new QInterningList with interned strings from the given iterable.

        All strings in the input iterable are automatically interned before being added
        to the list. If the input is a list (not just any iterable), it will be modified
        in-place to replace all values with their interned versions for maximum memory savings.

        Args:
            iterable: An iterable of strings to initialize the list with.
                     All strings will be interned automatically.
                     If this is a list, it will be modified in-place.
                     Defaults to an empty sequence.
            intern_func: A custom function to use for interning strings. If None, uses the
                        default interning function (configurable via set_default_intern_func).
                        Defaults to None.
        """
        from typed_linq_collections.collections import string_interning
        self._intern_func: Callable[[str], str] = intern_func if intern_func is not None else string_interning.default_intern_func

        # If it's a list, intern the values in-place
        if isinstance(iterable, list):
            for i in range(len(iterable)):
                iterable[i] = self._intern_func(iterable[i])
            super().__init__(iterable)
        else:
            super().__init__(self._intern_func(s) for s in iterable)

    @override
    def append(self, item: str) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Adds an interned version of the string to the end of the list.

        Args:
            item: The string to intern and append to the list.
        """
        super().append(self._intern_func(item))

    @override
    def insert(self, index: SupportsIndex, item: str) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Inserts an interned version of the string at the specified index.

        Args:
            index: The index at which to insert the item.
            item: The string to intern and insert.
        """
        super().insert(index, self._intern_func(item))

    @override
    def extend(self, iterable: Iterable[str]) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Extends the list by appending interned versions of strings from the iterable.

        Args:
            iterable: An iterable of strings to intern and append to the list.
        """
        super().extend(self._intern_func(s) for s in iterable)

    @override
    def __setitem__(self, index: SupportsIndex | slice, value: str | Iterable[str]) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Sets the item at the given index to an interned version of the string.

        Args:
            index: The index or slice to set.
            value: The string or iterable of strings to intern and set.
        """
        if isinstance(index, slice):
            # For slices, intern all strings in the iterable (including when value is a string)
            super().__setitem__(index, [self._intern_func(s) for s in value])  # pyright: ignore[reportArgumentType]
        else:
            # For single index, value must be a string
            if not isinstance(value, str):
                raise TypeError("value must be a string")
            super().__setitem__(index, self._intern_func(value))

    @override
    def __iadd__(self, iterable: Iterable[str]) -> QInterningList:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Extends the list with interned versions of strings from the iterable.

        Args:
            iterable: An iterable of strings to intern and add to the list.

        Returns:
            The list itself (for chaining).
        """
        self.extend(iterable)
        return self

    @override
    def copy(self) -> QInterningList:
        """Creates a shallow copy of the list, preserving the intern function.

        Returns:
            A new QInterningList with the same elements and intern function.
        """
        result = QInterningList(intern_func=self._intern_func)
        result.extend(super().copy())
        return result

    @override
    def __add__(self, other: Iterable[str]) -> QInterningList:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Returns a new list with interned strings from this list and the other iterable.

        Args:
            other: An iterable of strings to concatenate.

        Returns:
            A new QInterningList containing all strings from both lists.
        """
        result = self.copy()
        result.extend(other)
        return result

    @override
    def __mul__(self, n: int) -> QInterningList:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Returns a new list with the contents repeated n times.

        Args:
            n: The number of times to repeat the list.

        Returns:
            A new QInterningList with the contents repeated.
        """
        result = QInterningList(intern_func=self._intern_func)
        result.extend(super().__mul__(n))
        return result

    @override
    def __rmul__(self, n: int) -> QInterningList:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Returns a new list with the contents repeated n times.

        Args:
            n: The number of times to repeat the list.

        Returns:
            A new QInterningList with the contents repeated.
        """
        return self.__mul__(n)
