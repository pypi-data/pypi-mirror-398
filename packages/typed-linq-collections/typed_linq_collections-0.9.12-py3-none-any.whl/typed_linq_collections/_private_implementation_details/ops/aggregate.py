from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from typed_linq_collections.q_errors import EmptyIterableError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from typed_linq_collections._private_implementation_details.type_aliases import Selector

def aggregate_simple[TItem](self: Iterable[TItem], func: Callable[[TItem, TItem], TItem]) -> TItem:
    iterator = iter(self)
    try:
        accumulated_value = next(iterator)
    except StopIteration:
        raise EmptyIterableError() from None

    for item in iterator:
        accumulated_value = func(accumulated_value, item)

    return accumulated_value

def aggregate_seed[TItem, TAccumulate](
        self: Iterable[TItem],
        seed: TAccumulate,
        func: Callable[[TAccumulate, TItem], TAccumulate]
) -> TAccumulate:
    accumulated_value = seed
    for item in self:
        accumulated_value = func(accumulated_value, item)
    return accumulated_value

def aggregate[T, TAccumulate, TResult](self: Iterable[T], func: Callable[[T, T], T] | Callable[[TAccumulate, T], TAccumulate],
                                       seed: TAccumulate | None = None,
                                       result_selector: Selector[TAccumulate, TResult] | None = None) -> T | TAccumulate | TResult:
    if seed is None:
        return aggregate_simple(self, cast(Callable[[T, T], T], func))

    aggregated_value = aggregate_seed(self, seed, cast(Callable[[TAccumulate, T], TAccumulate], func))
    if result_selector is None:
        return aggregated_value

    return result_selector(aggregated_value)
