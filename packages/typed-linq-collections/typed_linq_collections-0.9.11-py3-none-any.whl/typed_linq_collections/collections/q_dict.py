from __future__ import annotations

from typing import TYPE_CHECKING, Self, cast, override

# noinspection PyPep8Naming,PyProtectedMember
from typed_linq_collections._private_implementation_details.q_zero_overhead_collection_contructors import ZeroImportOverheadConstructors as C
from typed_linq_collections.collections.q_key_value_pair import KeyValuePair
from typed_linq_collections.q_iterable import QIterable

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

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
            >>> QDict([("a", 1), ("b", 2)])
            {'a': 1, 'b': 2}
        """
        super().__init__(mappings)  # type: ignore

    def qitems(self) -> QIterable[KeyValuePair[TKey, TItem]]:
        """Returns a QIterable of KeyValuePair objects for LINQ operations on key-value pairs.

        This method provides access to both keys and values through KeyValuePair objects,
        enabling LINQ-style operations on the complete dictionary data. Each KeyValuePair
        has 'key' and 'value' properties for convenient access.

        Returns:
            A QIterable of KeyValuePair objects, each containing a key and its associated value.
        """
        return C.lazy_iterable(lambda: self.items()).select(KeyValuePair)

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

    def get_or_add(self, key: TKey, default: TItem) -> TItem:
        """Get the value for a key, or add and return a default if the key doesn't exist.

        This is a more intuitively named alias for dict.setdefault().

        Args:
            key: The key to look up or add.
            default: The value to set and return if the key doesn't exist.

        Returns:
            The existing value if the key exists, or the default value after adding it.

        Examples:
            >>> d = QDict({"a": 1})
            >>> d.get_or_add("a", 99)  # Key exists
            1
            >>> d.get_or_add("b", 2)   # Key doesn't exist, adds it
            2
            >>> d
            {'a': 1, 'b': 2}
        """
        return self.setdefault(key, default)

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
