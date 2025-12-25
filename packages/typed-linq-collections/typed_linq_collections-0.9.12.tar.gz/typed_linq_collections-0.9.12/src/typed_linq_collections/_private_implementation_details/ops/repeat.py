# src/queryablecollections/_private_implementation_details/ops/repeat.py
from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

from typed_linq_collections.q_errors import ArgumentError

if TYPE_CHECKING:
    from collections.abc import Iterable


def repeat[T](element: T, count: int) -> Iterable[T]:
    if count < 0:
        raise ArgumentError("Count must be greater than or equal to 0")
    return itertools.repeat(element, count)