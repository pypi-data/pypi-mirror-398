from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Hashable


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class InMemoryTTLCache:
    def __init__(self) -> None:
        self._data: dict[Hashable, CacheEntry] = {}

    def get_if_fresh(self, key: Hashable, now: float) -> tuple[bool, Any]:
        entry = self._data.get(key)
        if entry is None:
            return False, None
        if entry.expires_at <= now:
            self._data.pop(key, None)
            return False, None
        return True, entry.value

    def set(self, key: Hashable, value: Any, expires_at: float) -> None:
        self._data[key] = CacheEntry(value=value, expires_at=expires_at)

    def delete(self, key: Hashable) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()

    def size(self) -> int:
        return len(self._data)
