"""Organize other components to be a chatbot"""

import logging
import time

from typing import List
from threading import RLock

from .configs import Configs
from .response import Response
from .client import Client
from .exceptions import MsgError
from .decoraters import singleton


class Bot:

    def __init__(self, config_path: str):
        Configs().read(config_path)
        self._responses = dict()
        self._lock = RLock()

    def respond(self, msg: dict):
        """To create response based on user input.

        :param msg: dict, user input message which should contain:
            1.user_id - user identifier;
            2.text - what user said;
            3.other information such as customer id, platform, app version, etc.
        """
        for field in ["user_id", "text"]:
            if not str(msg.get(field, "")).strip():
                raise MsgError
        responses = Client(msg).respond()
        with self._lock:
            for response in responses:
                timestamp = int(time.time()) + response.delay
                if timestamp not in self._responses:
                    self._responses[timestamp] = [response]
                else:
                    self._responses[timestamp].append(response)

    def get_responses(self):
        responses = []
        with self._lock:
            for key in [k for k in self._responses if k < int(time.time())]:
                responses += self._responses.pop(key)

        return responses
