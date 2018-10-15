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
        self._previous_topics = None
        self._current_topic = None
        self._grounding = None
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
        if self._need_change_topic():
            return TopicFactory().create_topic(self._dialog.name)
        else:
            return self._class_topic(self._previous_topics["topic_id"])

    def _need_change_topic(self) -> bool:
        """Check if need to change to a new topic

        Processing logic:
        1. True if the current topic is None.
        2. True if the dialog domain changes.
        3. True if the dialog remains unchanged but intent changes.
        4. Otherwise False.
        """
        # logic 1
        if self._current_topic is None:
            return True
        # logic 2&3
        elif self._dialog.name != self._topic.name:
            return True
        # logic 4
        else:
            return False

    def respond(self) -> Response:
        """Respond to user according to msg, context and grounding"""
        return self._current_topic.respond()

    def _restore(self):
        """Restore the historical information to self"""
        cache = self._cache()
        if cache:
            self._previous_topics = cache.get("_previous_topics", [])
            self._current_topic = self._create_topic()
            self._grounding = cache.get("_grounding", {})
