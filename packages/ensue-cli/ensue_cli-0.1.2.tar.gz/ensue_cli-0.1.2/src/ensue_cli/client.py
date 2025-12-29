"""MCP client for communicating with the Ensue Memory Network."""

from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


@asynccontextmanager
async def create_session(url: str, token: str):
    """Create an MCP client session connected to the Ensue service."""
    headers = {"Authorization": f"Bearer {token}"}
    async with streamablehttp_client(url, headers=headers) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


async def list_tools(url: str, token: str) -> list[dict[str, Any]]:
    """Fetch the list of available tools from the MCP server."""
    async with create_session(url, token) as session:
        result = await session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
            for tool in result.tools
        ]


async def call_tool(url: str, token: str, name: str, arguments: dict[str, Any]) -> Any:
    """Call a tool on the MCP server."""
    async with create_session(url, token) as session:
        result = await session.call_tool(name, arguments)
        return result
