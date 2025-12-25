from __future__ import annotations

import asyncio
import threading
from typing import Hashable


class KeyedLockManagerSync:
    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._locks: dict[Hashable, threading.Lock] = {}

    def lock_for(self, key: Hashable) -> threading.Lock:
        with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._locks[key] = lock
            return lock


class KeyedLockManagerAsync:
    def __init__(self) -> None:
        self._guard = asyncio.Lock()
        self._locks: dict[Hashable, asyncio.Lock] = {}

    async def lock_for(self, key: Hashable) -> asyncio.Lock:
        async with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            return lock
