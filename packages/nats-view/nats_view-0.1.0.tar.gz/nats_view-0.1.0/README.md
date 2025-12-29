# nats-view

A command line utility for watching NATS and NATS JetStream topics with support for filtering, pretty-printing JSON, and historical replay.

## Features

- **Real-time Monitoring**: Watch core NATS subjects with ease.
- **JetStream Support**: Replay historical data using `--since`, `--deliver-all`, or `--deliver-last`.
- **Visualization**: Pretty-printed JSON, colorized output, timestamps, and headers.
- **Filtering**: Server-side subject filtering and client-side regex payload filtering.
- **Security**: Support for User/Pass, Token, Credentials, and TLS/SSL.
- **MCP Compatible**: Ready to be used as a tool for LLMs via the Model Context Protocol.

## Installation

### Via pipx (Recommended)
```bash
pipx install .
```

### Via Poetry (Development)
```bash
poetry install
poetry run nats-view --help
```

## Usage

### Basic
Watch all subjects on localhost:
```bash
nats-view
```

Watch specific subjects:
```bash
nats-view "orders.>" "logs.*"
```

### JetStream History
Replay messages from the last hour:
```bash
nats-view --js --since 1h "orders.>"
```

Get the last known value for a subject:
```bash
nats-view --js --deliver-last "status.system"
```

### Filtering & formatting
Show only messages containing "error", pretty-print the JSON, and exit after 5 matches:
```bash
nats-view --filter "error" --pretty --count 5 ">"
```

## MCP Tool Usage

This tool includes a definition for the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), allowing AI assistants to inspect your NATS clusters.

### Tool Definition
The tool definition is located in `mcp-tool.json`.

### Configuration Example (Claude Desktop / Generic MCP Client)
To use this with an MCP server that runs CLI commands (like a generic "command-runner" MCP server), map the arguments as follows:

**Executable**: `nats-view` (ensure it is in your PATH)

**Argument Mapping**:
- `subjects` -> Positional arguments
- `host` -> `-h`
- `port` -> `-p`
- `count` -> `-n`
- `filter` -> `--filter`
- `js` -> `--js`
- `since` -> `--since`
- `deliver_all` -> `--deliver-all`
- `deliver_last` -> `--deliver-last`
- `timestamp` -> `--timestamp`
- `headers` -> `--headers`

**Note for LLMs**: When using this tool, always specify a `count` (e.g., 10 or 50) to prevent the tool from running indefinitely when watching high-traffic subjects.
