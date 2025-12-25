from typing import Callable, Generic, TypeVar
from .delegate import func

T = TypeVar("T")


class readonly(Generic[T]):
    def __init__(self, getter: Callable[[], T] | func[T]):
        self.__getter = func[T](getter)

    @property
    def value(self) -> T:
        return self.__getter.invoke()


def as_readonly(obj: T) -> readonly[T]:
    return readonly(lambda: obj)
