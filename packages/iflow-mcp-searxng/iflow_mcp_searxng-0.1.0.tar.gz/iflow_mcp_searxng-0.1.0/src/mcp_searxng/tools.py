from mcp_searxng.server import server
import mcp.types as types
from mcp_searxng.search import search


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search",
            description="search the web using searXNG. This will aggregate the results from google, bing, brave, duckduckgo and many others. Use this to find information on the web. Even if you do not have access to the internet, you can still use this tool to search the web.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        )
    ]


async def search_tool(
    arguments: dict[str, str],
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    query: str = arguments["query"]
    result = await search(query)

    return [types.TextContent(type="text", text=result)]


@server.call_tool()
async def get_tool(
    name: str, arguments: dict[str, str] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if arguments is None:
        arguments = {}

    try:
        if name == "search":
            return await search_tool(arguments)

    except Exception as e:
        text = f"Tool {name} failed with error: {e}"
        return [types.TextContent(type="text", text=text)]

    raise ValueError(f"Unknown tool: {name}")
