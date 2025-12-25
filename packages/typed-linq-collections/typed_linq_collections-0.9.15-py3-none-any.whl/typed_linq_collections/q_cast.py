from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING, cast

# noinspection PyPep8Naming,PyProtectedMember
from typed_linq_collections._private_implementation_details.q_zero_overhead_collection_contructors import ZeroImportOverheadConstructors as C
from typed_linq_collections.q_iterable import QIterable

if TYPE_CHECKING:
    from typed_linq_collections.collections.numeric.q_decimal_types import QDecimalIterable
    from typed_linq_collections.collections.numeric.q_float_types import QFloatIterable
    from typed_linq_collections.collections.numeric.q_fraction_types import QFractionIterable
    from typed_linq_collections.collections.numeric.q_int_types import QIntIterable

class CheckedCast[TValue]:
    """A callable that performs type-checked casting of values.

    Provides runtime type checking to ensure values match the expected type before casting.
    Raises TypeError if the value is not of the expected type.

    Args:
        cast_to_type: The type to cast values to.
    """
    __slots__: tuple[str, ...] = ("_type",)

    def __init__(self, cast_to_type: type[TValue]) -> None:
        """Initialize a new CheckedCast instance.

        Args:
            cast_to_type: The type that values will be checked against and cast to.
        """
        self._type: type[TValue] = cast_to_type

    def __call__(self, value: object) -> TValue:
        """Perform type-checked casting of a value.

        Args:
            value: The value to cast.

        Returns:
            The value cast to TValue type.

        Raises:
            TypeError: If the value is not of the expected type.
        """
        if not isinstance(value, self._type): raise TypeError(f"Expected {self._type.__name__}, got {type(value).__name__}")
        return value


_checked_cast_int = CheckedCast(int)
_checked_cast_float = CheckedCast(float)
_checked_cast_fraction = CheckedCast(Fraction)
_checked_cast_decimal = CheckedCast(Decimal)

class QCast[TItem]:
    """Provides type casting operations for QIterable elements.

    Offers both unchecked and checked casting to numeric types (int, float, Decimal, Fraction)
    and generic type casting. Unchecked casting assumes the values are already of the target
    type, while checked casting performs runtime type validation.
    """
    __slots__: tuple[str, ...] = ("_iterable",)

    def __init__(self, iterable: QIterable[TItem]) -> None:
        """Initialize a new QCast instance.

        Args:
            iterable: The QIterable to perform casting operations on.
        """
        self._iterable: QIterable[TItem] = iterable

    @property
    def checked(self) -> QCheckedCast[TItem]:
        """Get a QCheckedCast instance for runtime type-checked casting.

        Returns:
            A QCheckedCast that performs runtime type validation before casting.
        """
        return QCheckedCast(self._iterable)

    def int(self) -> QIntIterable:
        """Cast elements to int type (unchecked).

        Assumes all elements are already integers. Use checked.int() for runtime validation.

        Returns:
            A QIntIterable with integer-specific operations.
        """
        return C.int_iterable(lambda: (cast(Iterable[int], self._iterable)))

    def float(self) -> QFloatIterable:
        """Cast elements to float type (unchecked).

        Assumes all elements are already floats. Use checked.float() for runtime validation.

        Returns:
            A QFloatIterable with float-specific operations.
        """
        return C.float_iterable(lambda: (cast(Iterable[float], self._iterable)))

    def fraction(self) -> QFractionIterable:
        """Cast elements to Fraction type (unchecked).

        Assumes all elements are already Fractions. Use checked.fraction() for runtime validation.

        Returns:
            A QFractionIterable with fraction-specific operations.
        """
        return C.fraction_iterable(lambda: (cast(Iterable[Fraction], self._iterable)))

    def decimal(self) -> QDecimalIterable:
        """Cast elements to Decimal type (unchecked).

        Assumes all elements are already Decimals. Use checked.decimal() for runtime validation.

        Returns:
            A QDecimalIterable with decimal-specific operations.
        """
        return C.decimal_iterable(lambda: cast(Iterable[Decimal], self._iterable))

    def to[TNew](self, _type: type[TNew]) -> QIterable[TNew]:  # pyright: ignore
        """Cast elements to a generic type (unchecked).

        Assumes all elements are already of the target type. Use checked.to() for runtime validation.

        Args:
            _type: The target type to cast to.

        Returns:
            A QIterable of the target type.
        """
        return cast(QIterable[TNew], self._iterable)

class QCheckedCast[TItem]:
    """Provides runtime type-checked casting operations for QIterable elements.

    Performs runtime validation to ensure all elements are of the expected type before casting.
    Raises TypeError if any element fails type validation.
    """
    __slots__: tuple[str, ...] = ("_iterable",)

    def __init__(self, iterable: QIterable[TItem]) -> None:
        """Initialize a new QCheckedCast instance.

        Args:
            iterable: The QIterable to perform checked casting operations on.
        """
        self._iterable: QIterable[TItem] = iterable

    def int(self) -> QIntIterable:
        """Cast elements to int type with runtime type checking.

        Validates that all elements are integers before casting.

        Returns:
            A QIntIterable with integer-specific operations.

        Raises:
            TypeError: If any element is not an integer.
        """
        return C.int_iterable(lambda: self._iterable.select(_checked_cast_int))

    def float(self) -> QFloatIterable:
        """Cast elements to float type with runtime type checking.

        Validates that all elements are floats before casting.

        Returns:
            A QFloatIterable with float-specific operations.

        Raises:
            TypeError: If any element is not a float.
        """
        return C.float_iterable(lambda: self._iterable.select(_checked_cast_float))

    def fraction(self) -> QFractionIterable:
        """Cast elements to Fraction type with runtime type checking.

        Validates that all elements are Fractions before casting.

        Returns:
            A QFractionIterable with fraction-specific operations.

        Raises:
            TypeError: If any element is not a Fraction.
        """
        return C.fraction_iterable(lambda: self._iterable.select(_checked_cast_fraction))

    def decimal(self) -> QDecimalIterable:
        """Cast elements to Decimal type with runtime type checking.

        Validates that all elements are Decimals before casting.

        Returns:
            A QDecimalIterable with decimal-specific operations.

        Raises:
            TypeError: If any element is not a Decimal.
        """
        return C.decimal_iterable(lambda: self._iterable.select(_checked_cast_decimal))

    def to[TNew](self, _type: type[TNew]) -> QIterable[TNew]:  # pyright: ignore
        """Cast elements to a generic type with runtime type checking.

        Validates that all elements are of the target type before casting.

        Args:
            _type: The target type to cast to.

        Returns:
            A QIterable of the target type.

        Raises:
            TypeError: If any element is not of the target type.
        """
        return self._iterable.select(CheckedCast(_type))
