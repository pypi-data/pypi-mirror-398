import asyncio
import functools
import time
import logging


def timer(logger_name: str = "timer", min_duration_ms: int = 0):
    """Log function duration in ms. Specify own logger or use default `timer` logger. Can set minimum threshold for logging.

    Usage:
        >>> @timer(min_duration_ms=100)
        >>> def my_function():
        >>>     time.sleep(1)
        >>>     return "Hello, World!"
        >>> print(my_function())
    """

    def decorator(func):
        # Handle both async and sync functions
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                logger = logging.getLogger(logger_name)
                t0 = time.perf_counter()
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - t0) * 1000
                if duration_ms >= min_duration_ms:
                    logger.info(
                        f"`{func.__name__}` took {duration_ms:.2f}ms",
                        extra={
                            "ms": duration_ms,
                            "fn": func.__name__,
                            "metric": "timer",
                        },
                    )
                return result
        else:

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                logger = logging.getLogger(logger_name)
                t0 = time.perf_counter()
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - t0) * 1000
                if duration_ms >= min_duration_ms:
                    logger.info(
                        f"`{func.__name__}` took {duration_ms:.2f}ms",
                        extra={
                            "ms": duration_ms,
                            "fn": func.__name__,
                            "metric": "timer",
                        },
                    )
                return result

        return wrapper

    return decorator
