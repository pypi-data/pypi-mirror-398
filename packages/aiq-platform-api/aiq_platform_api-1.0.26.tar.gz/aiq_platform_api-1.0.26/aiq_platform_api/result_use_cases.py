import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from aiq_platform_api import (
    AttackIQClient,
    AttackIQLogger,
    Results,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
from aiq_platform_api.core.testing import parse_test_choice, require_env

logger = AttackIQLogger.get_logger(__name__)


async def list_results(
    client: AttackIQClient,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = 10,
):
    logger.info(f"Listing up to {limit} results...")
    count = 0

    async for result in Results.get_results(
        client,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    ):
        count += 1
        logger.info(f"Result {count}:")
        logger.info(f"  Result ID: {result.get('id')}")
        logger.info("---")
    logger.info(f"Total results listed: {count}")
    return count


async def iterate_results_from(client: AttackIQClient, hours_ago: int):
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours_ago)
    logger.info(f"Iterating over results from {start_date} to {end_date}")
    return await list_results(client, start_date=start_date, end_date=end_date)


async def test_list_all_results(client: AttackIQClient):
    """Test listing results from last 3 months."""
    # Use 3 months (90 days) instead of no filter to avoid server issues
    hours_ago = 90 * 24  # 90 days
    total_results = await iterate_results_from(client, hours_ago)
    logger.info(f"Total results from last 3 months: {total_results}")


async def test_recent_results(client: AttackIQClient):
    """Test listing results from last 2 hours."""
    hours_ago = 2
    total_results = await iterate_results_from(client, hours_ago)
    logger.info(f"Total results from {hours_ago} hours ago: {total_results}")


async def test_daily_results(client: AttackIQClient):
    """Test listing results from last 24 hours."""
    hours_ago = 24
    total_results = await iterate_results_from(client, hours_ago)
    logger.info(f"Total results from {hours_ago} hours ago: {total_results}")


async def test_all(client: AttackIQClient):
    """Run all result tests."""
    for choice in TestChoice:
        if choice != TestChoice.ALL:
            await run_test(choice, client)


async def run_test(choice: "TestChoice", client: AttackIQClient):
    """Run the selected test."""
    test_functions = {
        TestChoice.LIST_ALL: lambda: test_list_all_results(client),
        TestChoice.RECENT_RESULTS: lambda: test_recent_results(client),
        TestChoice.DAILY_RESULTS: lambda: test_daily_results(client),
        TestChoice.ALL: lambda: test_all(client),
    }
    await test_functions[choice]()


class TestChoice(Enum):
    LIST_ALL = "list_all"
    RECENT_RESULTS = "recent_results"
    DAILY_RESULTS = "daily_results"
    ALL = "all"


async def main():
    require_env(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN)
    choice = parse_test_choice(TestChoice)

    async with AttackIQClient(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN) as client:
        await run_test(choice, client)


if __name__ == "__main__":
    asyncio.run(main())
