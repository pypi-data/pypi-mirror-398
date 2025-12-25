import json

from mcp.server import Server
from mcp.types import Tool, TextContent
from wizlib.parser import WizParser

from dyngle.command import DyngleCommand
from dyngle.model.context import Context
from dyngle.model.operation import OperationAccess
from dyngle.error import DyngleError


class McpCommand(DyngleCommand):
    """Run an MCP server exposing Dyngle operations as tools"""

    name = "mcp"

    @classmethod
    def add_args(cls, parser: WizParser):
        super().add_args(parser)
        parser.add_argument(
            "--transport",
            default="stdio",
            choices=["stdio"],
            help="Transport protocol to use",
        )

    def create_server(self) -> Server:
        """Create and configure the MCP server with tools for each
        operation"""
        server = Server("dyngle")

        # Store reference to operations for use in handlers
        operations = self.app.dyngleverse.operations

        @server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all public operations as MCP tools"""
            tools = []
            
            for op_name, operation in operations.items():
                # Skip private operations
                if operation.access != OperationAccess.PUBLIC:
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
                error_msg = f"Unknown operation: {name}"
                result = json.dumps({"error": error_msg})
                return [TextContent(type="text", text=result)]
            
            # Prepare data and args based on interface
            if operation.interface_schema:
                # Interface present - all arguments become data
                data = arguments
            else:
                # No interface - no data
                data = {}
            
            args = []
            
            # Create context from data
            context = Context(data)

            try:
                # Execute the operation
                return_value = operation.run(context, args)
                result = json.dumps({"result": return_value})
                
            except DyngleError as e:
                result = json.dumps({"error": str(e)})
            except Exception as e:
                error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
                result = json.dumps({"error": error_msg})
            
            return [TextContent(type="text", text=result)]

        return server

    @DyngleCommand.wrap
    def execute(self):
        """Start the MCP server"""
        server = self.create_server()

        # Import and run with the specified transport
        from mcp.server.stdio import stdio_server

        # Run the server with stdio transport
        import asyncio
        
        async def run_server():  # pragma: nocover
            async with stdio_server() as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options()
                )
        
        asyncio.run(run_server())

        # Realistically we don't ever get here.
        self.status = f"MCP server started on {self.transport}"
