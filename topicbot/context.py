"""Context base class to manage the context information"""

import json


class Context:

    def __init__(self):
        pass

    def __repr__(self) -> str:
        return json.dumps(self.values)

    @property
    def values(self) -> dict:
        return self.__dict__

    def to_features(self) -> dict:
        """Extract extended features from the context data"""
        raise NotImplementedError
