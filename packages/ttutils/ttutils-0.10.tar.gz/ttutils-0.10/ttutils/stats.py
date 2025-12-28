import asyncio
import json
import logging
import statistics
import time
from collections import abc, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, TypedDict, TypeVar

RT = TypeVar('RT')
CRT = abc.Callable[..., RT]


class Item(TypedDict):
    key: str    # идентификатор
    qty: int    # количество вызовов
    sum: int    # суммарное время в ms
    min: int    # миннимальное время в ms
    max: int    # максимальное время в ms
    avg: int    # среднее время в ms
    med: int    # медианное время в ms


@dataclass
class Collector:
    '''
        Collector предназначен для:
          - сбора данных о длительности выполнения функций, методов и блоков кода,
          - формированни периодических отчетов о статистике времени выполнения,
          - ведении лога медленных запросов.

        В основной лог выдается отчеты за заданный период
          `main_logger_name` (default: `stats`) - название лога (None для отключения)
          `reset_interval` (default: 60) - период сбора данных в секундах
        Основной лог представляет собой json из списка объектов, готовый для предачи
        в grafana. При отключении, отключается только лог, но не сбор данных.

        В slowlog попадает информация о запросах медленне заданного времени
          `slow_logger_name` (default: `slow`) - название лога (None для отключения)
          `slow_limit_ms` (default: 1000) - время в милисекундах, выше которого
            запрос попадет в медленные

        ```python
            stats = Collector()

            @stats.atimer('k1')
            async def func():
                ...

            class A:
                @stats.atimer('k2')
                async def func(self):
                    ...

            with stats.timer('k3'):
                sync_func()
                await async_func()
        ```
    '''

    data: defaultdict = field(default_factory=lambda: defaultdict(list))
    main_logger_name: str | None = 'stats'
    slow_logger_name: str | None = 'slow'
    slow_limit_ms: int = 1000  # ms
    reset_interval: int = 60     # sec
    main_logger: logging.Logger | None = None
    slow_logger: logging.Logger | None = None

    def __post_init__(self) -> None:
        if self.slow_logger_name:
            self.slow_logger = logging.getLogger(self.slow_logger_name)

        if self.main_logger_name:
            self.main_logger = logging.getLogger(self.main_logger_name)

            try:
                asyncio.get_running_loop().call_later(self.reset_interval, self._log)
            except RuntimeError:
                self.main_logger.warning('Running periodic stats log failed')
                self.main_logger = None

    def _log(self) -> None:
        asyncio.get_running_loop().call_later(self.reset_interval, self._log)

        if self.main_logger and (data := list(self.reset())):
            self.main_logger.debug('%s', json.dumps(data))

    def reset(self) -> abc.Iterator[Item]:
        '''
            Анализует накопленную информацию и выдает результаты,
            при этом накопитель данных очищается.
        '''
        self.data, data = defaultdict(list), self.data

        for key, vals in data.items():
            if vals:
                _qty, _sum = len(vals), sum(vals)
                yield {
                    'key': key,
                    'qty': _qty,
                    'sum': _sum,
                    'min': min(vals),
                    'max': max(vals),
                    'avg': int(_sum / _qty),
                    'med': int(statistics.median(vals)),
                }

    @contextmanager
    def timer(self, key: str) -> abc.Generator[None]:
        '''
            Контекстный менеджер для сбора информации о времени выполнения блока кода.
            Блок может содержать как синхронный, так и асинхронный код.
            Время выполнения измеряется с точностью до милисекунд.
        '''
        base_time = time.monotonic()

        try:
            yield
        finally:
            duration = int(1000 * (time.monotonic() - base_time))  # ms
            self.data[key].append(duration)

            if self.slow_logger and self.slow_limit_ms < duration:
                self.slow_logger.info('Slow %s: %s ms', key, duration)

    def atimer(self, key: str) -> abc.Callable[[CRT], CRT]:
        '''
            Декоратор для сбора информации о времни выполнения асинхронных функций и методов
        '''
        def _timer(func: CRT) -> CRT:
            @wraps(func)
            async def wrapper(*args: Any, **kw: Any) -> RT:  # noqa ANN401
                with self.timer(key):
                    return await func(*args, **kw)
            return wrapper
        return _timer
