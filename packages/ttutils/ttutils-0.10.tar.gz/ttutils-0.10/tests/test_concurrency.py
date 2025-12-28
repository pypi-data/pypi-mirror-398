import asyncio
import time
from unittest.mock import MagicMock

from ttutils.concurrency import concurrency_limit


async def test_concurrency_limit_ok() -> None:
    calls = {}

    @concurrency_limit(2)
    async def my_task(num: int) -> None:
        calls[num] = time.time()
        await asyncio.sleep(.01)

    await asyncio.gather(*[my_task(x) for x in range(5)])

    assert calls[1] - calls[0] < .001
    assert calls[3] - calls[2] < .001
    assert calls[2] - calls[0] > .01
    assert calls[3] - calls[1] > .01
    assert calls[4] - calls[3] > .01


async def test_concurrency_limit_ok_performance() -> None:
    @concurrency_limit(10)
    async def my_task(num: int) -> None:
        pass

    t = time.time()

    await asyncio.gather(*[my_task(x) for x in range(10_000)])

    assert time.time() - t < .5


async def test_concurrency_limit_ok_log() -> None:
    log = MagicMock()

    @concurrency_limit(2, logger=log)
    async def my_task(num: int) -> None:
        await asyncio.sleep(.01)

    await asyncio.gather(*[my_task(x) for x in range(5)])

    assert log.debug.call_count == 2
