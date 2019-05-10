"""Class to handle the output"""

import os
import json
import random
import inspect
import importlib.util

from inspect import isclass

from .configs import configs
from topicbot.utils import singleton


class Response:

    protocol = 0    # need to reset a new value in sub-class

    def __init__(self, response_data: dict, msg_data: dict):
        """
        :param response_data: Response data from topic, which include the final
            reply to user.
        :param msg_data: The original data from input message, offering additional
            information, such as platform, version, etc.
        """
        self._output = response_data.get("output", {})
        self._raw_data = response_data.get("raw_data", {})
        if response_data.get("no_delay", False):
            self._delay = 0
        else:
            delay = response_data.get("delay")
            if not delay:
                msg = response_data.get("output", {}).get("msg", "")
                if not msg:
                    delay = 0
                else:
                    delay_per_word = configs.get("Responses", "delay_per_word")
                    delay_ratio = configs.get("Responses", "dealy_ration")
                    delay = random.normalvariate(len(msg) * delay_per_word,
                                                 delay_ratio)
            self._delay = delay
        self._msg_data = msg_data

    def __repr__(self):
        return json.dumps(
            {
                "protocol": self.protocol,
                "output": self._output,
                "raw_data": self._raw_data,
                "delay": self._delay,
                "msg_data": self._msg_data
            }
        )

    @property
    def delay(self) -> float:
        """Make it possible for Bot instance to control the time
        to send out the response"""
        return self._delay

    def template(self) -> dict:
        """A empty response values to be filled with real data
        to create a response values."""
        raise NotImplementedError

    def values(self) -> dict:
        raise NotImplementedError


@singleton
class ResponseFactory:

    def __init__(self):
        self._responses = None

    def _load_responses(self):
        responses = {}
        path = configs.get("Responses", "response_path")
        if os.path.isdir(path):
            for f in os.listdir(path):

                if not f.endswith(".py"):
                    continue

                module_spec = importlib.util.spec_from_file_location(
                    f, os.path.join(path, f))
                module = importlib.util.module_from_spec(module_spec)
                module_spec.loader.exec_module(module)

                for attr, _ in inspect.getmembers(module):
                    memb = getattr(module, attr)
                    if isclass(memb) and issubclass(memb, Response):
                        try:
                            responses[memb.protocol] = memb
                        except NotImplementedError:
                            continue
        return responses

    def create_response(self, response_data: dict, additional_msg: dict) -> Response:
        """Create Response instance according to response data and response msg.

        :param response_data: Response data from topic respond method. It should
            have to have keys 'protocal' and 'data'.
            The structure:
            {
                "protocol": int,
                "output": dict,
                "raw_data": dict
            }
        :param additional_msg: Message from dialog including original message
            from user input and some information of dialog.
        :return: Response instance
        """
        protocol = response_data["protocol"]
        if self._responses is None:
            self._responses = self._load_responses()
        return self._responses[protocol](response_data, additional_msg)


response_factory = ResponseFactory()
