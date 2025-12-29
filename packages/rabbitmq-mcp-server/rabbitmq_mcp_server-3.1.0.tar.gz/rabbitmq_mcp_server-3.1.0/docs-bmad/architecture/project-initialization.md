# Project Initialization

**Development Setup:**

```bash
# Clone repository
git clone https://github.com/guercheLE/rabbitmq-mcp.git
cd rabbitmq-mcp

# Install uv package manager (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install project dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Generate OpenAPI-derived artifacts (schemas, operations, embeddings)
uv run python scripts/generate_schemas.py
uv run python scripts/generate_embeddings.py

# Run tests to verify setup
uv run pytest
```

**First Run (Stdio Transport):**

```bash
# Configure RabbitMQ connection
export AMQP_HOST=localhost
export AMQP_PORT=5672
export AMQP_USER=guest
export AMQP_PASSWORD=guest

# Run MCP server (stdio transport for AI assistants)
uv run python -m rabbitmq_mcp_server
```

**First Run (HTTP Transport):**

```bash
# Run MCP server on HTTP
uv run python -m rabbitmq_mcp_server --transport http --port 8000

# With CORS enabled for browser clients
uv run python -m rabbitmq_mcp_server --transport http --port 8000 \
  --cors-origins "https://app.example.com,http://localhost:3000"
```

**Claude Desktop Integration:**

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "rabbitmq": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/rabbitmq-mcp",
        "run",
        "python",
        "-m",
        "rabbitmq_mcp_server"
      ],
      "env": {
        "AMQP_HOST": "localhost",
        "AMQP_USER": "guest",
        "AMQP_PASSWORD": "guest"
      }
    }
  }
}
```
