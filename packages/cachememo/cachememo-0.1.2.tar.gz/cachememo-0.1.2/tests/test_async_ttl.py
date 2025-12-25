import pytest
from cachememo import memoize


@pytest.mark.asyncio
async def test_async_ttl_expires_and_recomputes():
    t = {"now": 0.0}

    def time_fn():
        return t["now"]

    calls = {"n": 0}

    @memoize(ttl=5, time_fn=time_fn)
    async def f(x: int) -> int:
        calls["n"] += 1
        return x + 1

    assert await f(1) == 2
    assert await f(1) == 2
    assert calls["n"] == 1

    t["now"] = 5.0
    assert await f(1) == 2
    assert calls["n"] == 2
