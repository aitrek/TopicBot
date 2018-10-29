"""Configs"""

from configparser import ConfigParser

from .exceptions import ConfigDataError
from .decoraters import singleton


@singleton
class Configs:

    def __init__(self):
        self._parser = ConfigParser()
        self._has_loaded = False

    def get(self, section: str, option: str) -> str:
        if not self._has_loaded:
            raise ConfigDataError
        try:
            value = self._parser.get(section, option)
        except Exception as e:
            # todo logging
            value = ""
        return value

    def read(self, filenames, encoding=None):
        """Read and parse the configs file"""
        if not self._has_loaded:
            self._parser.read(filenames, encoding=encoding)
            self._has_loaded = True
        return self
