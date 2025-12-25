from typing import Generic, Optional, TypeVar


T = TypeVar("T")


class nullable(Generic[T]):
    def __init__(self, value: Optional[T]) -> None:
        self.__value = value

    @property
    def value(self) -> T:
        if self.__value:
            return self.__value
        raise ValueError("No value present")

    @value.setter
    def value(self, value: Optional[T]) -> None:
        self.__value = value

    @property
    def has_value(self) -> bool:
        return self.__value is not None


def as_nullable(value: T) -> nullable[T]:
    return nullable(value)


if __name__ == "__main__":
    name = nullable[str](None)
    print(name.has_value, "\t:", name.value if name.has_value else "-")
    name.value = "a"
    print(name.has_value, "\t:", name.value if name.has_value else "-")
