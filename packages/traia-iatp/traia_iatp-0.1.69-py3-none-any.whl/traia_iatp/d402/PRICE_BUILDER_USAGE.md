# D402PriceBuilder - Simple Price Creation

## Overview

`D402PriceBuilder` is a helper class that simplifies creating `TokenAmount` objects for D402 payment configuration. It works with **any token** - just initialize it with your token configuration.

## Basic Usage

```python
from traia_iatp.d402 import D402PriceBuilder

# Initialize with YOUR token configuration (any token!)
builder = D402PriceBuilder(
    token_address="0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",  # Your token address
    token_decimals=6,                                              # Your token decimals
    network="sepolia",                                             # Your network
    token_symbol="USDC"                                            # Your token symbol
)

# Create prices easily
price_001 = builder.create_price(0.001)  # $0.001
price_01 = builder.create_price(0.01)    # $0.01
price_05 = builder.create_price(0.05)    # $0.05
```

## Examples with Different Tokens

### USDC (6 decimals)
```python
usdc_builder = D402PriceBuilder(
    token_address="0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
    token_decimals=6,
    network="sepolia",
    token_symbol="USDC"
)

price = usdc_builder.create_price(0.01)
# Result: TokenAmount(amount="10000", ...) → 0.01 * 10^6 = 10000
```

### TRAIA (18 decimals)
```python
traia_builder = D402PriceBuilder(
    token_address="0xYourTraiaTokenAddress...",
    token_decimals=18,  # Standard ERC20
    network="base-mainnet",
    token_symbol="TRAIA"
)

price = traia_builder.create_price(0.01)
# Result: TokenAmount(amount="10000000000000000", ...) → 0.01 * 10^18
```

### Any Custom Token
```python
custom_builder = D402PriceBuilder(
    token_address="0xYourCustomToken...",
    token_decimals=8,  # Your token's decimals
    network="arbitrum-mainnet",
    token_symbol="CUSTOM"
)

price = custom_builder.create_price(0.05)
# Result: TokenAmount(amount="5000000", ...) → 0.05 * 10^8 = 5000000
```

## Usage in Servers

### MCP Servers
```python
from traia_iatp.d402 import D402PriceBuilder
from traia_iatp.d402.servers.mcp import require_payment_for_tool

# Initialize builder from environment
builder = D402PriceBuilder(
    token_address=os.getenv("TOKEN_ADDRESS"),
    token_decimals=int(os.getenv("TOKEN_DECIMALS", "6")),
    network=os.getenv("NETWORK", "sepolia"),
    token_symbol=os.getenv("TOKEN_SYMBOL", "USDC")
)

# Use in decorators - clean and simple!
@mcp.tool()
@require_payment_for_tool(
    price=builder.create_price(0.001),  # $0.001
    description="Quick check"
)
async def quick_check(context):
    pass

@mcp.tool()
@require_payment_for_tool(
    price=builder.create_price(0.05),  # $0.05 - different price!
    description="Deep analysis"
)
async def deep_analysis(context):
    pass
```

### A2A Servers
```python
from traia_iatp.d402 import D402PriceBuilder
from traia_iatp.d402.servers.starlette import _build_payment_config

# Initialize builder from environment
builder = D402PriceBuilder(
    token_address=os.getenv("D402_TOKEN_ADDRESS"),
    token_decimals=int(os.getenv("D402_TOKEN_DECIMALS", "6")),
    network=os.getenv("D402_NETWORK", "sepolia"),
    token_symbol=os.getenv("D402_TOKEN_SYMBOL", "USDC")
)

# Create price
d402_token_amount = builder.create_price(float(os.getenv("D402_PRICE_USD", "0.01")))

# Build endpoint config
endpoint_payment_configs = {
    "/": _build_payment_config(
        price=d402_token_amount,
        server_address=contract_address,
        description="A2A request"
    )
}
```

### General FastAPI Servers
```python
from fastapi import FastAPI
from traia_iatp.d402 import D402PriceBuilder
from traia_iatp.d402.servers import require_payment, extract_payment_configs

app = FastAPI()

# Initialize builder from environment
builder = D402PriceBuilder(
    token_address=os.getenv("TOKEN_ADDRESS"),
    token_decimals=int(os.getenv("TOKEN_DECIMALS")),
    network=os.getenv("NETWORK"),
    token_symbol=os.getenv("TOKEN_SYMBOL")
)

# Use in decorators
@app.post("/analyze")
@require_payment(
    price=builder.create_price(0.01),
    endpoint_path="/analyze",
    description="Analysis"
)
async def analyze():
    pass

@app.post("/premium")
@require_payment(
    price=builder.create_price(0.10),  # Different price!
    endpoint_path="/premium",
    description="Premium analysis"
)
async def premium():
    pass
```

## Benefits

### Before (Manual TokenAmount creation)
```python
# Repetitive, error-prone
price1 = TokenAmount(
    amount="10000",
    asset=TokenAsset(
        address="0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
        decimals=6,
        network="sepolia",
        symbol="USDC",
        eip712=EIP712Domain(name="IATPWallet", version="1")
    )
)

price2 = TokenAmount(
    amount="50000",  # Have to calculate: 0.05 * 10^6
    asset=TokenAsset(
        address="0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",  # Same config repeated!
        decimals=6,
        network="sepolia",
        symbol="USDC",
        eip712=EIP712Domain(name="IATPWallet", version="1")
    )
)
```

### After (With D402PriceBuilder)
```python
# Clean, simple, reusable
builder = D402PriceBuilder(
    token_address="0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
    token_decimals=6,
    network="sepolia",
    token_symbol="USDC"
)

price1 = builder.create_price(0.01)   # Simple!
price2 = builder.create_price(0.05)   # No calculation needed!
```

## Methods

### `create_price(amount_usd: float) -> TokenAmount`

Create price from USD amount. Automatically converts to atomic units.

```python
builder = D402PriceBuilder(token_decimals=6, ...)

builder.create_price(0.01)   # → "10000" wei (0.01 * 10^6)
builder.create_price(0.001)  # → "1000" wei
builder.create_price(1.00)   # → "1000000" wei
```

### `create_price_wei(amount_wei: str) -> TokenAmount`

Create price from exact atomic units (when you don't want USD conversion).

```python
builder = D402PriceBuilder(token_decimals=6, ...)

builder.create_price_wei("10000")  # Exactly 10000 atomic units
builder.create_price_wei("1234")   # Exactly 1234 atomic units
```

## Token Decimals Reference

| Token | Decimals | Example: $0.01 |
|-------|----------|----------------|
| USDC | 6 | 10,000 |
| DAI | 18 | 10,000,000,000,000,000 |
| TRAIA | 18 | 10,000,000,000,000,000 |
| WBTC | 8 | 1,000,000 |

The builder handles the conversion automatically - you just specify the USD amount!

## Summary

✅ **Generic** - Works with any token  
✅ **Simple** - Initialize once, create many prices  
✅ **Type-safe** - Returns proper `TokenAmount` objects  
✅ **No calculation** - Automatically converts USD to atomic units  
✅ **Reusable** - One builder for all your endpoints  

**No more manual TokenAmount creation!**

