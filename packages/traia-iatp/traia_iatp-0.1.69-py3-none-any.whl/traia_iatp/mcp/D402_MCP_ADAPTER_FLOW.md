# d402 Payment Flow in MCP Adapter

This document explains how the `TraiaMCPAdapter` integrates with d402 payment protocol to handle HTTP 402 Payment Required responses from MCP servers.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CrewAI Agent/Task                             │
│  Calls MCP tool (e.g., get_prompt)                              │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              TraiaMCPAdapter (extends MCPServerAdapter)         │
│  - Monkey-patches httpx.AsyncClient.__init__                    │
│  - Adds d402 payment hooks to all httpx clients                 │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              MCPServerAdapter (from crewai_tools)               │
│  - Creates httpx.AsyncClient instances                          │
│  - Makes MCP protocol requests (tools/call)                     │
│  - Returns BaseTool instances                                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│         httpx.AsyncClient (with d402 hooks applied)            │
│  - Event hooks: on_request, on_response                         │
│  - Automatically handles 402 responses                           │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Server (FastMCP)                         │
│  - Receives tools/call request                                  │
│  - Returns 402 Payment Required if no payment                   │
│  - Processes request if payment provided                        │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Flow

### 1. Initialization Phase

When `TraiaMCPAdapter` is created with d402 payment support:

```python
adapter = create_mcp_adapter_with_x402(
    url="http://localhost:8000/mcp",
    account=client_account,
    max_value=1_000_000
)
```

**What happens:**
1. `TraiaMCPAdapter.__init__()` is called
2. If `d402_account` is provided, `_apply_d402_patch()` is called
3. This monkey-patches `httpx.AsyncClient.__init__` globally
4. The patch ensures ALL future `httpx.AsyncClient` instances get d402 payment hooks

```python
def _apply_d402_patch(self):
    original_init = httpx.AsyncClient.__init__
    
    def patched_init(client_self, *args, **kwargs):
        # Call original init first
        original_init(client_self, *args, **kwargs)
        
        # Add d402 payment hooks to the client
        hooks = d402_payment_hooks(d402_account, max_value=d402_max_value)
        client_self.event_hooks = hooks  # or merge with existing
```

### 2. Context Manager Entry

When entering the adapter context:

```python
with adapter as tools:
    # Tools are now available
```

**What happens:**
1. `TraiaMCPAdapter.__enter__()` is called
2. This calls `super().__enter__()` which calls `MCPServerAdapter.__enter__()`
3. `MCPServerAdapter` creates an `httpx.AsyncClient` instance
4. **Because of our monkey-patch, this client automatically gets d402 hooks**
5. `MCPServerAdapter` makes an initial request to list tools
6. Returns list of `BaseTool` instances

### 3. Tool Execution Phase

When a CrewAI agent calls an MCP tool:

```python
result = tool._run(query="test")
```

**What happens:**
1. The `BaseTool` (created by `MCPServerAdapter`) executes
2. Internally, it uses the `httpx.AsyncClient` that was created in step 2
3. Makes an MCP protocol request: `POST /mcp` with JSON-RPC:
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "tools/call",
     "params": {
       "name": "get_prompt",
       "arguments": {"query": "test"}
     }
   }
   ```

### 4. First Request (No Payment)

```
Client → Server: POST /mcp (no X-Payment header)
Server → Client: HTTP 402 Payment Required
```

**Server Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": 402,
    "message": "Payment required",
    "data": {
      "d402Version": 1,
      "accepts": [
        {
          "scheme": "exact",
          "network": "base-sepolia",
          "maxAmountRequired": "1000",
          "payTo": "0x...",
          "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
          ...
        }
      ]
    }
  }
}
```

### 5. d402 Hook Intercepts 402 Response

The `HttpxHooks.on_response()` method is automatically called:

```python
async def on_response(self, response: Response) -> Response:
    if response.status_code != 402:
        return response  # Not a 402, pass through
    
    # Parse payment requirements
    data = response.json()
    payment_response = d402PaymentRequiredResponse(**data)
    
    # Select payment requirements (matches token/network)
    selected_requirements = self.client.select_payment_requirements(
        payment_response.accepts
    )
    
    # Create signed payment header
    payment_header = self.client.create_payment_header(
        selected_requirements, payment_response.d402_version
    )
    
    # Retry request with payment
    request = response.request
    request.headers["X-Payment"] = payment_header
    
    # Retry the request
    async with AsyncClient() as client:
        retry_response = await client.send(request)
        return retry_response
```

**What happens:**
1. Hook detects HTTP 402 status
2. Parses payment requirements from response
3. Selects appropriate payment option (matches token/network)
4. Creates EIP-3009 signed payment authorization using client's account
5. Base64-encodes the payment header
6. Retries the original request with `X-Payment` header

