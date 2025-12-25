from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Predicate


def take_while[TItem](self: Iterable[TItem], predicate: Predicate[TItem]) -> Iterable[TItem]:
    return itertools.takewhile(predicate, self)
