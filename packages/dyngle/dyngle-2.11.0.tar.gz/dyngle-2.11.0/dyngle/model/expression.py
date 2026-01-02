from typing import Callable
import datetime
from pathlib import PurePath
import math
import json
import re
import yaml
import os

from dyngle.error import DyngleError
from dyngle.model.context import Context
from dyngle.model.template import Template
from dyngle.model.util import yamlify


def dtformat(dt: datetime, format_string=None) -> str:
    """Safe datetime formatting using string operations"""
    if format_string is None:
        format_string = "{year:04d}{month:02d}{day:02d}"
    components = {
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "hour": dt.hour,
        "minute": dt.minute,
        "second": dt.second,
        "microsecond": dt.microsecond,
        "weekday": dt.weekday(),  # Monday is 0
    }
    return format_string.format(**components)


GLOBALS = {
    "__builtins__": {
        # Basic data types and conversions
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict,
        "tuple": tuple,
        "set": set,
        # Essential functions
        "len": len,
        "min": min,
        "max": max,
        "sum": sum,
        "abs": abs,
        "round": round,
        "sorted": sorted,
        "reversed": reversed,
        "enumerate": enumerate,
        "zip": zip,
        "range": range,
        "type": type,
    },

    # Read-only perations selected for inclusion

    "math": math,
    "datetime": datetime.datetime,
    "date": datetime.date,
    "timedelta": datetime.timedelta,
    "dtformat": dtformat,
    "re": re,
    "PurePath": PurePath,
    "getenv": os.getenv,
    "getcwd": os.getcwd,
    "gethome": lambda: os.path.expanduser('~'),
    "to_json": lambda v: json.dumps(v, default=str),
    "from_json": json.loads,
    "to_yaml": lambda v: yamlify(v),
    "from_yaml": yaml.safe_load
}


def _evaluate(expression: str, locals: dict) -> str:
    """Evaluate a Python expression with safe globals and user data context.

    Safely evaluates a Python expression string using a restricted set of
    global functions and modules, combined with user-provided data. The
    expression is evaluated in a sandboxed environment that includes basic
    Python built-ins, mathematical operations, date/time handling, and data
    manipulation utilities.

    Parameters
    ----------
    expression : str
        A valid Python expression string to be evaluated.
    data : dict
        Dictionary containing variables and values to be made available during
        expression evaluation. Note that hyphens in keys will be replaced by
        underscores to create valid Python names.

    Returns
    -------
    str
        String representation of the evaluated expression result. If the result
        is a tuple, returns the string representation of the last element.

    Raises
    ------
    DyngleError
        If the expression contains invalid variable names that are not found in
        the provided data dictionary or global context.
    """
    try:
        result = eval(expression, GLOBALS, locals)
    except KeyError as error:
        raise DyngleError(
            f"The following expression contains "
            + f"invalid name '{error}:\n{expression}"
        )

    # Allow the use of a comma to separate sub-expressions, which can then use
    # warus to set values, and only the last expression in the list returns a
    # value.
    result = result[-1] if isinstance(result, tuple) else result

    return result


# The 'expression' function returns the expression object itself, which is
# really just a function.


def expression(text: str) -> Callable[[dict], str]:
    """Generate an expression, which is a function based on a string
    expression"""

    def definition(context: Context | dict | None = None) -> str:
        """The expression function itself"""

        # We only work if passed some data to use - also we don't know our name
        # so can't report it.

        if context is None:
            raise DyngleError("Expression called with no argument")

        # Translate names to underscore-separated instead of hyphen-separated
        # so they work within the Python namespace.

        items = context.items() if context else ()
        symbols = Context({k.replace("-", "_"): v for k, v in items})

        # Create a get function which allows references using the hyphen
        # syntax too - note it relies on the original context object (not the
        # locals with the key replacement). We're converting it to Context in
        # case for some reason we were passed a raw dict.

        context = Context(context)

        def get(key):
            return context.resolve(key)

        def format(template_string):
            return Template(template_string).render(context)
        
        def arg(index):  # pragma: nocover
            if 'args' in context and len(context['args']) > index:
                return context['args'][index] or ''
            return ''

        # Passing the context in again allows function(data) in expressions
        symbols = symbols | {"get": get, "format": format, "data": context, "arg": arg}

        # Perform the Python eval, expanded above
        return _evaluate(text, symbols)

    return definition


def expression_structure(structure: dict | list) -> Callable[[dict], any]:
    """Generate an expression from a YAML structure (dict/list).
    
    Converts a YAML structure into an expression function that recursively
    evaluates string values as Python expressions while preserving the
    structure.
    """
    def definition(context: Context | dict | None = None):
        """The expression function that evaluates the YAML structure"""
        if context is None:
            raise DyngleError("Expression called with no argument")
        
        # Convert to Context to ensure consistent behavior
        context = Context(context)
        
        def evaluate_structure(obj):
            """Recursively evaluate a structure"""
            if isinstance(obj, dict):
                return {k: evaluate_structure(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [evaluate_structure(item) for item in obj]
            elif isinstance(obj, str):
                # Create an expression for this string and evaluate it
                expr = expression(obj)
                return expr(context)
            else:  # pragma: nocover
                # Other types (numbers, booleans, None) pass through
                return obj
        
        return evaluate_structure(structure)
    
    return definition
