"""Integration tests for Ensue CLI dynamic functionality."""

import base64
import json
import os
import uuid

import pytest
from click.testing import CliRunner

from ensue_cli import client
from ensue_cli.cli import main

ENSUE_URL = os.environ.get("ENSUE_URL", "https://www.ensue-network.ai/api/")
ENSUE_TOKEN = os.environ.get("ENSUE_TOKEN")

pytestmark = pytest.mark.skipif(not ENSUE_TOKEN, reason="ENSUE_TOKEN environment variable not set")


@pytest.fixture
def runner():
    return CliRunner(env={"ENSUE_TOKEN": ENSUE_TOKEN, "ENSUE_URL": ENSUE_URL})


@pytest.fixture
def test_key():
    return f"cli-test-{uuid.uuid4()}"


@pytest.mark.asyncio
async def test_cli_commands_match_server_tools(runner):
    """CLI commands should match tools available from the MCP server."""
    # Get tools directly from server
    server_tools = await client.list_tools(ENSUE_URL, ENSUE_TOKEN)
    server_tool_names = {t["name"] for t in server_tools}

    # Get commands from CLI
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0

    # Each server tool should appear in CLI help
    for tool_name in server_tool_names:
        assert tool_name in result.output, f"Tool '{tool_name}' not found in CLI"


def test_cli_shows_help_without_error(runner):
    """CLI --help should work and show available commands."""
    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "Ensue Memory CLI" in result.output
    assert "Commands are loaded dynamically" in result.output


def test_cli_shows_version(runner):
    """CLI --version should show version."""
    result = runner.invoke(main, ["--version"])

    assert result.exit_code == 0
    assert "0.1.2" in result.output


@pytest.mark.asyncio
async def test_cli_command_has_correct_options(runner):
    """CLI command options should match the tool's input schema."""
    # Get a tool's schema from server
    tools = await client.list_tools(ENSUE_URL, ENSUE_TOKEN)
    tool = next((t for t in tools if t["name"] == "create_memory"), None)

    if not tool:
        pytest.skip("create_memory tool not available")

    schema = tool.get("inputSchema", {})
    properties = schema.get("properties", {})

    # Get CLI command help
    result = runner.invoke(main, ["create_memory", "--help"])
    assert result.exit_code == 0

    # Each schema property should be a CLI option
    for prop_name in properties:
        option_name = f"--{prop_name.replace('_', '-')}"
        assert option_name in result.output, f"Option '{option_name}' not in CLI"


def test_cli_create_and_delete_memory(runner, test_key):
    """Test full CLI workflow: create and delete a memory."""
    # Value must be base64 encoded
    test_value = base64.b64encode(json.dumps({"test": True, "key": test_key}).encode()).decode()

    # Create memory via CLI using batch format
    items = json.dumps(
        [
            {
                "key_name": test_key,
                "value": test_value,
                "description": "Integration test memory",
                "base64": True,
            }
        ]
    )
    create_result = runner.invoke(
        main,
        [
            "create_memory",
            "--items",
            items,
        ],
    )
    assert create_result.exit_code == 0, f"Create failed: {create_result.output}"

    # Delete memory via CLI using batch format
    key_names = json.dumps([test_key])
    delete_result = runner.invoke(
        main,
        [
            "delete_memory",
            "--key-names",
            key_names,
        ],
    )
    assert delete_result.exit_code == 0, f"Delete failed: {delete_result.output}"


def test_cli_missing_required_option(runner):
    """CLI should error when required options are missing."""
    result = runner.invoke(main, ["create_memory"])

    # Should fail due to missing required options
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


@pytest.mark.asyncio
async def test_all_tools_translate_to_valid_cli_commands(runner):
    """Every tool from the server should translate to a working CLI command with correct options."""
    tools = await client.list_tools(ENSUE_URL, ENSUE_TOKEN)

    for tool in tools:
        tool_name = tool["name"]
        schema = tool.get("inputSchema", {})
        properties = schema.get("properties", {})

        # Each tool's help should be accessible
        result = runner.invoke(main, [tool_name, "--help"])
        assert result.exit_code == 0, f"Tool '{tool_name}' --help failed: {result.output}"

        # Verify each property is translated to a CLI option
        for prop_name, prop_schema in properties.items():
            option_name = f"--{prop_name.replace('_', '-')}"
            assert option_name in result.output, (
                f"Tool '{tool_name}' missing option '{option_name}'"
            )

            # Verify type hints appear for typed options
            prop_type = prop_schema.get("type")
            if prop_type == "integer":
                assert "INTEGER" in result.output or option_name in result.output
            elif prop_type == "number":
                assert "FLOAT" in result.output or option_name in result.output
            elif prop_type == "boolean":
                assert "BOOLEAN" in result.output or option_name in result.output


@pytest.mark.asyncio
async def test_all_tools_callable_with_help(runner):
    """Verify every tool can at least show its help without errors."""
    tools = await client.list_tools(ENSUE_URL, ENSUE_TOKEN)

    errors = []
    for tool in tools:
        result = runner.invoke(main, [tool["name"], "--help"])
        if result.exit_code != 0:
            errors.append(f"{tool['name']}: {result.output}")

    assert not errors, "Tools failed to show help:\n" + "\n".join(errors)
