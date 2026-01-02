# X402 Payment Integration for IATP

This module integrates the x402 (HTTP 402 Payment Required) protocol into the Inter-Agent Transfer Protocol (IATP), enabling utility agents to monetize their services and client agents to pay for API access using on-chain stablecoin payments.

## Overview

The x402 integration connects three key components:

1. **Utility Agents (Servers)**: Accept x402 payments for API access
2. **Client Agents**: Pay for services using x402 protocol  
3. **IATP Settlement Layer**: On-chain smart contract for payment settlement

```
┌──────────────────┐     X-PAYMENT header       ┌──────────────────┐
│  Client Agent    │ ──────────────────────────▶│  Utility Agent   │
│  (Payer)         │                            │  (Payee)         │
└──────────────────┘                            └──────────────────┘
         │                                               │
         │ 1. EIP-3009                                   │ 2. Provider
         │    Authorization                              │    Attestation
         │                                               │
         ▼                                               ▼
┌──────────────────────────────────────────────────────────────────┐
│              IATP Settlement Facilitator (Relayer)               │
│  - Verifies consumer signature                                   │
│  - Verifies provider attestation                                 │
│  - Submits to on-chain settlement                                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│            IATPSettlementLayer.sol (Smart Contract)              │
│  - Validates signatures                                          │
│  - Processes payment                                             │
│  - Credits provider's epoch balance                              │
│  - Handles disputes                                              │
└──────────────────────────────────────────────────────────────────┘
```

## Key Concepts

### X402 Protocol

X402 is a modern HTTP payment protocol that:
- Uses HTTP 402 status code (Payment Required)
- Supports instant stablecoin payments (USDC/TRAIA)
- Works with EIP-3009 payment authorizations
- Enables programmatic payments by AI agents

### IATP Settlement Layer

The on-chain component that:
- Manages utility agent contracts (TraiaUtilityAgent.sol)
- Processes settlements in epochs
- Handles dispute resolution
- Maintains reputation scores

### Facilitator vs Relayer

- **Facilitator** (x402 term): Service that verifies and settles payments
- **Relayer** (IATP term): Service that submits transactions to blockchain
- In IATP: The facilitator IS the relayer - it handles both verification and on-chain submission

## Components

### Server-Side (Utility Agents)

#### 1. X402 Middleware

Protects API endpoints with payment requirements:

```python
from traia_iatp.x402 import X402Config, X402ServicePrice, require_iatp_payment
from fastapi import FastAPI, Request

app = FastAPI()

# Configure x402 payments
x402_config = X402Config(
    enabled=True,
    pay_to_address="0x1234...",  # Utility agent contract address
    default_price=X402ServicePrice(
        usd_amount="0.01",  # $0.01 per request
        network="base-mainnet",
        asset_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
        max_timeout_seconds=300
    ),
    facilitator_url="https://api.traia.io/x402/facilitator",
    service_description="AI-powered financial sentiment analysis"
)

# Add middleware
@app.middleware("http")
async def payment_middleware(request: Request, call_next):
    middleware = require_iatp_payment(x402_config)
    return await middleware(request, call_next)

@app.post("/analyze")
async def analyze(request: Request):
    # This endpoint now requires payment
    data = await request.json()
    return {"sentiment": "positive", "confidence": 0.95}
```

#### 2. Custom Facilitator

The IATP Settlement Facilitator that connects to the smart contract:

```python
from traia_iatp.x402 import create_iatp_facilitator

# Create custom facilitator
facilitator = create_iatp_facilitator(
    relayer_url="https://api.traia.io/relayer",
    relayer_api_key=os.getenv("TRAIA_RELAYER_API_KEY"),
    provider_operator_key=os.getenv("OPERATOR_PRIVATE_KEY"),
    web3_provider="https://mainnet.base.org"
)

# Use in middleware
x402_config = X402Config(
    # ... other config ...
    facilitator_url="custom"  # Signals to use custom facilitator
)
```

### Client-Side (Agent-to-Agent Payments)

#### 1. X402-Enabled A2A Client

Automatically handles payments when calling utility agents:

```python
from traia_iatp.client import create_x402_a2a_client

# Create client with payment support
client = create_x402_a2a_client(
    agent_endpoint="https://sentiment-agent.traia.io",
    payment_private_key=os.getenv("CLIENT_PRIVATE_KEY"),
    max_payment_usd=5.0  # Max $5 per request
)

# Send message (automatically pays if required)
response = await client.send_message_with_payment(
    "Analyze sentiment: 'Tech stocks rally on strong earnings'"
)
print(response)
```

#### 2. Integration with CrewAI

Use paid utility agents as CrewAI tools:

