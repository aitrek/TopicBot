"""Organize other components to be a chatbot"""

import logging
import time
import random

from threading import RLock
from collections import OrderedDict
from typing import Dict

from .configs import Configs
from .base import Base
from .client import Client
from .exceptions import MsgError


_default_silence_threhold = 600
_default_silence_threhold_variance = 30
_default_max_clients_num = 1024     # maximum clients to track


class Bot:

    _clients = OrderedDict()
    _silence_threhold = None
    _silence_threhold_variance = None
    _max_clients_num = None
    _responses = dict()

    def __init__(self, config_path: str):
        self._lock = RLock()

    def __new__(cls, *args, **kwargs):
        if not Configs().has_loaded:
            Configs().read(args[0])

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

        if cls._max_clients_num is None:
            cls._max_clients_num = Configs().get("Bot", "max_clients_num")
            if not cls._max_clients_num:
                cls._max_clients_num = _default_max_clients_num
            else:
                cls._max_clients_num = int(cls._max_clients_num)

        return super().__new__(cls)

    def respond(self, msg: dict):
        """To create response based on user input.

        :param msg: dict, user input message which should contain:
            1.user_id - user identifier;
            2.text - what user said;
            3.other information such as customer id, platform, app version, etc.
        """
        for field in ["user_id"]:
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
        client.save()

    def initiative_response_checking(self) -> Dict[str, int]:
        """Check if users need to be responded to initiatively.

        The results is a list of dict with user_id as key and corresponding
        initiative response code as value, like:
        {
            "user_id0": code0,
            ...
        }

        Response code:
        0 - silence
        """
        checks = {}
        for method in self._initiative_response_checking_methods():
            checks.update(method())
        return checks

    def _initiative_response_checking_methods(self):
        """Return intiative response checking methods."""
        # other initiative response checking methods
        # could be added in the returned list.
        return [self._silence_checking]

    def _silence_checking(self) -> Dict[str, int]:
        """Check if users have been silent for a long time."""
        checks = {}
        for user_id, ts in self._clients.items():
            if time.time() - ts > self._silence_threhold - int(
                    random.normalvariate(0, self._silence_threhold_variance)):
                checks[user_id] = 0

        with self._lock:
            for user_id in checks:
                del self._clients[user_id]

        return checks

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
            while len(self._clients) > self._max_clients_num:
                self._clients.popitem(last=True)
            self._clients[client.id] = client.state().get("timestamp",
                                                           int(time.time()))

