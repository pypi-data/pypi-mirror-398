from dataclasses import dataclass
from enum import Enum
from functools import cached_property
import re
import selectors
import shlex
import subprocess
import sys

from dyngle.error import DyngleError
from dyngle.model.context import Context
from dyngle.model.interface import Interface
from dyngle.model.template import Template


class OperationAccess(str, Enum):
    """Access levels for operations"""
    PUBLIC = "public"
    PRIVATE = "private"


class Operation:
    """A named operation defined in configuration. Can be called from a Dyngle
    command (i.e. `dyngle run`) or as a sub-operation."""

    local_constants = {}

    def __init__(self, dyngleverse, definition: dict | list, key: str):
        """
        definition: Either a dict containing steps and local
        expressions/constants, or a list containing only steps
        """
        self.key = key
        self.dyngleverse = dyngleverse
        if isinstance(definition, list):
            steps_def = definition
            local_declarations = Context()
            self.description = None
            self.return_key = None
            self.interface_schema = None
            access_str = OperationAccess.PUBLIC.value
            self._definition = {}
        elif isinstance(definition, dict):
            steps_def = definition.get("steps") or []
            local_declarations = dyngleverse.parse_declarations(definition)
            self.description = definition.get("description")
            self.return_key = definition.get("returns")
            self.interface_schema = definition.get("accepts")
            access_str = definition.get("access", OperationAccess.PUBLIC.value)
            self._definition = definition
        
        # Validate and set access level
        try:
            self.access = OperationAccess(access_str)
        except ValueError:
            valid_values = ", ".join([f"'{a.value}'" for a in OperationAccess])
            raise DyngleError(
                f"Invalid access value '{access_str}' for operation '{key}'. "
                f"Must be one of: {valid_values}"
            )
        
        self.declarations = dyngleverse.global_declarations | local_declarations
        self.sequence = Sequence(dyngleverse, self, steps_def)
        
        # Create interface instance if schema is defined
        if self.interface_schema:
            self.interface = Interface(self.interface_schema)
        else:
            self.interface = None

    def validate_and_set_defaults(self, inputs: dict):
        """Validate input data against interface schema if present.
        
        Uses custom Interface class to validate and apply defaults.
        """
        if self.interface:
            try:

                # Validate input data and apply defaults (mutates data in place)
                temp = dict(inputs)
                self.interface.process(temp)
                inputs.data.update(temp)

            except DyngleError as e:
                raise DyngleError(
                    f"Input validation failed for operation "
                    f"'{self.key}': {str(e)}"
                )

    def run(self, payload: Context, args: list, display="steps", 
            show_stdout=None):

        # Validate input data and apply defaults (mutates data in place)
        self.validate_and_set_defaults(payload)

        inputs = payload | {'args': args}

        # Determine stdout behavior: show if no return key (script-like)
        if show_stdout is None:
            show_stdout = (self.return_key is None)

        variables = Context()
        self.sequence.run(inputs, variables, display=display, show_stdout=show_stdout)
        
        # Return the specified value if return_key is set
        if self.return_key:
            context = inputs | self.declarations | variables
            return context.resolve(self.return_key)
        return None


class Sequence:
    """We allow for the possibility that a sequence of steps might run at other
    levels than the operation itself, for example in a conditional block."""

    def __init__(self, dyngleverse, operation: Operation, steps_def: list):
        self.steps = [
            Step.parse_def(dyngleverse, operation.declarations, d)
            for d in steps_def
        ]

    def run(self, inputs: Context, variables: Context, display="steps", 
            show_stdout=True):
        
        # We keep inputs and variables separate because variables is mutable,
        # and they have different spots in name precedence.

        for step in self.steps:
            step.run(inputs, variables, display=display, show_stdout=show_stdout)


class Step:

    @staticmethod
    def parse_def(dyngleverse, constants: Context, definition: dict | str):
        for step_type in [CommandStep, SubOperationStep, PromptStep]:
            if step_type.fits(definition):
                return step_type(dyngleverse, constants, definition)
        raise DyngleError(f"Unknown step definition\n{definition}")


# Ideally these would be subclasses in a ClassFamily (or use an ABC)


class CommandStep:
    """Executes a system command with optional input/output operators.

    Supports the following operators:
    - `->` (input): Passes a value from the namespace to stdin
    - `=>` (output): Captures stdout to live data

    The step creates a namespace by merging:
    1. Operation's constants (declared constants/expressions) - lowest precedence
    2. Shared live data (mutable across operations) - middle precedence
    3. Current args - highest precedence

    Template resolution happens in this namespace, but output assignments
    go directly to the shared live data to persist across operations.
    """

    PATTERN = re.compile(
        r"^\s*(?:([\w.-]+)\s+->\s+)?(.+?)(?:\s+=>\s+([\w.-]+))?\s*$"
    )

    @classmethod
    def fits(cls, definition: dict | str):
        return isinstance(definition, str)

    def __init__(self, dyngleverse, declarations: Context, definition: str):
        self.declarations = declarations
        self.markup = definition
        if match := self.PATTERN.match(definition):
            self.payload_context_path, self.command_template, self.result_key = match.groups()
        else:
            raise DyngleError(f"Invalid step markup {{markup}}")

    def display_step(self):
        """Display the step definition."""
        print(self.markup, file=sys.stderr)

    def run(self, inputs: Context, variables: Context, display="steps", 
            show_stdout=True):

        if display == "steps":
            self.display_step()
        
        context = inputs | self.declarations | variables

        rendered_command = Template(self.command_template).render_list(context)

        payload = context.resolve(self.payload_context_path) if self.payload_context_path else ''

        # If show_stdout=True and no output capture, don't set stdout
        # to allow subprocess.run to use default behavior (shows output)

        capture_stdout = bool(self.result_key)
        show_stdout = (not capture_stdout) and show_stdout

        returncode, result = run_subprocess(rendered_command, payload, show_stdout, capture_stdout)

        if returncode != 0:
            raise DyngleError(
                f"Step failed with code {returncode}: {self.markup}"
            )
        if self.result_key:
            variables[self.result_key] = result.rstrip()


