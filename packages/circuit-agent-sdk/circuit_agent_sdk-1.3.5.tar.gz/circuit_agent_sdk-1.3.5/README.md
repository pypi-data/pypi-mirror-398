# Circuit Agent SDK - Python

> NOTE: Please refer to our all in one [Circuit Documentation](https://app.gitbook.com/o/yfLOFAxdeW0k9oNMRvxo/s/JCFI1CxS0CCJGcFs2OVc/agent-developers/sdk-reference):
> We will be reducing this down to instructions for sdk developers and will refer agent developers to the public gitbooks.

> **Clean, unified, type-safe Python SDK for building cross-chain agents on Circuit**

A simplified Python SDK for building automated agents to deploy on Circuit. Agents receive a single `AgentContext` object containing everything they need - request data, SDK methods, and unified logging. No boilerplate, no return values to manage, just write your logic.

> **💡 Best used with [Circuit Agents CLI](https://github.com/circuitorg/agents-cli)** - Deploy, manage, and test your agents with ease

## 📑 Table of Contents

- [Circuit Agent SDK - Python](#circuit-agent-sdk---python)
  - [📑 Table of Contents](#-table-of-contents)
  - [🚀 Quick Start](#-quick-start)
    - [Install the SDK](#install-the-sdk)
    - [Create Your First Agent](#create-your-first-agent)
      - [Required Asset setup](#required-asset-setup)
  - [🎯 Core Concepts](#-core-concepts)
    - [The AgentContext Object](#the-agentcontext-object)
    - [Run/Unwind Function Requirements](#rununwind-function-requirements)
  - [📝 Unified Logging with agent.log()](#-unified-logging-with-agentlog)
  - [💾 Session Memory Storage](#-session-memory-storage)
  - [🌉 Cross-Chain Swaps with Swidge](#-cross-chain-swaps-with-swidge)
    - [Get and execute a quote](#get-and-execute-a-quote)
  - [📈 Polymarket Prediction Markets](#-polymarket-prediction-markets)
    - [Place Market Orders](#place-market-orders)
    - [Redeem Positions](#redeem-positions)
  - [Hyperliquid Trading](#hyperliquid-trading)
    - [Account Information](#account-information)
    - [Place Orders](#place-orders)
    - [Order Management](#order-management)
    - [Transfer Between Accounts](#transfer-between-accounts)
  - [📊 Transaction History](#-transaction-history)
  - [🚀 Sign \& Send Transactions](#-sign--send-transactions)
    - [Ethereum (any EVM chain)](#ethereum-any-evm-chain)
    - [Solana](#solana)
  - [⚡ Error Handling](#-error-handling)
  - [🛠️ Deployment](#️-deployment)
    - [What You Write](#what-you-write)
    - [Deploy to Circuit](#deploy-to-circuit)
    - [Test Locally](#test-locally)
  - [🧪 Manual Instantiation (Jupyter/Testing)](#-manual-instantiation-jupytertesting)
  - [📚 Working Examples](#-working-examples)
    - [`demo-agent.py`](#demo-agentpy)
    - [`examples/kitchen-sink.ipynb`](#exampleskitchen-sinkipynb)
  - [🎯 Key Takeaways](#-key-takeaways)
  - [📖 Additional Resources](#-additional-resources)

## 🚀 Quick Start

### Install the SDK
```bash
pip install circuit-agent-sdk
# or with uv
uv pip install circuit-agent-sdk
```

### Create Your First Agent

Every agent receives a single `AgentContext` object that provides:

**Session Data:**
- `agent.sessionId` - Unique session identifier
- `agent.sessionWalletAddress` - The wallet address for this session
- `agent.currentPositions` - Assets allocated to the agent at the start of this execution

**Available Methods:**
- `agent.log()` - Send messages to users and log locally
- `agent.memory` - Persist data across executions (`.set()`, `.get()`, `.list()`, `.delete()`)
- `agent.platforms.polymarket` - Trade prediction markets (`.market_order()`, `.redeem_positions()`)
- `agent.platforms.hyperliquid` -  trading (`.place_order()`, `.positions()`, `.balances()`, `.transfer()`)
- `agent.swidge` - Cross-chain swaps and bridges (`.quote()`, `.execute()`)
- `agent.sign_and_send()` - Execute custom built transactions on any supported chain
- `agent.sign_message()` - Sign messages (EVM only)
- `agent.transactions()` - Get transaction history with asset changes

**Important:** `currentPositions` reflects your allocated assets at the **start** of each execution. You will need to use the agent.get_current_positions() method to pull fresh values after executing transactions. It's important to consider the hasPendingTxs if you had recently submitted transactions. If hasPendingTxs is true, the balances you received may not be 100% up to date.

#### Required Asset setup
> Note: For native tokens, use the following null addresses for solana/ethereum
```toml
// Requiring 1 SOL
[[requiredAssets]]
network = "solana"
address = "11111111111111111111111111111111"
minimumAmount = "1000000000"

// Requiring 1 ETH
[[requiredAssets]]
network = "ethereum:<chainId>"
address = "0x0000000000000000000000000000000000000000"
minimumAmount = "1000000000000000000"
```


```python
from agent_sdk import Agent, AgentContext
import time

def run(agent: AgentContext) -> None:
    """
    Main agent logic - receives AgentContext with everything needed.
    No return value - errors are caught automatically.
    """
    # Access session data
    agent.log(f"Starting execution for session {agent.sessionId}")
    agent.log(f"Wallet: {agent.sessionWalletAddress}")
    agent.log(f"Managing {len(agent.currentPositions)} allocated positions")

    # Use SDK methods
    agent.memory.set("last_run", str(time.time()))

    # Your agent logic here - track position changes within this execution
    # Circuit will provide updated positions on the next run

def unwind(agent: AgentContext, positions: list) -> None:
    """
    Adjust the agent's allocation by unwinding a subset (or all) of positions.

    `positions` is the set Circuit is requesting you to unwind (may be a subset).
    """
    agent.log(f"Unwinding {len(positions)} positions")
    agent.memory.delete("temp_data")

# Boilerplate
agent = Agent(
    run_function=run,
    unwind_function=unwind,
)

handler = agent.get_handler()

if __name__ == "__main__":
    agent.run()
```

## 🎯 Core Concepts

### The AgentContext Object

Every agent function receives a single `AgentContext` object that contains:

**Request Data:**
- `agent.sessionId` - Unique session identifier
- `agent.sessionWalletAddress` - Wallet address for this session
- `agent.currentPositions` - Current positions allocated to this agent

**SDK Methods:**
- `agent.log()` - Unified logging (console + backend)
- `agent.memory` - Session-scoped key-value storage
- `agent.platforms.polymarket` - Prediction market operations
- `agent.swidge` - Cross-chain swap operations
- `agent.sign_and_send()` - Sign and broadcast transactions
- `agent.sign_message()` - Sign messages on EVM
- `agent.transactions()` - Get transaction history with asset changes

### Run/Unwind Function Requirements

1. **Signature (run)**: `def run(agent: AgentContext) -> None:`
2. **Signature (unwind)**: `def unwind(agent: AgentContext, positions: list[CurrentPosition]) -> None:`
3. **Return**: Always return `None` (or no return statement)
4. **Errors**: You should surface any relevant errors via agent.log('error message',error=True). All errors from built-in sdk functions will be caught gracefully and provided in the return data for you to handle as necessary.

## 📝 Unified Logging with agent.log()

Use `agent.log()` to communicate with your users and debug your agent. Every message appears in your terminal, and by default also shows up in the Circuit UI for your users to see. Simply pass debug=True to skip sending the message to the user.

```python
def run(agent: AgentContext) -> None:
    # Standard log: Shows to user in Circuit UI
    agent.log("Processing transaction")

    # Error log: Shows to user in Circuit UI (as an error)
    result = agent.memory.get("key")
    if not result.success:
        agent.log(result.error_message, error=True)

    # Debug log: Only you see this in your terminal
    agent.log("Internal state: processing...", debug=True)

    # Logging dicts and pydantic models
    # Both are pretty-printed to console and serialized/truncated for backend
    agent.log({"wallet": agent.sessionWalletAddress, "status": "active"})

    # Check if message reached the user
    log_result = agent.log("Important message")
    if not log_result.success:
        # Rare - usually means Circuit UI is unreachable
        pass
```

**What Your Users See:**

| Code | You See (Terminal) | User Sees (Circuit UI) |
|------|-------------------|----------------------|
| `agent.log("msg")` | ✅ In your terminal | ✅ In Circuit UI |
| `agent.log("msg", error=True)` | ✅ As error in terminal | ✅ As error in Circuit UI |
| `agent.log("msg", debug=True)` | ✅ In terminal | ❌ Hidden from user |
| `agent.log("msg", error=True, debug=True)` | ✅ As error in terminal | ❌ Hidden from user |

## 💾 Session Memory Storage

Store and retrieve data for your agent's session with simple operations. Memory is **automatically scoped to your session ID**, and for now is simple string storage. You will need to handle serialization of whatever data you want to store here.

```python
def run(agent: AgentContext) -> None:
    # Set a value
    result = agent.memory.set("lastSwapNetwork", "ethereum:42161")
    if not result.success:
        agent.log(result.error_message, error=True)

    # Get a value
    result = agent.memory.get("lastSwapNetwork")
    if result.success and result.data:
        network = result.data.value
        agent.log(f"Using network: {network}")
    else:
        agent.log("No saved network found")

    # List all keys
    result = agent.memory.list()
    if result.success and result.data:
        agent.log(f"Found {result.data.count} keys: {result.data.keys}")

    # Delete a key
    result = agent.memory.delete("tempData")
```

**All memory operations return responses with `.success` and `.error_message`:**

```python
result = agent.memory.set("key", "value")
if not result.success:
    agent.log(f"Failed to save: {result.error_message}", error=True)
```

## 🌉 Cross-Chain Swaps with Swidge

Built-in Swidge integration for seamless cross-chain token swaps and bridges.

### Get and execute a quote
> Note: It is important to always validate quotes before executing. Circuit will always do its best to return a quote, and as of now, will only filter out quotes with price impacts exceeding 100% to ensure maximum flexibility. It is on the agent to makes sure a quote is valid, given its own parameters

> **Bulk Execution:** `execute()` accepts both single quotes and lists. Pass a list to execute multiple swaps in parallel: `agent.swidge.execute([quote1.data, quote2.data])` returns a list of results. Note: Use explicit `is not None` checks for proper type narrowing.

```python
def run(agent: AgentContext) -> None:
    # 1. Get quote
    quote = agent.swidge.quote({
        "from": {"network": "ethereum:8453", "address": agent.sessionWalletAddress},
        "to": {"network": "ethereum:137", "address": agent.sessionWalletAddress},
        "amount": "1000000000000000",  # 0.001 ETH
        "toToken": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
        "slippage": "2.0",
        "priceImpact": "100.0"
    })

    if not quote.success:
        _ = agent.log(f"Quote failed: {quote.error_message}", error=True)
        return

    if abs(float(quote.data.priceImpact.percentage)) > 10:
        _ = agent.log(f"Warning: Price impact is too high: {quote.data.priceImpact.percentage}%", error=True, debug=True)
    else:
        _ = agent.log(f"You'll receive: {quote.data.assetReceive.amountFormatted}")
        _ = agent.log(f"Fees: {', '.join([f.name for f in quote.data.fees])}")

        # 2. Execute the swap
        result = agent.swidge.execute(quote.data)

        if result.success and result.data:
            agent.log(f"Swap status: {result.data.status}")
            if result.data.status == "success":
                agent.log("✅ Swap completed!")
                agent.log(f"In tx: {result.data.in_.txs}")
                agent.log(f"Out tx: {result.data.out.txs}")
            elif result.data.status == "failure":
                agent.log("❌ Swap failed", error=True)
        else:
            agent.log(result.error_message, error=True)
```

## 📈 Polymarket Prediction Markets

Trade prediction markets on Polygon.

### Place Market Orders
> Note: Right now, polymarket's API accepts different decimal precision for buys and sells, this will result in dust positions if you are selling out of a position before expiry. Once expired, dust can be cleaned up during the redeem step.

```python
def run(agent: AgentContext) -> None:
    # Buy order - size is USD amount to spend
    buy_order = agent.platforms.polymarket.market_order({
        "tokenId": "86192057611122246511563653509192966169513312957180910360241289053249649036697",
        "size": 3,  # Spend $3
        "side": "BUY"
    })

    if buy_order.success and buy_order.data:
        agent.log(f"Order ID: {buy_order.data.orderInfo.orderId}")
        agent.log(f"Price: ${buy_order.data.orderInfo.priceUsd}")
        agent.log(f"Total: ${buy_order.data.orderInfo.totalPriceUsd}")
    else:
        agent.log(buy_order.error_message, error=True)

    # Sell order - size is number of shares to sell
    sell_order = agent.platforms.polymarket.market_order({
        "tokenId": "86192057611122246511563653509192966169513312957180910360241289053249649036697",
        "size": 5.5,  # Sell 5.5 shares
        "side": "SELL"
    })
```

### Redeem Positions

```python
def unwind(agent: AgentContext, positions: list) -> None:
    """Redeem all settled positions (often done during unwind)."""
    redemption = agent.platforms.polymarket.redeem_positions()

    if redemption.success and redemption.data:
        successful = [r for r in redemption.data if r.success]
        agent.log(f"Redeemed {len(successful)} positions")
    else:
        agent.log(redemption.error_message, error=True)
```

## Hyperliquid Trading

Trade perpetual futures (with leverage) and spot markets on Hyperliquid DEX.

**Market Types:**
- **Perp**: Perpetual futures trading with leverage (use `market: "perp"` in order parameters)
- **Spot**: Spot trading (use `market: "spot"` in order parameters)

**Asset Naming for Spot:**
- Non-Hypercore-native assets use "Unit" prefix: `UBTC` (Unit BTC), `UETH` (Unit ETH)
- Example: To trade BTC spot, use symbol `UBTC-USDC`

### Account Information

```python
def run(agent: AgentContext) -> None:
    # Check balances
    balances = agent.platforms.hyperliquid.balances()
    if balances.success and balances.data:
        agent.log(f"Account value: ${balances.data.perp.accountValue}")
        agent.log(f"Withdrawable: ${balances.data.perp.withdrawable}")

    # View open positions
    positions = agent.platforms.hyperliquid.positions()
    if positions.success and positions.data:
        for pos in positions.data:
            agent.log(f"{pos.symbol}: {pos.side} {pos.size} @ {pos.entryPrice}")
            agent.log(f"Unrealized PnL: ${pos.unrealizedPnl}")
```

### Place Orders

```python
def run(agent: AgentContext) -> None:
    # Perp market order
    perp_order = agent.platforms.hyperliquid.place_order({
        "symbol": "BTC-USD",
        "side": "buy",
        "size": 0.0001,
        "price": 110000,  # Acts as slippage limit for market orders
        "market": "perp",
        "type": "market"
    })

    if perp_order.success and perp_order.data:
        agent.log(f"Perp Order {perp_order.data.orderId}: {perp_order.data.status}")
    else:
        agent.log(perp_order.error, error=True)

    # Spot market order (for non-Hypercore-native assets like BTC)
    spot_order = agent.platforms.hyperliquid.place_order({
        "symbol": "UBTC-USDC",  # Unit BTC
        "side": "buy",
        "size": 0.0001,
        "price": 110000,
        "market": "spot",  # Changed to spot
        "type": "market"
    })

    if spot_order.success and spot_order.data:
        agent.log(f"Spot Order {spot_order.data.orderId}: {spot_order.data.status}")
    else:
        agent.log(spot_order.error, error=True)
```

### Order Management

```python
def run(agent: AgentContext) -> None:
    # Get open orders
    open_orders = agent.platforms.hyperliquid.open_orders()

    # Get specific order details
    order = agent.platforms.hyperliquid.order("12345")

    # Cancel an order
    result = agent.platforms.hyperliquid.delete_order("12345", "BTC-USD")

    # View historical orders
    history = agent.platforms.hyperliquid.orders()

    # Check order fills
    fills = agent.platforms.hyperliquid.order_fills()
```

### Transfer Between Accounts

```python
def run(agent: AgentContext) -> None:
    # Transfer USDC from spot to perp account
    transfer = agent.platforms.hyperliquid.transfer({
        "amount": 1000.0,
        "toPerp": True
    })

    if transfer.success:
        agent.log("Transfer completed")
```

## 📊 Transaction History

Get a list of asset changes for all confirmed transactions during your session. This is useful for tracking what assets have moved in and out of the agent's wallet.

> **Note:** The system needs to index new transactions, so there may be a slight delay between when you execute a transaction and when the resulting asset changes are returned in this method. Make sure you are taking that into consideration if dealing with assets the agent just transacted with.

```python
def run(agent: AgentContext) -> None:
    # Get all transaction history for this session
    result = agent.transactions()

    if result.success and result.data:
        agent.log(f"Found {len(result.data)} asset changes")

        # Filter for outgoing transfers
        outgoing = [c for c in result.data if c.from_ == agent.sessionWalletAddress]
        agent.log(f"Outgoing transfers: {len(outgoing)}")

        # Calculate total USD value (where price data is available)
        total_usd = sum(
            float(c.amount) * float(c.tokenUsdPrice)
            for c in result.data
            if c.tokenUsdPrice
        )
        agent.log(f"Total USD value: ${total_usd:.2f}")

        # View specific transaction details
        for change in result.data:
            agent.log(f"{change.network}: {change.from_} → {change.to}")
            agent.log(f"  Amount: {change.amount} {change.tokenType}")
            if change.token:
                agent.log(f"  Token: {change.token}")
            agent.log(f"  Tx: {change.transactionHash}")
            agent.log(f"  Time: {change.timestamp}")
    else:
        agent.log(result.error or "Failed to fetch transactions", error=True)
```

**AssetChange Structure:**

Each asset change in the response contains:
- `network` - Network identifier (e.g., `"ethereum:1"`, `"solana"`)
- `transactionHash` - Transaction hash
- `from_` - Sender address (note the underscore to avoid Python keyword)
- `to` - Recipient address
- `amount` - Amount transferred (as string to preserve precision)
- `token` - Token contract address (`None` for native tokens)
- `tokenId` - Token ID for NFTs (`None` for fungible tokens)
- `tokenType` - Token type (e.g., `"native"`, `"ERC20"`, `"ERC721"`)
- `tokenUsdPrice` - Token price in USD at time of transaction (`None` if unavailable)
- `timestamp` - Transaction timestamp

## 🚀 Sign & Send Transactions

### Ethereum (any EVM chain)

```python
def run(agent: AgentContext) -> None:
    # Self-send demo - send a small amount to yourself
    response = agent.sign_and_send({
        "network": "ethereum:1",
        "request": {
            "to_address": agent.sessionWalletAddress,  # Send to self
            "data": "0x",
            "value": "100000000000000"  # 0.0001 ETH
        },
        "message": "Self-send demo"
    })

    if response.success:
        agent.log(f"Transaction sent: {response.tx_hash}")
        if response.transaction_url:
            agent.log(f"View: {response.transaction_url}")
    else:
        agent.log(response.error_message, error=True)
```

### Solana

```python
def run(agent: AgentContext) -> None:
    response = agent.sign_and_send({
        "network": "solana",
        "request": {
            "hex_transaction": "010001030a0b..."  # serialized VersionedTransaction
        }
    })

    if response.success:
        agent.log(f"Transaction: {response.tx_hash}")
    else:
        agent.log(response.error_message, error=True)
```

## ⚡ Error Handling

**All SDK methods return response objects with `.success` and `.error_message`:**


**Uncaught Exceptions:**

If your function throws an uncaught exception, the Agent SDK automatically:
1. Logs the error to console (visible in local dev and cloud logs)
2. Updates the job in the circuit backend with status='failed' and logs the error.

```python
def run(agent: AgentContext) -> None:
    # This typo will be caught and logged automatically
    agent.memmory.set("key", "value")  # AttributeError

    # No need for try/except around everything!
```

## 🛠️ Deployment

### What You Write

Your agent code should look like this - just define your functions and add the boilerplate at the bottom:

```python
from agent_sdk import Agent, AgentContext

def run(agent: AgentContext) -> None:
    agent.log("Hello from my agent!")
    # Your agent logic here

def unwind(agent: AgentContext, positions: list) -> None:
    agent.log(f"Unwinding {len(positions)} positions...")
    # Optional unwind logic

# ============================================================================
# BOILERPLATE - Don't modify, this handles local testing AND Circuit deployment
# ============================================================================
agent = Agent(
    run_function=run,
    unwind_function=unwind,
)

handler = agent.get_handler()

if __name__ == "__main__":
    agent.run()
```

That's it! The boilerplate code automatically handles the rest

### Deploy to Circuit

```bash
circuit publish
```
> See the circuit cli docs for more details


### Test Locally

## 🧪 Manual Instantiation (Jupyter/Testing)

For testing in Jupyter notebooks or scripts, you can manually create an `AgentContext`:

```python
from agent_sdk import AgentContext
from agent_sdk.agent_context import CurrentPosition

# Create agent context with test data
# Tip: Get a real session ID and wallet from running 'circuit run -m local -x execute'
SESSION_ID = <your-session-id>
WALLET_ADDRESS = "your-wallet-address"

# Create sample position data - helpful for testing your agents treatment of different scenarios
# for example if you want to test some re-balancing logic, you can build a sample set of positions here
# In production, or when using the cli, these will be live values for the session
SAMPLE_POSITION = CurrentPosition(
    network="ethereum:137",
    assetAddress="0x4d97dcd97ec945f40cf65f87097ace5ea0476045",
    tokenId="86192057611122246511563653509192966169513312957180910360241289053249649036697",
    avgUnitCost="0.779812797920499100",
    currentQty="41282044"
)

agent = AgentContext(
    sessionId=SESSION_ID,
    sessionWalletAddress=WALLET_ADDRESS,
    currentPositions=[SAMPLE_POSITION]
)

# Use it just like in production!
agent.log("Testing in Jupyter!")
agent.memory.set("test_key", "test_value")

result = agent.memory.get("test_key")
if result.success and result.data:
    print(f"Value: {result.data.value}")
```

**Key Points:**
- Use real session IDs from the CLI for proper testing
- `currentPositions` is optional but helps test position-related logic
- All SDK methods work the same way as in production

## 📚 Working Examples

The SDK includes complete working examples to help you get started:

### [`demo-agent.py`](./examples/demo-agent.py)
An agent demonstrating all main features of the sdk:
- Memory operations (set, get, list, delete)
- Polymarket integration (market orders, position redemption)
- Swidge
- Self sending using sign and send
- Unified logging patterns

This is a great starting point for building your own agent.

### [`examples/kitchen-sink.ipynb`](./examples/kitchen-sink.ipynb)
An interactive Jupyter notebook showing all SDK features:
- Manual AgentContext instantiation for testing
- All memory operations with examples
- Cross-chain swaps with Swidge (quotes, execution, price impact checks)
- Polymarket operations (buy/sell orders, redemptions)
- Custom transactions with sign_and_send
- Logging patterns (standard, error, debug)

Run this notebook to experiment with the SDK interactively before deploying your agent.

## 🎯 Key Takeaways

1. **Single Interface**: Everything you need is in the `AgentContext` object
2. **No Return Values**: Functions return `None` - uncaught errors are handled automatically by circuit
3. **Unified Logging**: `agent.log()` with simple `debug` and `error` flags
4. **Check `.success`**: All SDK methods return response objects with `.success` and `.error_message`
5. **Let Errors Bubble**: Uncaught exceptions are automatically logged and reported
6. **Copy the Boilerplate**: Use the same boilerplate code for local testing and Circuit deployment

## 📖 Additional Resources

- [Circuit CLI](https://github.com/circuitorg/agents-cli) - Deploy and manage agents
- [`example_agent.py`](./example_agent.py) - Production-ready agent template
- [`examples/kitchen-sink.ipynb`](./examples/kitchen-sink.ipynb) - Interactive SDK demo
