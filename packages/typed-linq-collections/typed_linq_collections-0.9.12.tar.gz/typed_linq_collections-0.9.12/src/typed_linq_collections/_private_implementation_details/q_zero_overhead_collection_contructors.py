from __future__ import annotations

from typing import TYPE_CHECKING, Never

if TYPE_CHECKING:
    import builtins
    from collections.abc import Iterable, Mapping
    from decimal import Decimal
    from fractions import Fraction

    from typed_linq_collections._private_implementation_details.sort_instruction import SortInstruction
    from typed_linq_collections._private_implementation_details.type_aliases import Func
    from typed_linq_collections.collections.numeric.q_decimal_types import QDecimalIterable
    from typed_linq_collections.collections.numeric.q_float_types import QFloatIterable
    from typed_linq_collections.collections.numeric.q_fraction_types import QFractionIterable
    from typed_linq_collections.collections.numeric.q_int_types import QIntIterable
    from typed_linq_collections.collections.q_default_dict import QDefaultDict
    from typed_linq_collections.collections.q_dict import QDict
    from typed_linq_collections.collections.q_frozen_set import QFrozenSet
    from typed_linq_collections.collections.q_list import QList
    from typed_linq_collections.collections.q_sequence import QSequence
    from typed_linq_collections.collections.q_set import QSet
    from typed_linq_collections.q_cast import QCast
    from typed_linq_collections.q_grouping import QGrouping
    from typed_linq_collections.q_iterable import QIterable
    from typed_linq_collections.q_ordered_iterable import QOrderedIterable


