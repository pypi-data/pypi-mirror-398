import asyncio
from typing import Awaitable, Callable, Optional, overload

global __interval_s
__interval_s = 0.1


@overload
def interval(value: float) -> None:
    """value is in seconds (e.g., 0.1)"""
    ...


@overload
def interval(value: int) -> None:
    """value is in milliseconds (e.g., 100)"""
    ...


def interval(value: float | int) -> None:
    global __interval_s
    match value:
        case float() as s:
            __interval_s = max(0.001, s)
        case int() as ms:
            __interval_s = max(0.001, ms / 1000.0)


async def wait_until(
    predicate: Callable[[], bool],
    timeout: Optional[float] = None,
) -> bool:
    loop = asyncio.get_running_loop()
    start = loop.time()

    while not predicate():
        if timeout is not None:
            if (loop.time() - start) > timeout:
                raise TimeoutError()

        await asyncio.sleep(__interval_s)

    return True


async def wait_while(
    predicate: Callable[[], bool],
    timeout: Optional[float] = None,
) -> bool:
    return await wait_until(lambda: not predicate(), timeout)


async def wait_all(*tasks: Awaitable):
    return await asyncio.gather(*tasks)


async def wait_any(*tasks: Awaitable):
    done, pending = await asyncio.wait(
        [asyncio.ensure_future(t) for t in tasks],
        return_when=asyncio.FIRST_COMPLETED,
    )
    return done, pending


async def with_timeout(task: Awaitable, timeout: float):
    return await asyncio.wait_for(task, timeout)


async def wait_frame():
    await asyncio.sleep(0)


async def delay(seconds: float):
    await asyncio.sleep(seconds)
