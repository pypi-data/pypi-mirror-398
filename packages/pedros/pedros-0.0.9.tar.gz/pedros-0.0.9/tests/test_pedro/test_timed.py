from time import sleep

import pytest

from pedros.timed import timed


def test_timed_sync():
    @timed
    def func():
        sleep(0.02)
        return True

    assert func()
    elapsed = getattr(func, "__last_elapsed__")
    assert isinstance(elapsed, float)
    assert elapsed >= 0.01


@pytest.mark.asyncio
async def test_timed_async():
    @timed
    async def func():
        sleep(0.02)
        return True

    assert await func()
    elapsed = getattr(func, "__last_elapsed__")
    assert isinstance(elapsed, float)
    assert elapsed >= 0.01

def test_timed_error():
    @timed
    def func():
        sleep(0.02)
        raise ValueError("Intended error raised in test")

    with pytest.raises(ValueError):
        func()

    elapsed = getattr(func, "__last_elapsed__")
    assert isinstance(elapsed, float)
    assert elapsed >= 0.01