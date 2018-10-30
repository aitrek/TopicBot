"""Utility functions"""

import os
import re
import json
import importlib
import importlib.util

from typing import List


def import_module(module_path: str, root_path: str=""):
    """ Import module that in the format of string

    Loigc to process the module path:
        Take module_path as absolute path first to import the module.
        If failed, join the root_path and module_path to get a new
        absolute to try again.

    :param module_path: module path string in format of dotted or absolute_path
        dotted string: "os.path.dirname"
        absolute_path: "/data/projects/some_project/core/utils.fun"
    :param root_path: root path to find module.

    :return: python object - class, instance or variable
    """
    def absolute_paths(module_path: str, root_path: str="") -> List[str]:
        paths = []
        if module_path.startswith("/"):
            paths = [module_path]

        if root_path:
            if not root_path.startswith("/"):
                root_path = "/" + root_path
            if root_path.endswith("/"):
                root_path = root_path[:-1]

            module_paths = module_path.split("/")
            for path in module_paths:
                if path == ".":
                    continue
                elif path == "..":
                    root_path = os.path.dirname(root_path)
                else:
                    root_path += "/" + path
            paths.append(root_path)

        return paths

    # dot style
    if "/" not in module_path and re.match("\.?(\w+\.)*\w+", module_path):
        try:
            return importlib.import_module(module_path)
        except ModuleNotFoundError:
            name = module_path.split(".")[-1]
            module = module_path[:-len(name) - 1]
            return getattr(importlib.import_module(module), name)

    # slash style
    elif re.match("/?(\w+/)*(\w+\.)*\w+", module_path):
        for ab_path in absolute_paths(module_path, root_path):
            # module_path without module name
            if os.path.isfile(ab_path) or os.path.isdir(ab_path):
                raise ModuleNotFoundError

            paths = ab_path.split(".")
            location = paths[0] + ".py"
            if not os.path.isfile(location):
                raise ModuleNotFoundError

            name = ".".join(paths[1:])
            spec = importlib.util.spec_from_file_location(name, location)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return getattr(module, name)

    # error
    else:
        raise ModuleNotFoundError


class CustomJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        try:
            return obj.values
        except TypeError:
            return super().default(obj)
