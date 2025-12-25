import time
from typing import Callable, Generic, TypeVar
from .delegate import action
from .readonly import readonly

T = TypeVar("T")


class RxEvent(Generic[T]):
    def __init__(self, pre: T, post: T) -> None:
        self.__pre = pre
        self.__post = post

    @property
    def pre(self) -> T:
        return self.__pre

    @property
    def new(self) -> T:
        return self.__post


class ReactiveProperty(Generic[T]):
    def __init__(self, value: T) -> None:
        self.__value = value
        self.on_changed = action[RxEvent[T]]()

    @property
    def value(self) -> T:
        return self.__value

    @value.setter
    def value(self, new_value: T) -> None:
        if self.__value != new_value:
            pre_value = self.__value
            self.__value = new_value
            self.on_changed.invoke(RxEvent(pre_value, new_value))

    def subscribe(
        self,
        cb: Callable[[RxEvent[T]], None],
        immediate: bool = False,
    ) -> None:
        self.on_changed.register(cb)
        if immediate:
            self.notify()

    def notify(self) -> None:
        self.on_changed.invoke(RxEvent(self.__value, self.__value))

    def as_readonly(self) -> "readonly[T]":
        return readonly(lambda: self.__value)

    def dispose(self) -> None:
        self.on_changed.clear()

    def __repr__(self) -> str:
        return repr(self.value)


if __name__ == "__main__":
    name = ReactiveProperty[str]("name0")
    name.subscribe(lambda e: print("changed from", e.pre, "to", e.new))

    for i in range(1, 10 + 1):
        name.value = f"name{i}"
        time.sleep(0.2)
