from __future__ import annotations

from typing import TYPE_CHECKING

# noinspection PyPep8Naming
from typed_linq_collections._private_implementation_details.q_zero_overhead_collection_contructors import ZeroImportOverheadConstructors as C

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Selector
    from typed_linq_collections.collections.q_default_dict import QDefaultDict
    from typed_linq_collections.q_grouping import QGrouping
    from typed_linq_collections.q_iterable import QIterable

def _group_by[TElement, TKey](self: Iterable[TElement], key_selector: Selector[TElement, TKey]) -> Iterable[QGrouping[TKey, TElement]]:
    from typed_linq_collections.collections.q_list import QList
    groups: QDefaultDict[TKey, QList[TElement]] = C.default_dict(QList[TElement])

    for item in self:
        groups[key_selector(item)].append(item)

    return groups.qitems().select(C.grouping)

def _group_by_with_element_selector[TSourceElement, TKey, TGroupElement](self: Iterable[TSourceElement],
                                                                         key_selector: Selector[TSourceElement, TKey],
                                                                         element_selector: Selector[TSourceElement, TGroupElement]) -> Iterable[QGrouping[TKey, TGroupElement]]:
    from typed_linq_collections.collections.q_list import QList
    groups: QDefaultDict[TKey, QList[TGroupElement]] = C.default_dict(QList[TGroupElement])

    for item in self:
        groups[key_selector(item)].append(element_selector(item))

    return groups.qitems().select(C.grouping)


def group_by_q[TItem, TKey, TElement](self: QIterable[TItem], key: Selector[TItem, TKey], element: Selector[TItem, TElement] | None = None) -> QIterable[QGrouping[TKey, TItem]] | QIterable[QGrouping[TKey, TElement]]:
    return (C.lazy_iterable(lambda: _group_by(self, key))
            if element is None
            else C.lazy_iterable(lambda: _group_by_with_element_selector(self, key, element)))
