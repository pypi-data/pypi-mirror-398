from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, Awaitable, Callable, Generic, ParamSpec, TypeVar, cast

import wrapt

P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class CallContext(Generic[P, R]):
    wrapped: Callable[P, R]
    instance: Any | None
    args: P.args
    kwargs: P.kwargs
    result: R | Awaitable[R] | None = None
    error: BaseException | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def set_result(self, value: R | Awaitable[R]) -> None:
        self.result = value

    def set_error(self, err: BaseException) -> None:
        self.error = err


BeforeHook = Callable[[CallContext[P, R]], None]
AfterHook = Callable[[CallContext[P, R]], None]


class _HookContext(Generic[P, R]):
    def __init__(
        self,
        ctx: CallContext[P, R],
        before: BeforeHook[P, R] | None,
        after: AfterHook[P, R] | None,
    ) -> None:
        self._ctx = ctx
        self._before = before
        self._after = after

    def __enter__(self) -> None:
        if self._before is not None:
            self._before(self._ctx)
        return None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None:
        if exc is not None:
            self._ctx.set_error(exc)

        if self._after is not None:
            self._after(self._ctx)

        return None


def make_around_decorator(
    *,
    before: BeforeHook[P, R] | None = None,
    after: AfterHook[P, R] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:

    @wrapt.decorator
    def _wrapper(
        wrapped: Callable[P, R],
        instance: Any | None,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> R | Awaitable[R]:
        ctx: CallContext[P, R] = CallContext(
            wrapped=cast(Callable[P, R], wrapped),
            instance=instance,
            args=cast(P.args, args),
            kwargs=cast(P.kwargs, kwargs),
        )

        is_async = inspect.iscoroutinefunction(wrapped)

        if not is_async:
            with _HookContext(ctx, before, after):
                value = wrapped(*args, **kwargs)
                ctx.set_result(cast(R, value))
                return cast(R, value)

        async def _run_async() -> R:
            with _HookContext(ctx, before, after):
                wrapped_async = cast(Callable[..., Awaitable[R]], wrapped)
                value = await wrapped_async(*args, **kwargs)
                ctx.set_result(cast(R, value))
                return cast(R, value)

        coro = _run_async()
        ctx.set_result(coro)
        return coro

    return cast(Callable[[Callable[P, R]], Callable[P, R]], _wrapper)
