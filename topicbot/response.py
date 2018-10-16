"""Class to handle the output"""

import os
import inspect
import importlib.util

from inspect import isclass

from .configs import Configs
from .decoraters import singleton


class Response:

    protocol = 0

    def __init__(self, data: dict):
        self._data = data

    def export(self) -> dict:
        raise NotImplementedError


@singleton
class ResponseFactory:

    def __init__(self):
        self._responses = self._load_responses()

    def _load_responses(self):
        responses = {}
        path = Configs.get("Responses", "response_path")
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

    def create_response(self, response: dict) -> Response:
        """Create Response instance according to response data.

        :param response: Response data from topic respond method. It should
            have to have keys 'protocal' and 'data'.
            The structure:
            {
                "protocol": int,
                "data": dict
            }
        :return: Response instance
        """
        protocol = response["protocol"]
        data = response["data"]
        return self._responses[protocol](data)


