from __future__ import annotations

from collections.abc import Callable, Iterable
from decimal import Decimal
from fractions import Fraction

from typed_linq_collections.q_iterable import QIterable, query


def swallow_exception_decorator(inner: ScalarOrActionOperator) -> ScalarOrActionOperator:
    def wrapper(argument: QIterable[int]) -> object:
        # noinspection PyBroadException
        try:
            return inner(argument)
        except:  # noqa: E722
            pass

    return wrapper


type CollectionReturningOperator = Callable[[QIterable[int]], Iterable[object]]
type ScalarOrActionOperator = Callable[[QIterable[int]], object]
iterator_generating_operators: list[tuple[str, CollectionReturningOperator]] = [
    ("qappend", lambda x1: x1.qappend(999)),
    ("as_decimals", lambda x1: x1.select(Decimal).as_decimals()),
    ("as_floats", lambda x1: x1.select(float).as_floats()),
    ("as_fractions", lambda x1: x1.select(Fraction).as_fractions()),
    ("as_ints", lambda x1: x1.as_ints()),
    ("as_iterable", lambda x1: x1.as_iterable()),
    ("cast", lambda x1: x1.cast.checked.to(int)),
    ("chunk", lambda x1: x1.chunk(2)),
    ("distinct", lambda x1: x1.distinct()),
    ("distinct_by", lambda x1: x1.distinct_by(lambda x2: x2)),
    ("group_by", lambda x1: x1.group_by(lambda x2: x2)),
    ("group_join", lambda x1: x1.group_join([1, 2, 3, 4], lambda key1: key1, lambda key2: key2, lambda val1, val2: (val1, list(val2)))),
    ("join", lambda x1: x1.join([1, 2, 3, 4], lambda key1: key1, lambda key2: key2, lambda val1, val2: val1 + val2)),
    ("of_type", lambda x1: x1.of_type(int)),
    ("order_by", lambda x1: x1.order_by(lambda x2: x2)),
    ("order_by_descending", lambda x1: x1.order_by_descending(lambda x2: x2)),
    ("prepend", lambda x1: x1.prepend(999)),
    ("qexcept", lambda x1: x1.qexcept([1, 2, 3, 4])),
    ("qexcept_by", lambda x1: x1.qexcept_by([1, 2, 3, 4], lambda x2: x2)),
    ("where_key_not_in", lambda x1: x1.where_key_not_in([1, 2, 3, 4], lambda x2: x2)),
    ("qindex", lambda x1: x1.qindex()),
    ("qunion", lambda x1: x1.qunion([1, 2, 3, 4])),
    ("qunion_by", lambda x1: x1.qunion_by([1, 2, 3, 4], lambda x2: x2)),
    ("qintersect", lambda x1: x1.qintersect([1, 2, 3, 4])),
    ("qintersect_by", lambda x1: x1.qintersect_by([1, 2, 3, 4], lambda x2: x2)),
    ("where_key_in", lambda x1: x1.where_key_in([1, 2, 3, 4], lambda x2: x2)),
    ("reversed", lambda x1: x1.reversed()),
    ("select", lambda x1: x1.select(lambda x2: x2)),
    ("select_index", lambda x1: x1.select_index(lambda index, element: (index, element))),
    ("select_many", lambda x1: x1.select_many(lambda _: [1, 2, 3])),
    ("skip", lambda x1: x1.skip(1)),
    ("skip_while", lambda x1: x1.skip_while(lambda val: val < 2)),
    ("skip_last", lambda x1: x1.skip_last(1)),
    ("take", lambda x1: x1.take(10)),
    ("take_last", lambda x1: x1.take_last(1)),
    ("take_while", lambda x1: x1.take_while(lambda _: True)),
    ("where", lambda x1: x1.where(lambda _: True)),
    ("where_not_none", lambda x1: x1.where_not_none()),
    ("zip", lambda x1: x1.zip([1, 2, 3, 4], lambda x2, x3: (x2, x3))),
    ("zip2", lambda x1: x1.zip2([1, 2, 3], [1, 2, 3], lambda x2, x3, x4: (x2, x3, x4))),
    ("zip3", lambda x1: x1.zip3([1, 2, 3], [1, 2, 3], [1, 2, 3], lambda x2, x3, x4, x5: (x2, x3, x4, x5))),
    ("zip_tuple", lambda x1: x1.zip_tuple([1, 2, 3])),
    ("zip_tuple2", lambda x1: x1.zip_tuple2([1, 2, 3], [1, 2, 3])),
    ("zip_tuple3", lambda x1: x1.zip_tuple3([1, 2, 3], [1, 2, 3], [1, 2, 3])),
]

