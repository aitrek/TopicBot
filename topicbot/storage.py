"""Storage for cache"""

import redis

from collections import OrderedDict
from threading import RLock


class Storage:
    """Base class for cache storage"""
    def __init__(self):
        self._lock = RLock()
        self._store = None

    def __contains__(self, item):
        raise NotImplementedError

    def add(self, key: str, value: dict):
        with self._lock:
            try:
                self._add(key, value)
            except:
                pass

    def _add(self, key: str, value: dict):
        raise NotImplementedError

    def get(self, key: str) -> dict:
        try:
            value = self._get(key)
        except:
            value = {}
        return value

    def _get(self, key: str) -> dict:
        raise NotImplementedError

    def delete(self, key: str):
        with self._lock:
            try:
                self._delete(key)
            except:
                pass

    def _delete(self, key: str):
        raise NotImplementedError

    def size(self) -> int:
        """Get quantity of the cache data."""
        raise NotImplementedError


class InMemoryStorage(Storage):
    """Memory-based implementation."""
    def __init__(self):
        super().__init__()
        self._store = OrderedDict()

    def __contains__(self, item: str) -> bool:
        return item in self._store

    def __len__(self):
        return len(self._store)

    def _add(self, key: str, value: dict):
        with self._lock:
            if key not in self._store:
                self._store[key] = value
            else:
                self._store[key] = value
                self._store.move_to_end(key)

    def _get(self, key: str) -> dict:
        return self._store[key]

    def _delete(self, key: str):
        del self._store[key]

    def has(self, key: str) -> bool:
        return self.__contains__(key)

    def size(self) -> int:
        return len(self._store)


class RedisStorage(Storage):
    """Redis-based implementation"""
    def __init__(self, redis_client: redis.Redis):
        super().__init__()
        self._store = redis_client

    def _add(self, key: str, value: dict):
        # todo
        pass

    def _get(self, key: str) -> dict:
        # todo
        pass

    def _delete(self, key: str):
        # todo
        pass

