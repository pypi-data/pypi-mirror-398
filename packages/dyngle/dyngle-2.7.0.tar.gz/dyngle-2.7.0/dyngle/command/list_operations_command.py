from yaml import safe_dump

from dyngle.command import DyngleCommand
from dyngle.model.operation import OperationAccess


class ListOperationsCommand(DyngleCommand):
    """List all available operations with their descriptions"""

    name = "list-operations"

    @DyngleCommand.wrap
    def execute(self):
        ops = self.app.dyngleverse.operations
        # Only include public operations
        ops_dict = {
            key: op.description 
            for key, op in ops.items() 
            if op.access == OperationAccess.PUBLIC
        }
        output = safe_dump({"operations": ops_dict}, default_flow_style=False)
        self.status = "Operations listed successfully"
        return output.rstrip()
