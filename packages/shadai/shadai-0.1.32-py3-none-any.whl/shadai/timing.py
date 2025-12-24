"""
Timing Utilities
----------------
Decorators for measuring execution time of async functions.
"""

import time
from functools import wraps
from typing import Any, Callable, Coroutine, TypeVar

F = TypeVar("F", bound=Callable[..., Coroutine[Any, Any, Any]])


def timed(func: F) -> F:
    """Decorator to measure and print execution time of async functions.

    Automatically measures the time taken by an async function
    and prints the duration after completion.

    Usage:
        @timed
        async def main():
            async for chunk in shadai.query(...):
                print(chunk, end="", flush=True)

    Args:
        func: Async function to measure

    Returns:
        Wrapped function that measures execution time
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        init_time = time.time()
        try:
            return await func(*args, **kwargs)
        finally:
            end_time = time.time()
            elapsed = end_time - init_time
            print(f"\n\n⏱️  Time taken: {elapsed:.2f} seconds")

    return wrapper  # type: ignore
