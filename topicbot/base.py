"""Base class for the bot objects"""

import logging
import uuid
import json

from .configs import Configs
from .utils import import_module


class Base:

    _attrs = []

    def __init__(self, id: str=None):
        self._id = id if id else str(uuid.uuid1())
        self._storage = import_module(Configs().get("modules", "base_storage"))

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

    def _save(self):
        self._storage.add(self._id, self.values)

