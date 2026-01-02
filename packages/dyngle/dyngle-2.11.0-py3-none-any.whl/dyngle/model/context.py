from collections import UserDict
from datetime import date, timedelta
from numbers import Number
from pathlib import PurePath
import re

from dyngle.error import DyngleError
from dyngle.model.util import yamlify

def raise_resolution_error(context_path, key):
    raise DyngleError(
        f"Unresolvable key '{key}' in context path '{context_path}'"
    )

class Context(UserDict):
    """Represents the entire set of values, expressions, and data which can be
    resolved in a template."""

    def resolve(self, context_path: str):
        """Given a context path (which might be dot-separated), return
        the value (which might include evaluating expressions). Note that
        context paths are resolved through all dicts and lists, even those that
        result from expression evaluation."""

        keys = context_path.split(".")
        node = self.data
        for key in keys:
            if isinstance(node, dict):
                if key not in node:
                    raise_resolution_error(context_path, key)
                node = node[key]
            elif isinstance(node, list):
                if key.isdigit():
                    index = int(key)
                    node = node[index] if index < len(node) else ''
                else:
                    raise_resolution_error(context_path, key)
            else:
                raise_resolution_error(context_path, key)
            if callable(node):
                node = node(self)
        return node