```python
from crewai import Agent, Task, Crew
from traia_iatp.client import X402CrewAITool

# Create tool with payment support
sentiment_tool = X402CrewAITool(
    agent_endpoint="https://sentiment-agent.traia.io",
    payment_private_key=os.getenv("CLIENT_PRIVATE_KEY"),
    max_payment_usd=1.0
)

# Use in CrewAI agent
analyst = Agent(
    role="Financial Analyst",
    goal="Analyze market sentiment",
    tools=[sentiment_tool],
    backstory="Expert in market analysis"
)

task = Task(
    description="Analyze sentiment of recent tech news",
    expected_output="Sentiment summary with confidence scores",
    agent=analyst
)

crew = Crew(agents=[analyst], tasks=[task])
result = crew.kickoff()
```

## Configuration

### Environment Variables

```bash
# For Utility Agents (Server)
UTILITY_AGENT_CONTRACT_ADDRESS=0x...  # On-chain contract address
OPERATOR_PRIVATE_KEY=0x...            # For signing provider attestations
TRAIA_RELAYER_API_KEY=your-api-key    # For relayer authentication
X402_ENABLED=true                      # Enable x402 payments
X402_DEFAULT_PRICE_USD=0.01           # Default price per request

# For Client Agents
CLIENT_PRIVATE_KEY=0x...               # For signing payment authorizations
CLIENT_CONTRACT_ADDRESS=0x...          # Optional: client agent contract
MAX_PAYMENT_USD=10.0                   # Maximum payment per request
```

### Pricing Configuration

Per-skill pricing can be configured:

```python
x402_config = X402Config(
    enabled=True,
    pay_to_address="0x1234...",
    default_price=X402ServicePrice(usd_amount="0.01", ...),
    skill_prices={
        "sentiment_analysis": X402ServicePrice(usd_amount="0.01", ...),
        "entity_extraction": X402ServicePrice(usd_amount="0.02", ...),
        "summarization": X402ServicePrice(usd_amount="0.05", ...)
    }
)
```

## Payment Flow

### 1. Initial Request (No Payment)

```
Client → Utility Agent: GET /analyze
Utility Agent → Client: 402 Payment Required
{
  "x402Version": 1,
  "accepts": [{
    "scheme": "exact",
    "network": "base-mainnet",
    "maxAmountRequired": "10000",  // 0.01 USDC (6 decimals)
    "payTo": "0x...",  // Utility agent contract
    "resource": "https://agent.example.com/analyze",
    "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  // USDC
  }]
}
```

### 2. Payment Authorization (Client)

Client creates EIP-3009 authorization:

```javascript
{
  "from": "0xClient...",        // Client wallet
  "to": "0xUtilityAgent...",    // Utility agent contract
  "value": "10000",             // Amount in atomic units
  "validAfter": "1640000000",   // Unix timestamp
  "validBefore": "1640001000",  // Unix timestamp
  "nonce": "0xrandom..."        // Random nonce
}
```

Signs with EIP-712 and sends as X-PAYMENT header.

### 3. Request with Payment

```
Client → Utility Agent: GET /analyze
  X-PAYMENT: base64(signed_authorization)
  
Utility Agent:
  1. Decodes X-PAYMENT header
  2. Calls facilitator.verify(payment, requirements)
  3. Processes request if valid
  4. Calls facilitator.settle(payment, requirements)
  5. Returns response with X-PAYMENT-RESPONSE header
```

### 4. Settlement (Facilitator → Relayer → Blockchain)

```
Facilitator:
  1. Verifies consumer signature (EIP-712)
  2. Creates provider attestation (signed by operator key)
  3. Submits to relayer

Relayer:
  1. Calls IATPSettlementLayer.settleRequest()
  2. Verifies both signatures on-chain
  3. Processes EIP-3009 transfer
  4. Credits provider's epoch balance
  
Smart Contract:
  1. Validates utility agent is registered
  2. Validates signatures
  3. Transfers payment
  4. Records in current epoch
  5. Updates reputation scores
```

## Smart Contract Integration

### TraiaUtilityAgent.sol

Each deployed utility agent has an on-chain contract that:
- Stores agent metadata (name, description, operator address)
- Manages earnings and withdrawals
- Interacts with settlement layer

```solidity
contract TraiaUtilityAgent {
    address public creator;
    address public operatorAddress;
    string public name;
    string public description;
    
    // Withdraw earnings from settlement layer
    function releaseAndWithdrawAvailableEpochs(bool withdrawToCreator) external;
    
    // View balances in settlement layer
    function getSettlementLayerUnlockedBalance() external view returns (uint256);
    function getSettlementLayerLockedBalance() external view returns (uint256);
}
```

### IATPSettlementLayer.sol

The main settlement contract that:
- Processes service requests with signatures
- Manages epoch-based settlement
- Handles disputes
- Maintains provider/consumer reputation

