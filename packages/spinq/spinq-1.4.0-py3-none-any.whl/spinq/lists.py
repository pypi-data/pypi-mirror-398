from typing import Callable, TypeVar, Optional
from collections.abc import Iterable

T = TypeVar('T')
T2 = TypeVar('T2')

def first_(sequence: list[T], predicate: Callable[[T], bool] = lambda x: True) -> T:
    try:
        return next((x for x in sequence if predicate(x)))
    except StopIteration:
        raise ValueError("No elements match the predicate.")

def first_or_none_(sequence: list[T], predicate: Callable[[T], bool] = lambda x: True) -> Optional[T]:
    return next((x for x in sequence if predicate(x)), None)

def first_or_none_with_index_(sequence: list[T], predicate: Callable[[T], bool] = lambda x: True) -> Optional[tuple[int, T]]:
    return next(((index, x) for index, x in enumerate(sequence) if predicate(x)), None)

def last_(sequence: list[T], predicate: Callable[[T], bool] = lambda x: True) -> T:
    try:
        return next((x for x in reversed(sequence) if predicate(x)))
    except StopIteration:
        raise ValueError("No elements match the predicate.")

def last_or_none_(sequence: list[T], predicate: Callable[[T], bool] = lambda x: True) -> Optional[T]:
    return next((x for x in reversed(sequence) if predicate(x)), None)

def single_(sequence: list[T], predicate: Callable[[T], bool]) -> T:
    filtered = [x for x in sequence if predicate(x)]
    if len(filtered) == 1:
        return filtered[0]
    elif len(filtered) == 0:
        raise ValueError("No elements match the predicate.")
    else:
        raise ValueError("More than one element matches the predicate.")

def single_or_none_(sequence: list[T], predicate: Callable[[T], bool]) -> Optional[T]:
    filtered = [x for x in sequence if predicate(x)]
    if len(filtered) == 1:
        return filtered[0]
    elif len(filtered) == 0:
        return None
    else:
        raise ValueError("More than one element matches the predicate.")

def filter_(sequence: list[T], predicate: Callable[[T], bool]) -> list[T]:
    return [x for x in sequence if predicate(x)]

def except_(sequence: list[T], exclusions: list[T]) -> list[T]:
    return [x for x in sequence if x not in exclusions]

def without_(sequence: list[T], predicate: Callable[[T], bool]) -> list[T]:
    return [x for x in sequence if not predicate(x)]

def union_(sequence1: list[T], sequence2: list[T]) -> list[T]:
    return list(set(sequence1) | set(sequence2))

def select_(sequence: list[T], selector: Callable[[T], T2]) -> list[T2]:
    return [selector(x) for x in sequence]

def select_many_(sequence: list[T], selector: Callable[[T], list[T2]]) -> list[T2]:
    seq_dict = {}
    for i in range(len(sequence)):
        transformed = selector(sequence[i])
        if isinstance(transformed, Iterable) and not isinstance(transformed, str):
            for j in range(len(transformed)):
                seq_dict[f"{i}{j}"] = transformed[j]
        else:
            seq_dict[f"{i}"] = transformed
    results = list(seq_dict.values())
    return results

def where_(sequence: list[T], predicate: Callable[[T], bool]) -> list[T]:
    return [x for x in sequence if predicate(x)]

def where_with_index_(sequence: list[T], predicate: Callable[[T], bool]) -> dict[int, T]:
    return {index: item for index, item in enumerate(sequence) if predicate(item)}

def distinct_(sequence: list[T]) -> list[T]:
    return list(set(sequence))

def order_by_(sequence: list[T], key_selector: Callable[[T], T]) -> list[T]:
    return sorted(sequence, key=key_selector)

def order_by_descending_(sequence: list[T], key_selector: Callable[[T], T]) -> list[T]:
    return sorted(sequence, key=key_selector, reverse=True)

def any_(sequence: list[T], predicate: Callable[[T], bool]) -> bool:
    return any(predicate(x) for x in sequence)

def all_(sequence: list[T], predicate: Callable[[T], bool]) -> bool:
    return all(predicate(x) for x in sequence)

def none_(sequence: list[T], predicate: Callable[[T], bool]) -> bool:
    return all(not predicate(x) for x in sequence)