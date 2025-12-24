from typing import Any, Callable, Dict, Iterable, List, Tuple


def sorted_items(d: Dict[str, object]) -> Iterable[Tuple[str, object]]:
    return sorted(d.items(), key=lambda kv: kv[0])


def stable_sort(items: Iterable[object], key: Callable[[object], Any]) -> List[object]:
    """
    Stable sort for items using the given key function.

    Note: Python's built-in sorted() is already stable. This wrapper exists
    for API consistency and potential future enhancements.
    """
    return sorted(items, key=key)
