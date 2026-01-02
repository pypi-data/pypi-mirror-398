"""
Circuit Agent Python SDK v1.2 — clean, unified, agent automation.

**Major Simplification:**
- Agent functions receive a single `AgentContext` object with everything they need
- Functions return `None` - all error handling is automatic
- Unified `agent.log()` for both console and backend logging
- No more boilerplate code

Install: `pip install circuit-agent-sdk`

Minimal example (v1.2):
```python
from agent_sdk import Agent, AgentContext

def run_function(agent: AgentContext) -> None:
    agent.log(f"Starting execution for session {agent.sessionId}")
    agent.memory.set("last_run", str(time.time()))
    positions = agent.platforms.polymarket.positions()
    if positions.success:
        agent.log(f"Found {len(positions.data.positions)} positions")

agent = Agent(run_function=run_function)

# For local development
if __name__ == "__main__":
    agent.run()

# For Circuit deployment
handler = agent.get_handler()
```

Features:
- Unified Interface: Single `AgentContext` object with request data + SDK methods
- Simple Logging: `agent.log()` handles console + backend with debug/error flags
- Type Safety: Full type hints and Pydantic models
- Cross-Chain: Unified interface for EVM and Solana networks
- Swidge: Cross-chain swaps via `agent.swidge.quote()` and `agent.swidge.execute()`
- Polymarket: Prediction markets via `agent.platforms.polymarket.*`
- Memory: Session-scoped key-value storage via `agent.memory.*`
- Error Handling: Automatic catching and reporting of uncaught exceptions
- Deployment: Simple local dev with `agent.run()`, production with `agent.get_handler()`

For more information, see the README.md file or visit:
https://github.com/circuitorg/agent-sdk-python
"""

# Main SDK exports (v1.2 - simplified)
# Agent wrapper for local/worker deployment
from .agent import (
    Agent,
    AgentConfig,
    AgentRequest,
    AgentResponse,
    ExecutionFunctionContract,
    HealthCheckFunctionContract,
    HealthResponse,
    UnwindFunctionContract,
    create_agent_handler,
)
from .agent_context import AgentContext  # New unified interface
from .agent_sdk import AgentSdk

# Core types
from .types import (
    CurrentPosition,
    Network,
    SDKConfig,
    get_chain_id_from_network,
    is_ethereum_network,
    is_solana_network,
)

# Utility functions
from .utils import get_agent_config_from_pyproject, setup_logging

__all__ = [
    # Main SDK (v1.2)
    "AgentSdk",  # Low-level SDK for advanced users
    "AgentContext",  # New unified interface (recommended)
    # Agent wrapper for HTTP server deployment
    "Agent",
    "AgentConfig",
    "AgentRequest",
    "AgentResponse",
    "HealthResponse",
    "create_agent_handler",
    "ExecutionFunctionContract",
    "UnwindFunctionContract",
    "HealthCheckFunctionContract",
    # Core types
    "CurrentPosition",  # For type hints on request payload
    "Network",
    "SDKConfig",
    # Network detection utilities
    "is_ethereum_network",
    "is_solana_network",
    "get_chain_id_from_network",
    # Utility functions
    "get_agent_config_from_pyproject",
    "setup_logging",
]
