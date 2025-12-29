"""Dynamic CLI for Ensue Memory Network."""

import asyncio
import json
import os
import sys

import click
from rich.console import Console
from rich.json import JSON

from . import client

console = Console()
DEFAULT_URL = "https://api.ensue-network.ai/"


def run_async(coro):
    """Run async coroutine, handling nested event loops."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # If there's already a running loop, create a new one in a thread
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor() as pool:
        return pool.submit(asyncio.run, coro).result()


def get_config():
    url = os.environ.get("ENSUE_URL", DEFAULT_URL)
    token = os.environ.get("ENSUE_TOKEN")
    if not token:
        console.print("[red]Error:[/red] ENSUE_TOKEN environment variable required")
        sys.exit(1)
    return url, token


def print_result(result):
    if hasattr(result, "content"):
        for item in result.content:
            if hasattr(item, "text"):
                try:
                    console.print(JSON(item.text))
                except Exception:
                    console.print(item.text)
    else:
        console.print(JSON(json.dumps(result, indent=2)))


TYPE_MAP = {
    "integer": click.INT,
    "number": click.FLOAT,
    "boolean": click.BOOL,
}


def parse_arg(value, schema_type):
    if schema_type in ("array", "object") and isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    return value


def build_command(tool):
    """Build a Click command from an MCP tool definition."""
    schema = tool.get("inputSchema", {})
    props = schema.get("properties", {})
    required = set(schema.get("required", []))

    params = [
        click.Option(
            [f"--{name.replace('_', '-')}"],
            type=TYPE_MAP.get(p.get("type"), click.STRING),
            required=name in required,
            help=p.get("description", ""),
        )
        for name, p in props.items()
    ]

    def callback(**kwargs):
        url, token = get_config()
        args = {
            k.replace("-", "_"): parse_arg(v, props.get(k.replace("-", "_"), {}).get("type"))
            for k, v in kwargs.items()
            if v is not None
        }
        result = run_async(client.call_tool(url, token, tool["name"], args))
        print_result(result)

    return click.Command(
        name=tool["name"],
        callback=callback,
        params=params,
        help=tool.get("description", ""),
    )


class MCPToolsCLI(click.Group):
    """CLI that loads commands dynamically from MCP server."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tools = None

    @property
    def tools(self):
        if self._tools is None:
            url, token = get_config()
            self._tools = {t["name"]: t for t in run_async(client.list_tools(url, token))}
        return self._tools

    def list_commands(self, ctx):
        try:
            return sorted(self.tools.keys())
        except Exception as e:
            console.print("[red]Connection error:[/red] Could not connect to MCP server")
            console.print(f"[dim]{e}[/dim]")
            return []

    def get_command(self, ctx, name):
        if name not in self.tools:
            return None
        return build_command(self.tools[name])


@click.group(cls=MCPToolsCLI)
@click.version_option()
def main():
    """Ensue Memory CLI - A distributed memory network for AI agents.

    Commands are loaded dynamically from the MCP server.
    Set ENSUE_TOKEN to authenticate.
    """


if __name__ == "__main__":
    main()
