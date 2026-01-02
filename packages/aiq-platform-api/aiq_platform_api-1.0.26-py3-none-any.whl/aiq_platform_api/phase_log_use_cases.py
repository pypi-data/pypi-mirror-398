import asyncio
import os
from enum import Enum
from typing import Optional

from aiq_platform_api import (
    AttackIQClient,
    AttackIQLogger,
    PhaseLogs,
    Assessments,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
from aiq_platform_api.core.testing import parse_test_choice, require_env

logger = AttackIQLogger.get_logger(__name__)


async def list_phase_logs(
    client: AttackIQClient,
    node_instance_id: Optional[str] = None,
    scenario_job_id: Optional[str] = None,
    limit: Optional[int] = 10,
):
    """List phase logs. UI uses node_instance_id as primary filter."""
    filter_desc = f"node_instance_id={node_instance_id}" if node_instance_id else f"scenario_job_id={scenario_job_id}"
    logger.info(f"Listing up to {limit} phase logs for {filter_desc}...")
    count = 0

    async for log in PhaseLogs.get_phase_logs(
        client, node_instance_id=node_instance_id, scenario_job_id=scenario_job_id, limit=limit
    ):
        count += 1
        value = log.get("value", {})
        logger.info(f"Phase Log {count}:")
        logger.info(f"  Log ID: {log.get('id')}")
        logger.info(f"  Trace Type ID: {log.get('trace_type_id')}")
        logger.info(f"  Phase Number: {log.get('phase_number')}")
        logger.info(f"  Message: {value.get('ai_message', '')[:100]}")
        logger.info("---")
    logger.info(f"Total phase logs listed: {count}")


async def get_recent_assessment_results(
    client: AttackIQClient, assessment_id: str, assessment_version: int, limit: int = 10
) -> list:
    """Fetches results from the most recent run of an assessment."""
    run = await Assessments.get_most_recent_run_status(client, assessment_id, without_detection=True)
    if not run:
        logger.warning(f"No runs found for assessment {assessment_id}")
        return []

    run_id = run.get("id")
    logger.info(f"Getting results for recent run {run_id} of assessment {assessment_id}")

    results = [r async for r in Assessments.get_results_by_run_id(client, run_id, assessment_version, limit=limit)]
    logger.info(f"Fetched {len(results)} results for assessment ID: {assessment_id}")
    return results


async def test_list_phase_logs(client: AttackIQClient, assessment_id: str):
    """Test listing phase logs for results from an assessment."""
    if not assessment_id:
        logger.error("ATTACKIQ_ATOMIC_ASSESSMENT_ID environment variable not set.")
        return

    assessment = await Assessments.get_assessment_by_id(
        client, assessment_id, include_tests=False, scenarios_limit=None
    )
    if not assessment:
        logger.error(f"Assessment {assessment_id} not found")
        return
    assessment_version = assessment["version"]

    assessment_results = await get_recent_assessment_results(client, assessment_id, assessment_version)
    if assessment_results:
        for assessment_result in assessment_results[:3]:  # Limit to first 3 results
            # node_instance_id is in intermediate_results (same as UI)
            intermediate = assessment_result.get("intermediate_results", [])
            if intermediate:
                node_instance_id = intermediate[0].get("node_instance_id")
                if node_instance_id:
                    logger.info(f"\n--- Fetching logs for node_instance_id: {node_instance_id} ---")
                    await list_phase_logs(client, node_instance_id=node_instance_id, limit=5)
                    return  # Only test first one with logs
            else:
                logger.warning(f"No intermediate_results in result: {assessment_result.get('id')}")


async def test_all(client: AttackIQClient, assessment_id: str):
    """Run all phase log tests."""
    for choice in TestChoice:
        if choice != TestChoice.ALL:
            await run_test(choice, client, assessment_id)


async def run_test(choice: "TestChoice", client: AttackIQClient, assessment_id: str):
    """Run the selected test."""
    test_functions = {
        TestChoice.LIST_PHASE_LOGS: lambda: test_list_phase_logs(client, assessment_id),
        TestChoice.ALL: lambda: test_all(client, assessment_id),
    }
    await test_functions[choice]()


class TestChoice(Enum):
    LIST_PHASE_LOGS = "list_phase_logs"
    ALL = "all"


async def main():
    require_env(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN)
    choice = parse_test_choice(TestChoice)

    async with AttackIQClient(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN) as client:
        assessment_id = os.environ.get("ATTACKIQ_ATOMIC_ASSESSMENT_ID")
        await run_test(choice, client, assessment_id)


if __name__ == "__main__":
    asyncio.run(main())
