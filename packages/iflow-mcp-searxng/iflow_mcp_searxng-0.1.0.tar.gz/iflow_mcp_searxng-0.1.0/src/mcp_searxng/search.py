from logging import info
from typing import Optional
from httpx import AsyncClient, ConnectError, TimeoutException
from os import getenv

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    url: str
    title: str
    content: str
    # thumbnail: Optional[str] = None
    # engine: str
    # parsed_url: list[str]
    # template: str
    # engines: list[str]
    # positions: list[int]
    # publishedDate: Optional[str] = None
    # score: float
    # category: str


class InfoboxUrl(BaseModel):
    title: str
    url: str


class Infobox(BaseModel):
    infobox: str
    id: str
    content: str
    # img_src: Optional[str] = None
    urls: list[InfoboxUrl]
    # attributes: list[str]
    # engine: str
    # engines: list[str]


class Response(BaseModel):
    query: str
    number_of_results: int
    results: list[SearchResult]
    # answers: list[str]
    # corrections: list[str]
    infoboxes: list[Infobox]
    # suggestions: list[str]
    # unresponsive_engines: list[str]


async def search(query: str, limit: int = 3) -> str:
    try:
        client = AsyncClient(base_url=str(getenv("SEARXNG_URL", "http://localhost:8080")))

        params: dict[str, str] = {"q": query, "format": "json"}

        response = await client.get("/search", params=params, timeout=5.0)
        response.raise_for_status()

        data = Response.model_validate_json(response.text)

        text = ""

        for index, infobox in enumerate(data.infoboxes):
            text += f"Infobox: {infobox.infobox}\n"
            text += f"ID: {infobox.id}\n"
            text += f"Content: {infobox.content}\n"
            text += "\n"

        if len(data.results) == 0:
            text += "No results found\n"

        for index, result in enumerate(data.results):
            text += f"Title: {result.title}\n"
            text += f"URL: {result.url}\n"
            text += f"Content: {result.content}\n"
            text += "\n"

            if index == limit - 1:
                break

        return str(text)
    except (ConnectError, TimeoutException) as e:
        # Return mock result when SEARXNG server is not available
        return f"Search query: {query}\n\nNote: SEARXNG server is not configured or unavailable. Please set SEARXNG_URL environment variable to use this tool.\n\nMock result:\nTitle: Example Result\nURL: https://example.com\nContent: This is a mock result because SEARXNG server is not available.\n"


if __name__ == "__main__":
    import asyncio

    # test case for search
    print(asyncio.run(search("hello world")))
