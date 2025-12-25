from __future__ import annotations

import asyncio
import contextlib
import dataclasses
from asyncio.futures import Future
from collections.abc import AsyncGenerator, Awaitable, Callable, Coroutine, Iterable
from typing import Any, Generic, Literal, TypeAlias, TypeVar, cast, overload

from .traces import TRACE_ID_VAR

TRet = TypeVar("TRet")
TVal = TypeVar("TVal")


async def adummy(value: TVal) -> TVal:
    return value


async def named_await(name: str, func: Callable[[], Awaitable[TRet]]) -> tuple[str, TRet]:
    """Convenience helper for `asyncio.gather`ing into a dict of results"""
    result = await func()
    return (name, result)


def _get_task_child_next_id(attr_name: str = "_trace_child_next_id") -> int:
    task = asyncio.current_task()
    value = getattr(task, attr_name, None) or 0
    value += 1
    setattr(task, attr_name, value)
    return value


def wrap_with_trace_id(coro: Awaitable[TRet]) -> Coroutine[Any, Any, TRet]:
    """
    Wrap a coroutine with `TRACE_ID_VAR` updater,
    that generates consecutive subtask ids,
    resulting in a task trace (path) in the `TRACE_ID_VAR`.

    Automatically used in `aiogather` and `aiogather_it`.
    """
    current_trace_id = TRACE_ID_VAR.get()
    if not current_trace_id:
        # Nothing to handle, can skip the wrapping.
        if asyncio.iscoroutine(coro):
            return coro

        # Have to wrap to satisfy the types.
        new_trace_id = None
    else:
        child_id = _get_task_child_next_id()
        new_trace_id = f"{current_trace_id}__{child_id}"

    async def wrapped_with_trace_id() -> TRet:
        if new_trace_id is not None:
            TRACE_ID_VAR.set(new_trace_id)
        return await coro

    return wrapped_with_trace_id()


# Due to wrapped `asyncio.gather`,
# adapted from
# https://github.com/python/mypy/blob/ea49e1fa488810997d192a36d85357dadb4a7f14/mypy/typeshed/stdlib/asyncio/tasks.pyi#L99
_T = TypeVar("_T")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")
_T4 = TypeVar("_T4")
_T5 = TypeVar("_T5")
_T6 = TypeVar("_T6")
# For wrapping simplicity, omitting the `Generator[Any, None, _T]` from `_FutureLike`
_FutureLike: TypeAlias = Future[_T] | Awaitable[_T]


@overload
async def aiogather(  # type: ignore[overload-overlap]
    __coro_or_future1: _FutureLike[_T1],
    /,
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1]: ...


@overload
async def aiogather(  # type: ignore[overload-overlap]
    __coro_or_future1: _FutureLike[_T1],
    __coro_or_future2: _FutureLike[_T2],
    /,
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2]: ...


@overload
async def aiogather(  # type: ignore[overload-overlap]
    __coro_or_future1: _FutureLike[_T1],
    __coro_or_future2: _FutureLike[_T2],
    __coro_or_future3: _FutureLike[_T3],
    /,
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2, _T3]: ...


@overload
async def aiogather(  # type: ignore[overload-overlap]
    __coro_or_future1: _FutureLike[_T1],
    __coro_or_future2: _FutureLike[_T2],
    __coro_or_future3: _FutureLike[_T3],
    __coro_or_future4: _FutureLike[_T4],
    /,
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2, _T3, _T4]: ...


@overload
async def aiogather(  # type: ignore[overload-overlap]
    __coro_or_future1: _FutureLike[_T1],
    __coro_or_future2: _FutureLike[_T2],
    __coro_or_future3: _FutureLike[_T3],
    __coro_or_future4: _FutureLike[_T4],
    __coro_or_future5: _FutureLike[_T5],
    /,
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2, _T3, _T4, _T5]: ...


@overload
async def aiogather(  # type: ignore[overload-overlap]
    __coro_or_future1: _FutureLike[_T1],
    __coro_or_future2: _FutureLike[_T2],
    __coro_or_future3: _FutureLike[_T3],
    __coro_or_future4: _FutureLike[_T4],
    __coro_or_future5: _FutureLike[_T5],
    __coro_or_future6: _FutureLike[_T6],
    /,
    *,
    return_exceptions: Literal[False] = False,
) -> tuple[_T1, _T2, _T3, _T4, _T5, _T6]: ...


