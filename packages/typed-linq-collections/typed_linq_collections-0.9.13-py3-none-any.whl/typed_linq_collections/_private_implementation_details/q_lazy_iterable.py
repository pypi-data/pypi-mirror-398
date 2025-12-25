from __future__ import annotations

from typing import TYPE_CHECKING, override

from typed_linq_collections.q_iterable import QIterable

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from typed_linq_collections._private_implementation_details.type_aliases import Func


class QLazyIterableImplementation[TItem](QIterable[TItem]):
    """A lazy implementation of QIterable that defers execution until iteration.

    This implementation stores a factory function that produces the iterable when
    needed, enabling true lazy evaluation of LINQ operations. The factory is called
    each time the iterable is enumerated, allowing for fresh iterations of dynamic sources.
    """
    __slots__: tuple[str, ...] = ("_factory",)

    def __init__(self, iterable_factory: Func[Iterable[TItem]]) -> None:
        """Initialize with a factory function that produces the source iterable.

        Args:
            iterable_factory: A function that returns an iterable when called.
        """
        self._factory: Func[Iterable[TItem]] = iterable_factory

    @override
    def __iter__(self) -> Iterator[TItem]: yield from self._factory()

class QCachingIterableImplementation[TItem](QIterable[TItem]):
    """A caching implementation of QIterable that wraps an existing iterable.

    This implementation provides a QIterable interface around any Python iterable,
    enabling LINQ-style operations on existing collections. The wrapped iterable
    is used directly without caching individual elements.
    """
    __slots__: tuple[str, ...] = ("_iterable",)

    def __init__(self, iterable: Iterable[TItem]) -> None:
        """Initialize with an existing iterable to wrap.

        Args:
            iterable: The iterable to wrap with QIterable functionality.
        """
        self._iterable: Iterable[TItem] = iterable

    @override
    def __iter__(self) -> Iterator[TItem]:
        yield from iter(self._iterable)