class SubOperationStep:
    """Calls another operation as a sub-step.

    Sub-operations are isolated by default - they do not automatically
    inherit parent's live data (=> assignments). Data must be explicitly
    passed using send: and received using receive:.

    Supports optional send: and receive: attributes:
    - send: passes a dict from context as the sub-operation's data context
      (the dict's keys/values become available to the sub-operation).
      The resolved value must be a dict.
    - receive: captures the sub-operation's return value and stores it in
      the parent's data context (stores None if sub has no return: key)
    """

    @classmethod
    def fits(cls, definition: dict | str):
        return isinstance(definition, dict) and "sub" in definition

    def __init__(self, dyngleverse, declarations: Context, definition: dict):
        self.dyngleverse = dyngleverse
        self.declarations = declarations
        self.operation_key = definition["sub"]
        self.payload_key = definition.get("send")
        self.result_key = definition.get("receive")

    def run(self, inputs: Context, variables: Context, display="steps", 
            show_stdout=True):

        context = inputs | self.declarations | variables

        suboperation = self.dyngleverse.operations.get(self.operation_key)
        if not suboperation:
            raise DyngleError(f"Unknown operation {self.operation_key}")

        # Args are global
        sub_args = inputs['args']
        
        # Prepare the data context for the sub-operation
        if self.payload_key:
            # Resolve the outbound payload - must be a dict
            payload = context.resolve(self.payload_key)
            if not isinstance(payload, dict):
                raise DyngleError(
                    f"send: attribute must resolve to a dict, "
                    f"got {type(payload).__name__}"
                )
            # Create new isolated context with the dict's keys and values
            sub_inputs = Context(payload)
        else:
            # No send - sub-operation gets empty context (isolated)
            sub_inputs = Context()
        
        # Run the sub-operation, inheriting stdout behavior from parent
        result = suboperation.run(sub_inputs, sub_args, display=display, 
                             show_stdout=show_stdout)
        
        # Store the return value in parent's data if receive is specified
        if self.result_key:
            variables[self.result_key] = result


class PromptStep:
    """Prompts the user for input using WizLib's UI handler.
    
    Supports:
    - prompt: Message to display (supports template substitution)
    - receive: (optional) Variable name to store the input
    
    Uses WizLib's UI handler which accesses the TTY directly via readchar,
    allowing prompts to work even when stdin is redirected for operation
    data input.
    """

    @classmethod
    def fits(cls, definition: dict | str):
        return isinstance(definition, dict) and "prompt" in definition

    def __init__(self, dyngleverse, declarations: Context, definition: dict):
        self.dyngleverse = dyngleverse
        self.declarations = declarations
        self.prompt_template = definition["prompt"]
        self.result_key = definition.get("receive")

    def run(self, inputs: Context, variables: Context, display="steps", 
            show_stdout=True):
        context = inputs | self.declarations | variables
        
        # Render the prompt message with template substitution
        prompt_message = Template(self.prompt_template).render(context)
        
        # Get input from user via WizLib's UI handler
        user_input = self.dyngleverse.app.ui.get_text(prompt_message)
        
        # Store the input if receive key is specified
        if self.result_key:
            variables[self.result_key] = user_input


# Like subprocess.run, but ensures output always goes through patches and such

def run_subprocess(command:list, input:str='', show_stdout:bool=True, capture_stdout:bool=False):
    result = ''
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0, text=True
    )
    try:
        if input:
            proc.stdin.write(input)
        proc.stdin.close()

        # Set up selector to monitor both stdout and stderr
        sel = selectors.DefaultSelector()
        sel.register(proc.stdout, selectors.EVENT_READ, data='stdout')
        sel.register(proc.stderr, selectors.EVENT_READ, data='stderr')

        # Read from both streams as data becomes available
        while sel.get_map():
            events = sel.select(timeout=0.1)
            for key, _ in events:
                char = key.fileobj.read(1)
                if not char:  # EOF on this stream
                    sel.unregister(key.fileobj)
                    continue

                if key.data == 'stdout':
                    if capture_stdout:
                        result += char
                    if show_stdout:
                        sys.stdout.write(char)
                        sys.stdout.flush()
                elif key.data == 'stderr':
                    sys.stderr.write(char)
                    sys.stderr.flush()

        sel.close()
        proc.wait()
        return proc.returncode, result

    finally:
        proc.stdout.close()
        proc.stderr.close()
        if proc.stdin and not proc.stdin.closed: #pragma: nocover
            proc.stdin.close()
