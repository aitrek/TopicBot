"""The conversation client according instanced according different users"""

import logging

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


def _custom_class_dialog() -> Type[Dialog]:
    return import_module(Configs().get("Client", "class_dialog"))


def _custom_class_topic() -> Type[Topic]:
    return import_module(Configs().get("Client", "class_topic"))


class Client(Base):

    _attrs = [
        "id",                  # Client instance id
        "previous_topics",     # Topic status list of previous Topic instances
        "context",             # Context of the conversation
        "grounding"            # The conversation grounding
    ]
    _class_dialog = _custom_class_dialog()
    _class_topic = _custom_class_topic()

    def __init__(self, msg: dict):
        super().__init__(msg["user_id"])
        self._previous_topics = None
        self._grounding = None
        self._context = None
        self._restore()
        self._dialog = self._create_dialog(msg)
        self._context.update(self._dialog)
        self._topic = self._create_topic()

    @property
    def previous_topics(self):
        return self._previous_topics

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
    def context(self, context_values: dict):
        self._context = Context(context_values)

    @property
    def grounding(self):
        return self._grounding

    @grounding.setter
    def grounding(self, grounding_values: dict):
        self._grounding = Grounding(grounding_values)

    def __del__(self):
        self._update_previous_topics()

    def _create_context(self) -> dict:
        """Create context which will be helpful for later processes"""
        raise NotImplementedError

    def _create_dialog(self, msg: dict) -> Dialog:
        """Create Dialog instance for this round of conversation

        The grounding will be update in Dialog instance if necessary.
        """
        return self._class_dialog(msg, self._context, self._grounding)

    def _create_topic(self) -> Topic:
        if self._need_change_topic():
            self._grounding.update(self._context)
            return TopicFactory().create_topic(self._dialog.name)
        else:
            last_topic = self._previous_topics.popitem()
            topic_id = last_topic[0]
            topic_name = last_topic[1]["name"]
            return TopicFactory().create_topic(topic_name, topic_id)

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
        responses = self._topic.respond(self._dialog, self._context, self._grounding)
        results = []
        if isinstance(responses, dict):
            results.append(ResponseFactory().create_response(responses))
        elif isinstance(responses, (tuple, list)):
            for res in responses:
                results.append(ResponseFactory().create_response(res))

        return results

    def _restore(self):
        """Restore the historical information to self."""
        cache = self._cache()
        if cache:
            self._previous_topics = OrderedDict(cache.get("previous_topics", []))
            self._grounding = Grounding(cache.get("grounding", {}))
            self._context = Context(cache.get("context", {}))
        else:
            self._previous_topics = OrderedDict()
            self._grounding = Grounding()
            self._context = Context()

    def _update_previous_topics(self):
        if self._topic is not None:
            self._previous_topics[self._topic.id] = self._topic.status()