```solidity
contract IATPSettlementLayer {
    // Settle a single request (called by relayer)
    function settleRequest(
        bytes calldata signedRequest,
        ServiceRequest calldata req,
        bytes calldata providerSignature,
        uint256 attestationTimestamp
    ) external onlyRelayer;
    
    // Provider withdraws earnings after release delay
    function releaseAndWithdrawAvailableEpochs(address provider) external;
    
    // Dispute resolution
    function disputeRequest(bytes32 requestId, string calldata reason) external;
    function resolveDispute(bytes32 requestId, bool consumerWon) external;
}
```

## Security Considerations

### Payment Verification

1. **Signature Validation**: All payments must have valid EIP-712 signatures
2. **Expiration Checks**: Authorizations have time bounds (validAfter/validBefore)
3. **Nonce Protection**: Prevents replay attacks
4. **Amount Verification**: Ensures payment matches requirements

### Provider Protection

1. **Epoch-Based Release**: Funds locked for dispute window (default: 2 epochs)
2. **Dispute System**: Consumers can dispute within window
3. **Reputation Tracking**: Maintains provider/consumer scores
4. **Operator Separation**: Operator key != creator key for security

### Client Protection

1. **Max Value Limits**: Clients can set maximum payment per request
2. **Pre-Verification**: Payment verified before service execution
3. **Dispute Rights**: Can dispute if service not delivered
4. **Auto-Refill Control**: Optional auto-refill with caps

## Testing

### Local Testing

```bash
# Start local test environment
docker-compose up -d

# Deploy test contracts
cd traia-contracts
npx hardhat deploy --network localhost

# Run IATP tests
cd IATP
pytest tests/test_x402_integration.py -v
```

### Integration Testing

```python
# Test utility agent with payments
async def test_paid_utility_agent():
    from traia_iatp.x402 import X402Config, X402ServicePrice
    from traia_iatp.client import create_x402_a2a_client
    
    # Configure test agent
    config = X402Config(
        enabled=True,
        pay_to_address="0xtest...",
        default_price=X402ServicePrice(
            usd_amount="0.01",
            network="base-sepolia",  # Testnet
            asset_address="0x...",   # Test USDC
        ),
        facilitator_url="http://localhost:8080/facilitator"
    )
    
    # Create test client
    client = create_x402_a2a_client(
        agent_endpoint="http://localhost:8000",
        payment_private_key="0xtest...",
        max_payment_usd=1.0
    )
    
    # Test payment flow
    response = await client.send_message_with_payment("test request")
    assert response is not None
```

## Deployment

### Deploying a Utility Agent with X402

```python
from traia_iatp.deployment import deploy_utility_agent_with_x402

result = await deploy_utility_agent_with_x402(
    mcp_server_name="sentiment-mcp",
    agent_name="FinBERT Sentiment Agent",
    # Contract will be deployed on-chain
    contract_network="base-mainnet",
    # X402 configuration
    x402_enabled=True,
    default_price_usd="0.01",
    facilitator_url="https://api.traia.io/x402/facilitator",
    # Deployment options
    deploy_to_cloudrun=True,
    push_to_mongodb=True
)

print(f"Deployed agent: {result['cloud_service_url']}")
print(f"Contract address: {result['contract_address']}")
print(f"X402 enabled: {result['x402_enabled']}")
```

## Troubleshooting

### Common Issues

1. **402 Response but Client Has No Payment Client**
   ```python
   # Solution: Configure payment client
   client = create_x402_a2a_client(
       agent_endpoint="...",
       payment_private_key="0x..."  # ← Add this
   )
   ```

2. **Payment Amount Exceeds Maximum**
   ```python
   # Solution: Increase max_payment_usd or negotiate with provider
   client = create_x402_a2a_client(
       agent_endpoint="...",
       payment_private_key="0x...",
       max_payment_usd=10.0  # ← Increase limit
   )
   ```

3. **Signature Verification Failed**
   - Check operator private key is correct
   - Ensure EIP-712 domain matches contract configuration
   - Verify timestamp is within valid bounds

4. **Settlement Fails**
   - Check relayer is accessible
   - Verify relayer API key is valid
   - Ensure provider is registered in UtilityAgentFactory
   - Check consumer has deposited funds in settlement layer

## Resources

- [X402 Protocol Specification](https://docs.cdp.coinbase.com/x402/welcome)
- [EIP-3009: Transfer With Authorization](https://eips.ethereum.org/EIPS/eip-3009)
- [EIP-712: Typed Structured Data Hashing](https://eips.ethereum.org/EIPS/eip-712)
- [IATP Repository](https://github.com/Traia-IO/IATP)
- [Smart Contracts Repository](https://github.com/Traia-IO/traia-contracts)

## Support

For issues or questions:
- GitHub Issues: [https://github.com/Traia-IO/IATP/issues](https://github.com/Traia-IO/IATP/issues)
- Discord: [https://discord.gg/traia](https://discord.gg/traia)
- Email: support@traia.io

