from __future__ import annotations

from typing import TypeVar

TValue = TypeVar("TValue", covariant=True)
TKey = TypeVar("TKey")


class KeyValuePair(tuple[TKey, TValue]):
    """A strongly-typed wrapper around tuple for representing key-value pairs in LINQ operations.

    KeyValuePair provides a convenient and type-safe way to work with key-value pairs
    in LINQ-style operations, particularly when querying dictionary items. It extends
    tuple to provide named property access while maintaining all tuple functionality
    including immutability and hashability.

    This class is primarily used by QDict and QDefaultDict qitems() methods to provide
    a more readable API for working with dictionary data in LINQ operations.

    Inheritance:
    - Inherits from tuple[TKey, TValue] for all standard tuple operations
    - Immutable and hashable like tuples
    - Can be used anywhere a tuple is expected

    Key Features:
    - **Named Access**: Properties 'key' and 'value' for readable code
    - **Type Safety**: Generic types ensure compile-time type checking
    - **Immutable**: Cannot be modified after creation
    - **Hashable**: Can be used in sets or as dictionary keys
    - **Tuple Compatible**: Works with all tuple operations and unpacking
    """
    __slots__: tuple[str, ...] = ()

    def __new__(cls, value: tuple[TKey, TValue]) -> KeyValuePair[TKey, TValue]:
        """Creates a new KeyValuePair from a key-value tuple.

        Args:
            value: A tuple containing exactly two elements: (key, value).

        Returns:
            A new KeyValuePair instance wrapping the provided tuple.
        """
        return super().__new__(cls, value)

    @property
    def key(self) -> TKey:
        """Gets the key component of this key-value pair.

        Returns:
            The key (first element) of the tuple.
        """
        return self[0]

    @property
    def value(self) -> TValue:
        """Gets the value component of this key-value pair.

        Returns:
            The value (second element) of the tuple.
        """
        return self[1]
