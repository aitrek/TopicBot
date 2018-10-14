"""Organize other components to be a chatbot"""

import logging

from typing import Type

from .configs import Configs
from .response import Response
from .client import Client
from .exceptions import MsgError
from .utils import import_module
from .decoraters import singleton


def _custom_class_client(config_path: str) -> Type[Client]:
    return import_module(
        Configs().read(config_path).get("Bot", "class_client"))


@singleton
class Bot:

    def __init__(self, config_path: str):
        self._class_client = _custom_class_client(config_path)

    def response(self, msg: dict) -> Response:
        """Return response based on user input message.

        :param msg: dict, user input message which should contain:
            1.user_id - user identifier;
            2.text - what user said;
            3.other information such as customer id, platform, app version, etc.
        """
        for field in ["user_id", "text"]:
            if not str(msg.get(field, "")).strip():
                raise MsgError
        return self._class_client(msg).respond()
