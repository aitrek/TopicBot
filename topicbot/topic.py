"""Core component of topic chatbot"""

import logging
import os
import uuid
import inspect
import importlib.util

from inspect import isclass
from typing import Dict, Type, List

from .decoraters import singleton
from .configs import Configs
from .dialog import Dialog
from .response import Response


class Topic:

    def __init__(self, id: str=None):
        self._id = id if id else str(uuid.uuid1())
        self.dialog = None
        self.conext = {}
        self.grounding = {}

    @property
    def id(self):
        return self._id

    @classmethod
    def domain(cls) -> str:
        raise NotImplementedError

    @classmethod
    def intent(cls) -> str:
        raise NotImplementedError

    def case(self, dialog_cases: List[str]) -> str:
        """Calculate topic case with dialog cases."""
        raise NotImplementedError

    def case_maps(self) -> Dict[str, dict]:
        """Maps from case to intent method.

        According to the case from self.case(), the correct method will
        be selected to generate response of this round of conversation.

        Notice:
            The case in the case_maps, the key of this dict, should have to
            match the results of self.case().

        Example:
        {
            "case0": {
                "desc": "xxx",
                "method": "_response_case0",
                "params": [
                    {"param": "param1", "meaning": "the name of xxx"},
                    {"param": "param2", "meaning": "the name of xxx"},
                ],
            },
            ...
        }
        """
        raise NotImplementedError

    @classmethod
    def _name(cls) -> str:
        return cls.domain() + "." + cls.intent() if cls.intent() else cls.domain()

    @property
    def name(self) -> str:
        return self._name()

    def _respond_param_missing(self) -> Response:
        """Respond if some param miss. If no param miss,
        just return empty dict."""
        # todo
        return {}

    def respond(self, dialog: Dialog, context: dict, grounding: dict) -> Response:
        """Respond to user input"""
        self.dialog = dialog
        self.conext = context
        self.grounding = grounding

        # check params
        res_param_missing = self._respond_param_missing()
        if res_param_missing:
            return res_param_missing

        method_name = self.case_maps()[self.case(dialog.cases)]["method"]
        return getattr(self, method_name)()

    def status(self):
        # todo add other status
        return {
            "domain": self.domain(),
            "intent": self.intent(),
            "name": self.name,
        }


@singleton
class TopicFactory:

    def __init__(self):
        self._topics = self._load_topics()

    def _load_topics(self) -> Dict[str, Type[Topic]]:
        """Load all topics from topic path written in Configs instance"""
        topics = {}
        path = Configs().get("Topics", "topic_path")
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
                    if isclass(memb) and issubclass(memb, Topic):
                        try:
                            topic_name = memb._name()
                            topics[topic_name] = memb
                        except NotImplementedError:
                            continue

        return topics

    def create_topic(self, topic_name: str="others", id: str=None) -> Topic:
        """Create specific sub-Topic instance according to topic name.

        :return: If parameter id is None, a completely empty instance without
            any conversation data will be returned. Otherwise, the returned
            instance will have previous conversation data restored from cache.
        """
        return self._topics.get(topic_name, "others")(id)