class ZeroImportOverheadConstructors:
    """This class contains static methods that are used to construct the collection classes with zero import overhead and without the need to complicate methods thoughouht the library by having to import these classes within functions in order to avoid circular imports."""
    @staticmethod
    def list[TItem](iterable: Iterable[TItem] = ()) -> QList[TItem]:
        from typed_linq_collections.collections.q_list import QList

        ZeroImportOverheadConstructors.list = QList  # replace this method with a direct call so that future calls have zero import overhead
        return ZeroImportOverheadConstructors.list(iterable)  # use the new version to prove from the very first call that it works

    @staticmethod
    def sequence[TItem](iterable: Iterable[TItem]) -> QSequence[TItem]:
        from typed_linq_collections.collections.q_immutable_sequence import QImmutableSequence

        ZeroImportOverheadConstructors.sequence = QImmutableSequence  # replace this method with a direct call so that future calls have zero import overhead
        return ZeroImportOverheadConstructors.sequence(iterable)  # use the new version to prove from the very first call that it works

    @staticmethod
    def set[TItem](iterable: Iterable[TItem]) -> QSet[TItem]:
        from typed_linq_collections.collections.q_set import QSet

        ZeroImportOverheadConstructors.set = QSet  # replace this method with a direct call so that future calls have zero import overhead
        return ZeroImportOverheadConstructors.set(iterable)  # use the new version to prove from the very first call that it works

    @staticmethod
    def frozen_set[TItem](iterable: Iterable[TItem]) -> QFrozenSet[TItem]:
        from typed_linq_collections.collections.q_frozen_set import QFrozenSet

        ZeroImportOverheadConstructors.frozen_set = QFrozenSet  # replace this method with a direct call so that future calls have zero import overhead
        return ZeroImportOverheadConstructors.frozen_set(iterable)  # use the new version to prove from the very first call that it works

    @staticmethod
    def cast[TItem](qiterable: QIterable[TItem]) -> QCast[TItem]:
        from typed_linq_collections.q_cast import QCast
        ZeroImportOverheadConstructors.cast = QCast  # replace this method with a direct call so that future calls have zero import overhead  # pyright: ignore [reportAttributeAccessIssue]
        return ZeroImportOverheadConstructors.cast(qiterable)  # use the new version to prove from the very first call that it works

    @staticmethod
    def empty_iterable[TItem]() -> QIterable[Never]:  # pyright: ignore [reportInvalidTypeVarUse]
        empty_iterable = ZeroImportOverheadConstructors.lazy_iterable(lambda: ())
        def get_empty() -> QIterable[TItem]: return empty_iterable  # pyright: ignore [reportReturnType]
        ZeroImportOverheadConstructors.empty_iterable = get_empty  # replace this method itself with  # pyright: ignore [reportAttributeAccessIssue]
        return ZeroImportOverheadConstructors.empty_iterable()

    @staticmethod
    def lazy_iterable[TItem](iterable_factory: Func[Iterable[TItem]]) -> QIterable[TItem]:
        from typed_linq_collections._private_implementation_details.q_lazy_iterable import QLazyIterableImplementation
        ZeroImportOverheadConstructors.lazy_iterable = QLazyIterableImplementation  # replace this method with a direct call so that future calls have zero import overhead  # pyright: ignore [reportAttributeAccessIssue]
        return ZeroImportOverheadConstructors.lazy_iterable(iterable_factory)  # use the new version to prove from the very first call that it works

    @staticmethod
    def caching_iterable[TItem](iterable: Iterable[TItem]) -> QIterable[TItem]:
        from typed_linq_collections._private_implementation_details.q_lazy_iterable import QCachingIterableImplementation
        ZeroImportOverheadConstructors.caching_iterable = QCachingIterableImplementation  # replace this method with a direct call so that future calls have zero import overhead  # pyright: ignore [reportAttributeAccessIssue]
        return ZeroImportOverheadConstructors.caching_iterable(iterable)  # use the new version to prove from the very first call that it works

    @staticmethod
    def ordered_iterable[TItem](factory: Func[QIterable[TItem]], sorting_instructions: builtins.list[SortInstruction[TItem]]) -> QOrderedIterable[TItem]:
        from typed_linq_collections.q_ordered_iterable import QOrderedIterable
        ZeroImportOverheadConstructors.ordered_iterable = QOrderedIterable  # replace this method with a direct call so that future calls have zero import overhead  # pyright: ignore [reportAttributeAccessIssue]
        return ZeroImportOverheadConstructors.ordered_iterable(factory, sorting_instructions)  # use the new version to prove from the very first call that it works

    @staticmethod
    def grouping[TKey, TItem](values: tuple[TKey, QList[TItem]]) -> QGrouping[TKey, TItem]:
        from typed_linq_collections.q_grouping import QGrouping
        ZeroImportOverheadConstructors.grouping = QGrouping  # replace this method with a direct call so that future calls have zero import overhead  # pyright: ignore [reportAttributeAccessIssue]
        return ZeroImportOverheadConstructors.grouping(values)  # use the new version to prove from the very first call that it works

    @staticmethod
    def default_dict[TKey, TElement](factory: Func[TElement]) -> QDefaultDict[TKey, TElement]:  # pyright: ignore [reportInvalidTypeVarUse]
        from typed_linq_collections.collections.q_default_dict import QDefaultDict
        ZeroImportOverheadConstructors.default_dict = QDefaultDict  # replace this method with a direct call so that future calls have zero import overhead  # pyright: ignore [reportAttributeAccessIssue]
        return ZeroImportOverheadConstructors.default_dict(factory)

    @staticmethod
    def dict[TKey, TValue](mappings: Mapping[TKey, TValue] | Iterable[tuple[TKey, TValue]] = ()) -> QDict[TKey, TValue]:
        from typed_linq_collections.collections.q_dict import QDict
        ZeroImportOverheadConstructors.dict = QDict  # replace this method with a direct call so that future calls have zero import overhead
        return ZeroImportOverheadConstructors.dict(mappings)  # use the new version to prove from the very first call that it works

    @staticmethod
    def int_iterable(factory: Func[Iterable[int]]) -> QIntIterable:  # pyright: ignore [reportInvalidTypeVarUse]
        from typed_linq_collections.collections.numeric.q_int_types import QIntIterableImplementation
        ZeroImportOverheadConstructors.int_iterable = QIntIterableImplementation  # replace this method with a direct call so that future calls have zero import overhead  # pyright: ignore [reportAttributeAccessIssue]
        return ZeroImportOverheadConstructors.int_iterable(factory)  # use the new version to prove from the very first call that it works

    @staticmethod
    def float_iterable(factory: Func[Iterable[float]]) -> QFloatIterable:  # pyright: ignore [reportInvalidTypeVarUse]
        from typed_linq_collections.collections.numeric.q_float_types import QFloatIterableImplementation
        ZeroImportOverheadConstructors.float_iterable = QFloatIterableImplementation  # replace this method with a direct call so that future calls have zero import overhead  # pyright: ignore [reportAttributeAccessIssue]
        return ZeroImportOverheadConstructors.float_iterable(factory)  # use the new version to prove from the very first call that it works

    @staticmethod
    def fraction_iterable(factory: Func[Iterable[Fraction]]) -> QFractionIterable:  # pyright: ignore [reportInvalidTypeVarUse]
        from typed_linq_collections.collections.numeric.q_fraction_types import QFractionIterableImplementation
        ZeroImportOverheadConstructors.fraction_iterable = QFractionIterableImplementation  # replace this method with a direct call so that future calls have zero import overhead  # pyright: ignore [reportAttributeAccessIssue]
        return ZeroImportOverheadConstructors.fraction_iterable(factory)  # use the new version to prove from the very first call that it works

    @staticmethod
    def decimal_iterable(factory: Func[Iterable[Decimal]]) -> QDecimalIterable:  # pyright: ignore [reportInvalidTypeVarUse]
        from typed_linq_collections.collections.numeric.q_decimal_types import QDecimalIterableImplementation
        ZeroImportOverheadConstructors.decimal_iterable = QDecimalIterableImplementation  # replace this method with a direct call so that future calls have zero import overhead  # pyright: ignore [reportAttributeAccessIssue]
        return ZeroImportOverheadConstructors.decimal_iterable(factory)  # use the new version to prove from the very first call that it works
