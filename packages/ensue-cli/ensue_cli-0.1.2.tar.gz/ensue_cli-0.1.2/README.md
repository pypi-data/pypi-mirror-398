# ensue-cli

CLI for Ensue Memory - a distributed memory network for AI agents built on MCP, enabling persistent, shared context across conversations and applications.

## Installation

```bash
pip install ensue-cli
```

## Usage

Set your authentication token:

```bash
export ENSUE_TOKEN=your-token
```

List available commands:

```bash
ensue --help
```

Commands are loaded dynamically from the MCP server.

## Configuration

- `ENSUE_TOKEN` (required): Your Ensue API token
- `ENSUE_URL` (optional): API endpoint (defaults to https://www.ensue-network.ai/api/)
