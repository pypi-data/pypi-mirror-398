from __future__ import annotations

import collections.abc
import sys

if sys.version_info >= (3, 10):
    import typing
else:
    import typing_extensions as typing

__all__ = (
    "AwaitableFunction",
    "CoroutineFunction",
    "CoroFunctionLike",
    "Coroutine",
    "Generator",
    "GeneratorFunction",
)

P = typing.ParamSpec("P")
ReturnT = typing.TypeVar("ReturnT")
ReturnT_co = typing.TypeVar("ReturnT_co", covariant=True)

Generator: typing.TypeAlias = "collections.abc.Generator[typing.Any, typing.Any, ReturnT]"
"""generator object returned by `__await__`"""
Coroutine: typing.TypeAlias = "collections.abc.Coroutine[typing.Any, typing.Any, ReturnT]"
"""coroutine object returned by a function with `async/await` syntax"""

GeneratorFunction: typing.TypeAlias = "collections.abc.Callable[P, Generator[ReturnT]]"
"""function implementation for `__await__`"""
CoroutineFunction: typing.TypeAlias = "collections.abc.Callable[P, Coroutine[ReturnT]]"
"""function defined with `async/await` syntax"""
AwaitableFunction: typing.TypeAlias = "collections.abc.Callable[P, collections.abc.Awaitable[ReturnT]]"
"""Function that returns an object that implements `__await__`"""

CoroFunctionLike: typing.TypeAlias = "typing.Union[CoroutineFunction[P, ReturnT], AwaitableFunction[P, ReturnT]]"
