"""Context base class to manage the context information"""

import json

from .dialog import Dialog


class Context:

    def __init__(self, data: dict=None):
        self._data = data if data else {}

    @property
    def values(self) -> dict:
        return self._data

    def __repr__(self) -> str:
        return json.dumps(self.values)

    @classmethod
    def create_instance_from_msg(cls, msg: dict):
        """Create instance with original message from user input."""
        raise NotImplementedError

    def to_features(self) -> dict:
        """Extract extended features from the context data"""
        raise NotImplementedError

    def update(self, dialog: Dialog):
        """Update context with the Dialog instance of this round of conversation"""
        raise NotImplementedError
