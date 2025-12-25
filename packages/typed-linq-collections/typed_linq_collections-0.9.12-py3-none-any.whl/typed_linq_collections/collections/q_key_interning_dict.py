from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload, override

from typed_linq_collections.collections.q_dict import QDict

if TYPE_CHECKING:
    from collections.abc import Iterable

_T = TypeVar("_T")


class QKeyInterningDict[TValue](QDict[str, TValue]):
    """A specialized QDict that automatically interns all string keys before storing them.

    Inheritance:
    - Inherits from QDict[str, TValue], providing all dictionary operations with automatic key interning
    - Maintains all LINQ-style query operations from QIterable on the keys

    Examples:
        >>> qdict = QKeyInterningDict([("name", "Alice"), ("city", "NYC")])
        >>> # All stored keys are interned
        >>> "name" in qdict  # Uses interned comparison
        True
        >>> qdict["country"] = "USA"
        >>> # "country" is automatically interned before storage
    """
    __slots__: tuple[str, ...] = ()

    @override
    def __init__(self, elements: Iterable[tuple[str, TValue]] = ()) -> None:
        """Initializes a new QKeyInterningDict with interned keys from the given iterable.

        All string keys in the input iterable are automatically interned before being added
        to the dictionary.

        Args:
            elements: An iterable of (key, value) tuples to initialize the dictionary with.
                     All keys will be interned automatically.
                     Defaults to an empty sequence.
        """
        super().__init__(self._intern_keys(elements))

    @staticmethod
    def _intern_keys(elements: Iterable[tuple[str, TValue]]) -> Iterable[tuple[str, TValue]]:
        """Interns all keys in the given iterable of key-value pairs.

        Args:
            elements: An iterable of (key, value) tuples.

        Returns:
            An iterable of (interned_key, value) tuples.
        """
        import sys
        return ((sys.intern(key), value) for key, value in elements)

    @override
    def __setitem__(self, key: str, value: TValue) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Sets the value for an interned version of the key.

        Args:
            key: The string key to intern and use.
            value: The value to associate with the key.
        """
        import sys
        super().__setitem__(sys.intern(key), value)

    @override
    def setdefault(self, key: str, default: TValue | None = None) -> TValue | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Gets the value for an interned key, setting it to default if not present.

        Args:
            key: The string key to intern and look up/set.
            default: The value to set if the key is not found.

        Returns:
            The value associated with the key.
        """
        import sys
        return super().setdefault(sys.intern(key), default)  # pyright: ignore[reportArgumentType]

    @override
    def update(self, *args: Iterable[tuple[str, TValue]] | dict[str, TValue], **kwargs: TValue) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Updates the dictionary with interned keys from the given mappings.

        Args:
            *args: Iterables of (key, value) tuples or dictionaries to update from.
            **kwargs: Keyword arguments to add to the dictionary.
        """
        import sys

        # Handle positional arguments
        for arg in args:
            if isinstance(arg, dict):
                for key, value in arg.items():  # pyright: ignore[reportUnknownVariableType]
                    super().__setitem__(sys.intern(key), value)  # pyright: ignore[reportArgumentType, reportUnknownArgumentType]
            else:
                for key, value in arg:  # pyright: ignore[reportUnknownVariableType]
                    super().__setitem__(sys.intern(key), value)

        # Handle keyword arguments
        for key, value in kwargs.items():
            super().__setitem__(sys.intern(key), value)

    @classmethod
    @overload
    def fromkeys(cls, keys: Iterable[str]) -> QKeyInterningDict[None]: ...

    @classmethod
    @overload
    def fromkeys(cls, keys: Iterable[str], value: _T) -> QKeyInterningDict[_T]: ...

    @classmethod
    @override
    def fromkeys(cls, keys: Iterable[str], value: _T | None = None) -> QKeyInterningDict[_T] | QKeyInterningDict[None]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Creates a new dictionary with interned keys from an iterable and values set to value.

        Args:
            keys: An iterable of string keys to intern.
            value: The value to set for all keys.

        Returns:
            A new QKeyInterningDict with the given keys.
        """
        import sys
        interned_keys = (sys.intern(key) for key in keys)
        result = QKeyInterningDict[_T | None]()  # pyright: ignore[reportInvalidTypeArguments]
        for key in interned_keys:
            result[key] = value  # pyright: ignore[reportArgumentType]
        return result  # pyright: ignore[reportReturnType]
