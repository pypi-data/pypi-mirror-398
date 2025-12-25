from __future__ import annotations

import asyncio
import inspect
import threading
from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec, cast

from .cache import InMemoryTTLCache
from .clocks import resolve_time_fn
from .keys import make_key
from .locks import KeyedLockManagerAsync, KeyedLockManagerSync
from .types import CacheInfo, TimeFn

P = ParamSpec("P")
R = TypeVar("R")


def memoize(
    *,
    ttl: float,
    typed: bool = False,
    time_fn: TimeFn | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    if ttl <= 0:
        raise ValueError("ttl must be > 0")

    tf = resolve_time_fn(time_fn)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        if inspect.iscoroutinefunction(func):
            wrapped = _wrap_async(cast(Callable[P, Any], func), ttl=ttl, typed=typed, time_fn=tf)
            return cast(Callable[P, R], wrapped)
        else:
            wrapped = _wrap_sync(func, ttl=ttl, typed=typed, time_fn=tf)
            return wrapped

    return decorator


def _wrap_sync(func: Callable[P, R], *, ttl: float, typed: bool, time_fn: TimeFn) -> Callable[P, R]:
    cache = InMemoryTTLCache()
    locks = KeyedLockManagerSync()
    hits = 0
    misses = 0
    stats_guard = threading.Lock()

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        nonlocal hits, misses
        key = make_key(args, kwargs, typed)
        now = time_fn()

        ok, value = cache.get_if_fresh(key, now)
        if ok:
            with stats_guard:
                hits += 1
            return cast(R, value)

        lock = locks.lock_for(key)
        with lock:
            now2 = time_fn()
            ok2, value2 = cache.get_if_fresh(key, now2)
            if ok2:
                with stats_guard:
                    hits += 1
                return cast(R, value2)

            with stats_guard:
                misses += 1

            result = func(*args, **kwargs)
            cache.set(key, result, expires_at=now2 + ttl)
            return result

    def cache_clear() -> None:
        nonlocal hits, misses
        cache.clear()
        with stats_guard:
            hits = 0
            misses = 0

    def cache_info() -> CacheInfo:
        with stats_guard:
            return CacheInfo(hits=hits, misses=misses, currsize=cache.size())

    wrapper.cache_clear = cache_clear
    wrapper.cache_info = cache_info
    return wrapper


def _wrap_async(func: Callable[P, Any], *, ttl: float, typed: bool, time_fn: TimeFn) -> Callable[P, Any]:
    cache = InMemoryTTLCache()
    locks = KeyedLockManagerAsync()
    hits = 0
    misses = 0
    stats_guard = asyncio.Lock()

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
        nonlocal hits, misses
        key = make_key(args, kwargs, typed)
        now = time_fn()

        ok, value = cache.get_if_fresh(key, now)
        if ok:
            async with stats_guard:
                hits += 1
            return value

        lock = await locks.lock_for(key)
        async with lock:
            now2 = time_fn()
            ok2, value2 = cache.get_if_fresh(key, now2)
            if ok2:
                async with stats_guard:
                    hits += 1
                return value2

            async with stats_guard:
                misses += 1

            result = await func(*args, **kwargs)
            cache.set(key, result, expires_at=now2 + ttl)
            return result

    def cache_clear() -> None:
        nonlocal hits, misses
        cache.clear()
        hits = 0
        misses = 0

    def cache_info() -> CacheInfo:
        return CacheInfo(hits=hits, misses=misses, currsize=cache.size())

    wrapper.cache_clear = cache_clear
    wrapper.cache_info = cache_info
    return wrapper
