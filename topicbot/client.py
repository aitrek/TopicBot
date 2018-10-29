"""The conversation client according instanced according different users"""

import logging
import time

from typing import Type, List
from collections import OrderedDict

from .base import Base
from .dialog import Dialog
from .topic import Topic, TopicFactory
from .response import Response, ResponseFactory
from .configs import Configs
from .utils import import_module
from .grounding import Grounding
from .context import Context

_configs = Configs()


def _custom_class_dialog() -> Type[Dialog]:
    return import_module(module_path=_configs.get("Client", "class_dialog"),
                         root_path=_configs.get("Root", "root_path"))


def _custom_class_context() -> Type[Context]:
    return import_module(module_path=_configs.get("Client", "class_context"),
                         root_path=_configs.get("Root", "root_path"))


def _custom_class_grounding() -> Type[Grounding]:
    return import_module(module_path=_configs.get("Client", "class_grounding"),
                         root_path=_configs.get("Root", "root_path"))


class Client(Base):

    _attrs = [
        "id",                  # Client instance id
        "previous_topics",     # Topic status list of previous Topic instances
        "context",             # Context of the conversation
        "grounding"            # The conversation grounding
    ]
    _class_dialog = None
    _class_context = None
    _class_grounding = None

    def __init__(self, msg: dict):
        super().__init__(msg["user_id"])
        self._previous_topics = None
        self._grounding = None
        self._context = None
        self._topic = None
        self._restore()
        self._dialog = None
        self._update(msg)

    def __new__(cls, *args, **kwargs):
        if cls._class_dialog is None:
            cls._class_dialog = _custom_class_dialog()
        if cls._class_context is None:
            cls._class_context = _custom_class_context()
        if cls._class_grounding is None:
            cls._class_grounding = _custom_class_grounding()
        return super().__new__(cls)

    def __del__(self):
        self._update_previous_topics()

    @property
    def previous_topics(self) -> list:
        """Return listified OrderdDict items"""
        return list(self._previous_topics.items())

    @previous_topics.setter
    def previous_topics(self, items: list):
        """
        :param items: listified OrderdDict items
        """
        self._previous_topics = OrderedDict(items)

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, context_values: dict=None):
        self._context = self._class_context(context_values)

    @property
    def grounding(self):
        return self._grounding

    @grounding.setter
    def grounding(self, grounding_values: dict):
        self._grounding = self._class_grounding(grounding_values)

    def _need_change_topic(self) -> bool:
        """Check if need to change to a new topic

        Processing logic:
        1. True if the current topic is None.
        2. True if the dialog domain changes.
        3. True if the dialog remains unchanged but intent changes.
        4. Otherwise False.
        """
        def last_topic_name(previous_topics: OrderedDict) -> str:
            if not previous_topics:
                return ""
            last_id = list(previous_topics.keys())[-1]
            return previous_topics[last_id]["name"]

        if self._topic is None:
            return True
        elif self._dialog.name != last_topic_name(self._previous_topics):
            return True
        else:
            return False

    def respond(self) -> List[Response]:
        """Respond to user according to msg, context and grounding."""
        results = []
        msg_data = self._dialog.response_msg_data
        responses = self._topic.respond(self._dialog)

        if isinstance(responses, dict):
            results.append(
                ResponseFactory().create_response(responses, msg_data)
            )
        elif isinstance(responses, (tuple, list)):
            for res in responses:
                results.append(
                    ResponseFactory().create_response(res, msg_data)
                )
        else:
            # todo logging
            pass

        return results

    def status(self) -> dict:
        """Status of this Client instance"""
        # todo add other status
        return {
            "user_id": self.id,
            "timestamp": time.time()
        }

    def _update_previous_topics(self):
        if self._topic is not None:
            self._previous_topics[self._topic.id] = self._topic.status()

    def _update(self, msg: dict):
        """
        Update client data(dialog, context, grounding, previous_topics)
        with input message from user.
        """
        if self._previous_topics is None:
            self._previous_topics = OrderedDict()

        if self._context is None:
            self._context = self._class_context.create_instance_from_msg(msg)
        else:
            self._context.consume(msg)

        if self._grounding is None:
            self._grounding = self._class_grounding()

        self._dialog = self._class_dialog(msg, self.context, self.grounding)

        if self._need_change_topic():
            self._grounding.update(self._context)
            self._context.update(self._dialog)
            self._topic = TopicFactory().create_topic(self._dialog.name)
        else:
            self._context.update(self._dialog)
            last_topic = self._previous_topics.popitem()
            topic_id = last_topic[0]
            topic_name = last_topic[1]["name"]
            self._topic = TopicFactory().create_topic(topic_name, topic_id)
