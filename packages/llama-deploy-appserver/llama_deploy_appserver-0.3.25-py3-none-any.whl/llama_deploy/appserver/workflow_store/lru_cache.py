from collections import OrderedDict
from collections.abc import Iterator
from typing import Generic, TypeVar, overload

K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    def __init__(self, maxsize: int = 128):
        self.maxsize = maxsize
        self._store: OrderedDict[K, V] = OrderedDict()

    @overload
    def get(self, key: K) -> V | None: ...

    @overload
    def get(self, key: K, default: V) -> V: ...

    def get(self, key: K, default: V | None = None) -> V | None:
        if key not in self._store:
            return default
        return self[key]

    def set(self, key: K, value: V) -> None:
        if key in self._store:
            # remove old so we can push to end
            self._store.pop(key)
        elif len(self._store) >= self.maxsize:
            # evict least recently used (first item)
            self._store.popitem(last=False)
        self._store[key] = value

    def __contains__(self, key: K) -> bool:
        return key in self._store

    def __getitem__(self, key: K) -> V:
        # mark as recently used
        if key not in self._store:
            raise KeyError(key)
        value = self._store.pop(key)
        self._store[key] = value
        return value

    def __setitem__(self, key: K, value: V) -> None:
        self.set(key, value)

    def __len__(self) -> int:
        return len(self._store)

    def __iter__(self) -> Iterator[K]:
        return iter(self._store)
