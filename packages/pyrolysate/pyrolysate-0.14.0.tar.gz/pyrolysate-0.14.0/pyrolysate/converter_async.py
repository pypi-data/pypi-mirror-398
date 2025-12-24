# Function decorator functionality
from functools import update_wrapper

# Async Support
import asyncio
import inspect
import types


class AsyncWrapper:
    def __init__(self, func):
        self._func = func
        self._is_coroutine = inspect.iscoroutinefunction(func)
        update_wrapper(self, func)  # Copy dunder metadata from original function

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    async def run_async(self, *args, **kwargs):
        if self._is_coroutine:
            return await self._func(*args, **kwargs)  # Awaits already async function
        else:
            return await asyncio.to_thread(
                self._func, *args, **kwargs
            )  # Sends sync function to thread

    def __get__(self, instance, owner):
        # Support instance methods (bind 'self')
        return types.MethodType(self, instance)


def async_support(func):
    return AsyncWrapper(func)
