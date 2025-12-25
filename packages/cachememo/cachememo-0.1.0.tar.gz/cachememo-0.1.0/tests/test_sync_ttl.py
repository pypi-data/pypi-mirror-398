from cachememo import memoize


def test_sync_ttl_expires_and_recomputes():
    t = {"now": 0.0}

    def time_fn():
        return t["now"]

    calls = {"n": 0}

    @memoize(ttl=10, time_fn=time_fn)
    def f(x: int) -> int:
        calls["n"] += 1
        return x * 2

    assert f(2) == 4
    assert f(2) == 4
    assert calls["n"] == 1

    t["now"] = 9.999
    assert f(2) == 4
    assert calls["n"] == 1

    t["now"] = 10.0
    assert f(2) == 4
    assert calls["n"] == 2
