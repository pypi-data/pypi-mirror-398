# Copyright (c) 2025, UChicago Argonne, LLC
# BSD OPEN SOURCE LICENSE. Full license can be found in LICENSE.md
from itertools import islice
from typing import List, Optional, TypeVar
from collections.abc import Iterable

T = TypeVar("T")


def first_and_only(a_list: Iterable[T]) -> T:
    a_list = list(a_list)
    if len(a_list) == 0:
        raise RuntimeError("Expected a single thing, but there was nothing")
    if len(a_list) > 1:
        raise RuntimeError("Expected a single thing, but there were many")
    return a_list[0]


def zero_or_one(a_list: Iterable[T]) -> Optional[T]:
    a_list = list(a_list)
    if len(a_list) == 0:
        return None
    if len(a_list) > 1:
        raise RuntimeError(f"Expected no more than a single thing, but there were many ({a_list})")
    return a_list[0]


def flatten(list_of_lists: List[List]):
    return [e for list in list_of_lists for e in list]


def in_groups_of(iterable: Iterable[T], n: int) -> Iterable[tuple[T, ...]]:
    if n < 1:
        raise RuntimeError(f"Can't have negative or zero sized group [n={n}]")

    it = iter(iterable)
    while True:
        chunk = tuple(islice(it, n))
        if not chunk:
            return
        yield chunk
