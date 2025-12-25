from __future__ import annotations

import time

from .types import TimeFn


def default_time_fn() -> float:
    return time.monotonic()


def resolve_time_fn(time_fn: TimeFn | None) -> TimeFn:
    return time_fn if time_fn is not None else default_time_fn
