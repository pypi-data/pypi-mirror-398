from dataclasses import dataclass
from functools import partial
import re
import shlex
from functools import cached_property

from dyngle.error import DyngleError
from dyngle.model.context import Context
from dyngle.model.util import jsonify


PLACEHOLDER = re.compile(r"\{\{\s*([^}]+)\s*\}\}")


@dataclass
class Template:
    """Take a string possible containing double-curly-brace delimited
    placeholders, and render it with a context. Output depends on what it
    finds:

    String literal only - Return the string

    A single placeholder with no other string characters - Resolve the context path
    and return the relevant Python type
    
    String characters and placeholder, or multiple adjacent placeholders - Resolve
    the paths and replace the results into the response as JSON.
    """

    template: str

    def render(self, context: Context | dict | None = None) -> str:
        """Render the template with the provided context and return the correct type"""

        context = Context(context)
        if (single_placeholder:=PLACEHOLDER.fullmatch(self.template)):
            return _resolve_context_path(single_placeholder, context=context)
        else:
            resolver = partial(_resolve_context_path, context=context, json=True)
            return PLACEHOLDER.sub(resolver, self.template)

    @cached_property
    def template_words(self):
        return [Template(w) for w in shlex.split(self.template.strip())]

    def render_list(self, context: Context | dict | None = None) -> list:
        """Render the template as a command-type list, allowing for multi-wor
        resolution by flattening lists"""

        rendered_words = []
        for template_word in self.template_words:
            obj = template_word.render(context)
            if isinstance(obj, (list, tuple)):
                # Lists become multiple words
                for word in obj:
                    rendered_words.append(word.strip() if isinstance(word, str) else word)
            elif isinstance(obj, dict):
                # Dicts become like command options
                for key in obj:
                    rendered_words.append('--' + key)
                    if (val:=obj[key]):
                        rendered_words.append(val)
            else:
                rendered_words.append(str(obj).strip())
        return rendered_words

def _resolve_context_path(match, *, context: Context, json: bool = False):
    """Get the value for a context path from the context - might include
    traversing the structure and evaluating expressions."""
    context_path = match.group(1).strip()
    value = context.resolve(context_path)
    return jsonify(value) if json else value




