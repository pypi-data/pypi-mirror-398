from typing import Callable, Generic, Iterator, TypeVar, TypeVarTuple


T_RESULT = TypeVar("T_RESULT")
T_SOURCE = TypeVarTuple("T_SOURCE")


class action(Generic[*T_SOURCE]):
    def __init__(self, *callbacks: Callable[[*T_SOURCE], None]) -> None:
        self.__callbacks = list(callbacks)

    def register(self, *callbacks: Callable[[*T_SOURCE], None]) -> None:
        for cb in callbacks:
            self.__callbacks.append(cb)

    def unregister(self, *callbacks: Callable[[*T_SOURCE], None]) -> None:
        for cb in callbacks:
            self.__callbacks.remove(cb)

    def invoke(self, *args: *T_SOURCE) -> None:
        if self.__callbacks:
            for cb in self.__callbacks:
                cb(*args)

    def as_callable(self) -> Iterator[Callable[[*T_SOURCE], None]]:
        for cb in self.__callbacks:
            yield cb

    def clear(self) -> None:
        self.__callbacks.clear()

    def __iadd__(self, callback: Callable[[*T_SOURCE], None]) -> "action[*T_SOURCE]":
        self.__callbacks.append(callback)
        return self

    def __isub__(self, callback: Callable[[*T_SOURCE], None]) -> "action[*T_SOURCE]":
        self.__callbacks.remove(callback)
        return self

    def __len__(self) -> int:
        return len(self.__callbacks)

    def __call__(self, *args: *T_SOURCE) -> None:
        for cb in self.__callbacks:
            cb(*args)


class func(Generic[*T_SOURCE, T_RESULT]):
    def __init__(self, *callbacks: Callable[[*T_SOURCE], T_RESULT]) -> None:
        self.__callbacks = list(callbacks)

    def register(self, *callbacks: Callable[[*T_SOURCE], T_RESULT]) -> None:
        for cb in callbacks:
            self.__callbacks.append(cb)

    def unregister(self, *callbacks: Callable[[*T_SOURCE], T_RESULT]) -> None:
        for cb in callbacks:
            self.__callbacks.remove(cb)

    def invoke(self, *args: *T_SOURCE) -> T_RESULT:
        if self.__callbacks.__len__() <= 0:
            raise ValueError("No callbacks registered")
        return [cb(*args) for cb in self.__callbacks][0]

    def as_callable(self) -> Callable[[*T_SOURCE], T_RESULT]:
        return self.__call__

    def clear(self) -> None:
        self.__callbacks.clear()

    def __iadd__(
        self, callback: Callable[[*T_SOURCE], T_RESULT]
    ) -> "func[*T_SOURCE, T_RESULT]":
        self.__callbacks.append(callback)
        return self

    def __isub__(
        self, callback: Callable[[*T_SOURCE], T_RESULT]
    ) -> "func[*T_SOURCE, T_RESULT]":
        self.__callbacks.remove(callback)
        return self

    def __len__(self) -> int:
        return len(self.__callbacks)

    def __call__(self, *args: *T_SOURCE) -> T_RESULT:
        return [cb(*args) for cb in self.__callbacks][0]


def on_int_value_changed(i: int) -> None:
    print("on_int_value_changed:", i)


def on_authorised_callback() -> bool:
    print("on_authorised")
    return True


if __name__ == "__main__":
    on_value_changed = action[int]()
    on_value_changed += on_int_value_changed
    on_value_changed += on_int_value_changed
    on_value_changed -= on_int_value_changed
    on_value_changed(12)

    on_authorised = func[bool]()
    on_authorised += on_authorised_callback
    on_authorised += on_authorised_callback
    on_authorised -= on_authorised_callback
    print("authorise result:", on_authorised())

    on_user_updated = action[int, float, str]()
    on_user_updated += lambda user_id, score, name: print(user_id, score, name)
    on_user_updated.invoke(123, 99.8, "trrne")
