"""Class for common ground"""

import json

from .context import Context


class Grounding:

    def __init__(self, data: dict=None):
        self._data = data if data else {}

    def __repr__(self):
        return json.dumps(self.values)

    def get(self, key: str):
        """Get grounding data from self._data"""
        return self._data.get(key)

    @property
    def values(self) -> dict:
        return self._data

    def update(self, context: Context):
        """Update grounding with Context instance of previous conversations."""
        raise NotImplementedError
