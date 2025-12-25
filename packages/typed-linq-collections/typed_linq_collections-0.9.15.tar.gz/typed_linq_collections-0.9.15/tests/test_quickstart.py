from __future__ import annotations

from typed_linq_collections.collections.q_list import QList
from typed_linq_collections.q_iterable import query

fruits = ("apple", "apricot", "mango", "melon", "peach", "pineapple")

def test_querying_built_in_collections() -> None:
    fruits_by_first_character = (query(fruits)
                                 .group_by(lambda fruit: fruit[0])
                                 .where(lambda group: group.key in {"a", "p"})
                                 .to_list())

    assert fruits_by_first_character == [["apple", "apricot"], ["peach", "pineapple"]]

def test_querying_with_queryable_collections() -> None:
    fruits_by_first_character = (QList(fruits)
                                 .group_by(lambda fruit: fruit[0])
                                 .where(lambda group: group.key in {"a", "p"})
                                 .to_list())

    assert fruits_by_first_character == [["apple", "apricot"], ["peach", "pineapple"]]

def test_numeric_operations() -> None:
    total_lenght_of_fruits = (query(fruits)
                              .select(len)
                              .as_ints() # get's you a QIntIterable with numeric operations support. typed so that it is only available on a QIterable[int]
                              .sum())

    assert total_lenght_of_fruits == 36