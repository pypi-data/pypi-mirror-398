import pytest
from cachememo import memoize


def test_sync_exceptions_not_cached():
    calls = {"n": 0}

    @memoize(ttl=60)
    def boom(x: int) -> int:
        calls["n"] += 1
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError):
        boom(1)
    with pytest.raises(RuntimeError):
        boom(1)

    assert calls["n"] == 2
