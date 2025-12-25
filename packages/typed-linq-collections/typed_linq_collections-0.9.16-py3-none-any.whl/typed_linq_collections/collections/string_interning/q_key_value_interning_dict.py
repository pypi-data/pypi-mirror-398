from __future__ import annotations

from typing import TYPE_CHECKING, Self, TypeVar, overload, override

from typed_linq_collections.collections.string_interning.q_key_interning_dict import QKeyInterningDict

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

_T = TypeVar("_T")


class QKeyValueInterningDict(QKeyInterningDict[str]):
    """A specialized QKeyInterningDict that automatically interns both string keys and string values.

    This class extends QKeyInterningDict to also intern all string values before storing them,
    providing maximum memory efficiency and comparison performance for dictionaries where both
    keys and values are strings that may be repeated.

    Inheritance:
    - Inherits from QKeyInterningDict[str], providing all dictionary operations with automatic
      key and value interning
    - Maintains all LINQ-style query operations from QIterable

    Examples:
        >>> qdict = QKeyValueInterningDict([("name", "Alice"), ("city", "NYC")])
        >>> # All stored keys and values are interned
        >>> qdict["country"] = "USA"
        >>> # Both "country" and "USA" are automatically interned before storage
    """
    __slots__: tuple[str, ...] = ()

    @override
    def __init__(self, elements: Iterable[tuple[str, str]] = (), *, intern_func: Callable[[str], str] | None = None) -> None:
        """Initializes a new QKeyValueInterningDict with interned keys and values.

        All string keys and values in the input iterable are automatically interned before
        being added to the dictionary.

        Args:
            elements: An iterable of (key, value) tuples to initialize the dictionary with.
                     All keys and values will be interned automatically.
                     Defaults to an empty sequence.
            intern_func: A custom function to use for interning strings. If None, uses the
                        default interning function (configurable via set_default_intern_func).
                        Defaults to None.
        """
        # Call parent's __init__ which will call our overridden _intern_keys
        super().__init__(elements, intern_func=intern_func)

    @override
    def _intern_keys(self, elements: Iterable[tuple[str, str]]) -> Iterable[tuple[str, str]]:
        """Interns all keys and values in the given iterable of key-value pairs.

        Args:
            elements: An iterable of (key, value) tuples.

        Returns:
            An iterable of (interned_key, interned_value) tuples.
        """
        return ((self._intern_func(key), self._intern_func(value)) for key, value in elements)

    @override
    def __setitem__(self, key: str, value: str) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Sets the interned value for an interned version of the key.

        Args:
            key: The string key to intern and use.
            value: The string value to intern and store.
        """
        super().__setitem__(key, self._intern_func(value))

    @override
    def setdefault(self, key: str, default: str | None = None) -> str | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Gets the value for an interned key, setting it to interned default if not present.

        Args:
            key: The string key to intern and look up/set.
            default: The value to intern and set if the key is not found.

        Returns:
            The interned value associated with the key.
        """
        if default is not None:
            default = self._intern_func(default)
        return super().setdefault(key, default)

    @override
    def update(self, *args: Iterable[tuple[str, str]] | dict[str, str], **kwargs: str) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Updates the dictionary with interned keys and values from the given mappings.

        Args:
            *args: Iterables of (key, value) tuples or dictionaries to update from.
            **kwargs: Keyword arguments to add to the dictionary.
        """
        # Handle positional arguments
        for arg in args:
            if isinstance(arg, dict):
                for key, value in arg.items():  # pyright: ignore[reportUnknownVariableType]
                    self.__setitem__(key, value)  # pyright: ignore[reportArgumentType, reportUnknownArgumentType]
            else:
                for key, value in arg:  # pyright: ignore[reportUnknownVariableType]
                    self.__setitem__(key, value)  # pyright: ignore[reportUnknownArgumentType]

        # Handle keyword arguments
        for key, value in kwargs.items():
            self.__setitem__(key, value)

    @override
    def copy(self) -> Self:
        """Creates a shallow copy of the dictionary, preserving the intern function.

        Returns:
            A new QKeyValueInterningDict with the same items and intern function.
        """
        result = type(self)(intern_func=self._intern_func)
        result.update(dict(super().copy()))
        return result

    @classmethod
    @classmethod
    @overload
    def fromkeys(cls, keys: Iterable[str], value: None = None, *, intern_func: Callable[[str], str] | None = None) -> QKeyValueInterningDict: ...

    @classmethod
    @overload
    def fromkeys(cls, keys: Iterable[str], value: str, *, intern_func: Callable[[str], str] | None = None) -> QKeyValueInterningDict: ...

    @classmethod
    @override
    def fromkeys(cls, keys: Iterable[str], value: str | None = None, *, intern_func: Callable[[str], str] | None = None) -> QKeyValueInterningDict:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Creates a new dictionary with interned keys from an iterable and values set to interned value.

        Args:
            keys: An iterable of string keys to intern.
            value: The string value to intern and set for all keys.
            intern_func: A custom function to use for interning strings. If None, uses the
                        default interning function (configurable via set_default_intern_func).
                        Defaults to None.

        Returns:
            A new QKeyValueInterningDict with the given keys.
        """
        from typed_linq_collections.collections import string_interning
        _intern_func = intern_func if intern_func is not None else string_interning.default_intern_func
        interned_value = _intern_func(value) if value is not None else None
        interned_keys = (_intern_func(key) for key in keys)
        result = QKeyValueInterningDict(intern_func=intern_func)
        for key in interned_keys:
            result[key] = interned_value  # pyright: ignore[reportArgumentType]
        return result
