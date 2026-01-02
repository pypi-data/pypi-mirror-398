# IATP-D402: Inter-Agent Transfer Protocol with Payment Support

[![PyPI version](https://badge.fury.io/py/traia-iatp.svg)](https://badge.fury.io/py/traia-iatp)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-docs.d402.net-blue)](https://docs.d402.net)

**IATP-D402** enables AI agents and APIs to charge for their services using the D402 payment protocol (HTTP 402 Payment Required). Build payment-enabled:
- 🌐 APIs and web servers
- 🔧 MCP (Model Context Protocol) servers
- 🤖 A2A utility agents
- 🤝 CrewAI tools and agents

## 🚀 Quick Start

### Installation

```bash
pip install traia-iatp
```

### Add D402 to Your FastAPI Server (5 lines)

```python
from fastapi import FastAPI
from traia_iatp.d402.servers.fastapi import D402FastAPIMiddleware
from traia_iatp.d402.price_builder import D402PriceBuilder

app = FastAPI()

# Add D402 (5 lines)
price_builder = D402PriceBuilder(network="sepolia")
d402 = D402FastAPIMiddleware(server_address="0x...", facilitator_url="https://test-facilitator.d402.net")
price = price_builder.create_price(0.01)  # $0.01 USD
d402.register_endpoint("/api/analyze", price_wei=price.amount, token_address=price.asset.address, network="sepolia", description="Analysis")
d402.add_to_app(app)

# Your endpoint (unchanged!)
@app.post("/api/analyze")
async def analyze(request: Request):
    return {"result": "done"}
```

### Call D402-Protected Servers (2 lines)

```python
from traia_iatp.d402.clients.httpx import d402HttpxClient
from eth_account import Account

async with d402HttpxClient(
    operator_account=Account.from_key("0x..."),
    wallet_address="0x...",
    max_value=100000,
    base_url="http://localhost:8000"
) as client:
    # Payment automatic!
    response = await client.post("/api/analyze", json={"text": "test"})
```

## 📚 Documentation

**Full documentation**: [docs.d402.net](https://docs.d402.net)

### Quick Links

- **[Complete Examples](docs/examples/overview.md)** - Step-by-step integration examples (0-6)
- **[Server Integration](docs/d402-servers/overview.md)** - Add D402 to existing servers
- **[Client Integration](docs/d402-clients/overview.md)** - Call D402-protected APIs
- **[MCP Servers](docs/mcp-servers/overview.md)** - Build payment-enabled MCP servers
- **[Utility Agents](docs/utility-agents/overview.md)** - Build A2A utility agents
- **[CrewAI Integration](docs/crewai-integration/overview.md)** - Use D402 tools in CrewAI

### Complete Integration Examples

The [examples section](docs/examples/overview.md) provides complete, working code for:

0. **[Wallet Creation & Funding](docs/examples/0-wallet-creation-funding.md)** - Setup wallets, get testnet USDC
1. **[Existing Server → D402](docs/examples/1-server-to-d402.md)** - Add payments to your API (before/after)
2. **[Calling D402 Servers](docs/examples/2-calling-d402-servers.md)** - Build payment-enabled client
3. **[API → MCP Server](docs/examples/3-api-to-mcp-server.md)** - Convert REST to MCP tools
4. **[CrewAI + MCP](docs/examples/4-crewai-using-mcp.md)** - Use MCP server in crews
5. **[MCP → Utility Agent](docs/examples/5-mcp-to-utility-agent.md)** - Wrap MCP as A2A agent
6. **[CrewAI + Utility Agent](docs/examples/6-crewai-using-utility-agent.md)** - Use agents in crews

## 🌟 Key Features

### D402 Payment Protocol
- ✅ **HTTP 402 Payment Required** - Standard payment protocol
- ✅ **EIP-712 Signatures** - Secure payment authorization
- ✅ **On-Chain Settlement** - Smart contract-based settlements
- ✅ **Hosted Facilitators** - No infrastructure setup required

### Server Integration
- ✅ **FastAPI** - `D402FastAPIMiddleware`
- ✅ **Starlette** - `D402PaymentMiddleware`
- ✅ **Any ASGI Framework** - `D402ASGIWrapper` (Flask, Django, Quart, etc.)
- ✅ **5-line integration** - Minimal code changes

### Client Integration
- ✅ **HTTPX (Async)** - `d402HttpxClient` with automatic payment
- ✅ **Requests (Sync)** - Wrapper for synchronous apps
- ✅ **2-line integration** - Just make requests normally

### MCP & A2A
- ✅ **MCP Servers** - Payment-enabled tool servers
- ✅ **Utility Agents** - A2A protocol with D402
- ✅ **CrewAI Integration** - A2AToolkit for paid tools
- ✅ **Template Generation** - Auto-generate server code

## 🔧 What's in the Package

### Core Components (IN pip package)

```
src/traia_iatp/
├── d402/                     # D402 payment protocol
│   ├── servers/             # Server middleware (FastAPI, Starlette, MCP)
│   ├── clients/             # Client libraries (HTTPX, base client)
│   ├── asgi_wrapper.py      # Universal ASGI wrapper
│   ├── price_builder.py     # USD-based pricing
│   └── facilitator.py       # Facilitator client
│
├── mcp/                      # MCP server templates & tools
├── server/                   # Utility agent templates
├── client/                   # A2A client & CrewAI tools
├── contracts/                # Smart contract integration
└── registry/                 # Agent discovery & search
```

### Examples (NOT in pip package)

```
examples/                     # Integration examples
├── servers/                 # FastAPI, Starlette, ASGI examples
└── clients/                 # HTTPX, Requests examples
```

### Documentation (NOT in pip package)

```
docs/                         # GitBook documentation
├── getting-started/         # Installation, quick start
├── examples/                # Complete integration examples (0-6)
├── wallet-setup/            # Wallet creation & CLI
├── d402-servers/            # Server integration guides
├── d402-clients/            # Client integration guides
├── mcp-servers/             # MCP server guides
├── utility-agents/          # Utility agent guides
└── crewai-integration/      # CrewAI guides
```

## 🏗 Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Your Application                         │
│      (API / MCP Server / Utility Agent / CrewAI Crew)      │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                  IATP-D402 Framework                        │
│  • Server Middleware  • Client Libraries  • Templates      │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                  D402 Payment Protocol                      │
│  • HTTP 402  • EIP-712 Signing  • Facilitator Service      │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│               Smart Contracts (On-Chain)                    │
│         • IATPWallet  • Settlement  • Tokens                │
└────────────────────────────────────────────────────────────┘
```

## 🌐 Facilitators (No Setup Required)

**You don't need to run your own facilitator!**

- **All Testnets**: `https://test-facilitator.d402.net` (currently: Sepolia)
- **All Mainnets**: `https://facilitator.d402.net` (currently: Arbitrum)

See [Facilitator URLs](docs/getting-started/facilitators.md) for details.

## 🔐 Wallet Creation

```bash
# Create IATP wallet (owner creates their own wallet)
traia-iatp create-iatp-wallet \
  --owner-key 0x... \
  --create-operator \
  --wallet-name "My Server" \
  --wallet-type MCP_SERVER \
  --network sepolia
```

See [Creating Wallets](docs/wallet-setup/creating-wallets.md) for complete guide.

## 📦 Use Cases

### 1. Monetize Your API

```python
# Add payment to any endpoint
d402.register_endpoint("/api/analyze", price_usd=0.01)
```

### 2. Build Payment-Enabled MCP Servers

```python
@mcp.tool()
@require_payment_for_tool(price=price_builder.create_price(0.01))
def analyze(text: str) -> dict:
    return analyze_sentiment(text)
```

### 3. Use Paid Tools in CrewAI

```python
toolkit = A2AToolkit.create_from_endpoint(
    endpoint="http://localhost:9001",
    payment_private_key="0x...",
    wallet_address="0x...",
    max_payment_usd=1.0
)

agent = Agent(role="Analyst", tools=toolkit.tools)
```

## 🛠 CLI Commands

```bash
# Create IATP wallet
traia-iatp create-iatp-wallet --owner-key 0x... --create-operator

# Create utility agency from MCP server
traia-iatp create-agency --name "My Agent" --mcp-name "Trading MCP"

# List available agencies
traia-iatp list-agencies

# Search for tools
traia-iatp find-tools --query "sentiment analysis"
```

## 🔗 Links

- **Documentation**: [docs.d402.net](https://docs.d402.net)
- **PyPI**: [pypi.org/project/traia-iatp](https://pypi.org/project/traia-iatp)
- **GitHub**: [github.com/Traia-IO/IATP](https://github.com/Traia-IO/IATP)
- **Examples**: [docs/examples/](docs/examples/overview.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Support

- 📖 **Documentation**: [docs.d402.net](https://docs.d402.net)
- 🐛 **Issues**: [GitHub Issues](https://github.com/Traia-IO/IATP/issues)
- 💬 **Website**: [traia.io](https://traia.io)
- 📧 **Email**: support@traia.io

---

**Made with ❤️ by the Traia Team**
