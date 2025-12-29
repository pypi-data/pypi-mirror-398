"""Unit tests for CLI internals (no network required)."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ensue_cli.cli import get_config, main, parse_arg, print_result


class TestGetConfig:
    def test_missing_token_exits(self):
        """get_config should exit when ENSUE_TOKEN is not set."""
        runner = CliRunner(env={"ENSUE_TOKEN": ""})
        with runner.isolated_filesystem():
            with patch.dict("os.environ", {"ENSUE_TOKEN": ""}, clear=False):
                with pytest.raises(SystemExit):
                    get_config()

    def test_returns_url_and_token(self):
        """get_config should return URL and token from env."""
        with patch.dict(
            "os.environ",
            {"ENSUE_TOKEN": "test-token", "ENSUE_URL": "http://test.com"},
            clear=False,
        ):
            url, token = get_config()
            assert url == "http://test.com"
            assert token == "test-token"

    def test_default_url(self):
        """get_config should use default URL when not set."""
        with patch.dict("os.environ", {"ENSUE_TOKEN": "test-token"}, clear=False):
            # Remove ENSUE_URL if present
            import os

            os.environ.pop("ENSUE_URL", None)
            url, token = get_config()
            assert "ensue-network.ai" in url


class TestParseArg:
    def test_parses_json_array(self):
        """parse_arg should parse JSON arrays."""
        result = parse_arg('["a", "b"]', "array")
        assert result == ["a", "b"]

    def test_parses_json_object(self):
        """parse_arg should parse JSON objects."""
        result = parse_arg('{"key": "value"}', "object")
        assert result == {"key": "value"}

    def test_returns_original_on_invalid_json(self):
        """parse_arg should return original value on JSON parse failure."""
        result = parse_arg("not-json", "array")
        assert result == "not-json"

    def test_returns_value_for_other_types(self):
        """parse_arg should return value unchanged for non-array/object types."""
        assert parse_arg("hello", "string") == "hello"
        assert parse_arg(42, "integer") == 42


class TestPrintResult:
    def test_prints_mcp_content(self, capsys):
        """print_result should handle MCP CallToolResult with content."""
        mock_result = MagicMock()
        mock_item = MagicMock()
        mock_item.text = '{"success": true}'
        mock_result.content = [mock_item]

        print_result(mock_result)
        # Should not raise

    def test_prints_mcp_content_invalid_json(self, capsys):
        """print_result should handle non-JSON text content."""
        mock_result = MagicMock()
        mock_item = MagicMock()
        mock_item.text = "plain text response"
        mock_result.content = [mock_item]

        print_result(mock_result)
        captured = capsys.readouterr()
        assert "plain text response" in captured.out

    def test_prints_dict_result(self, capsys):
        """print_result should handle dict results."""
        print_result({"key": "value"})
        # Should not raise


class TestCLIErrorHandling:
    def setup_method(self):
        """Reset the CLI tools cache before each test."""
        main._tools = None

    def test_unknown_command(self):
        """CLI should handle unknown commands gracefully."""
        runner = CliRunner(env={"ENSUE_TOKEN": "test"})
        # Mock client.list_tools to return known tools
        with patch("ensue_cli.cli.client.list_tools") as mock_list:
            mock_list.return_value = [{"name": "known_cmd", "inputSchema": {}}]
            result = runner.invoke(main, ["unknown_command"])
            assert result.exit_code != 0

    def test_connection_error_on_list(self):
        """CLI should handle connection errors when listing tools."""
        runner = CliRunner(env={"ENSUE_TOKEN": "invalid"})

        with patch("ensue_cli.cli.client.list_tools", side_effect=Exception("Connection failed")):
            result = runner.invoke(main, ["--help"])
            assert "Connection error" in result.output
