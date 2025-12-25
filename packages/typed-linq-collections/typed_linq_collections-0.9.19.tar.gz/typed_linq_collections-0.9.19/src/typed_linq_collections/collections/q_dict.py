from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Self, cast, override

# noinspection PyPep8Naming,PyProtectedMember
from typed_linq_collections._private_implementation_details.q_zero_overhead_collection_contructors import ZeroImportOverheadConstructors as C
from typed_linq_collections.collections.q_key_value_pair import KeyValuePair
from typed_linq_collections.q_iterable import QIterable

if TYPE_CHECKING:
    from collections.abc import Iterable

class QDict[TKey, TItem](dict[TKey, TItem], QIterable[TKey]):
    """A mutable dictionary that extends Python's built-in dict with LINQ-style query operations on keys.

    QDict provides all the functionality of Python's standard dictionary while also implementing
    the QIterable interface for LINQ-style operations on the dictionary keys. It maintains all
    the performance characteristics and mutability of the built-in dict, making it a drop-in
    replacement that adds powerful querying capabilities.

    Note that the QIterable operations work on the dictionary keys, not the values. Use the
    qitems() method to perform LINQ operations on key-value pairs.

    Inheritance:
    - Inherits from dict[TKey, TItem] for all standard dictionary operations and seamless interoperability with the built-in dict
    - Implements QIterable[TKey] for LINQ-style query operations on keys
    """
    __slots__: tuple[str, ...] = ()

    def __init__(self, mappings: Mapping[TKey, TItem] | Iterable[tuple[TKey, TItem]] = ()) -> None:
        """Initializes a new QDict with key-value pairs from the given mapping or iterable.

        Args:
            mappings: Either a mapping (dict-like object) or an iterable of (key, value) tuples
                                 to initialize the dictionary with. Defaults to an empty sequence.

        Examples:
            >>> QDict({"a": 1, "b": 2})
            {'a': 1, 'b': 2}
            >>> QDict([('a', 1), ('b', 2)])
            {'a': 1, 'b': 2}
        """
        super().__init__(cast(Mapping[TKey, TItem], mappings))

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
            >>> d = QDict({"a": 1, "b": 2, "c": 3})
            >>> d.qvalues().where(lambda x: x > 1).to_list()
            [2, 3]
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
            >>> d = QDict({"a": 1, "b": 2})
            >>> d.remove("a")
            >>> d
            {'b': 2}
        """
        del self[key]

    def discard(self, key: TKey) -> None:
        """Remove a key from the dictionary without raising an error.

        If the key is not found, this method does nothing (silent success).
        This provides consistency with set.discard() behavior.

        Args:
            key: The key to remove from the dictionary.

        Examples:
            >>> d = QDict({"a": 1, "b": 2})
            >>> d.discard("a")
            >>> d
            {'b': 2}
            >>> d.discard("z")  # No error
        """
        self.pop(key, None)

    def get_or_add(self, key: TKey, factory: Callable[[TKey], TItem]) -> TItem:
        """Get the value for a key, or add and return a factory-created value if the key doesn't exist.

        The factory function receives the key as an argument, allowing constructors and other
        single-argument functions to be passed directly without lambda wrapping.

        Args:
            key: The key to look up or add.
            factory: A callable that takes the key and returns the value to add if the key doesn't exist.
                    Only called if the key is not present.

        Returns:
            The existing value if the key exists, or the factory result after adding it.

        Examples:
            >>> d = QDict({"a": 1})
            >>> d.get_or_add("a", lambda k: 99)  # Key exists, factory not called
            1
            >>> d.get_or_add("b", lambda k: len(k) * 10)  # Key doesn't exist, factory called
            10
            >>> d
            {'a': 1, 'b': 10}
            >>> # Pass constructors directly without lambda
            >>> class Item:
            ...     def __init__(self, name: str):
            ...         self.name = name
            >>> items = QDict[str, Item]()
            >>> item = items.get_or_add("key1", Item)  # No lambda needed!
            >>> item.name
            'key1'
        """
        if key in self:
            return self[key]
        value = factory(key)
        self[key] = value
        return value

    def get_value_or_default(self, key: TKey, factory: Callable[[TKey], TItem]) -> TItem:
        """Get the value for a key, or return a factory-created value without modifying the dictionary.

        Unlike get_or_add, this method does not add the key to the dictionary.
        The factory function receives the key as an argument.

        Args:
            key: The key to look up.
            factory: A callable that takes the key and returns the value if the key doesn't exist.
                    Only called if the key is not present.

        Returns:
            The existing value if the key exists, or the factory result.

        Examples:
            >>> d = QDict({"a": 1})
            >>> d.get_value_or_default("a", lambda k: 99)  # Key exists, factory not called
            1
            >>> d.get_value_or_default("b", lambda k: 2)   # Key doesn't exist, factory called
            2
            >>> d  # Dictionary unchanged
            {'a': 1}
        """
        if key in self:
            return self[key]
        return factory(key)

    def remove_where(self, predicate: Callable[[KeyValuePair[TKey, TItem]], bool]) -> int:
        """Remove all key-value pairs matching the predicate.

        Args:
            predicate: A function that takes a KeyValuePair and returns True for pairs to remove.

        Returns:
            The number of pairs removed.

        Examples:
            >>> d = QDict({"a": 1, "b": 2, "c": 3})
            >>> d.remove_where(lambda kv: kv.value > 1)
            2
            >>> d
            {'a': 1}
        """
        keys_to_remove = [kv.key for kv in self.qitems() if predicate(kv)]
        for key in keys_to_remove:
            del self[key]
        return len(keys_to_remove)

    @override
    def _optimized_length(self) -> int: return len(self)

    @override
    def __or__(self, other: dict[TKey, TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return type(self)(super().__or__(other).items())

    @override
    def __ror__(self, other: dict[TKey, TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        return type(self)(cast(dict[TKey, TItem], dict.__or__(other, self)).items())  # pyright: ignore[reportUnknownMemberType]

    @override
    def __ior__(self, other: dict[TKey, TItem]) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        super().__ior__(other)
        return self

    @override
    def copy(self) -> Self:
        return type(self)(super().copy().items())
