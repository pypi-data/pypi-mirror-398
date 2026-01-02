# FAR Oracle - MCP Server

An MCP (Model Context Protocol) server that provides AI agents with access to Federal Acquisition Regulations (FAR) search.

<!-- mcp-name: io.github.blueskylineassets/far-mcp-server -->

## Installation

### Option 1: Install from PyPI

```bash
pip install far-oracle
```

### Option 2: Clone this repository

```bash
git clone https://github.com/blueskylineassets/far-mcp-server.git
cd far-mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Get Your API Key

Get your RapidAPI key from:
https://rapidapi.com/yschang/api/far-rag-federal-acquisition-regulation-search

## Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "far-oracle": {
      "command": "python",
      "args": ["-m", "server"],
      "env": {
        "RAPIDAPI_KEY": "your-rapidapi-key"
      }
    }
  }
}
```

Or if installed from source:

```json
{
  "mcpServers": {
    "far-oracle": {
      "command": "/path/to/far-mcp-server/venv/bin/python",
      "args": ["/path/to/far-mcp-server/server.py"],
      "env": {
        "RAPIDAPI_KEY": "your-rapidapi-key"
      }
    }
  }
}
```

## Usage

Once configured, ask Claude Desktop questions like:

- "What are the FAR requirements for cybersecurity?"
- "Explain small business set-aside rules"
- "What contract clauses apply to data rights?"

## Pricing

See RapidAPI for pricing tiers:
https://rapidapi.com/yschang/api/far-rag-federal-acquisition-regulation-search/pricing

## License

MIT
