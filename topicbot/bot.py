"""Organize other components to be a chatbot"""

import logging
import time
import random

from threading import RLock
from collections import OrderedDict

from .configs import Configs
from .base import Base
from .client import Client
from .exceptions import MsgError


_default_silence_threhold = 600             # 10 minutes
_default_silence_threhold_variance = 30     # 30 seconds
_max_clients_num = 1024


class Bot:

    _clients = OrderedDict()
    _silence_threhold = None
    _silence_threhold_variance = None

    def __init__(self, config_path: str):
        Configs().read(config_path)
        self._responses = dict()
        self._lock = RLock()

    def __new__(cls, *args, **kwargs):
        if cls._silence_threhold is None:
            cls._silence_threhold = Configs().get("Bot", "silence_threhold")
            if not cls._silence_threhold:
                cls._silence_threhold = _default_silence_threhold
            else:
                cls._silence_threhold = int(cls._silence_threhold)

        if cls._silence_threhold_variance is None:
            cls._silence_threhold_variance = Configs().get(
                "Bot", "silence_threhold_variance")
            if not cls._silence_threhold_variance:
                cls._silence_threhold_variance = _default_silence_threhold_variance
            else:
                cls._silence_threhold_variance = int(cls._silence_threhold_variance)

        return super().__new__(cls)

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

        client = Client(msg)
        responses = client.respond()
        with self._lock:
            for response in responses:
                timestamp = int(time.time()) + response.delay
                if timestamp not in self._responses:
                    self._responses[timestamp] = [response]
                else:
                    self._responses[timestamp].append(response)

        self._update(client)

    def silence_checking(self):
        """Check if users has been silent for a long time."""
        checks = []
        for user_id, ts in self._clients.items():
            if time.time() - ts > self._silence_threhold - int(
                    random.normalvariate(0, self._silence_threhold_variance)):
                checks.append(user_id)

        with self._lock:
            for user_id in checks:
                del self._clients[user_id]

    def actively_respond(self, user_id: str):
        """Actively response to the silent user."""
        cache = Base.get_cache_by_id(user_id)
        if cache:
            msg = cache.get("msg", {})
            if msg:
                msg["text"] = ""
                msg["is_active"] = True
                self.respond(msg)

    def get_responses(self):
        responses = []
        with self._lock:
            for key in [k for k in self._responses if k < int(time.time())]:
                responses += self._responses.pop(key)

        return responses

    def _update(self, client: Client):
        with self._lock:
            while len(self._clients) > _max_clients_num:
                self._clients.popitem(last=True)
            self._clients[client.id] = client.status().get("timestamp",
                                                           int(time.time()))

