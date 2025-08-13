from __future__ import annotations

from typing import Callable, Iterable, List, Tuple, TypeVar


def sanitize_label(value: str | None) -> str:
    value = (value or "").strip()
    return value if value else "unknown"


T = TypeVar("T")


def topn_with_other(rows: List[T], key: Callable[[T], float], n: int) -> Tuple[List[T], float]:
    rows = [r for r in rows if r is not None]
    rows.sort(key=key, reverse=True)
    head, tail = rows[:n], rows[n:]
    other = sum(key(r) for r in tail)
    return head, other


