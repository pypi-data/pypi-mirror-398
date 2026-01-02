from functools import cached_property
import shlex
import subprocess
import json
from yaml import safe_load

from wizlib.parser import WizParser

from dyngle.command import DyngleCommand
from dyngle.model.context import Context
from dyngle.model.expression import expression
from dyngle.model.operation import OperationAccess
from dyngle.model.template import Template
from dyngle.error import DyngleError
from dyngle.model.util import yamlify


class RunCommand(DyngleCommand):
    """Run a workflow defined in the configuration"""

    name = "run"

    @classmethod
    def add_args(cls, parser: WizParser):
        super().add_args(parser)
        parser.add_argument(
            "operation", help="Operation name to run", nargs="?"
        )
        parser.add_argument(
            "args", nargs="*", help="Optional operation arguments"
        )
        parser.add_argument(
            "--display",
            choices=["steps", "none"],
            default="steps",
            help="Display option for operation execution (default: steps)"
        )

    def handle_vals(self):
        super().handle_vals()
        keys = self.app.dyngleverse.operations.keys()
        if not self.provided("operation"):
            self.operation = self.app.ui.get_text("Operation: ", sorted(keys))
            if not self.operation:
                raise DyngleError(f"Operation required.")
        if self.operation not in keys:
            raise DyngleError(f"Invalid operation {self.operation}.")
        
        # Check if operation is private
        operation = self.app.dyngleverse.operations[self.operation]
        if operation.access != OperationAccess.PUBLIC:
            raise DyngleError(
                f"Operation '{self.operation}' is not executable."
            )

    @DyngleCommand.wrap
    def execute(self):
        payload_string = self.app.stream.text
        payload = safe_load(payload_string) or {}
        operation = self.app.dyngleverse.operations[self.operation]
        return_value = operation.run(
            Context(payload), self.args, display=self.display
        )
        self.status = f'Operation "{self.operation}" completed successfully'
        
        # Print return value if present
        if return_value is not None:
            return yamlify(return_value)
    