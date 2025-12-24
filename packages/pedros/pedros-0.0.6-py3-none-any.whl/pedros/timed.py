from time import perf_counter
from typing import Callable, ParamSpec, TypeVar

from pedros.decorator_factory import CallContext, make_around_decorator
from pedros.logger import get_logger

logger = get_logger()

P = ParamSpec("P")
R = TypeVar("R")


def _before(ctx: CallContext[P, R]) -> None:
    ctx.extra["start_time"] = perf_counter()


def _after(ctx: CallContext[P, R]) -> None:
    start_time = ctx.extra.get("start_time")
    if start_time is None:
        return

    elapsed = perf_counter() - start_time

    setattr(ctx.wrapped, "__last_elapsed__", elapsed)
    logger.info(f"{ctx.wrapped.__name__} took {elapsed} seconds to execute.")


def timed(func: Callable[P, R]) -> Callable[P, R]:
    return make_around_decorator(before=_before, after=_after)(func)
