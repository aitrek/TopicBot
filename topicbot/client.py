"""The conversation client according instanced according different users"""

import logging

from typing import Type

from .base import Base
from .dialog import Dialog
from .topic import Topic, TopicFactory
from .response import Response
from .configs import Configs
from .utils import import_module


def _custom_class_dialog() -> Type[Dialog]:
    return import_module(Configs().get("Client", "class_dialog"))


def _custom_class_topic() -> Type[Topic]:
    return import_module(Configs().get("Client", "class_topic"))


class Client(Base):

    _attrs = [
        "_id",                  # Client instance id
        "_previous_topics",     # Topic status list of previous Topic instances
        "_current_topic_id",    # Current Topic instance
        "_grounding"            # The conversation grounding
    ]
    _class_dialog = _custom_class_dialog()
    _class_topic = _custom_class_topic()

    def __init__(self, msg: dict):
        super().__init__(msg["user_id"])
        self._previous_topics = []
        self._grounding = {}
        self._restore()
        self._msg = msg
        self._context = self._create_context()
        self._dialog = self._create_dialog()
        self._topic = self._create_topic()

    def _create_context(self) -> dict:
        """Create context which will be helpful for later processes"""
        raise NotImplementedError

    def _create_dialog(self) -> Dialog:
        """Create Dialog instance for this round of conversation

        The grounding will be update in Dialog instance if necessary.
        """
        return self._class_dialog(self._msg, self._context, self._grounding)

    def _create_topic(self) -> Topic:
        change_code = self._need_change_topic()
        if change_code == 0:    # no need to update previous_topics
            return TopicFactory().create_topic(self._dialog.name)
        elif change_code == 1:
            self._update_previous_topics(self._topic)
            return TopicFactory().create_topic(self._dialog.name)
        else:
            topic_name = self._previous_topics[-1]["name"]
            topic_id = self._previous_topics[-1]["id"]
            return TopicFactory().create_topic(topic_name, topic_id)

    def _need_change_topic(self) -> int:
        """Check if need to change to a new topic

        Processing logic:
        1. True if the current topic is None.
        2. True if the dialog domain changes.
        3. True if the dialog remains unchanged but intent changes.
        4. Otherwise False.

        :return:
            0 - case logic#1
            1 - case logic#2&3
            2 - case logic#4
        """
        # logic 1
        if self._topic is None:
            return 0
        # logic 2&3
        elif self._dialog.name != self._topic.name:
            return 1
        # logic 4
        else:
            return 2

    def _respond(self) -> dict:
        """Respond to user according to msg, context and grounding."""
        return self._topic.respond(self._dialog, self._context, self._grounding)

    def respond(self) -> Response:
        """Convert returned dict from self._respond() to Response instance.

        Notice:
            The final response should be assign to dialog.response before return.
        """
        raise NotImplementedError

    def _restore(self):
        """Restore the historical information to self"""
        cache = self._cache()
        if cache:
            self._previous_topics = cache.get("_previous_topics", [])
            self._grounding = cache.get("_grounding", {})

    def _update_previous_topics(self, topic: Topic):
        if self._topic is not None:
            self._previous_topics.append(topic.status())
