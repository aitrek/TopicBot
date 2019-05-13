"""Organize other components to be a chatbot"""

import logging
import time
import random

from threading import RLock
from collections import OrderedDict
from typing import Dict, List

from .configs import configs
from .base import Base
from .client import Client
from .exceptions import MsgError


_default_silence_threhold = 180
_default_silence_threhold_variance = 5
_default_max_clients_num = 1024     # maximum clients to track


class Bot:

    _clients = {}
    _silence_threhold = None
    _silence_threhold_variance = None
    _max_clients_num = None
    _responses = dict()

    def __init__(self, configs_path: str, ner, intent_classifiers: dict):
        """

        Parameters
        ----------
        configs_path: absolute path of the config file.
        """
        self._lock = RLock()
        self._ner = ner
        self._intent_classifiers = intent_classifiers

    def __new__(cls, *args, **kwargs):
        if not configs.has_loaded():
            configs.read(kwargs["configs_path"])

        if cls._silence_threhold is None:
            cls._silence_threhold = configs.get("Bot", "silence_threhold")
            if not cls._silence_threhold:
                cls._silence_threhold = _default_silence_threhold
            else:
                cls._silence_threhold = int(cls._silence_threhold)

        if cls._silence_threhold_variance is None:
            cls._silence_threhold_variance = configs.get(
                "Bot", "silence_threhold_variance")
            if not cls._silence_threhold_variance:
                cls._silence_threhold_variance = \
                    _default_silence_threhold_variance
            else:
                cls._silence_threhold_variance = \
                    int(cls._silence_threhold_variance)

        if cls._max_clients_num is None:
            cls._max_clients_num = configs.get("Bot", "max_clients_num")
            if not cls._max_clients_num:
                cls._max_clients_num = _default_max_clients_num
            else:
                cls._max_clients_num = int(cls._max_clients_num)

        return super().__new__(cls)

    def respond(self, msg: dict):
        """To create response based on user input.

        :param msg: dict, user input message which should contain:
            1.user - user identifier;
            2.text - what user said;
            3.other information such as customer id, platform, app version, etc.
        """
        for field in ["user"]:
            if not str(msg.get(field, "")).strip():
                raise MsgError

        customer = msg.get("customer", "common")

        client = Client(msg, self._ner, self._intent_classifiers[customer])
        with self._lock:
            for response in client.respond():
                timestamp = int(time.time()) + response.delay
                if timestamp not in self._responses:
                    self._responses[timestamp] = [response]
                else:
                    self._responses[timestamp].append(response)

        self._update(client)
        client.save()

    def initiative_response_checking(self) -> List[str]:
        """
        Check if users need to be responded to initiatively and return
        these users.
        """
        checks = []
        for method in self._initiative_response_checking_methods():
            checks += method()
        return checks

    def _initiative_response_checking_methods(self):
        """Return initiative response checking methods."""
        # other initiative response checking methods
        # could be added in the returned list.
        return [self._silence_users]

    def _silence_users(self) -> List[str]:
        """Find users have been silent for a long time."""
        users = []
        for user, data in self._clients.items():
            initiative = data.get("initiative", True)
            if initiative:
                ts = data.get("ts", 0)
                if time.time() - ts > self._silence_threhold - int(
                        random.normalvariate(
                            0, self._silence_threhold_variance)):
                    users.append(user)

        with self._lock:
            for user in users:
                self._clients[user]["ts"] = int(time.time())
                self._clients[user]["initiative"] = False

        return users

    def actively_respond(self, user: str):
        """
        Actively response to the silent user.

        :param user:
        :param initiative_code:
        0 - silence
        """
        # get the cached msg format
        cache = Base.get_cache_by_id(user)
        if cache:
            msg = cache.get("msg", {})
            if msg:
                msg["text"] = ""
                msg["initiative"] = True
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
                users = [(user, self._clients[user].get("ts", 0))
                         for user in self._clients]
                users = sorted(users, key=lambda x: x[1], reverse=True)
                del_users = [data[0] for data in users][self._max_clients_num:]
                with self._lock:
                    for user in del_users:
                        del self._clients[user]

            user = client.id
            if user not in self._clients:
                self._clients[user] = {"ts": int(time.time()),
                                       "initiative": True}
            else:
                self._clients[client.id]["ts"] = client.state().get(
                    "timestamp", int(time.time()))
