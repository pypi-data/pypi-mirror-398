from __future__ import annotations

from typing import TYPE_CHECKING

# noinspection PyPep8Naming
from typed_linq_collections._private_implementation_details.q_zero_overhead_collection_contructors import ZeroImportOverheadConstructors as C

if TYPE_CHECKING:
    from decimal import Decimal
    from fractions import Fraction

    from typed_linq_collections.collections.numeric.q_decimal_types import QDecimalIterable
    from typed_linq_collections.collections.numeric.q_float_types import QFloatIterable
    from typed_linq_collections.collections.numeric.q_fraction_types import QFractionIterable
    from typed_linq_collections.collections.numeric.q_int_types import QIntIterable
    from typed_linq_collections.q_iterable import QIterable

def as_ints(self: QIterable[int]) -> QIntIterable: return C.int_iterable(lambda: self)
def as_floats(self: QIterable[float]) -> QFloatIterable: return C.float_iterable(lambda: self)
def as_decimals(self: QIterable[Decimal]) -> QDecimalIterable: return C.decimal_iterable(lambda: self)
def as_fractions(self: QIterable[Fraction]) -> QFractionIterable: return C.fraction_iterable(lambda: self)