scalar_or_action_operators: list[tuple[str, ScalarOrActionOperator]] = [
    ("all", lambda x1: x1.all(lambda _: True)),
    ("aggregate", lambda x1: x1.aggregate(lambda acc, item: acc + item)),
    ("aggregate_seed", lambda x1: x1.aggregate(lambda acc, item: acc + item, 0)),
    ("aggregate_seed_result", lambda x1: x1.aggregate(lambda acc, item: acc + item, 0, lambda acc: acc)),
    ("any", lambda x1: x1.any()),
    ("contains", lambda x1: x1.contains(1)),
    ("element_at", lambda x1: x1.element_at(0)),
    ("element_at_or_none", lambda x1: x1.element_at_or_none(0)),
    ("first", lambda x1: x1.first()),
    ("first_or_none", lambda x1: x1.first_or_none()),
    ("last", lambda x1: x1.last()),
    ("last_or_none", lambda x1: x1.last_or_none()),
    ("max_by", lambda x1: x1.max_by(lambda v: v)),
    ("min_by", lambda x1: x1.min_by(lambda v: v)),
    ("for_each", lambda x1: x1.for_each(null_op)),
    ("none", lambda x1: x1.none()),
    ("pipe", lambda x1: x1.pipe(lambda iterator: iterator.for_each(null_op))),
    ("qcount", lambda x1: x1.qcount()),
    ("qcount_by", lambda x1: x1.qcount_by(lambda x: x)),
    ("single", swallow_exception_decorator(lambda x1: x1.single())),
    ("single_or_none", swallow_exception_decorator(lambda x1: x1.single_or_none())),
    ("to_built_in_list", lambda x1: x1.to_built_in_list()),
    ("to_dict", lambda x1: x1.to_dict(lambda x2: x2, lambda x2: x2)),
    ("to_frozenset", lambda x1: x1.to_frozenset()),
    ("to_list", lambda x1: x1.to_list()),
    ("to_sequence", lambda x1: x1.to_sequence()),
    ("to_set", lambda x1: x1.to_set()),
    ("to_tuple", lambda x1: x1.to_tuple()),
    ("sequence_equal", lambda x1: x1.sequence_equal([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])),
]

def assert_has_10_elements[T](iterable: QIterable[T]) -> QIterable[T]:
    assert sum(1 for _ in iterable) == 10
    return iterable

def assert_is_empty[T](iterable: QIterable[T]) -> QIterable[T]:
    assert sum(1 for _ in iterable) == 0
    return iterable

def generate_10_ints() -> QIterable[int]:
    return query(i for i in collection_10_ints())

def collection_10_ints() -> QIterable[int]:
    return query([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

def test_query_can_only_enumerate_once_given_a_generator() -> None:
    generator_query = query(i for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    assert_has_10_elements(generator_query)
    assert_is_empty(generator_query)

def test_query_can_iterate_again_given_a_collection() -> None:
    generator_query = query([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    assert_has_10_elements(generator_query)
    assert_has_10_elements(generator_query)

def null_op(_: object) -> None: pass


exceptional_operators: set[str] = {"concat"}

all_tested_operator_names: set[str] = query(iterator_generating_operators).select(lambda x: x[0]).to_set() | query(scalar_or_action_operators).select(lambda x: x[0]).to_set()

def get_all_operator_names_defined_in__q_iterable_mixin() -> set[str]:
    return (query(QIterable.__dict__.items())
            .where(lambda x: not isinstance(x[1], (staticmethod, classmethod)))
            .select(lambda x: x[0])  # member names
            .where(lambda x: not x.startswith("_"))
            .to_set())

def test_all_operators_are_tested() -> None:
    missing_tests = get_all_operator_names_defined_in__q_iterable_mixin() - all_tested_operator_names - exceptional_operators
    if missing_tests: raise AssertionError(f"Missing tests for operators: {missing_tests}")

def test_no_iterator_generating_operator_consumes_elements_on_call_without_iteration() -> None:
    for operator_name, operator in iterator_generating_operators:
        original_iterator = generate_10_ints()
        operator(original_iterator)
        assert original_iterator.qcount() == 10, f"Operator {operator_name} consumed elements on first call"

def test_all_iterator_generating_operators_when_called_on_generator_backed_iterable_consume_elements_but_only_once_iterated_and_the_results_they_return_change_on_second_iteration() -> None:
    for operator_name, operator in iterator_generating_operators:
        original_iterator = generate_10_ints()
        result = operator(original_iterator)
        length_of_iterable_returned_by_operator = sum(1 for _ in result)
        length_of_iterator_returned_by_operator_on_second_iteration = sum(1 for _ in result)

        assert length_of_iterable_returned_by_operator != 0, f"Operator {operator_name} did not return any elements"
        assert length_of_iterator_returned_by_operator_on_second_iteration != length_of_iterable_returned_by_operator, f"Operator {operator_name} returned the same results on second call"
        assert original_iterator.qcount() != 10, f"Operator {operator_name} did not consume any elements from source generator"

def test_no_iterator_generating_operators_when_called_on_collection_backed_iterator_consume_elements_and_they_return_the_same_result_repeatedly() -> None:
    for operator_name, operator in iterator_generating_operators:
        original_iterator = collection_10_ints()
        result_iterator = operator(original_iterator)
        length_of_iterable_returned_by_operator = sum(1 for _ in result_iterator)
        length_of_iterator_returned_by_operator_on_second_iteration = sum(1 for _ in result_iterator)
        assert length_of_iterable_returned_by_operator != 0, f"Operator {operator_name} did not return any elements"
        assert length_of_iterator_returned_by_operator_on_second_iteration == length_of_iterable_returned_by_operator, f"Operator {operator_name} consumed elements"
        assert original_iterator.qcount() == 10, f"Operator {operator_name} mutated source collection"

def test_all_scalar_or_action_operators_when_called_on_generator_backed_iterable_consume_elements() -> None:
    for operator_name, operator in scalar_or_action_operators:
        original_iterator = generate_10_ints()
        operator(original_iterator)
        assert original_iterator.qcount() != 10, f"Operator {operator_name} consumed no elements"

def test_no_scalar_or_action_operators_when_called_on_collection_backed_iterator_consume_elements() -> None:
    for operator_name, operator in scalar_or_action_operators:
        original_iterator = collection_10_ints()
        operator(original_iterator)
        assert original_iterator.qcount() == 10, f"Operator {operator_name} mutated source collection"
