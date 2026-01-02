import asyncio
from enum import Enum
from typing import Optional

from aiq_platform_api import (
    AttackIQClient,
    AttackIQLogger,
    Connectors,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
from aiq_platform_api.core.testing import parse_test_choice, require_env

logger = AttackIQLogger.get_logger(__name__)


async def fetch_and_log_connectors(client: AttackIQClient, limit: Optional[int] = 10):
    logger.info(f"Fetching and processing up to {limit} company connectors...")
    connector_count = 0

    async for connector in Connectors.get_connectors(client, limit=limit):
        connector_count += 1
        logger.info(f"Connector {connector_count}:")
        logger.info(f"  ID: {connector.get('id')}")
        logger.info(f"  Name: {connector.get('name')}")
        logger.info(f"  Type: {connector.get('type')}")
        logger.info(f"  Status: {connector.get('status')}")
        logger.info("---")

    if connector_count == 0:
        logger.info("No company connectors found.")
    else:
        logger.info(f"Successfully processed {connector_count} company connectors.")


async def test_list_connectors(client: AttackIQClient):
    """Test listing connectors."""
    await fetch_and_log_connectors(client, limit=5)


async def test_all(client: AttackIQClient):
    """Run all integration tests."""
    for choice in TestChoice:
        if choice != TestChoice.ALL:
            await run_test(choice, client)


async def run_test(choice: "TestChoice", client: AttackIQClient):
    """Run the selected test."""
    test_functions = {
        TestChoice.LIST_CONNECTORS: lambda: test_list_connectors(client),
        TestChoice.ALL: lambda: test_all(client),
    }
    await test_functions[choice]()


class TestChoice(Enum):
    LIST_CONNECTORS = "list_connectors"
    ALL = "all"


async def main():
    require_env(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN)
    choice = parse_test_choice(TestChoice)

    async with AttackIQClient(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN) as client:
        await run_test(choice, client)


if __name__ == "__main__":
    asyncio.run(main())
