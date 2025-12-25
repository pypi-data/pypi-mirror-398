from dataclasses import dataclass
from functools import partial
import re

from dyngle.error import DyngleError
from dyngle.model.context import Context

PATTERN = re.compile(r"\{\{\s*([^}]+)\s*\}\}")


@dataclass
class Template:

    template: str

    def render(self, context: Context | dict | None = None) -> str:
        """Render the template with the provided context."""

        context = Context(context)
        resolver = partial(self._dig, context=context)
        return PATTERN.sub(resolver, self.template)

    def _dig(self, match, *, context: Context):
        """Get the value for a single key from the context"""
        key = match.group(1).strip()
        return context.dig(key)

