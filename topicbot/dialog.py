"""Class to respresent dialog of one loop"""

import logging

from .base import Base
from .response import Response


class Dialog(Base):

    _attrs = [
        "_id",              # str, instance identifier
        "_msg",             # dict, client msg
        "_parsed_data",     # dict, parsed data of msg
        "_domain",          # str, domain of the conversation
        "_intent",          # str, intent of the domain
        "_cases",           # List[str], cases of the intent
        "_response"         # instance, final response to user
    ]

    def __init__(self, msg: dict, context: dict, grounding: dict):
        super().__init__()
        self._msg = msg
        self._context = context
        self._grounding = grounding
        self._domain = None
        self._intent = None
        self._cases = None
        self._response = None
        self._parse()

    @property
    def domain(self):
        return self._domain

    @property
    def intent(self):
        return self._intent

    @property
    def cases(self):
        return self._cases

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, response: Response):
        self._response = response

    @property
    def name(self):
        return self.domain + "." + self.intent if self.intent else self.domain

    def _parse(self):
        raise NotImplementedError