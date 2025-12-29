from __future__ import annotations

import inspect
import sys

if sys.version_info >= (3, 10):
    import typing
else:
    import typing_extensions as typing

from awaitable_tools.types import CoroFunctionLike, GeneratorFunction

__all__ = ("isgeneratorcoroutinefunction", "iscoroutinefunctionlike")

def isgeneratorcoroutinefunction(
    o: object,
) -> typing.TypeGuard[GeneratorFunction[..., typing.Any]]:
    return inspect.isgeneratorfunction(o) and bool(
        o.__code__.co_flags & inspect.CO_ITERABLE_COROUTINE
    )


def iscoroutinefunctionlike(
    o: object,
) -> typing.TypeGuard[CoroFunctionLike[..., typing.Any]]:
    return inspect.iscoroutinefunction(o) or isgeneratorcoroutinefunction(o)
