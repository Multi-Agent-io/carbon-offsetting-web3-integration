"""Thread wrapper function for async functions execution"""

import asyncio
import functools
import typing as tp


def to_thread(func: tp.Callable) -> tp.Coroutine:
    """
    Wrapper to run functions in new async thread.

    :param func: Wrapped function.

    :return: Async coroutine.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        """
        Wrapper function itself.

        :param args: Wrapped function args.
        :param kwargs: Wrapped function kwargs.

        :return: Wrapped function return.

        """
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper
