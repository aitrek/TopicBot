"""Context base class to manage the context information"""

import json


class Context:

    def __init__(self, msg: dict):
        self._user_id = str(msg["user_id"]).strip()
        self._text = msg["text"].strip()
        self._context_data = self._create_context(msg)

    @property
    def values(self) -> dict:
        return self.__dict__

    def __repr__(self) -> str:
        return json.dumps(self.values)

    def _create_context(self, msg: dict):
        raise NotImplementedError

    def to_features(self) -> dict:
        """Extract extended features from the context data"""
        raise NotImplementedError
