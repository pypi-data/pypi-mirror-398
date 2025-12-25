from collections import UserDict
from datetime import date, timedelta
from numbers import Number

from yaml import safe_dump

from dyngle.error import DyngleError
from dyngle.model.safe_path import SafePath


class Context(UserDict):
    """Represents the entire set of values, expressions, and data which can be
    resolved in a template."""

    def dig(self, key: str, str_only: bool = True):
        """Given a key (which might be dot-separated), return
        the value (which might include evaluating expressions). Method name
        borrowed from Ruby."""

        parts = key.split(".")
        current = self.data
        for part in parts:
            if part not in current:
                raise DyngleError(
                    f"Invalid expression or data reference '{key}'"
                )
            current = current[part]
            # Evaluate expressions immediately after accessing
            if callable(current):
                current = current(self)
        return _stringify(current) if str_only else current


def _stringify(value) -> str:
    if isinstance(value, bool):
        return "." if value is True else ""
    elif isinstance(value, (Number, str, date, timedelta, SafePath)):
        return str(value)
    elif isinstance(value, (list, dict, tuple)):
        return safe_dump(value)
    elif isinstance(value, set):
        return safe_dump(list(value))
    else:
        raise DyngleError(f"Unable to serialize value of type {type(value)}")
