"""MCP server operations for exposing Dyngle operations as tools"""

import json
from mcp.server import Server
from mcp.types import Tool, TextContent

from dyngle.model.context import Context
from dyngle.model.operation import OperationAccess
from dyngle.error import DyngleError


def create_mcp_server(operations: dict, command_args: list = None, operations_filter: set = None) -> Server:
    """Create and configure an MCP server with tools for each operation
    
    Args:
        operations: Dictionary of operation name -> Operation objects
        command_args: Optional list of command-line arguments to pass to operations
        operations_filter: Optional set of operation names to expose (None = all public ops)
    
    Returns:
        Configured MCP Server instance
    """
    server = Server("dyngle")
    
    # Use empty list if no args provided
    command_args = command_args if command_args else []

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all public operations as MCP tools"""
        tools = []
        
        for op_name, operation in operations.items():
            # Skip private operations
            if operation.access != OperationAccess.PUBLIC:
                continue
            
            # Skip operations not in filter if filter is set
            if operations_filter and op_name not in operations_filter:
                continue
            
            # Create input schema
            if operation.interface:
                # Use Interface's JSON Schema conversion
                properties = operation.interface.to_json_schema()
                required = operation.interface.get_required_fields()
                
                input_schema = {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            else:
                # No interface - no parameters
                input_schema = {
                    "type": "object",
                    "properties": {},
                }
            
            # Create tool with metadata
            tool = Tool(
                name=op_name,
                description=operation.description or f"Execute {op_name} operation",
                inputSchema=input_schema,
            )
            tools.append(tool)
        
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Execute a Dyngle operation"""
        operation = operations.get(name)
        if not operation:  # pragma: nocover
            raise DyngleError(f"Unknown operation: {name}")
        
        # Prepare data and args based on interface
        if operation.interface_schema:
            # Interface present - all arguments become data
            data = arguments
        else:
            # No interface - no data
            data = {}
        
        # Create context from data
        context = Context(data)

        # Execute the operation with command-line args
        # Block stdout for MCP operations - results should come via return value
        return_value = operation.run(context, command_args, show_stdout=False)
        # Use default parameter to handle non-serializable types like Path objects
        result = json.dumps({"result": return_value}, default=str)
        
        return [TextContent(type="text", text=result)]

    return server


def parse_operations_filter(operations_filter_str: str, operations: dict) -> set:
    """Parse and validate operations filter string
    
    Args:
        operations_filter_str: Comma-separated list of operation names
        operations: Dictionary of available operations
        
    Returns:
        Set of operation names to expose, or None if empty
        
    Raises:
        DyngleError: If any operation name in filter doesn't exist
    """
    if not operations_filter_str:  # pragma: nocover
        return None
        
    # Parse comma-separated list and strip whitespace
    op_list = [op.strip() for op in operations_filter_str.split(',')]
    # Filter out empty strings
    op_list = [op for op in op_list if op]
    
    if not op_list: # pragma: nocover
        return None
    
    # Validate all keys exist
    for op_key in op_list:
        if op_key not in operations:
            raise DyngleError(
                f"Operation '{op_key}' not found in dyngleverse"
            )
    
    return set(op_list)
