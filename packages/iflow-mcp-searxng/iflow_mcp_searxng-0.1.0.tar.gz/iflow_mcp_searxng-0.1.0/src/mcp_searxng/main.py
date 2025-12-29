from mcp.server import NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

from mcp_searxng.server import server
import mcp_searxng.prompts  # noqa: F401
import mcp_searxng.tools  # noqa: F401


async def run():
    # Run the server as STDIO
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="searxng",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
