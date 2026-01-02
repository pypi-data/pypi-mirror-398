from dyngle.command import DyngleCommand
from dyngle.model.operation import OperationAccess
from dyngle.model.util import yamlify


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
        output = yamlify({"operations": ops_dict})
        self.status = "Operations listed successfully"
        return output.rstrip()
