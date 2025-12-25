from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import Never, override

# noinspection PyProtectedMember
from typed_linq_collections._private_implementation_details.q_lazy_iterable import QLazyIterableImplementation
from typed_linq_collections.q_iterable import QIterable


class QSequence[TItem](Sequence[TItem], QIterable[TItem], ABC):
    """Abstract base class for sequence-like collections with LINQ-style query operations.

    QSequence provides the foundation for ordered, indexed collections that support both
    the Python Sequence protocol and LINQ-style operations. It serves as the base class
    for concrete implementations like QList and QImmutableSequence, providing common
    functionality for indexed access and sequence-specific operations.

    Inheritance:
    - Inherits from Sequence[TItem] for standard sequence operations (indexing, length, etc.)
    - Implements QIterable[TItem] for LINQ-style query operations
    - Abstract base class - must be subclassed for concrete implementations
    """
    __slots__: tuple[str, ...] = ()
    @override
    def _optimized_length(self) -> int: return len(self)

    @override
    def reversed(self) -> QIterable[TItem]: return QLazyIterableImplementation[TItem](lambda: reversed(self))

    @staticmethod
    @override
    def empty() -> QSequence[Never]:
        from typed_linq_collections.collections.q_immutable_sequence import QImmutableSequence
        empty = QImmutableSequence[Never]()
        def get_empty() -> QSequence[Never]: return empty  # pyright: ignore [reportReturnType]
        QSequence.empty = get_empty
        return QSequence[TItem].empty()
