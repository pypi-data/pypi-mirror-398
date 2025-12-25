from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Self, cast, overload, override

# noinspection PyPep8Naming,PyProtectedMember
from typed_linq_collections._private_implementation_details.q_zero_overhead_collection_contructors import ZeroImportOverheadConstructors as C
from typed_linq_collections.collections.q_key_value_pair import KeyValuePair
from typed_linq_collections.q_iterable import QIterable

if TYPE_CHECKING:
    # noinspection PyProtectedMember
    from typed_linq_collections._private_implementation_details.type_aliases import Func


class QDefaultDict[TKey, TItem](defaultdict[TKey, TItem], QIterable[TKey]):
    """A dictionary with automatic default value creation that extends defaultdict with LINQ operations.

    QDefaultDict provides all the functionality of Python's collections.defaultdict while also
    implementing the QIterable interface for LINQ-style operations on the dictionary keys.
    When accessing a missing key, it automatically creates and returns a default value using
    the provided factory function.

    Note that the QIterable operations work on the dictionary keys, not the values. Use the
    qitems() method to perform LINQ operations on key-value pairs.

    Inheritance:
    - Inherits from defaultdict[TKey, TItem] for automatic default value creation and seamless interoperability with the built-in defaultdict
    - Implements QIterable[TKey] for LINQ-style query operations on keys
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, factory: Func[TItem]) -> None:
        """Initializes a new QDefaultDict with the specified default value factory.

        Args:
            factory: A callable that returns default values for missing keys.
                    Common factories include list, int, set, or custom lambda functions.
        """
        super().__init__(factory)

    def qitems(self) -> QIterable[KeyValuePair[TKey, TItem]]:
        """Returns a QIterable of KeyValuePair objects for LINQ operations on key-value pairs.

        This method provides access to both keys and values through KeyValuePair objects,
        enabling LINQ-style operations on the complete dictionary data. Each KeyValuePair
        has 'key' and 'value' properties for convenient access.

        Returns:
            A QIterable of KeyValuePair objects, each containing a key and its associated value.
        """
        return C.lazy_iterable(lambda: self.items()).select(KeyValuePair)

    def qvalues(self) -> QIterable[TItem]:
        """Returns a QIterable of values for LINQ operations.

        This method provides access to dictionary values through a QIterable,
        enabling LINQ-style query operations on the values.

        Returns:
            A QIterable of the dictionary values.

        Examples:
            >>> d = QDefaultDict(int)
            >>> d["a"] = 1
            >>> d["b"] = 2
            >>> d.qvalues().where(lambda x: x > 1).to_list()
            [2]
        """
        return C.lazy_iterable(lambda: self.values())

    def remove(self, key: TKey) -> None:
        """Remove a key from the dictionary.

        Unlike pop(), this method doesn't return the removed value, making it
        consistent with list.remove() and set.remove().

        Args:
            key: The key to remove from the dictionary.

        Raises:
            KeyError: If the key is not found in the dictionary.

        Examples:
            >>> d = QDefaultDict(int)
            >>> d["a"] = 1
            >>> d.remove("a")
            >>> "a" in d
            False
        """
        del self[key]

    def discard(self, key: TKey) -> None:
        """Remove a key from the dictionary without raising an error.

        If the key is not found, this method does nothing (silent success).
        This provides consistency with set.discard() behavior.

        Args:
            key: The key to remove from the dictionary.

        Examples:
            >>> d = QDefaultDict(int)
            >>> d["a"] = 1
            >>> d.discard("a")
            >>> "a" in d
            False
            >>> d.discard("z")  # No error
        """
        self.pop(key, None)

    @overload
    def get_or_add(self, key: TKey, default: TItem) -> TItem: ...
    @overload
    def get_or_add(self, key: TKey, default: Callable[[], TItem]) -> TItem: ...

    def get_or_add(self, key: TKey, default: TItem | Callable[[], TItem]) -> TItem:
        """Get the value for a key, or add and return a default if the key doesn't exist.

        This is a more intuitively named alias for dict.setdefault() with added support
        for factory functions for lazy evaluation.

        Args:
            key: The key to look up or add.
            default: Either a value to set and return if the key doesn't exist,
                    or a callable that returns the value when invoked.

        Returns:
            The existing value if the key exists, or the default/factory result after adding it.

        Examples:
            >>> d = QDefaultDict(int)
            >>> d["a"] = 1
            >>> d.get_or_add("a", 99)  # Key exists
            1
            >>> d.get_or_add("b", 2)   # Key doesn't exist, adds it
            2
            >>> d.get_or_add("c", lambda: 3)  # Factory function
            3
            >>> "b" in d and "c" in d
            True
        """
        # For callable factories, we need to check if key exists first to avoid calling unnecessarily
        if callable(default):
            if key in self:
                return self[key]
            value = cast(Callable[[], TItem], default)()
            self[key] = value
            return value
        # For direct values, use optimized setdefault (single lookup)
        return self.setdefault(key, cast(TItem, default))

    @overload
    def get_value_or_default(self, key: TKey, default: TItem) -> TItem: ...
    @overload
    def get_value_or_default(self, key: TKey, default: Callable[[], TItem]) -> TItem: ...

    def get_value_or_default(self, key: TKey, default: TItem | Callable[[], TItem]) -> TItem:
        """Get the value for a key, or return a default without modifying the dictionary.

        Unlike get_or_add, this method does not add the key to the dictionary.
        Note: For QDefaultDict, this won't trigger the default_factory.

        Args:
            key: The key to look up.
            default: Either a value to return if the key doesn't exist,
                    or a callable that returns the value when invoked.

        Returns:
            The existing value if the key exists, or the default/factory result.

        Examples:
            >>> d = QDefaultDict(int)
            >>> d["a"] = 1
            >>> d.get_value_or_default("a", 99)  # Key exists
            1
            >>> d.get_value_or_default("b", 2)   # Key doesn't exist
            2
            >>> "b" in d  # Dictionary unchanged
            False
            >>> d.get_value_or_default("c", lambda: 3)  # Factory function
            3
        """
        # For callable factories, check if key exists first to avoid calling unnecessarily
        if callable(default):
            if key in self:
                return self[key]
            return cast(Callable[[], TItem], default)()
        # For direct values, use optimized get (single lookup)
        return self.get(key, cast(TItem, default))

    def remove_where(self, predicate: Callable[[KeyValuePair[TKey, TItem]], bool]) -> int:
        """Remove all key-value pairs matching the predicate.

        Args:
            predicate: A function that takes a KeyValuePair and returns True for pairs to remove.

        Returns:
            The number of pairs removed.

        Examples:
            >>> d = QDefaultDict(int)
            >>> d["a"] = 1
            >>> d["b"] = 2
            >>> d.remove_where(lambda kv: kv.value > 1)
            1
            >>> "b" in d
            False
        """
        keys_to_remove = [kv.key for kv in self.qitems() if predicate(kv)]
        for key in keys_to_remove:
            del self[key]
        return len(keys_to_remove)

    @override
    def _optimized_length(self) -> int: return len(self)

    @override
    def __or__(self, other: dict[TKey, TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        result = type(self)(cast(Callable[[], TItem], self.default_factory))
        result.update(self)
        result.update(other)
        return result

    @override
    def __ror__(self, other: dict[TKey, TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        result = type(self)(cast(Callable[[], TItem], self.default_factory))
        result.update(other)
        result.update(self)
        return result

    @override
    def __ior__(self, other: dict[TKey, TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        super().__ior__(other)
        return self

    @override
    def copy(self) -> Self:
        result = type(self)(cast(Callable[[], TItem], self.default_factory))
        result.update(self)
        return result
