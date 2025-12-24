"""This module contains generic decorators."""

import functools
import logging
import time
from typing import Any, Type

logger = logging.getLogger(__name__)


def log_error(exception_type: Type[Exception], message: str) -> Any:
    """This decorator logs the error in the decorated function
    and raises the given exception type.

    :param exception_type: The type of the exception to raise.
    :param message: The message to log.

    :raises exception_type: The given exception type.

    :return: The wrapped function.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                logger.exception(message)
                raise exception_type(message) from exc

        return wrapper

    return decorator


def measure_time(func) -> Any:
    """This decorator measures the total elapsed time
    it takes to execute the decorated function.

    :param func: The function to decorate.

    :return: The wrapped function.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_time = time.perf_counter() - start_time
        logger.debug("`%s()` executed in %.4f ms.", func.__name__, elapsed_time * 1000)
        return result

    return wrapper
