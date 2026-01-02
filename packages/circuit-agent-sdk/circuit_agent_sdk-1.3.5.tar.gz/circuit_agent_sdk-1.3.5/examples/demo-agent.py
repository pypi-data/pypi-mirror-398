"""
Circuit Agent - SDK v1.2 Python Demo

This agent demonstrates the v1.2 sdk features. You may need to alter the values for the self send, swidge, and polymarket examples based on your test wallets holdings.
"""

from agent_sdk import Agent, AgentContext

# Note: All agent.* methods return a response object that contains standardized success, data, error, and error_message attributes.
# This avoids the need to wrap all SDK methods in try/except blocks and provides a cleaner way to handle errors.


def run(agent: AgentContext) -> None:
    # Note: You will most likely just call agent.log() without assigning to a variable, this is just for demonstration purposes highlighting there is a response object for all agent.* methods
    _ = agent.log("Starting execution")

    # Memory example
    agent.log("Memory example")
    run_count = None
    run_count_memory = agent.memory.get("run-count")
    if run_count_memory.success:
        run_count = int(run_count_memory.data.value)
    else:
        run_count = 0
    run_count += 1

    _updated_memory = agent.memory.set("run-count", str(run_count))
    agent.log(f"Session run count: {run_count}")

    # Self send example using low level sign and send function
    agent.log("Self send example using low level sign and send function")
    sign_and_send = agent.sign_and_send(
        {
            "network": "ethereum:1",
            "request": {
                "to_address": agent.sessionWalletAddress,
                "data": "0x",  # Self send
                "value": "100000000000000",  # 0.0001 ETH
            },
            "message": "Self-send demo",
        }
    )
    if sign_and_send.success:
        agent.log(f"Transaction sent: {sign_and_send.data.tx_hash}")
    else:
        agent.log(sign_and_send.error_message, error=True)

    # Swidge example
    agent.log("Swidge example")
    ARBITRUM_NETWORK = "ethereum:42161"
    BASE_NETWORK = "ethereum:8453"

    quote = agent.swidge.quote(
        {
            "from": {
                "network": ARBITRUM_NETWORK,
                "address": agent.sessionWalletAddress,
            },
            "to": {"network": BASE_NETWORK, "address": agent.sessionWalletAddress},
            "amount": "100000000000000",  # 0.0001 ETH
            "slippage": "2.0",
        }
    )
    if quote.success:
        execute = agent.swidge.execute(quote.data)
        if execute.success:
            agent.log(f"Transaction sent: {execute.data.out.txs[0]}")
        else:
            agent.log(execute.error_message, error=True)
    else:
        agent.log(quote.error_message, error=True)

    # Polymarket example
    agent.log("Polymarket example")
    sell_order = agent.platforms.polymarket.market_order(
        {
            "tokenId": "43316042420532542168140438864501868551184980388178338105513819372697332591887",  # Steelers vs Bengals - Steelers
            "size": 3,
            "side": "SELL",
        }
    )

    if sell_order.success:
        agent.log("Sold some steelers positions")
    else:
        agent.log(f"Sell order failed: {sell_order.error_message}", error=True)


def unwind(agent: AgentContext, positions: list) -> None:
    agent.log(f"Unwinding {len(positions)} positions")
    agent.log("Unwind completed")


agent = Agent(run_function=run, unwind_function=unwind)

handler = agent.get_handler()

if __name__ == "__main__":
    agent.run()
