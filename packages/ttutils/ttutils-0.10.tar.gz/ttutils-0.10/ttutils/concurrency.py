import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

R = TypeVar('R')
P = ParamSpec('P')
F = Callable[P, R]


def concurrency_limit(
    max_coroutines: int = 5,
    *,
    logger: logging.Logger | None = None
) -> Callable[[F], F]:
    '''
        Decorated asynchronous function will be limit for concurrency calling.

        max_coroutines (default: 5) - maximum number of сoncurrently running functions
        logger (default: None) - log of queue length
    '''
    semaphore = asyncio.Semaphore(max_coroutines)

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:  # type: ignore[valid-type]
            if logger and (queue_length := len(semaphore._waiters or [])):
                logger.debug('Overloaded %s - %s tasks awaiting', func.__qualname__, queue_length)

            async with semaphore:
                return await func(*args, **kwargs)

        return wrapper

    return decorator
