"""Core component of topic chatbot"""

import logging
import os
import uuid
import inspect
import importlib.util

from inspect import isclass
from typing import Dict, Type, List, Tuple, Union

from .decoraters import singleton
from .configs import Configs
from .dialog import Dialog


class Topic:

    def __init__(self, id: str=None):
        self._id = id if id else str(uuid.uuid1())
        self._dialog = None

    @property
    def id(self):
        return self._id

    @property
    def dialog(self) -> Dialog:
        return self._dialog

    @classmethod
    def domain(cls) -> str:
        raise NotImplementedError

    @classmethod
    def intent(cls) -> str:
        raise NotImplementedError

    def case(self, dialog_cases: List[str]) -> str:
        """Calculate topic case with dialog cases."""
        raise NotImplementedError

    def get(self, key: str):
        """Get the most possible value from self._dialog.
        If no data found, None will be returned."""
        return self._dialog[key]

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

    def _respond_param_missing(self) -> Union[dict, List[dict], Tuple[dict]]:
        """Return Response instance if some param miss, or None if no param missing."""
        raise NotImplementedError

    def respond(self, dialog: Dialog, **kwargs) -> Union[dict, List[dict], Tuple[dict]]:
        """Respond to user input"""
        self._dialog = dialog
        # check params
        res_param_missing = self._respond_param_missing()
        if res_param_missing:
            responses = res_param_missing
        else:
            method_name = self.case_maps()[self.case(self.dialog.cases)]["method"]
            responses = getattr(self, method_name)()

        return responses

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
        self._default_topic = Configs().get("Topics", "default_topic")

    @property
    def default_topic_name(self):
        return ".".join(self._default_topic.split(".")[:2])

    @property
    def default_topic_cases(self):
        return [self._default_topic.split(".")[-1]]

    def _get_all_paths(self, path: str) -> List[str]:
        all_paths = [path]
        for f in os.listdir(path):
            sub_path = os.path.join(path, f)
            if os.path.isdir(sub_path):
                all_paths += self._get_all_paths(sub_path)
        return all_paths

    def _load_topics_by_top_folder(self, top_folder: str) -> dict:
        topics = {}
        for path in self._get_all_paths(top_folder):
            for f in os.listdir(path):

                if not f.endswith(".py"):
                    continue

                sub_path = os.path.join(path, f)

                module_spec = importlib.util.spec_from_file_location(f, sub_path)
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

    def _load_topics(self) -> Dict[str, Type[Topic]]:
        """Load all topics from topic path written in Configs instance"""
        topics = {}
        try:
            topics = self._load_topics_by_top_folder(
                Configs().get("Topics", "topic_path"))
        except FileNotFoundError:
            # todo logging
            pass

        if not topics:
            try:
                topics = self._load_topics_by_top_folder(
                    os.path.join(Configs().get("Root", "root_path"),
                                 Configs().get("Topics", "topic_path"))
                )
            except FileNotFoundError:
                # todo logging
                pass

        return topics

    def has_topic(self, topic_name: str=""):
        return topic_name in self._topics

    def create_topic(self, topic_name: str="others", id: str=None) -> Topic:
        """Create specific sub-Topic instance according to topic name.

        :return: If parameter id is None, a completely empty instance without
            any conversation data will be returned. Otherwise, the returned
            instance will have previous conversation data restored from cache.
        """
        return self._topics.get(topic_name,
                                self._topics[self.default_topic_name])(id)
