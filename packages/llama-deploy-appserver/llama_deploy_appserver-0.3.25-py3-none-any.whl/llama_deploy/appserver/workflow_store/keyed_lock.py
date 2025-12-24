import asyncio
from collections import Counter
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


class AsyncKeyedLock:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._refcnt: Counter[str] = Counter()
        self._registry_lock = asyncio.Lock()  # protects _locks/_refcnt

    @asynccontextmanager
    async def acquire(self, key: str) -> AsyncIterator[None]:
        async with self._registry_lock:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            self._refcnt[key] += 1

        try:
            await lock.acquire()
            try:
                yield
            finally:
                lock.release()
        finally:
            async with self._registry_lock:
                self._refcnt[key] -= 1
                if self._refcnt[key] == 0:
                    self._locks.pop(key, None)
                    del self._refcnt[key]
