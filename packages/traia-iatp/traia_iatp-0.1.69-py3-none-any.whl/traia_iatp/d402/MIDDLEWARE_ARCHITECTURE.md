# D402 Payment Middleware Architecture

## Overview

The D402 payment protocol provides two middleware implementations to support different server types:

1. **`d402/starlette_middleware.py`** - MCP-specific (legacy, backwards compatible)
2. **`d402/servers/starlette.py`** - Generalized (recommended for new code)

## Middleware Comparison

| Feature | `starlette_middleware.py` | `servers/starlette.py` |
|---------|--------------------------|------------------------|
| **Use Case** | MCP servers only | Any Starlette server |
| **Endpoint Patterns** | `/mcp` only | `/mcp`, `/`, `*`, custom |
| **Configuration** | `tool_payment_configs` only | `tool_payment_configs` OR `price`+`endpoint_patterns` |
| **Type Safety** | Dict-based configs | Supports `TokenAmount`/`TokenAsset` objects |
| **Status** | Maintained for compatibility | Recommended for new code |

## Usage Patterns

### Pattern 1: MCP Servers (with decorators)

MCP servers use decorators like `@require_payment_for_tool()` which auto-generate payment configs.

```python
from traia_iatp.d402.starlette_middleware import D402PaymentMiddleware
from traia_iatp.d402.payment_introspection import extract_payment_configs_from_mcp

# Extract configs from decorators
tool_payment_configs = extract_payment_configs_from_mcp(mcp, SERVER_ADDRESS)

# Add middleware
app.add_middleware(
    D402PaymentMiddleware,
    tool_payment_configs=tool_payment_configs,
    server_address=SERVER_ADDRESS,
    requires_auth=True,
    internal_api_key=API_KEY
)
```

**Files using this pattern:**
- `mcp/templates/server.py.j2` (MCP server template)
- Generated MCP servers (e.g., `coingecko-api-mcp-server`)

### Pattern 2: A2A Servers (with price + patterns)

A2A servers don't use decorators - they specify price and endpoint patterns directly.

```python
from traia_iatp.d402.servers import D402PaymentMiddleware
from traia_iatp.d402.types import TokenAmount, TokenAsset, EIP712Domain

# Create price with proper types
price = TokenAmount(
    amount="10000",  # 0.01 USDC
    asset=TokenAsset(
        address="0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
        decimals=6,
        network="sepolia",
        eip712=EIP712Domain(
            name="IATPWallet",
            version="1"
        )
    )
)

# Add middleware with price + patterns
app.add_middleware(
    D402PaymentMiddleware,
    price=price,
    endpoint_patterns=["/"],  # Protect root endpoint
    server_address=CONTRACT_ADDRESS,
    description="A2A request",
    requires_auth=False  # Payment-only (no API keys)
)
```

**Files using this pattern:**
- `server/templates/__main__.py.j2` (A2A utility agent template)
- Generated utility agents

### Pattern 3: General Servers (with tool configs)

General servers can also use the generalized middleware with pre-built configs.

```python
from traia_iatp.d402.servers import D402PaymentMiddleware

# Build configs manually
tool_payment_configs = {
    "/api/analyze": {
        "price_wei": "10000",
        "token_address": "0x...",
        # ... full config
    }
}

# Add middleware
app.add_middleware(
    D402PaymentMiddleware,
    tool_payment_configs=tool_payment_configs,
    server_address=SERVER_ADDRESS
)
```

## Endpoint Pattern Matching

The generalized middleware supports multiple endpoint patterns:

| Pattern | Example | Matches |
|---------|---------|---------|
| **MCP** | `/mcp` with `tools/call` | MCP tool calls: `/mcp/tools/{tool_name}` |
| **A2A** | `/` | A2A JSON-RPC at root path |
| **Exact Match** | `/api/analyze` | Only `/api/analyze` |
| **Wildcard** | `*` | All POST endpoints |

## Migration Guide

### Existing MCP Servers
**No action needed** - continue using `starlette_middleware.py`

### New MCP Servers
Can use either middleware (both work the same for MCP)

### New A2A/Utility Servers
**Must use** `servers/starlette.py` with `price` + `endpoint_patterns`

### Custom Servers
**Recommended** to use `servers/starlette.py` for flexibility

## Code Organization

```
traia_iatp/
├── d402/
│   ├── starlette_middleware.py   # MCP-specific (legacy)
│   ├── servers/
│   │   ├── __init__.py
│   │   └── starlette.py          # Generalized (recommended)
│   ├── types.py                  # TokenAmount, TokenAsset, etc.
│   └── ...
├── mcp/
│   └── templates/
│       └── server.py.j2          # Uses starlette_middleware.py
└── server/
    └── templates/
        └── __main__.py.j2        # Uses servers/starlette.py
```

## Key Differences

### Configuration Building

**MCP (decorator-based):**
```python
# Configs extracted from @require_payment_for_tool decorators
tool_payment_configs = extract_payment_configs_from_mcp(mcp, SERVER_ADDRESS)
# Result: {"tool_name": {"price_wei": "...", "token_address": "...", ...}}
```

**A2A (price-based):**
```python
# Price defined with type-safe objects
price = TokenAmount(amount="10000", asset=TokenAsset(...))
# Middleware builds configs internally: {"/": {"price_wei": "10000", ...}}
```

### Endpoint Protection

**MCP:**
- Protects individual tools within `/mcp` endpoint
- Each tool can have different prices
- Example: `/mcp/tools/get_price` costs 0.001 USDC

**A2A:**
- Protects entire endpoint (usually `/`)
- Single price for all methods on that endpoint
- Example: All JSON-RPC methods to `/` cost 0.01 USDC

## Testing

Both middlewares are tested through their respective server types:

**MCP Servers:**
```bash
# Test MCP server with D402
uv run pytest automated-tests/mcp/coingecko-api-mcp-server/ -v
```

**A2A Servers:**
```bash
# Test utility agent with D402
uv run pytest automated-tests/agents/coingecko-utility-agent/ -v
```

## Summary

- **Use `starlette_middleware.py`** for MCP servers (backwards compatible)
- **Use `servers/starlette.py`** for A2A servers and new code (flexible, type-safe)
- Both middlewares share the same core payment validation logic
- Both support facilitator integration for settlement
- The generalized version is recommended for all new development

