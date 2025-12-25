from typing import Final, Generic, Iterable, Iterator, TypeAlias, TypeVar
from .math import abs

_Index: TypeAlias = int | float  # TypeVar("_Index", int, float)
T_INDEX = TypeVar("T_INDEX", int, float)


class frange(Generic[T_INDEX]):
    """
    flexible range

    ```python
    frange(0, 2, 1) # [0, 1, 2]
    frange(0, 2, 1.0) # [0.0, 1.0, 2.0]
    frange(0, 2.0, 1) # [0.0, 1.0, 2.0]
    frange(0.0, 2.0, 1) # [0.0, 1.0, 2.0]
    ```
    """

    def __init__(self, begin: T_INDEX, end: T_INDEX, step: T_INDEX) -> None:
        self.__begin = begin
        self.__end = end
        self.__step = step
        self.__forward: Final = self.__begin < self.__end

    def __iter__(self):
        if (step := abs(self.__step)) == 0:
            raise ValueError("step must not be zero")

        value = self.__begin
        if self.__forward:
            while value <= self.__end:
                yield (value)
                value += step
        else:
            while value >= self.__end:
                yield (value)
                value -= step


T = TypeVar("T")


class step:
    """
    ## with iterator:
    ```python
    items = [0, 2, 4, 6, 8]
    for i in step(items):
        print(i) # [0, 1, 2, 3, 4]
    ```

    ## with count:
    ```python
    for i in step(3):
        print(i) # [0, 1, 2]
    ```
    """

    def __init__(self, src, *, reverse=False) -> None:
        if isinstance(src, Iterable):
            self.__len = len(list(iter(src)))
        elif isinstance(src, int):
            self.__len = src
        self.__reverse = reverse

    def __iter__(self) -> Iterator[int]:
        r = range(self.__len)
        if self.__reverse:
            r = reversed(r)
        for i in r:  # range(self.__len):
            yield i

    def __len__(self) -> int:
        return self.__len

    def __getitem__(self, i: int) -> int:
        return i


if __name__ == "__main__":
    print(f"-10, +10: {list(frange(-10, 10, -1))}")
    print(f"+10, -10: {list(frange(10, -10, -1))}")
    print(f"0.0, 1.0: {list(frange(0, 1, 0.1))}")
    _ = list(frange[float](0, 1, 0.1))

    print("---")

    src = [i for i in frange(0, 10, 1)]
    print(src)
    print(list(step(src)))

    print("---")

    items = [i for i in range(0, 10, 2)]
    for i in step(items):
        print(i)  # [0, 2, 4, 6, 8]
