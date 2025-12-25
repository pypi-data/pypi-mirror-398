from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable, Mapping, Sequence

TKey = TypeVar("TKey")
TVal = TypeVar("TVal")


def ensure_unique_keys(items: Iterable[tuple[TKey, TVal]]) -> dict[TKey, TVal]:
    """Replacement for dict comprehension that checks the keys' uniqueness"""
    result: dict[TKey, TVal] = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"Key conflict: {key=!r}, first_value={result[key]!r}, second_value={value!r}")
        result[key] = value
    return result


def pop_keys(data: dict[TKey, TVal], keys: Sequence[TKey]) -> dict[TKey, TVal]:
    result = data.copy()
    for key in keys:
        result.pop(key, None)
    return result


def clear_none(data: Mapping[TKey, TVal | None]) -> dict[TKey, TVal]:
    return {key: val for key, val in data.items() if val is not None}


def groupby(items: Iterable[tuple[TKey, TVal]]) -> dict[TKey, list[TVal]]:
    """
    Simple "group by" over iterable items.

    >>> groupby([(1, 1), (2, 2), (1, 3)])
    {1: [1, 3], 2: [2]}
    """
    res: dict[TKey, list[TVal]] = {}
    for key, val in items:
        try:
            group_list = res[key]
        except KeyError:
            res[key] = [val]
        else:
            group_list.append(val)
    return res


def _is_common_prefix(item_a: Sequence[Any], item_b: Sequence[Any]) -> bool:
    """
    Check whether one (either) element is a prefix of another.

    >>> _is_common_prefix("abc", "ab")
    True
    >>> _is_common_prefix("ab", "abc")
    True
    >>> _is_common_prefix("abc", "abd")
    False
    >>> _is_common_prefix("abc", "ax")
    False
    """
    min_len = min(len(item_a), len(item_b))
    return item_a[:min_len] == item_b[:min_len]


TGroupbyRecLeaf = list[TVal]
TGroupbyRecNode = dict[TKey, "TGroupbyRecNode | TGroupbyRecLeaf"]
TGroupbyRecRet = TGroupbyRecNode


def groupby_rec(items: Iterable[tuple[Sequence[TKey], TVal]]) -> TGroupbyRecRet:
    """
    Recursive "group by" over iterable items.

    >>> groupby_rec([([1, 1], 11), ([1, 2], 12), ([2, 1], 21)])
    {1: {1: [11], 2: [12]}, 2: {1: [21]}}
    >>> groupby_rec([([1, 1], 11), ([1, 2], 12), ([1], 2)])
    Traceback (most recent call last):
      ...
    ValueError: Key path (1,) conflicts with previously seen paths [(1, 1), (1, 2)]
    >>> groupby_rec([([1], 2), ([1, 1], 11)])
    Traceback (most recent call last):
      ...
    ValueError: Key path (1, 1) conflicts with previously seen paths [(1,)]
    """
    res: TGroupbyRecRet = {}
    seen: set[tuple[TKey, ...]] = set()
    for key_path_raw, val in items:
        key_path = tuple(key_path_raw)

        if not key_path:
            raise ValueError("Empty key path")
        conflicts = [seen_path for seen_path in seen if _is_common_prefix(seen_path, key_path)]
        if conflicts:
            raise ValueError(f"Key path {key_path!r} conflicts with previously seen paths {conflicts!r}")
        seen.add(key_path)

        here: TGroupbyRecNode = res
        for key in key_path[:-1]:
            if key in here:
                next_here = here[key]
                assert isinstance(next_here, dict)
                here = next_here
            else:
                new_here: TGroupbyRecNode = {}
                here[key] = new_here
                here = new_here

        leaf_key = key_path[-1]
        group_list: list[TVal]
        if leaf_key in here:
            here_leaf = here[leaf_key]
            assert isinstance(here_leaf, list)
            group_list = here_leaf
        else:
            group_list = []
            here[leaf_key] = group_list

        group_list.append(val)

    return res


def chunks(items: Sequence[TVal], size: int) -> Generator[Sequence[TVal], None, None]:
    """Yield successive chunks from `lst` with no padding"""
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def iterchunks(items: Iterable[TVal], size: int) -> Generator[tuple[TVal, ...], None, None]:
    """
    Same as 'chunks' but works on any iterable.

    Converts the chunks to tuples for simplicity.

    http://stackoverflow.com/a/8991553
    """
    assert size > 0
    it = iter(items)
    while True:
        chunk = tuple(itertools.islice(it, size))
        if not chunk:
            return
        yield chunk


def split_list(items: Iterable[TVal], condition: Callable[[TVal], bool]) -> tuple[list[TVal], list[TVal]]:
    """Split list items into `(matching, non_matching)` by `cond(item)` callable"""
    matching = []
    non_matching = []
    for item in items:
        if condition(item):
            matching.append(item)
        else:
            non_matching.append(item)
    return matching, non_matching
