# IATP Search API Guide

The `iatp_search_api.py` module provides a high-level API for searching and retrieving information about utility agents and MCP servers from the IATP registry.

## Overview

This API provides read-only access to the MongoDB registry without requiring direct database dependencies. It automatically handles authentication using X.509 certificates or username/password.

## Authentication

The API automatically detects and uses the appropriate authentication method:

1. **X.509 Certificate** (if `MONGODB_X509_CERT_FILE` is set)
2. **Username/Password** (if `MONGODB_USER` and `MONGODB_PASSWORD` are set)
3. **Connection String** (if `MONGODB_CONNECTION_STRING` is set)

## Available Functions

### Utility Agent Functions

#### `find_utility_agent(name=None, capability=None, tag=None, query=None)`
Find a single utility agent by specific criteria.

```python
from traia_iatp.registry.iatp_search_api import find_utility_agent

# Find by exact name
agent = find_utility_agent(name="hyperliquid-mcp-traia-utility-agency")

# Find by capability
agent = find_utility_agent(capability="market_info")

# Find by tag
agent = find_utility_agent(tag="trading")

# Find by text query
agent = find_utility_agent(query="trading bot")
```

#### `list_utility_agents(limit=10, tags=None, capabilities=None, active_only=True)`
List utility agents with optional filters.

```python
from traia_iatp.registry.iatp_search_api import list_utility_agents

# List all active agents
agents = list_utility_agents(limit=20)

# Filter by tags
agents = list_utility_agents(tags=["trading", "defi"])

# Filter by capabilities
agents = list_utility_agents(capabilities=["market_info", "trading_orders"])
```

#### `search_utility_agents(query, limit=10, active_only=True, embedding_fields=None)`
Search utility agents using vector search.

```python
from traia_iatp.registry.iatp_search_api import search_utility_agents

# Search using default search_text embedding (recommended for best performance)
agents = await search_utility_agents("trading hyperliquid", limit=5)

# Search using specific embedding fields
agents = await search_utility_agents(
    "trading hyperliquid", 
    limit=5,
    embedding_fields=["description", "tags"]
)

# Search across all embedding fields (slower but more comprehensive)
agents = await search_utility_agents(
    "market data", 
    limit=5,
    embedding_fields=["description", "tags", "capabilities", "agent_card"]
)
```

### MCP Server Functions

#### `find_mcp_server(name=None, capability=None, tag=None, query=None)`
Find a single MCP server by specific criteria.

```python
from traia_iatp.registry.iatp_search_api import find_mcp_server

# Find by exact name
server = find_mcp_server(name="hyperliquid-mcp")

# Find by capability
server = find_mcp_server(capability="trading_orders")
```

#### `list_mcp_servers(limit=10, tags=None, capabilities=None)`
List MCP servers with optional filters.

```python
from traia_iatp.registry.iatp_search_api import list_mcp_servers

# List all servers
servers = list_mcp_servers(limit=10)

# Filter by capabilities
servers = list_mcp_servers(capabilities=["market_info"])
```

#### `search_mcp_servers(query, limit=10, embedding_fields=None)`
Search MCP servers using vector search.

```python
from traia_iatp.registry.iatp_search_api import search_mcp_servers

# Search using default embedding fields (description and capabilities)
servers = await search_mcp_servers("trading", limit=5)

# Search using only description embedding
servers = await search_mcp_servers(
    "trading", 
    limit=5,
    embedding_fields=["description"]
)
```

#### `get_mcp_server(name)`
Get detailed MCP server information by name (returns raw MongoDB document).

```python
from traia_iatp.registry.iatp_search_api import get_mcp_server

# Get full server details
server_doc = get_mcp_server("hyperliquid-mcp")
if server_doc:
    print(f"Server ID: {server_doc['_id']}")
    print(f"Capabilities: {server_doc['capabilities']}")
```

## Data Models

### UtilityAgentInfo
```python
@dataclass
class UtilityAgentInfo:
    agent_id: str
    name: str
    description: str
    base_url: str
    capabilities: List[str]
    tags: List[str]
    is_active: bool
    metadata: Dict[str, Any]
    skills: List[Dict[str, Any]]
```

### MCPServerInfo
```python
@dataclass
class MCPServerInfo:
    id: str
    name: str
    url: str
    description: str
    server_type: str
    capabilities: List[str]
    metadata: Dict[str, Any]
    tags: List[str]
```

## Complete Example

```python
#!/usr/bin/env python
import asyncio
import os
from traia_iatp.registry.iatp_search_api import (
    find_utility_agent,
    list_utility_agents,
    search_utility_agents,
    find_mcp_server,
    list_mcp_servers,
    search_mcp_servers
)


async def main():
    # Set authentication (choose one)
    os.environ["MONGODB_X509_CERT_FILE"] = "/path/to/cert.pem"
    # OR
    # os.environ["MONGODB_USER"] = "username"
    # os.environ["MONGODB_PASSWORD"] = "password"

    # Search for trading agents using vector search (default search_text embedding)
    print("Trading agents:")
    agents = await search_utility_agents("trading", limit=5)
    for agent in agents:
        print(f"- {agent.name}: {agent.base_url}")

    # Find specific agent
    agent = find_utility_agent(name="hyperliquid-mcp-traia-utility-agency")
    if agent:
        print(f"\nFound agent: {agent.name}")
        print(f"Capabilities: {', '.join(agent.capabilities)}")
        print(f"Tags: {', '.join(agent.tags)}")

    # List MCP servers
    print("\nMCP Servers:")
    servers = list_mcp_servers(limit=5)
    for server in servers:
        print(f"- {server.name}: {server.url}")
    
    # Search MCP servers with specific embedding field
    print("\nSearching MCP servers by description:")
    servers = await search_mcp_servers("trading", limit=3, embedding_fields=["description"])
    for server in servers:
        print(f"- {server.name}: {server.description}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Environment Configuration

Set the environment to control which MongoDB collections are used:

```bash
export ENV=test      # Uses test collections (default)
export ENV=staging   # Uses staging collections  
export ENV=prod      # Uses production collections
```

## Error Handling

The API will raise a `ValueError` if no authentication method is configured:

```python
try:
    agents = list_utility_agents()
except ValueError as e:
    print(f"Authentication error: {e}")
```

## Performance Notes

- The API uses connection pooling for efficiency
- Results are returned as Python dataclasses for easy access
- Text search requires MongoDB text indexes to be configured
- Consider using `limit` parameter to control result size

## Testing

Run the example script to test the API:

```bash
cd traia-centralized-backend
uv run python tests/test_mongodb_registry/example_iatp_registry_api.py
``` 