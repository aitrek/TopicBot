"""Class to respresent dialog of one loop"""

import logging
import re
import copy

from typing import List, Tuple, Union

from .base import Base
from .response import ResponseFactory
from .utils import create_template


class Dialog(Base):

    _attrs = [
        "id",              # str, instance identifier
        "msg",             # dict, client msg
        "parsed_data",     # dict, parsed data of msg
        "response"         # instance, final response to user
    ]

    def __init__(self, msg: dict, context, grounding, intent_classifier):
        super().__init__()
        self._msg = msg
        self._context = context
        self._grounding = grounding
        self._intent_classifier = intent_classifier
        self._response = None
        self._parsed_data = {}

    def _get_from_parsed_value(self, key: str):
        if re.match(".*\D0$", key):
            value = self._parsed_data.get(key[:-1])
        else:
            value = self._parsed_data.get(key)
        return value

    def get(self, key: str):
        """
        Get the most possible value. None will be returned if no data found.
        """
        parsed_value = self._get_from_parsed_value(key)
        if parsed_value:
            return parsed_value

        context_value = self._context[key]
        if context_value:
            return context_value

        grounding_value = self._grounding[key]
        if grounding_value:
            return grounding_value

    @property
    def msg(self) -> dict:
        return self._msg

    @msg.setter
    def msg(self, msg: dict):
        self._msg = msg

    @property
    def parsed_data(self) -> dict:
        return self._parsed_data

    @parsed_data.setter
    def parsed_data(self, parsed_data: dict):
        self._parsed_data = parsed_data

    @property
    def intent_labels(self) -> str:
        return self._parsed_data.get("intent_labels", [])

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, response_data: dict):
        """
        :param response_data: Serialized data of a Response instance.
        """
        additional_msg = response_data["additional_msg"]
        self._response = ResponseFactory().create_response(response_data,
                                                           additional_msg)

    def _merged_context(self) -> dict:
        """Merge context and grounding"""
        merged_context = copy.deepcopy(self._context.values)
        for k, v in self._grounding.value.items():
            if k not in merged_context:
                merged_context[k] = v
        return merged_context

    def parse(self, ner, intent_classifier):
        """
        Parse user input including ner, intent recognition from any available
        data, such as msg, context and grounding, etc.
        """
        text = self._msg.get("text", "")
        entities = sorted(ner(text), key=lambda x: x["start"])
        template = create_template(text, entities)
        intent_labels = intent_classifier.predict(text, self._merged_context())

        self._parsed_data = {"text": text,
                             "template": template,
                             "entities": entities,
                             "intent_labels": intent_labels}