@overload
async def aiogather(  # type: ignore[overload-overlap]
    *coros_or_futures: _FutureLike[_T], return_exceptions: Literal[False] = False
) -> list[_T]: ...


@overload
async def aiogather(  # type: ignore[overload-overlap]
    __coro_or_future1: _FutureLike[_T1], /, *, return_exceptions: bool
) -> tuple[_T1 | BaseException]: ...


@overload
async def aiogather(  # type: ignore[overload-overlap]
    __coro_or_future1: _FutureLike[_T1], __coro_or_future2: _FutureLike[_T2], /, *, return_exceptions: bool
) -> tuple[_T1 | BaseException, _T2 | BaseException]: ...


@overload
async def aiogather(  # type: ignore[overload-overlap]
    __coro_or_future1: _FutureLike[_T1],
    __coro_or_future2: _FutureLike[_T2],
    __coro_or_future3: _FutureLike[_T3],
    /,
    *,
    return_exceptions: bool,
) -> tuple[_T1 | BaseException, _T2 | BaseException, _T3 | BaseException]: ...


@overload
async def aiogather(  # type: ignore[overload-overlap]
    __coro_or_future1: _FutureLike[_T1],
    __coro_or_future2: _FutureLike[_T2],
    __coro_or_future3: _FutureLike[_T3],
    __coro_or_future4: _FutureLike[_T4],
    /,
    *,
    return_exceptions: bool,
) -> tuple[_T1 | BaseException, _T2 | BaseException, _T3 | BaseException, _T4 | BaseException]: ...


@overload
async def aiogather(  # type: ignore[overload-overlap]
    __coro_or_future1: _FutureLike[_T1],
    __coro_or_future2: _FutureLike[_T2],
    __coro_or_future3: _FutureLike[_T3],
    __coro_or_future4: _FutureLike[_T4],
    __coro_or_future5: _FutureLike[_T5],
    /,
    *,
    return_exceptions: bool,
) -> tuple[_T1 | BaseException, _T2 | BaseException, _T3 | BaseException, _T4 | BaseException, _T5 | BaseException]: ...


@overload
async def aiogather(  # type: ignore[overload-overlap]
    __coro_or_future1: _FutureLike[_T1],
    __coro_or_future2: _FutureLike[_T2],
    __coro_or_future3: _FutureLike[_T3],
    __coro_or_future4: _FutureLike[_T4],
    __coro_or_future5: _FutureLike[_T5],
    __coro_or_future6: _FutureLike[_T6],
    /,
    *,
    return_exceptions: bool,
) -> tuple[
    _T1 | BaseException,
    _T2 | BaseException,
    _T3 | BaseException,
    _T4 | BaseException,
    _T5 | BaseException,
    _T6 | BaseException,
]: ...


@overload
async def aiogather(*coros_or_futures: _FutureLike[_T], return_exceptions: bool) -> list[_T | BaseException]: ...


async def aiogather(
    *coros_or_futures: _FutureLike[_T], return_exceptions: bool = False
) -> list[_T] | list[BaseException] | list[_T | BaseException] | tuple[_T | BaseException, ...]:
    """
    Wrapper around `asyncio.gather` (wihout extra parameters) with various conveniences.

    NOTE: takes a single argument, rather than a coro-per-arg.
    This makes gathering from a list/generator comprehension easier.
    """
    if not coros_or_futures:
        return []

    if len(coros_or_futures) == 1:
        try:
            result = await coros_or_futures[0]
        except BaseException as exc:
            if return_exceptions:
                return [exc]
            raise
        return [result]

    return await asyncio.gather(*[wrap_with_trace_id(coro) for coro in coros_or_futures])


def aiogather_it(coros_or_futures: Iterable[_FutureLike[_T]]) -> Awaitable[list[_T]]:
    return aiogather(*coros_or_futures)


