"""Base class for the bot objects"""

import logging
import uuid
import json

from .configs import Configs
from .utils import import_module


class Base:

    _attrs = []
    _storage = import_module(Configs().get("Base", "storage"))()

    def __init__(self, id: str=None):
        self._id = id if id else str(uuid.uuid1())

    def __repr__(self):
        return json.dumps(self.values)

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
    def instanced_by_id(cls, id: str):
        raise NotImplementedError

    @classmethod
    def deserialize(cls, values: dict):
        raise NotImplementedError

    def _cache(self) -> dict:
        """Get data cached in storage"""
        try:
            return json.loads(self._storage.get(self._id))
        except KeyError:
            return {}

    def _restore(self):
        """Restore cache data to self instance"""
        raise NotImplementedError

    def save(self):
        self._storage.add(self._id, self.values)

