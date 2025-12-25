from __future__ import annotations

from collections.abc import Callable

type Action = Callable[[], None]
type Action1[TIn] = Callable[[TIn], None]
type Action2[TIn, TIn2] = Callable[[TIn, TIn2], None]
type Action3[TIn, TIn2, TIn3] = Callable[[TIn, TIn2, TIn3], None]
type Action4[TIn, TIn2, TIn3, TIn4] = Callable[[TIn, TIn2, TIn3, TIn4], None]

type Func[TOut] = Callable[[], TOut]
type Func1[TIn, TOut] = Callable[[TIn], TOut]
type Func2[TIn, TIn2, TOut] = Callable[[TIn, TIn2], TOut]
type Func3[TIn, TIn2, TIn3, TOut] = Callable[[TIn, TIn2, TIn3], TOut]
type Func4[TIn, TIn2, TIn3, TIn4, TOut] = Callable[[TIn, TIn2, TIn3, TIn4], TOut]


type Predicate[TIn] = Callable[[TIn], bool]
type Selector[TIn, TOut] = Callable[[TIn], TOut]
