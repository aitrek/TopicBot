"""Base class for the bot objects"""

import logging
import uuid
import json

from .configs import Configs
from .utils import import_module
from .storage import Storage


def _get_storage() -> Storage:
    configs = Configs()
    return import_module(module_path=configs.get("Base", "storage"),
                         root_path=configs.get("Root", "root_path"))()


class Base:

    _attrs = []
    _storage = None

    def __init__(self, id: str=None):
        if id is None:
            self._id = str(uuid.uuid1())
        else:
            self._id = id
            self._restore()

    def __new__(cls, *args, **kwargs):
        if cls._storage is None:
            cls._storage = _get_storage()
        return super().__new__(cls)

    def __repr__(self):
        return json.dumps(self.values)

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, id: str):
        self._id = id

    @property
    def values(self) -> dict:
        values = dict()
        for attr in self._attrs:
            value = getattr(self, attr)
            if type(value).__repr__ is object.__repr__:
                logging.error("%s.__repr__() is not implemented!" %
                              value.__class__.__name__)
                continue
            values[attr] = value

        return values

    @classmethod
    def instance_by_id(cls, id: str):
        raise NotImplementedError

    @classmethod
    def deserialize(cls, values: dict):
        raise NotImplementedError

    def _cache(self) -> dict:
        """Get data cached in storage"""
        try:
            return self._storage.get(self._id)
        except KeyError:
            return {}

    @classmethod
    def get_cache_by_id(cls, id: str):
        """Get data from storage. Raise KeyError if no data found."""
        return json.loads(cls._storage.get(id))

    def _restore(self):
        """Restore cache data to self instance"""
        cache = self._cache()
        if cache:
            for attr in self._attrs:
                try:
                    setattr(self, attr, cache[attr])
                except Exception:
                    continue

    def save(self):
        self._storage.add(self._id, self.values)

