"""Core component of topic chatbot"""

import logging
import os
import uuid
import inspect
import importlib.util

from abc import abstractclassmethod, abstractmethod
from inspect import isclass
from typing import Dict, Type, List, Tuple, Union

from topicbot.utils import singleton
from .configs import configs
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

    def get(self, key: str):
        """Get the most possible value from self._dialog.
        If no data found, None will be returned."""
        return self._dialog[key]

    @abstractmethod
    def intent_maps(self) -> Dict[str, dict]:
        """Maps from case to intent method.

        According to the case from self.case(), the correct method will
        be selected to generate response of this round of conversation.

        Notice:
            The case in the intent_maps, the key of this dict, should have to
            match the results of self.case().

        Example:
        {
            "intent_label0": {
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
        ...

    @abstractclassmethod
    def _name(cls) -> str:
        ...

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
            responses = []
            for label in self.dialog.intent_labels:
                method_name = self.intent_maps()[label]["method"]
                responses.append(getattr(self, method_name)())

        return responses

    def status(self):
        # todo add other status
        return {
            "name": self.name,
        }


@singleton
class TopicFactory:

    def __init__(self):
        self._topics = self._load_topics()
        self._default_topic = configs.get("Topics", "default_topic")

    @property
    def default_topic_name(self):
        return self._default_topic

    def _get_all_paths(self, path: str) -> List[str]:
        all_paths = [path]
        for f in os.listdir(path):
            sub_path = os.path.join(path, f)
            if os.path.isdir(sub_path):
                all_paths += self._get_all_paths(sub_path)
        return all_paths

    def _load_topics_by_models_folder(self, models_folder: str) -> dict:
        """

        Parameters
        ----------
        models_folder: the folder contains topics of different customers.
            The names of its sub-folder are customers' names.

        Returns
        -------

        """
        topics = {}

        for path in self._get_all_paths(models_folder):

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
                            if topic_name is not None:
                                topics[topic_name] = memb
                        except NotImplementedError:
                            continue

        return topics

    def _load_topics(self) -> Dict[str, Type[Topic]]:
        """Load all topics from topic path written in Configs instance"""
        topics = {}
        try:
            topics = self._load_topics_by_models_folder(
                configs.get("Topics", "topic_path"))
        except FileNotFoundError:
            # todo logging
            pass

        if not topics:
            try:
                topics = self._load_topics_by_models_folder(
                    os.path.join(configs.get("Root", "root_path"),
                                 configs.get("Topics", "topic_path"))
                )
            except FileNotFoundError:
                # todo logging
                pass

        return topics

    def has_topic(self, topic_name: str=""):
        return topic_name in self._topics

    def _get_topic_name(self, intent_label: str) -> str:
        """Get topic name through comparing intent_label and topic names."""
        match = 0
        topic_name = ""
        for name in self._topics:
            score = len(name)
            if intent_label.startswith(name) and score > match:
                topic_name = name
                match = score
        return topic_name

    def create_topic(self, intent_labels: List[str], id: str=None) -> List[Topic]:
        """Create specific sub-Topic instances according to topic names.

        :return: If parameter id is None, a completely empty instance without
            any conversation data will be returned. Otherwise, the returned
            instance will have previous conversation data restored from cache.
        """
        topics = []
        topic_names = [self._get_topic_name(label) for label in intent_labels]
        for name in [n for n in topic_names if n]:
            if name in self._topics:
                topics.append(self._topics[name](id))
        return topics if topics else \
            [self._topics[self.default_topic_name](id)]
