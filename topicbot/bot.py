"""Organize other components to be a chatbot"""

import logging

from typing import List

from .configs import Configs
from .response import Response
from .client import Client
from .exceptions import MsgError
from .decoraters import singleton


@singleton
class Bot:

    def __init__(self, config_path: str):
        Configs().read(config_path)

    def respond(self, msg: dict) -> List[Response]:
        """Return response based on user input message.

        :param msg: dict, user input message which should contain:
            1.user_id - user identifier;
            2.text - what user said;
            3.other information such as customer id, platform, app version, etc.
        """
        for field in ["user_id", "text"]:
            if not str(msg.get(field, "")).strip():
                raise MsgError
        return Client(msg).respond()
