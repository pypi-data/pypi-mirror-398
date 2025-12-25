import time
from typing import Callable, Final, Literal, Optional, TypeVar
from os import urandom
from numba import njit
from numpy import uint64, int64

try:
    from . import omnim_rng_rust

    HAS_RUST = True
except ImportError:
    HAS_RUST = False

T = TypeVar("T")


def has_rust():
    return HAS_RUST


@njit
def _xorshift64_next(state: int) -> int:
    x = state
    x ^= (x << 13) & 0xFFFFFFFFFFFFFFFF
    x ^= (x >> 7) & 0xFFFFFFFFFFFFFFFF
    x ^= (x << 17) & 0xFFFFFFFFFFFFFFFF
    return x


@njit
def _pcg32_next(state: int, inc: int):
    oldstate = uint64(state)
    new_state = oldstate * uint64(6364136223846793005) + uint64(inc)

    shifted = uint64(((oldstate >> 18) ^ oldstate) >> 27)
    rot = oldstate >> 59
    output = (shifted >> rot) | (shifted << (uint64(-rot) & uint64(31)))

    return int64(new_state), int64(output & uint64(0xFFFFFFFF))


class _xorshift64:
    def __init__(self, seed: int):
        if HAS_RUST:
            self.impl = omnim_rng_rust.Xorshift64(0)
        else:
            self.state: int = seed & 0xFFFFFFFFFFFFFFFF or 0xDEADBEEF
        self.max: Final = 0xFFFFFFFFFFFFFFFF

    def next(self) -> int:
        if HAS_RUST:
            self.state = self.impl.next()
        else:
            self.state = _xorshift64_next(self.state)
        return self.state

    def nexts(self, count: int, min_value: int, max_value: int) -> list[int]:
        self.state = self.impl.next_ints(count, min_value, max_value)
        return self.state


class _pcg32:
    def __init__(self, seed: int):
        if HAS_RUST:
            self.impl = omnim_rng_rust.Pcg32(0)
        else:
            self.state = (seed + 0xDA3E39CB94B95BDB) & 0xFFFFFFFFFFFFFFFF
            self.inc = (seed | 1) & 0xFFFFFFFFFFFFFFFF
        self.max: Final = 0xFFFFFFFF

    def next(self) -> int:
        if HAS_RUST:
            self.state = result = self.impl.next()
        else:
            self.state, result = _pcg32_next(self.state, self.inc)
        return result

    def nexts(self, count: int, min_value: int, max_value: int) -> list[int]:
        self.state = self.impl.next_ints(count, min_value, max_value)
        return self.state


class rng:
    def __init__(
        self,
        *,
        seed: Optional[int] = None,
        mode: Literal["xorshift", "pcg"] = "xorshift",
    ):
        import time

        if seed is None:
            seed = int(time.time() * 1000)

        self.__generator = None
        match mode:
            case "xorshift":
                self.__generator = _xorshift64(seed)
            case "pcg":
                self.__generator = _pcg32(seed)

    def _next(self) -> int:
        return self.__generator.next()

    def next_int(self, min_value: int, max_value: int) -> int:
        return self._next() % (max_value - min_value + 1) + min_value

    def next_float(self, min_value: float, max_value: float) -> float:
        return self._next() / self.__generator.max * (max_value - min_value) + min_value

    def next_ints(self, count: int, min_value: int, max_value: int) -> list[int]:
        if HAS_RUST:
            raw_values = self.__generator.impl.next_batch(count)
            range_size = max_value - min_value + 1
            return [val % range_size + min_value for val in raw_values]
            # return self.__generator.impl.next_ints(count, min_value, max_value)
        else:
            range_size = max_value - min_value + 1
            return [(self._next() % range_size + min_value) for _ in range(count)]

    def next_floats(
        self, count: int, min_value: float, max_value: float
    ) -> list[float]:
        if HAS_RUST:
            raw_values = self.__generator.impl.next_batch(count)
            max_val = self.__generator.max
            diff = max_value - min_value
            return [(val / max_val * diff + min_value) for val in raw_values]
        else:
            max_val = self.__generator.max
            diff = max_value - min_value
            return [(self._next() / max_val * diff + min_value) for _ in range(count)]

    def rnexts(self, count: int, min_value: int, max_value: int) -> list[int]:
        return self.__generator.impl.next_ints(count, min_value, max_value)

    def runiforms(self, count: int, min_value: float, max_value: float) -> list[float]:
        return self.__generator.impl.next_floats(count, min_value, max_value)

    def choice(self, seq: list[T]):
        if not seq:
            raise IndexError("Cannot choose from an empty sequence")
        return seq[self.next_int(0, len(seq) - 1)]


try:
    _g = rng(seed=int.from_bytes(urandom(8), "big"), mode="pcg")
except Exception:  # NotImplementedError
    _g = rng()

T = TypeVar("T", int, float)

uniform = _g.next_float
uniforms = _g.next_floats
randint = _g.next_int
randints = _g.next_ints
rnexts = _g.rnexts
runiforms = _g.runiforms


def rand(min: T, max: T) -> T:
    if isinstance(min, int) and isinstance(max, int):
        return _g.next_int(min, max)
    return _g.next_float(min, max)


if __name__ == "__main__":
    _rng = rng(seed=10)
    print(_rng.next_int(0, 100))
    print(_rng.next_float(0.0, 1.0))
    print(_rng.choice([1, 2, 3, 4, 5]))

    print([rand(0, 3) for _ in range(10)])
    print([rand(0, 1.0) for _ in range(10)])
