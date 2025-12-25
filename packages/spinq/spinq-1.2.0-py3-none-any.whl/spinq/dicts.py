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


def get_by_index_(dictionary: dict[K, V], index: int) -> tuple[K, V]:
    try:
        return next(islice(self.data.__dict__.items(), idx, idx + 1))
    except IndexError:
        raise ValueError("Index out of range.")