@contextlib.asynccontextmanager
async def task_cm(coro_or_future: Coroutine | Future) -> AsyncGenerator[asyncio.Task, None]:
    task = asyncio.ensure_future(coro_or_future)
    try:
        yield task
    finally:
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


TArgsKey = tuple[
    # args
    tuple[Any, ...],
    # kwargs
    tuple[tuple[str, Any], ...],
]
TAIOMemoStorage = dict[TArgsKey, tuple[asyncio.Lock, None] | tuple[None, TRet] | None]


@dataclasses.dataclass()
class AIOLockedMemoized(Generic[TRet]):
    """
    Storage states:

        none: `None`
        none -> locked
        locked: `Lock, None`
        locked -> saved
        locked -> error
        saved: `None, TRet`
        error: `None`
        error -> none
    """

    func: Callable[..., Awaitable[TRet]]
    miss_count: int = 0
    wait_count: int = 0
    hit_count: int = 0
    error_in_count: int = 0
    error_count: int = 0

    def __post_init__(self) -> None:
        func_name = self.func.__name__
        if "<" in func_name:
            raise ValueError(f"Attempting to memoize a non-normal function with name={func_name!r}")
        self._storage_key = f"_{func_name}_cache"

    @staticmethod
    def _get_args_key(args: tuple[Any, ...], kwargs: dict[str, Any]) -> TArgsKey:
        return args, tuple(sorted(kwargs.items()))

    def _get_storage(self, obj: Any) -> TAIOMemoStorage[TRet]:
        data: TAIOMemoStorage[TRet]
        storage = getattr(obj, self._storage_key, None)
        if storage is not None:
            assert isinstance(storage, tuple)
            assert len(storage) == 2
            owner, data = storage
            assert owner is self
            assert data is not None
            return data

        data = {}
        setattr(obj, self._storage_key, (self, data))
        return data

    async def __call__(self, obj: Any, *args: Any, **kwargs: Any) -> TRet:
        args_key = self._get_args_key(args, kwargs)
        storage = self._get_storage(obj)

        state = storage.get(args_key)
        lock: asyncio.Lock | None

        if state is None:  # `none`
            self.miss_count += 1

        else:  # `locked` | `saved`
            assert isinstance(state, tuple)
            assert len(state) == 2
            lock, pre_result = state

            if lock is None:  # `saved`
                self.hit_count += 1
                # It can be `result: TRet = None`; for correct typing, might have to use a sentinel object.
                return cast("TRet", pre_result)

            # `locked`
            assert pre_result is None
            self.wait_count += 1
            async with lock:
                state = storage[args_key]

            if state is not None:  # `saved` | `error`->`locked`
                assert isinstance(state, tuple)
                assert len(state) == 2
                lock, pre_result = state
                if lock is None:
                    return cast("TRet", pre_result)

            # `error`
            self.error_count += 1

            # NOTE: in case of error, all lock-waiters will go generate their own locks in parallel.

        # `none` | `error` | `error`->`locked`
        lock = asyncio.Lock()
        state = (lock, None)
        if storage.get(args_key) is None:
            storage[args_key] = state
        async with lock:
            try:
                result = await self.func(obj, *args, **kwargs)
            except Exception:
                self.error_in_count += 1
                # Another process could have generated a valid state,
                # if the previous state was `error`.
                # Thus, don't clean the state that wasn't our own.
                if storage.get(args_key) is state:
                    storage[args_key] = None
                raise

            storage[args_key] = (None, result)

        return result


def aio_locked_memoized(
    *,
    memo_cls: type[AIOLockedMemoized] = AIOLockedMemoized,
    memo_key: str = "memo",
) -> Callable[[Callable[..., Awaitable[TRet]]], Callable[..., Awaitable[TRet]]]:
    def aio_locked_memoized_wrap(func: Callable[..., Awaitable[TRet]]) -> Callable[..., Awaitable[TRet]]:
        memo = memo_cls(func=func)

        async def aio_locked_memoized_wrapped(self: Any, *args: Any, **kwargs: Any) -> TRet:
            return await memo(self, *args, **kwargs)

        setattr(aio_locked_memoized_wrapped, memo_key, memo)
        return aio_locked_memoized_wrapped

    return aio_locked_memoized_wrap
