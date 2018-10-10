"""Utility functions"""

import os
import re
import importlib
import importlib.util


def import_module(module_path: str):
    """ Import module that in the format of string

    :param module_path: module path string in format of dotted or absolute_path
        dotted string: "os.path.dirname"
        absolute_path: "/data/projects/some_project/core/utils.fun"

    :return: python object - class, instance or variable
    """
    if "/" not in module_path and re.match("\.?(\w+\.)*\w+", module_path):
        try:
            return importlib.import_module(module_path)
        except ModuleNotFoundError:
            name = module_path.split(".")[-1]
            module = module_path[:-len(name) - 1]
            return getattr(importlib.import_module(module), name)

    elif re.match("/?(\w+/)*(\w+\.)*\w+", module_path):
        # module_path without module name
        if os.path.isfile(module_path) or os.path.isdir(module_path):
            raise ModuleNotFoundError

        paths = module_path.split(".")
        location = paths[0] + ".py"
        if not os.path.isfile(location):
            raise ModuleNotFoundError

        name = ".".join(paths[1:])
        spec = importlib.util.spec_from_file_location(name, location)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, name)

    else:
        raise ModuleNotFoundError
