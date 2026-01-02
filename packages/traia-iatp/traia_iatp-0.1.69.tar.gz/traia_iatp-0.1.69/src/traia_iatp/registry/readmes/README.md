# IATP Registry Module

The IATP Registry provides a centralized database for discovering and managing:
- **Utility Agents**: IATP-enabled AI agents exposed via the A2A protocol
- **MCP Servers**: Model Context Protocol servers that can be wrapped as utility agents

## Architecture

The registry module has a layered architecture:

```
┌─────────────────────────────────────┐
│     External Clients / Services      │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│      iatp_registry_api.py           │  ← High-level API (no MongoDB write dependency)
│   (find_*, list_*, search_*)        │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│       mongodb_registry.py           │  ← MongoDB implementation
│  (UtilityAgentRegistry, etc.)       │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│        MongoDB Atlas Cloud          │  ← Database backend
└─────────────────────────────────────┘
```

## Authentication Methods

The registry supports two authentication methods for MongoDB access, with the following priority:

### 1. X.509 Certificate Authentication (Recommended) ⭐

Use SSL/TLS certificates for authentication without passwords. Most secure option.

```bash
export MONGODB_X509_CERT_FILE=/path/to/certificate.pem
```

See [MONGODB_X509_AUTH.md](./MONGODB_X509_AUTH.md) for detailed setup instructions.

### 2. Username/Password Authentication

Traditional username/password authentication.

```bash
export MONGODB_USER=username
export MONGODB_PASSWORD=password
```

You can also provide a full connection string:

```bash
export MONGODB_CONNECTION_STRING=mongodb+srv://user:pass@cluster.mongodb.net/...
```

## Quick Start

### Using the High-Level API (No MongoDB Required)

```python
from traia_iatp.registry.iatp_search_api import find_utility_agent, list_mcp_servers

# Find a specific utility agent
agent = await find_utility_agent(name="trading-agent")

# List available MCP servers
servers = list_mcp_servers(limit=10)
```

### Direct MongoDB Access

```python
from traia_iatp.registry.mongodb_registry import UtilityAgentRegistry

# Registry will automatically use configured authentication
registry = UtilityAgentRegistry()

# Query agents
agents = await registry.query_agents(
    query="trading",
    tags=["finance"],
    limit=10
)
```

## Search Capabilities

The registry supports multiple search methods:

### 1. Text Search
Basic MongoDB text search across indexed fields.

```python
agents = await registry.query_agents(query="trading bot")
```

### 2. Atlas Search
Advanced full-text search using MongoDB Atlas Search.

```python
agents = await registry.atlas_search("AI trading assistant")
```

### 3. Vector Search
Vector search uses OpenAI embeddings to find semantically similar agents:

```python
# By default, searches using the comprehensive search_text embedding (recommended)
results = await registry.vector_search_text("trading bots", limit=5)

# You can also search on specific embedding fields
results = await registry.vector_search_text("defi", search_field="tags", limit=5)
```

The `search_text` field contains a concatenation of:
- Agent name and description
- All capabilities and tags
- Agent card details (name, description)
- All skill names, descriptions, examples, and tags

This makes it ideal for comprehensive semantic search.

## Environment Configuration

### Required Settings

- `ENV`: Environment name (`test`, `staging`, `prod`)
- One of the authentication methods above

### Optional Settings

- `ENABLE_EMBEDDINGS`: Enable vector search (`true`/`false`, default: `true`)
- `OPENAI_API_KEY`: Required if embeddings are enabled

## Collections

The registry uses environment-specific collections:

- **Utility Agents**: `iatp-utility-agent-registry-{env}`
- **MCP Servers**: `iatp-mcp-server-registry-{env}`

## Indexes

### Regular Indexes (Created Automatically)
- `agent_id` (unique)
- `name` (unique)
- `base_url` (unique)
- `is_active`
- `tags`
- `capabilities`
- `registered_at`

### Search Indexes (Create via Atlas UI)
- Atlas Search indexes for full-text search
- Vector Search indexes for semantic search

See [atlas_search_indexes.json](./atlas_search_indexes.json) for index definitions.

## Examples

### Register a New Utility Agent

```python
from traia_iatp.core.models import UtilityAgent, AgentEndpoints

agent = UtilityAgent(
    name="My Trading Bot",
    description="An AI agent for automated trading",
    capabilities=["trade", "analyze", "report"],
    endpoints=AgentEndpoints(
        base_url="https://mybot.example.com"
    )
)

registry = UtilityAgentRegistry()
entry = await registry.add_utility_agent(agent)
```

### Search with Filters

```python
# Find agents with specific capabilities
agents = await registry.query_agents(
    capabilities=["trade", "analyze"],
    tags=["crypto"],
    active_only=True
)
```

## Testing

### Test Authentication

```bash
# Test X.509 certificate authentication
uv run python tests/test_mongodb_registry/test_mongodb_x509_auth.py

# Run general registry tests
uv run python -m pytest tests/test_mongodb_registry/
```

### Example Scripts

```bash
# X.509 authentication example
uv run python tests/test_mongodb_registry/example_x509_auth.py

# IATP Registry API example
uv run python tests/test_mongodb_registry/example_iatp_registry_api.py
```

## Security Best Practices

1. **Use X.509 certificates** for production deployments
2. **Rotate credentials** regularly
3. **Use environment-specific** collections and credentials
4. **Enable IP whitelisting** in MongoDB Atlas
5. **Monitor access logs** for unauthorized attempts

## Troubleshooting

### Connection Issues

1. Check authentication environment variables
2. Verify MongoDB Atlas IP whitelist
3. Test with `test_mongodb_x509_auth.py`

### Search Not Working

1. Ensure Atlas Search indexes are created
2. Wait for index building to complete
3. Check `ENABLE_EMBEDDINGS` setting

### Certificate Authentication Failed

1. Verify certificate file exists and is readable
2. Check certificate user in `$external` database
3. Ensure certificate hasn't expired

## Related Documentation

- [MONGODB_X509_AUTH.md](./MONGODB_X509_AUTH.md) - X.509 certificate setup
- [ATLAS_SEARCH_SETUP.md](./ATLAS_SEARCH_SETUP.md) - Atlas Search configuration
- [../api/README.md](../api/README.md) - REST API service 