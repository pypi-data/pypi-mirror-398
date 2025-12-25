from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable,  Hashable, Protocol


TimeFn = Callable[[], float]


@dataclass(frozen=True)
class CacheInfo:
    hits: int
    misses: int
    currsize: int

class SupportsCacheClear(Protocol):
    def cache_clear(self) -> None: ...


class SupportsCacheInfo(Protocol):
    def cache_info(self) -> CacheInfo: ...

Key = Hashable
Value = Any