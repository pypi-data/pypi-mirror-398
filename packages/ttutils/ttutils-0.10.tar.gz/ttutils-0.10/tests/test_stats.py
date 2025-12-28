import asyncio
import json
import time
from unittest.mock import Mock, patch

from ttutils.stats import Collector


async def test_Collector_post_init_ok_default() -> None:
    collector = Collector()

    assert collector.main_logger
    assert collector.slow_logger


async def test_Collector_post_init_ok_only_main() -> None:
    collector = Collector(slow_logger_name=None)

    assert collector.main_logger
    assert collector.slow_logger is None


async def test_Collector_post_init_ok_only_slow() -> None:
    collector = Collector(main_logger_name=None)

    assert collector.main_logger is None
    assert collector.slow_logger


@patch.object(asyncio, 'get_running_loop', Mock(side_effect=RuntimeError))
async def test_Collector_post_init_ok_no_loop() -> None:
    collector = Collector()

    assert collector.main_logger is None


@patch.object(asyncio, 'get_running_loop')
@patch.object(json, 'dumps')
async def test_Collector_log_ok_with_data(dumps_mock: Mock, loop_mock: Mock) -> None:
    collector = Collector()
    collector.data['a'].extend([100, 130, 220])

    collector._log()

    loop_mock.assert_called()
    dumps_mock.assert_called()


@patch.object(asyncio, 'get_running_loop')
@patch.object(json, 'dumps')
async def test_Collector_log_ok_with_no_data(dumps_mock: Mock, loop_mock: Mock) -> None:
    collector = Collector()
    collector.data['a'] = []

    collector._log()

    loop_mock.assert_called()
    dumps_mock.assert_not_called()


async def test_Collector_timer_ok() -> None:
    collector = Collector()
    collector.slow_logger = Mock()

    with collector.timer('a'):
        time.sleep(.001)  # noqa ASYNC251

    with collector.timer('a'):
        await asyncio.sleep(.002)

    assert len(collector.data['a']) == 2
    collector.slow_logger.info.assert_not_called()


async def test_Collector_timer_ok_slow() -> None:
    collector = Collector(slow_limit_ms=1)
    collector.slow_logger = Mock()

    with collector.timer('a'):
        await asyncio.sleep(.002)

    collector.slow_logger.info.assert_called()


async def test_Collector_atimer_ok() -> None:
    collector = Collector(slow_limit_ms=2)

    @collector.atimer('a')
    async def check() -> None:
        await asyncio.sleep(.001)

    await check()

    assert collector.data['a'] == [1]
