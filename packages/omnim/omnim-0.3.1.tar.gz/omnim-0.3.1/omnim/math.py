import builtins
from math import floor as _floor
import sys
from typing import Final, TypeVar

_builtins_min = builtins.min
_builtins_max = builtins.max

T_NUM = TypeVar("T_NUM", int, float)

pi: Final = 3.14159265358979323846
e: Final = 2.718281828459045235360287471352
eps: Final = 1 - (((4 / 3) - 1) + ((4 / 3) - 1) + ((4 / 3) - 1))

rad_to_deg: Final = 180 / pi
deg_to_rad: Final = pi / 180


def to_degrees(x: float) -> float:
    return x * rad_to_deg


def to_radians(x: float) -> float:
    return x * deg_to_rad


def sqrt(x: T_NUM) -> float:
    return x ** (1 / 2)


def min(*xs: T_NUM) -> T_NUM:
    return _builtins_min(*xs)


def max(*xs: T_NUM) -> T_NUM:
    return _builtins_max(*xs)


def clamp(x: T_NUM, min_value: T_NUM, max_value: T_NUM) -> T_NUM:
    if x < min_value:
        return min_value
    elif x > max_value:
        return max_value
    return x


def sign(x: T_NUM) -> int:
    if x == 0:
        return 0
    elif x > 0:
        return 1
    else:
        return -1


def abs(a: T_NUM) -> T_NUM:
    return -a if a < 0 else a


def floor(x: T_NUM, d=0) -> T_NUM:
    def _inner_floor(x: T_NUM) -> T_NUM:
        return type(x)(x - (x % 1))

    if d != 0:
        p = 10**d
        return type(x)(_inner_floor(x * p) / p)

    return _inner_floor(x)


def round(x: T_NUM, d: int = 0) -> T_NUM:
    p = 10**d
    res = _floor(x * p + 0.5) / p
    return type(x)(res)


def is_prime(n: int) -> bool:
    if n == 2:
        return True
    elif n < 2 or n % 2 == 0:
        return False

    for i in range(3, _floor(sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True
