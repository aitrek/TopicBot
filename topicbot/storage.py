"""Storage for multi-rounds dialogue data"""

import time
import json

import redis

from threading import RLock


class Storage:
    """Base class for cache storage"""

    def __init__(self, ttl: int=3600):
        self._ttl = ttl
        self._lock = RLock()
        self._store = None

    def __contains__(self, item):
        raise NotImplementedError

    def add(self, key: str, value: dict, ttl: int=None):
        raise NotImplementedError

    def clear(self):
        """Empty the storage"""
        raise NotImplementedError

    def delete(self, key: str):
        raise NotImplementedError

    def expired(self, key: str) -> bool:
        raise NotImplementedError

    def get(self, key: str) -> dict:
        raise NotImplementedError

    def has(self, key: str) -> bool:
        return self.__contains__(key)


class InMemoryStorage(Storage):
    """Memory-based implementation."""

    def __init__(self):
        super().__init__()
        self._store = dict()
        self._expires = dict()

    def __contains__(self, key: str) -> bool:
        return key in self._expires

    def add(self, key: str, value: dict, ttl: int=None):
        if ttl and ttl > 0:
            expire = time.time() + ttl
        else:
            expire = time.time() + self._ttl

        with self._lock:
            self._expires[key] = expire
            self._store[key] = value

    def clear(self):
        with self._lock:
            self._store = dict()
            self._expires = dict()

    def delete(self, key: str):
        with self._lock:
            if key in self._store:
                del self._store[key]
            if key in self._expires:
                del self._expires[key]

    def expired(self, key: str) -> bool:
        try:
            return time.time() > self._expires[key]
        except KeyError:
            return not self.__contains__(key)

    def get(self, key: str) -> dict:
        if time.time() > self._expires[key]:
            self.delete(key)
            raise KeyError
        return self._store[key]


class RedisStorage(Storage):
    """Redis-based implementation"""

    def __init__(self, redis_client: redis.Redis, redis_name: str="TopicChat#"):
        super().__init__()
        self._store = redis_client
        self._expires = dict()
        self._redis_name = redis_name

    def __contains__(self, key: str) -> bool:
        return key in self._expires

    def add(self, key: str, value: dict, ttl: int=None):
        if ttl and ttl > 0:
            expire = time.time() + ttl
        else:
            expire = time.time() + self._ttl

        with self._lock:
            self._expires[key] = expire
        self._store.hset(self._redis_name, self._redis_name + key, value)

    def clear(self):
        with self._lock:
            self._expires = dict()
        self._store.delete(self._redis_name)

    def delete(self, key: str):
        with self._lock:
            if key in self._expires:
                del self._expires[key]
        self._store.hdel(self._redis_name, key)

    def expired(self, key: str) -> bool:
        try:
            return time.time() > self._expires[key]
        except KeyError:
            return not self.__contains__(key)

    def get(self, key: str) -> dict:
        if time.time() > self._expires[key]:
            self.delete(key)
            raise KeyError
        return json.loads(self._store.hget(self._redis_name, key))

