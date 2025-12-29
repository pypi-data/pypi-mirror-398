from __future__ import annotations

import functools
import types
import sys

import awaitable_tools
from awaitable_tools.types import GeneratorFunction

if sys.version_info >= (3, 10):
    import typing
else:
    import typing_extensions as typing

__all__ = ("native_coroutine",)

P = typing.ParamSpec("P")
R = typing.TypeVar("R")


def wrap_generatorcoroutine(f: awaitable_tools.GeneratorFunction[P, R]) -> GeneratorFunction[P, R]:
    @functools.wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> awaitable_tools.Generator[R]:
        return (yield from f(*args, **kwargs))
    return wrapper


def native_coroutine(
    f: awaitable_tools.GeneratorFunction[P, R] | awaitable_tools.CoroFunctionLike[P, R],
) -> awaitable_tools.GeneratorFunction[P, R]:
    """Decorator for implementing __await__ in classes using coroutine functions.
    ```
    class Example:
        @native_coroutine
        async def __await__(self):
            return 1
        
        @native_coroutine
        def __await__(self):
            yield from asyncio.sleep(1)
            return 1
    ```
    WARNING: Only use on methods implementing __await__ in classes.
    Doesn't work for standalone functions.

    """
    f = typing.cast("awaitable_tools.CoroFunctionLike[P, R]", types.coroutine(f))
    if awaitable_tools.isgeneratorcoroutinefunction(f):
       return wrap_generatorcoroutine(f)
    if not awaitable_tools.iscoroutinefunctionlike(f):
        raise ValueError("%r is not a valid coroutine function" % f)
    @functools.wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> awaitable_tools.Generator[R]:
        return f(*args, **kwargs).__await__()
    return wrapper
