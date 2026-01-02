from wizlib.parser import WizParser

from dyngle.command import DyngleCommand
from dyngle.servers.mcp_server import create_mcp_server, parse_operations_filter


class McpCommand(DyngleCommand):
    """Run an MCP server exposing Dyngle operations as tools"""

    name = "mcp"

    @classmethod
    def add_args(cls, parser: WizParser):
        super().add_args(parser)
        parser.add_argument(
            "args", nargs="*", help="Optional operation arguments"
        )
        parser.add_argument(
            "--transport",
            default="stdio",
            choices=["stdio"],
            help="Transport protocol to use",
        )
        parser.add_argument(
            "--operations",
            default=None,
            help="Comma-separated list of operations to expose as tools",
        )

    def create_server(self):
        """Create and configure the MCP server with tools for each
        operation"""
        # Get operations from dyngleverse
        operations = self.app.dyngleverse.operations
        
        # Get command line args
        command_args = getattr(self, 'args', [])
        
        # Parse and validate --operations filter if provided
        operations_filter = None
        if hasattr(self, 'operations') and self.operations:
            operations_filter = parse_operations_filter(
                self.operations, 
                operations
            )
        
        # Create server using the new module
        return create_mcp_server(operations, command_args, operations_filter)

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
