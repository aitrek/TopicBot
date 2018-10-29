"""Context base class to manage the context information"""

import json

from .dialog import Dialog


class Context:
    """
    Class to manage context information that is not available in parsed data
    of the input text.

    The context data comes from two sources:
    1. Consume input message to create useful data other than the text.
    2. Update dialog to create data from dialog's parsed data.
    """

    def __init__(self, data: dict=None):
        self._data = data if data else {}

    def get(self, key: str):
        """Get context data from self._data"""
        return self._data.get(key)

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

    def consume(self, msg: dict):
        """Consume input message to update context data."""
        raise NotImplementedError

    def update(self, dialog: Dialog):
        """Update context with the Dialog instance of this round of conversation"""
        raise NotImplementedError
