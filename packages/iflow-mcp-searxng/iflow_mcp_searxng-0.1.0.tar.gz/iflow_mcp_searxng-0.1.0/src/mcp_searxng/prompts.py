import mcp.types as types
from mcp_searxng.server import server


# Add prompt capabilities
@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="search",
            description="Use searXNG to search the web",
            arguments=[
                types.PromptArgument(
                    name="query", description="Search query", required=True
                )
            ],
        )
    ]


def search_prompt(arguments: dict[str, str]) -> types.GetPromptResult:
    return types.GetPromptResult(
        description="searXNG search",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text", text=f"Searching for {arguments['query']} using searXNG"
                ),
            )
        ],
    )


@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    if arguments is None:
        arguments = {}

    if name == "search":
        return search_prompt(arguments)

    raise ValueError(f"Unknown prompt: {name}")
