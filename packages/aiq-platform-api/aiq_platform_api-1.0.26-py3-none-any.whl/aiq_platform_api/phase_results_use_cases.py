import asyncio
import os
from enum import Enum
from typing import Optional

from aiq_platform_api import (
    AttackIQClient,
    AttackIQLogger,
    PhaseResults,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
from aiq_platform_api.core.testing import parse_test_choice, require_env

logger = AttackIQLogger.get_logger(__name__)


async def list_phase_results(
    client: AttackIQClient,
    assessment_id: str,
    project_run_id: Optional[str] = None,
    result_summary_id: Optional[str] = None,
    limit: Optional[int] = 10,
):
    logger.info(f"Listing up to {limit} phase results ...")
    count = 0

    async for phase_result in PhaseResults.get_phase_results(
        client,
        assessment_id=assessment_id,
        project_run_id=project_run_id,
        result_summary_id=result_summary_id,
        limit=limit,
    ):
        count += 1
        logger.info(f"Phase Result {count}:")
        logger.info(f"  Result ID: {phase_result.get('id')}")
        phase = phase_result.get("phase")
        if phase:
            logger.info(f"  Phase ID: {phase.get('id')}")
            logger.info(f"  Phase Name: {phase.get('name')}")
        logger.info(f"  Created: {phase_result.get('created')}")
        logger.info(f"  Modified: {phase_result.get('modified')}")
        logger.info(f"  Outcome: {phase_result.get('outcome_description')}")
        logger.info("---")
    logger.info(f"Total phase results listed: {count}")


async def test_list_phase_results(client: AttackIQClient, assessment_id: str):
    """Test listing phase results for an assessment."""
    if not assessment_id:
        logger.error("ATTACKIQ_ATOMIC_ASSESSMENT_ID environment variable not set.")
        return
    await list_phase_results(client, assessment_id, limit=100)


async def test_all(client: AttackIQClient, assessment_id: str):
    """Run all phase results tests."""
    for choice in TestChoice:
        if choice != TestChoice.ALL:
            await run_test(choice, client, assessment_id)


async def run_test(choice: "TestChoice", client: AttackIQClient, assessment_id: str):
    """Run the selected test."""
    test_functions = {
        TestChoice.LIST_PHASE_RESULTS: lambda: test_list_phase_results(client, assessment_id),
        TestChoice.ALL: lambda: test_all(client, assessment_id),
    }
    await test_functions[choice]()


class TestChoice(Enum):
    LIST_PHASE_RESULTS = "list_phase_results"
    ALL = "all"


async def main():
    require_env(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN)
    choice = parse_test_choice(TestChoice)

    async with AttackIQClient(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN) as client:
        assessment_id = os.environ.get("ATTACKIQ_ATOMIC_ASSESSMENT_ID")
        await run_test(choice, client, assessment_id)


if __name__ == "__main__":
    asyncio.run(main())
