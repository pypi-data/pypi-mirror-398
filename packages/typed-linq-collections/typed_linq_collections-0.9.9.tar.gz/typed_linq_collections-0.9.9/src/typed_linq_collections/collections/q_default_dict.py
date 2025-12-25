from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, Self, cast, override

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
