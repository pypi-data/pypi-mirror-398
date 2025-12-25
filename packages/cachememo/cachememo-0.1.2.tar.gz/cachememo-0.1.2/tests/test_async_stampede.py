import asyncio
import pytest

from cachememo import memoize


@pytest.mark.asyncio
async def test_async_stampede_single_flight():
    calls = {"n": 0}

    @memoize(ttl=60)
    async def slow(x: int) -> int:
        calls["n"] += 1
        await asyncio.sleep(0.05)
        return x * 10

    results = await asyncio.gather(*[slow(2) for _ in range(50)])

    assert results == [20] * 50
    assert calls["n"] == 1
