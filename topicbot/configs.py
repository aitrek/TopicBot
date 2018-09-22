"""Configs"""

from configparser import ConfigParser

from .exceptions import ConfigDataError


class Configs:

    def __init__(self):
        self._parser = ConfigParser()
        self._loaded = False

    def get(self, section: str, option: str) -> str:
        if not self._loaded:
            raise ConfigDataError
        return self._parser.get(section, option)

    def read(self, filenames, encoding=None):
        """Read and parse the configs file"""
        self._parser.read(filenames, encoding=encoding)
        self._loaded = True
        return self
