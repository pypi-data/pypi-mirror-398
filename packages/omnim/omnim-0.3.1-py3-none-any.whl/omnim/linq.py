from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Optional,
    TypeVar,
)
from builtins import range as _range
from builtins import any as _any
from builtins import zip as _zip

T_SOURCE = TypeVar("T_SOURCE")
T_RESULT = TypeVar("T_RESULT")

T_ZIP_INNER = TypeVar("T_ZIP_INNER")
T_ZIP_OUTER = TypeVar("T_ZIP_OUTER")
T_ZIP_RESULT = TypeVar("T_ZIP_RESULT")

T_JOIN_INNER = TypeVar("T_JOIN_INNER")
T_JOIN_SELECTOR_RESULT = TypeVar("T_JOIN_SELECTOR_RESULT")
T_JOIN_RESULT = TypeVar("T_JOIN_RESULT")


class linq(Generic[T_SOURCE]):
    def __init__(self, src: Iterator[T_SOURCE] | Iterable[T_SOURCE]) -> None:
        self.__src = src

    def __iter__(self) -> Iterator[T_SOURCE]:
        return iter(self.__src)

    def count(self, pred: Optional[Callable[[T_SOURCE], bool]] = None) -> int:
        return count(self.__src, pred)

    def any(self, pred: Optional[Callable[[T_SOURCE], bool]] = None) -> bool:
        return any(self, pred)

    def where(self, pred: Callable[[T_SOURCE], bool]) -> "linq[T_SOURCE]":
        return linq(where(self, pred))

    def select(self, pred: Callable[[T_SOURCE], T_RESULT]) -> "linq[T_RESULT]":
        return linq(select(self, pred))

    def zip(
        self,
        other: Iterable[T_ZIP_OUTER],
        selector: Callable[[T_SOURCE, T_ZIP_OUTER], T_ZIP_RESULT],
    ) -> "linq[T_ZIP_RESULT]":
        return linq(zip(self.__src, other, selector))

    def join(
        self,
        inner: Iterable[T_JOIN_INNER],
        outer_selector: Callable[[T_SOURCE], T_JOIN_SELECTOR_RESULT],
        inner_selector: Callable[[T_JOIN_INNER], T_JOIN_SELECTOR_RESULT],
        result_selector: Callable[[T_SOURCE, T_JOIN_INNER], T_JOIN_RESULT],
    ) -> "linq[T_JOIN_RESULT]":
        return linq(join(self, inner, outer_selector, inner_selector, result_selector))

    def first(
        self,
        pred: Optional[Callable[[T_SOURCE], bool]] = None,
    ) -> Optional[T_SOURCE]:
        return first(self, pred)

    def last(self, pred: Optional[Callable[[T_SOURCE], bool]] = None) -> T_SOURCE:
        return last(self, pred)

    def order_by(
        self,
        selector: Callable[[T_SOURCE], Any],
        descending: bool = False,
    ) -> "linq[T_SOURCE]":
        return linq(iter(order_by(self, selector, descending)))

    def as_list(self) -> list[T_SOURCE]:
        return as_list(self)


def count(
    src: Iterable[T_SOURCE],
    pred: Optional[Callable[[T_SOURCE], bool]] = None,
) -> int:
    if pred:
        return sum(1 for e in src if pred(e))
    else:
        return sum(1 for _ in src)


def any(
    src: Iterable[T_SOURCE],
    pred: Optional[Callable[[T_SOURCE], bool]] = None,
) -> bool:
    for e in src:
        if (not pred) or (pred and pred(e)):
            return True
    return False


def where(
    src: Iterable[T_SOURCE],
    pred: Callable[[T_SOURCE], bool],
) -> Iterable[T_SOURCE]:
    return iter(e for e in src if pred(e))


def select(
    src: Iterable[T_SOURCE],
    pred: Callable[[T_SOURCE], T_RESULT],
) -> Iterable[T_RESULT]:
    return iter(pred(e) for e in src)


def zip(
    src: Iterable[T_SOURCE],
    other: Iterable[T_ZIP_OUTER],
    selector: Callable[[T_SOURCE, T_ZIP_OUTER], T_ZIP_RESULT],
) -> Iterable[T_ZIP_RESULT]:
    return iter(selector(x, y) for x, y in _zip(src, other))


def join(
    src: Iterable[T_SOURCE],
    inner: Iterable[T_JOIN_INNER],
    outer_selector: Callable[[T_SOURCE], T_JOIN_SELECTOR_RESULT],
    inner_selector: Callable[[T_JOIN_INNER], T_JOIN_SELECTOR_RESULT],
    result_selector: Callable[[T_SOURCE, T_JOIN_INNER], T_JOIN_RESULT],
) -> Iterable[T_JOIN_RESULT]:
    def generator():
        inner_table = {}
        for item in inner:
            inner_table.setdefault(inner_selector(item), []).append(item)

        for oi in src:
            if (ok := outer_selector(oi)) in inner_table:
                for ii in inner_table[ok]:
                    yield result_selector(oi, ii)

    return generator()


def first(
    src: Iterable[T_SOURCE],
    pred: Optional[Callable[[T_SOURCE], bool]] = None,
) -> Optional[T_SOURCE]:
    for e in src:
        if pred is None or pred(e):
            return e
    return None


def last(self, pred: Optional[Callable[[T_SOURCE], bool]] = None) -> T_SOURCE:
    if pred is None:
        try:
            return next(reversed(self.__src))  # type: ignore
        except (TypeError, StopIteration) as e:
            raise e

    last_item = None
    found = False
    for e in self:
        if pred is None or pred(e):
            last_item = e
            found = True

    if not found:
        raise ValueError()
    return last_item  # type: ignore


def order_by(
    src: Iterable[T_SOURCE],
    selector: Callable[[T_SOURCE], Any],
    descending: bool = False,
) -> Iterable[T_SOURCE]:
    def generator():
        items = list(src)
        items.sort(key=selector, reverse=descending)
        for item in items:
            yield item

    return generator()


def as_linq(src: Iterable[T_SOURCE]) -> linq[T_SOURCE]:
    return linq(src)


def as_list(src: Iterable[T_SOURCE]) -> list[T_SOURCE]:
    return list(src)


def repeat(e: T_SOURCE, count: int) -> linq[T_SOURCE]:
    return linq(e for _ in _range(count))


def range(start: int, count: int) -> linq[int]:
    return linq(i for i in _range(start, start + count))
