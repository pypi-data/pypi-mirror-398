from concurrent.futures import ThreadPoolExecutor
import time

from cachememo import memoize


def test_sync_stampede_single_flight():
    calls = {"n": 0}

    @memoize(ttl=60)
    def slow(x: int) -> int:
        calls["n"] += 1
        time.sleep(0.05)
        return x * 10

    with ThreadPoolExecutor(max_workers=20) as ex:
        results = list(ex.map(lambda _: slow(2), range(50)))

    assert results == [20] * 50
    assert calls["n"] == 1