### 6. Payment Header Creation

The `d402Client.create_payment_header()` method:

```python
def create_payment_header(self, payment_requirements, d402_version):
    # Creates unsigned header structure
    unsigned_header = {
        "d402Version": d402_version,
        "scheme": payment_requirements.scheme,
        "network": payment_requirements.network,
        "payload": {
            "signature": None,
            "authorization": {
                "from": self.account.address,  # CLIENT's address
                "to": payment_requirements.pay_to,  # SERVER's address
                "value": payment_requirements.max_amount_required,
                "validAfter": timestamp - 60,
                "validBefore": timestamp + timeout,
                "nonce": random_nonce(),
            },
        },
    }
    
    # Signs with EIP-3009 transferWithAuthorization
    signed_header = sign_payment_header(
        self.account,  # CLIENT signs
        payment_requirements,
        unsigned_header
    )
    
    return base64_encode(signed_header)
```

**Key Points:**
- **CLIENT signs**: The payment is signed by the client's account (`d402_account`)
- **SERVER receives**: Payment is sent to server's address (`pay_to`)
- **EIP-3009**: Uses transferWithAuthorization (gasless payment)
- **Base64 encoded**: Payment header is base64-encoded for HTTP header

### 7. Retry Request (With Payment)

```
Client → Server: POST /mcp (with X-Payment header)
Server → Client: HTTP 200 OK (with result)
```

**Request Headers:**
```
X-Payment: <base64-encoded-signed-payment>
Content-Type: application/json
```

**Server Processing:**
1. MCP server's `D402MCPMiddleware` extracts `X-Payment` header
2. Decodes and validates the payment signature
3. Verifies payment matches endpoint requirements
4. Processes the tool call
5. Returns result

**Server Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Tool result here..."
      }
    ]
  }
}
```

## Key Components

### 1. Monkey-Patching Strategy

**Why monkey-patch?**
- `MCPServerAdapter` is from `crewai_tools` - we don't control its implementation
- It creates `httpx.AsyncClient` instances internally
- We need to inject d402 hooks into those clients
- Monkey-patching `__init__` ensures ALL httpx clients get hooks

**Limitations:**
- Global patch affects ALL httpx clients (not just MCP)
- Must restore original `__init__` in `__exit__`
- Thread-safety: Only one adapter should be active at a time

### 2. Event Hooks

httpx event hooks are called automatically:
- `on_request`: Before request is sent (currently no-op)
- `on_response`: After response is received (handles 402)

### 3. Payment Flow

```
1. Tool call → httpx request
2. Server returns 402
3. Hook intercepts 402
4. Creates signed payment
5. Retries request with X-Payment header
6. Server processes and returns result
```

## Example: Complete Flow

```python
from eth_account import Account
from traia_iatp.mcp.mcp_agent_template import run_with_mcp_tools, MCPServerInfo
from crewai import Agent, Task

# 1. Setup
account = Account.from_key("0x...")  # CLIENT's account
mcp_server = MCPServerInfo(
    id="canza-001",
    name="canza-mcp",
    url="http://localhost:8000/mcp",
    ...
)

# 2. Create agent and task
agent = MCPAgentBuilder.create_agent(...)
task = Task(description="Call get_prompt", agent=agent)

# 3. Run with d402 payment
result = run_with_mcp_tools(
    tasks=[task],
    mcp_server=mcp_server,
    d402_account=account,  # CLIENT's account for signing
    d402_max_value=1_000_000  # Safety limit
)

# What happens internally:
# 1. TraiaMCPAdapter patches httpx.AsyncClient.__init__
# 2. MCPServerAdapter creates httpx client (gets hooks automatically)
# 3. Agent calls tool → httpx makes request
# 4. Server returns 402 → hook intercepts
# 5. Hook creates payment → retries with X-Payment header
# 6. Server processes → returns result
# 7. Result returned to agent
```

## Important Notes

1. **Client Account**: The `d402_account` is the CLIENT's account that signs payments
2. **Server Address**: The server's payment address is configured server-side (SERVER_ADDRESS env var)
3. **Automatic**: The entire payment flow is automatic - agents don't need to handle 402s
4. **Transparent**: CrewAI agents see normal tool execution, payment happens behind the scenes
5. **Per-Request**: Each tool call that requires payment goes through this flow

## Troubleshooting

**Payment not working?**
- Check that monkey-patch is applied (look for debug logs)
- Verify httpx client has event_hooks set
- Check that 402 response is being intercepted
- Verify payment signature is valid

**Hooks not applied?**
- Ensure `d402_account` is provided
- Check that `D402_AVAILABLE` is True
- Verify httpx.AsyncClient is being created AFTER patch is applied

