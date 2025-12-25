from itertools import islice
from typing import Callable, TypeVar, Optional

K = TypeVar('K')
V = TypeVar('V')

def first_(dictionary: dict[K, V], predicate: Callable[[V], bool] = lambda x: True) -> tuple[K, V]:
    try:
        return next(((k, v) for k, v in dictionary.items() if predicate(v)))
    except StopIteration:
        raise ValueError("No elements match the predicate.")


def first_or_none_(dictionary: dict[K, V], predicate: Callable[[V], bool] = lambda x: True) -> Optional[tuple[K, V]]:
    return next(((k, v) for k, v in dictionary.items() if predicate(v)), None)


def get_key_by_index_(dictionary: dict[K, V], index: int) -> tuple[K, V]:
    try:
        return next(islice(dictionary, index, index + 1))
    except IndexError:
        raise ValueError("Index out of range.")


def get_key_value_by_index_(dictionary: dict[K, V], index: int) -> tuple[K, V]:
    try:
        return next(islice(dictionary.items(), index, index + 1))
    except IndexError:
        raise ValueError("Index out of range.")