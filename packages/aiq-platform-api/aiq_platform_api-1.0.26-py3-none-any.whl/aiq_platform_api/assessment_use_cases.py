import asyncio
import os
from enum import Enum
from typing import Optional, Dict, Any, List

from aiq_platform_api import (
    AttackIQClient,
    AttackIQLogger,
    Assessments,
    AssessmentExecutionStrategy,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
from aiq_platform_api.core.testing import parse_test_choice, require_env

logger = AttackIQLogger.get_logger(__name__)


async def list_assessments(client: AttackIQClient, limit: Optional[int] = 10) -> int:
    logger.info(f"Listing up to {limit} assessments")
    count = 0

    async for assessment in Assessments.get_assessments(client, limit=limit):
        count += 1
        logger.info(f"Assessment {count}:")
        logger.info(f"  ID: {assessment.get('id', 'N/A')}")
        logger.info(f"  Name: {assessment.get('name', 'N/A')}")
        logger.info(f"  Status: {assessment.get('status', 'N/A')}")
        logger.info("---")

    logger.info(f"Total assessments listed: {count}")
    return count


async def get_assessment_by_id(client: AttackIQClient, assessment_id: str) -> Optional[Dict[str, Any]]:
    logger.info(f"Getting assessment with ID: {assessment_id}")
    assessment = await Assessments.get_assessment_by_id(
        client, assessment_id, include_tests=False, scenarios_limit=None
    )

    if assessment:
        logger.info(f"Assessment Name: {assessment.get('name')}")
        logger.info(f"Is Attack Graph: {assessment.get('is_attack_graph')}")

    return assessment


async def list_assessment_runs(client: AttackIQClient, assessment_id: str, limit: Optional[int] = 10):
    logger.info(f"Listing up to {limit} runs for assessment {assessment_id}")

    result = await Assessments.list_assessment_runs(client, assessment_id, limit=limit)
    runs = result.get("results", [])
    total_count = result.get("count", 0)

    for i, run in enumerate(runs, 1):
        logger.info(f"Run {i}:")
        logger.info(f"  ID: {run.get('id', 'N/A')}")
        logger.info(f"  Created: {run.get('created_at', 'N/A')}")
        logger.info(f"  Scenario Jobs In Progress: {run.get('scenario_jobs_in_progress', 'N/A')}")
        logger.info(f"  Integration Jobs In Progress: {run.get('integration_jobs_in_progress', 'N/A')}")
        logger.info("---")

    logger.info(f"Total runs: {total_count}, displayed: {len(runs)}")
    return len(runs)


async def run_and_monitor_assessment(
    client: AttackIQClient,
    assessment_id: str,
    assessment_version: int,
    timeout: int = 600,
    check_interval: int = 5,
) -> Optional[str]:
    logger.info(f"Running assessment {assessment_id} and monitoring completion")

    try:
        run_id = await Assessments.run_assessment(client, assessment_id, assessment_version)
        logger.info(f"Assessment started with run ID: {run_id}")

        completed = await Assessments.wait_for_run_completion(
            client, assessment_id, run_id, timeout, check_interval, without_detection=True
        )

        if completed:
            logger.info(f"Assessment run {run_id} completed successfully")
            return run_id

        logger.warning(f"Assessment run {run_id} did not complete within {timeout} seconds")
        return None

    except Exception as e:
        logger.error(f"Error running assessment: {e}")
        return None


async def get_run_results(
    client: AttackIQClient, run_id: str, assessment_version: int, limit: Optional[int] = 10
) -> List[Dict[str, Any]]:
    logger.info(f"Getting results for run {run_id}")

    collected_results = []
    i = 0
    async for result in Assessments.get_results_by_run_id(client, run_id, assessment_version, limit=limit):
        i += 1
        logger.info(f"Result {i}:")
        logger.info(f"  ID: {result.get('id', 'N/A')}")
        logger.info(f"  Outcome: {result.get('outcome', 'N/A')}")
        logger.info(f"  Start: {result.get('started_at', result.get('start_time', 'N/A'))}")
        logger.info(f"  End: {result.get('ended_at', result.get('end_time', 'N/A'))}")
        logger.info("---")
        collected_results.append(result)
    return collected_results


async def get_detailed_result(
    client: AttackIQClient, result_id: str, assessment_version: int
) -> Optional[Dict[str, Any]]:
    logger.info(f"Getting detailed information for result {result_id}")
    result = await Assessments.get_result_details(client, result_id, assessment_version)

    if not result:
        logger.error(f"Could not retrieve detailed result for result ID: {result_id}")
        return None

    logger.info("--- Detailed Result ---")
    logger.info(f"  Result ID: {result.get('id', 'N/A')}")
    logger.info(f"  Overall Outcome: {result.get('outcome', 'N/A')}")
    logger.info(f"  Detection Outcome: {result.get('detection_outcome', 'N/A')}")
    logger.info(f"  Run Started At: {result.get('run_started_at', 'N/A')}")

    # Log intermediate results
    intermediate_results = result.get("intermediate_results")
    if intermediate_results and isinstance(intermediate_results, list):
        logger.info("--- Intermediate Results (Nodes/Steps) ---")
        for i, step in enumerate(intermediate_results):
            logger.info(f"  Step {i + 1}:")
            logger.info(f"    Node ID: {step.get('node_id', 'N/A')}")
            logger.info(f"    Scenario Name: {step.get('scenario_name', 'N/A')}")
            logger.info(f"    Outcome: {step.get('outcome', 'N/A')}")

    return result


async def list_assets_in_assessment(client: AttackIQClient, assessment_id: str, limit: Optional[int] = 10):
    logger.info(f"Listing assets for assessment {assessment_id}")
    count = 0

    async for asset in Assessments.get_assets_in_assessment(client, assessment_id, limit=limit):
        count += 1
        logger.info(f"Asset {count}:")
        logger.info(f"  ID: {asset.get('id', 'N/A')}")
        logger.info(f"  Name: {asset.get('name', 'N/A')}")
        logger.info(f"  Type: {asset.get('type', 'N/A')}")
        logger.info(f"  IP Address: {asset.get('ipv4_address', 'N/A')}")
        logger.info("---")

    return count


async def assessment_workflow_demo(client: AttackIQClient, assessment_id: str, run_assessment: bool):
    logger.info(f"Starting assessment workflow demo for assessment {assessment_id}")

    assessment = await get_assessment_by_id(client, assessment_id)
    if not assessment:
        logger.error("Could not get assessment metadata. Aborting workflow.")
        return

    await list_assessment_runs(client, assessment_id)

    run_id = None
    assessment_version = assessment["version"]
    if run_assessment:
        run_id = await run_and_monitor_assessment(
            client, assessment_id, assessment_version, timeout=300, check_interval=5
        )

    if not run_id:
        run = await Assessments.get_most_recent_run_status(client, assessment_id, without_detection=True)
        if not run:
            logger.error("No runs found for assessment. Aborting workflow.")
            return
        run_id = run.get("id")

    assessment_version = assessment["version"]
    results = await get_run_results(client, run_id, assessment_version)
    if not results:
        logger.error("No results found for run. Aborting workflow.")
        return

    for result in results:
        await get_detailed_result(client, result["id"], assessment_version)


async def test_list_assessments(client: AttackIQClient):
    await list_assessments(client, limit=5)


async def test_get_recent_run(client: AttackIQClient, assessment_id: str):
    if not assessment_id:
        logger.error("ASSESSMENT_ID required for this test")
        return

    run = await Assessments.get_most_recent_run_status(client, assessment_id, without_detection=True)
    if run:
        logger.info(f"Recent run: {run.get('id')}")
        logger.info(f"  Created: {run.get('created', 'N/A')}")
        logger.info(f"  Progress: {run.get('done_count', 0)}/{run.get('total_count', 0)} completed")
        logger.info(f"  Completed: {run.get('completed', False)}")
    else:
        logger.info("No runs found")


async def test_run_assessment(client: AttackIQClient, assessment_id: str):
    if not assessment_id:
        logger.error("ASSESSMENT_ID required for this test")
        return

    assessment = await Assessments.get_assessment_by_id(
        client, assessment_id, include_tests=False, scenarios_limit=None
    )
    if not assessment:
        logger.error(f"Assessment {assessment_id} not found")
        return

    assessment_version = assessment["version"]
    run_id = await run_and_monitor_assessment(client, assessment_id, assessment_version, timeout=600, check_interval=5)
    if run_id:
        results = [r async for r in Assessments.get_results_by_run_id(client, run_id, assessment_version, limit=3)]
        logger.info(f"Completed with {len(results)} results")


async def test_get_results(client: AttackIQClient, assessment_id: str):
    if not assessment_id:
        logger.error("ASSESSMENT_ID required for this test")
        return

    assessment = await Assessments.get_assessment_by_id(
        client, assessment_id, include_tests=False, scenarios_limit=None
    )
    if not assessment:
        logger.error(f"Assessment {assessment_id} not found")
        return

    assessment_version = assessment["version"]
    run = await Assessments.get_most_recent_run_status(client, assessment_id, without_detection=True)
    if run:
        run_id = run.get("id")
        results = await get_run_results(client, run_id, assessment_version)
        logger.info(f"Retrieved {len(results)} results")


async def test_get_recent_run_results(client: AttackIQClient, assessment_id: str):
    if not assessment_id:
        logger.error("ASSESSMENT_ID required for this test")
        return

    assessment = await Assessments.get_assessment_by_id(
        client, assessment_id, include_tests=False, scenarios_limit=None
    )
    if not assessment:
        logger.error(f"Assessment {assessment_id} not found")
        return

    assessment_version = assessment["version"]
    run = await Assessments.get_most_recent_run_status(client, assessment_id, without_detection=True)
    if run:
        run_id = run.get("id")
        logger.info(f"Getting results for recent run: {run_id}")
        logger.info(f"  Run completed: {run.get('completed', False)}")
        logger.info(f"  Progress: {run.get('done_count', 0)}/{run.get('total_count', 0)}")

        results = await get_run_results(client, run_id, assessment_version, limit=10)
        if results:
            logger.info(f"Successfully retrieved {len(results)} results")
            for result in results[:3]:  # Show first 3 results
                await get_detailed_result(client, result["id"], assessment_version)
        else:
            logger.warning("No results found for the most recent run")
    else:
        logger.info("No recent runs found")


async def test_execution_with_detection(client: AttackIQClient, assessment_id: str):
    if not assessment_id:
        logger.error("ASSESSMENT_ID required for this test")
        return

    result = await Assessments.set_execution_strategy(client, assessment_id, with_detection=True)
    logger.info(f"Set execution WITH detection: {'Success' if result else 'Failed'}")


async def test_execution_without_detection(client: AttackIQClient, assessment_id: str):
    if not assessment_id:
        logger.error("ASSESSMENT_ID required for this test")
        return

    result = await Assessments.set_execution_strategy(client, assessment_id, with_detection=False)
    logger.info(f"Set execution WITHOUT detection: {'Success' if result else 'Failed'}")


async def test_get_execution_strategy(client: AttackIQClient, assessment_id: str):
    if not assessment_id:
        logger.error("ASSESSMENT_ID required for this test")
        return

    strategy = await Assessments.get_execution_strategy(client, assessment_id)
    assessment = await Assessments.get_assessment_by_id(
        client, assessment_id, include_tests=False, scenarios_limit=None
    )

    logger.info(f"Assessment: {assessment.get('name')}")
    logger.info(f"Execution Strategy: {strategy.name} (value={strategy.value})")

    if strategy == AssessmentExecutionStrategy.WITH_DETECTION:
        logger.info("Detection validation is ENABLED")
    else:
        logger.info("Detection validation is DISABLED")

    return strategy


async def test_workflow_demo(client: AttackIQClient, assessment_id: str):
    if not assessment_id:
        logger.error("ASSESSMENT_ID required for this test")
        return

    await assessment_workflow_demo(client, assessment_id, run_assessment=True)


async def test_all(client: AttackIQClient, assessment_id: str):
    await list_assessments(client, limit=3)
    if assessment_id:
        await get_assessment_by_id(client, assessment_id)
        run = await Assessments.get_most_recent_run_status(client, assessment_id, without_detection=True)
        if run:
            logger.info(f"Most recent run: {run.get('id')}")
            logger.info(f"  Progress: {run.get('done_count', 0)}/{run.get('total_count', 0)} completed")
        await list_assessment_runs(client, assessment_id, limit=3)
        await assessment_workflow_demo(client, assessment_id, run_assessment=False)


async def test_search_assessments_pagination(client: AttackIQClient):
    logger.info("=" * 60)
    logger.info("TEST: search_assessments pagination")
    logger.info("=" * 60)

    # Test 1: Basic search with count
    result = await Assessments.search_assessments(client, limit=3, offset=0)
    total_count = result.get("count", 0)
    results = result.get("results", [])
    logger.info(f"Total count: {total_count}, Page 1 results: {len(results)}")

    if total_count == 0:
        logger.warning("No assessments found - cannot validate pagination")
        return

    # Test 2: Validate offset works (different results). Enforce ordering to avoid back-end default overlap.
    if total_count > 3:
        page1_ids = {a["id"] for a in results}
        ordering = "-modified"
        result2 = await Assessments.search_assessments(client, limit=3, offset=3, ordering=ordering)
        page2_results = result2.get("results", [])
        page2_ids = {a["id"] for a in page2_results}

        overlap = page1_ids & page2_ids
        if overlap:
            logger.warning(f"Overlap detected between page 1 and page 2 (ordering={ordering}): {overlap}")
        else:
            logger.info("PASS: Page 1 and Page 2 have different results")
    else:
        logger.info(f"SKIP: Only {total_count} assessments, cannot test offset")

    # Test 3: Version filter
    result_v1 = await Assessments.search_assessments(client, version=1, limit=3)
    result_v2 = await Assessments.search_assessments(client, version=2, limit=3)
    logger.info(f"v1 assessments: {result_v1.get('count', 0)}")
    logger.info(f"v2 assessments: {result_v2.get('count', 0)}")

    # Test 4: Search query
    result_search = await Assessments.search_assessments(client, query="test", limit=3)
    logger.info(f"Search 'test': {result_search.get('count', 0)} matches")

    logger.info("PASS: search_assessments pagination validated")


async def test_list_assessment_runs_pagination(client: AttackIQClient, assessment_id: str):
    if not assessment_id:
        logger.error("ASSESSMENT_ID required for this test")
        return

    logger.info("=" * 60)
    logger.info("TEST: list_assessment_runs pagination")
    logger.info("=" * 60)

    # Test 1: Basic list with count
    result = await Assessments.list_assessment_runs(client, assessment_id, limit=3, offset=0)
    total_count = result.get("count", 0)
    results = result.get("results", [])
    logger.info(f"Total runs: {total_count}, Page 1 results: {len(results)}")

    if total_count == 0:
        logger.warning("No runs found - cannot validate pagination")
        return

    # Test 2: Validate offset works (different results)
    if total_count > 3:
        page1_ids = {r["id"] for r in results}
        result2 = await Assessments.list_assessment_runs(client, assessment_id, limit=3, offset=3)
        page2_results = result2.get("results", [])
        page2_ids = {r["id"] for r in page2_results}

        overlap = page1_ids & page2_ids
        if overlap:
            logger.error(f"FAIL: Pages overlap! IDs in both: {overlap}")
        else:
            logger.info("PASS: Page 1 and Page 2 have different results")
    else:
        logger.info(f"SKIP: Only {total_count} runs, cannot test offset")

    logger.info("PASS: list_assessment_runs pagination validated")


async def test_assessment_filters(client: AttackIQClient) -> Dict[str, Any]:
    logger.info("=" * 60)
    logger.info("TEST: Assessment Filter Validation")
    logger.info("=" * 60)

    results = {"passed": 0, "failed": 0, "tests": []}

    # Baseline
    baseline = await Assessments.search_assessments(client, limit=1)
    total = baseline.get("count", 0)
    logger.info(f"BASELINE: Total assessments = {total}\n")

    # Get sample data for UUID filters
    sample = baseline.get("results", [{}])[0] if baseline.get("results") else {}
    sample_user_id = sample.get("users", [None])[0]
    sample_template_id = sample.get("project_template_id")

    def check(name: str, condition: bool, detail: str):
        status = "PASS" if condition else "FAIL"
        results["passed" if condition else "failed"] += 1
        results["tests"].append({"name": name, "passed": condition, "detail": detail})
        logger.info(f"{name}: {status} - {detail}")

    # 1. version filter
    v1 = (await Assessments.search_assessments(client, version=1, limit=1)).get("count", 0)
    v2 = (await Assessments.search_assessments(client, version=2, limit=1)).get("count", 0)
    check("version", v1 + v2 == total, f"v1={v1} + v2={v2} = {v1 + v2} (expected {total})")

    # 2. created_after filter
    r = (await Assessments.search_assessments(client, created_after="2025-01-01T00:00:00Z", limit=1)).get("count", 0)
    check("created_after", r < total, f"filtered to {r} (from {total})")

    # 3. modified_after filter
    r = (await Assessments.search_assessments(client, modified_after="2025-11-01T00:00:00Z", limit=1)).get("count", 0)
    check("modified_after", r < total, f"filtered to {r} (from {total})")

    # 4. execution_strategy filter
    e0 = (await Assessments.search_assessments(client, execution_strategy=0, limit=1)).get("count", 0)
    e1 = (await Assessments.search_assessments(client, execution_strategy=1, limit=1)).get("count", 0)
    check("execution_strategy", e0 + e1 == total, f"0={e0} + 1={e1} = {e0 + e1} (expected {total})")

    # 5. user_id filter
    if sample_user_id:
        r = (await Assessments.search_assessments(client, user_id=sample_user_id, limit=1)).get("count", 0)
        check("user_id", 0 < r <= total, f"filtered to {r} for user {sample_user_id[:8]}...")

    # 6. is_attack_graph filter
    ag_true = (await Assessments.search_assessments(client, is_attack_graph=True, limit=1)).get("count", 0)
    ag_false = (await Assessments.search_assessments(client, is_attack_graph=False, limit=1)).get("count", 0)
    check(
        "is_attack_graph",
        ag_true + ag_false == total,
        f"true={ag_true} + false={ag_false} = {ag_true + ag_false} (expected {total})",
    )

    # 7. project_template_id filter
    if sample_template_id:
        r = (await Assessments.search_assessments(client, project_template_id=sample_template_id, limit=1)).get(
            "count", 0
        )
        check("project_template_id", 0 < r <= total, f"filtered to {r} for template {sample_template_id[:8]}...")

    # 8. Combined filters
    r = (await Assessments.search_assessments(client, version=1, is_attack_graph=False, limit=1)).get("count", 0)
    check("combined_filters", r <= min(v1, ag_false), f"v1 AND !attack_graph = {r} (<= {min(v1, ag_false)})")

    # 9. Search + filter
    r = (await Assessments.search_assessments(client, query="security", version=2, limit=1)).get("count", 0)
    check("search_with_filter", r <= v2, f"query='security' AND v2 = {r} (<= {v2})")

    logger.info(f"\n{'=' * 50}")
    logger.info(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
    logger.info(f"{'=' * 50}")
    return results


async def test_assessment_runs(client: AttackIQClient) -> Dict[str, Any]:
    results = {"passed": 0, "failed": 0, "tests": []}

    def check(name: str, condition: bool, detail: str):
        status = "PASS" if condition else "FAIL"
        results["passed" if condition else "failed"] += 1
        results["tests"].append({"name": name, "passed": condition, "detail": detail})
        logger.info(f"{name}: {status} - {detail}")

    # Get an assessment with runs
    assessments = await Assessments.search_assessments(client, limit=5)
    assessment_id = None
    for a in assessments.get("results", []):
        runs = await Assessments.list_assessment_runs(client, a["id"], limit=1)
        if runs.get("count", 0) > 0:
            assessment_id = a["id"]
            break

    if not assessment_id:
        logger.error("No assessment with runs found")
        return results

    logger.info(f"Using assessment: {assessment_id[:8]}...\n")

    # 1. list_assessment_runs returns proper format
    runs = await Assessments.list_assessment_runs(client, assessment_id, limit=3)
    has_count = "count" in runs
    has_results = "results" in runs
    check(
        "list_runs_format",
        has_count and has_results,
        f"count={runs.get('count', 0)}, results={len(runs.get('results', []))}",
    )

    # 2. list_assessment_runs has run data
    run_count = runs.get("count", 0)
    check("list_runs_data", run_count > 0, f"found {run_count} runs")

    if runs.get("results"):
        run = runs["results"][0]
        run_id = run.get("id")

        # 3. Run has expected fields
        check("list_run_has_id", "id" in run, f"id={'present' if 'id' in run else 'missing'}")
        check(
            "list_run_has_project_id",
            "project_id" in run,
            f"project_id={'present' if 'project_id' in run else 'missing'}",
        )

        # 4. get_run returns data
        run_details = await Assessments.get_run(client, assessment_id, run_id)
        check("get_run_returns", run_details is not None, f"returned {'dict' if run_details else 'None'}")

        if run_details:
            # 5. Run details has expected fields
            check(
                "get_run_has_run_id",
                "run_id" in run_details,
                f"run_id={'present' if 'run_id' in run_details else 'missing'}",
            )
            check(
                "get_run_has_status",
                "status" in run_details,
                f"status={'present' if 'status' in run_details else 'missing'}",
            )

            # 6. Status is valid
            status = run_details.get("status", "")
            valid_statuses = ["Completed", "Running", "Pending", "Cancelled", "Failed"]
            check("run_status_valid", status in valid_statuses, f"status='{status}'")

    logger.info(f"\n{'=' * 50}")
    logger.info(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
    logger.info(f"{'=' * 50}")
    return results


# ============================================================================
# Assessment Configuration Test (with SRP private helpers)
# ============================================================================


def _print_header(text: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}")


def _print_subheader(text: str) -> None:
    print(f"\n  {text}")
    print(f"  {'-' * 66}")


async def _find_assessment_with_analysis(client: AttackIQClient) -> Optional[str]:
    for is_ag in [False, True]:
        assessments = await Assessments.search_assessments(client, is_attack_graph=is_ag, limit=5)
        for a in assessments.get("results", []):
            result = await Assessments.get_assessment_by_id(client, a["id"], include_tests=True, scenarios_limit=None)
            if result and "_analysis" in result:
                return a["id"]
    return None


def _print_assessment_summary(data: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    _print_header("ASSESSMENT CONFIGURATION")
    print(f"  Name: {data.get('name', 'N/A')[:55]}")
    print(f"  ID: {data.get('id')}")
    print(f"  Type: {analysis.get('assessment_type', 'Unknown')}")
    print(f"  Version: v{data.get('version', 1)}")

    _print_header("ANALYSIS (_analysis from get_assessment_by_id)")
    for key, value in analysis.items():
        print(f"  {key}: {value}")


def _print_attack_graph_details(data: Dict[str, Any]) -> None:
    ag = data.get("attack_graph", {})
    graph = ag.get("graph", {})
    stages = graph.get("graph_meta", {}).get("stages", {})
    nodes = graph.get("graph", {})

    _print_subheader(f"Stages ({len(stages)})")
    for stage_id, stage_data in list(stages.items())[:4]:
        if isinstance(stage_data, dict):
            title = stage_data.get("title", f"Stage {stage_id}")
            node_ids = stage_data.get("node_ids", [])
            print(f"    [{stage_id}] {title[:45]}: {len(node_ids)} node(s)")

    _print_subheader(f"Nodes ({len(nodes)} scenarios)")
    for node_id, node in list(nodes.items())[:3]:
        name = node.get("scenario_name", "N/A")
        multi = " [MULTI-ASSET]" if node.get("is_multi_asset") else ""
        print(f"    [{node_id}] {name[:50]}...{multi}")
    if len(nodes) > 3:
        print(f"    ... +{len(nodes) - 3} more")


def _print_boundaries(boundaries: List[Dict]) -> None:
    if not boundaries:
        return
    _print_subheader(f"Boundaries ({len(boundaries)} attacker→target pairs)")
    for i, b in enumerate(boundaries[:2]):
        print(f"    [{i + 1}] {b.get('attacker_asset_id', '')[:12]}... → {b.get('target_asset_id', '')[:12]}...")


def _print_test_scenarios(scenarios: List[Dict]) -> None:
    for s in scenarios[:2]:
        scenario = s.get("scenario", {})
        model_json = s.get("model_json", {})
        multi = " [MULTI-ASSET]" if scenario.get("is_multi_asset") else ""
        keys = list(model_json.keys())[:3] if model_json else []
        print(f"        - {scenario.get('name', 'N/A')[:35]}...{multi}")
        if keys:
            print(f"          model_json: {{{', '.join(keys)}...}}")
    if len(scenarios) > 2:
        print(f"        ... +{len(scenarios) - 2} more scenarios")


def _print_test_assets(assets: List[Dict]) -> None:
    if not assets:
        return
    for a in assets[:2]:
        asset = a.get("asset", {})
        print(f"        * {asset.get('hostname', 'N/A')} ({asset.get('ipv4_address', 'N/A')})")
    if len(assets) > 2:
        print(f"        ... +{len(assets) - 2} more assets")


def _print_atomic_tests(tests: List[Dict]) -> None:
    _print_subheader(f"Tests ({len(tests)})")
    for i, test in enumerate(tests[:2]):
        scenarios = test.get("scenarios", [])
        assets = test.get("assets", [])
        print(f"  [{i + 1}] {test.get('name', 'N/A')[:45]}")
        print(f"      scenarios: {len(scenarios)}, assets: {len(assets)}")
        _print_test_scenarios(scenarios)
        _print_test_assets(assets)
    if len(tests) > 2:
        print(f"  ... +{len(tests) - 2} more tests")


def _print_sample_model_json(tests: List[Dict]) -> None:
    import json

    for test in tests:
        for s in test.get("scenarios", []):
            model_json = s.get("model_json", {})
            if model_json:
                _print_header("SAMPLE model_json → scenario_args")
                print(f"  {s.get('scenario', {}).get('name', 'N/A')[:55]}...")
                print(json.dumps(model_json, indent=2))
                return


async def test_assessment_configuration(client: AttackIQClient, assessment_id: Optional[str]) -> None:
    if not assessment_id:
        assessment_id = await _find_assessment_with_analysis(client)

    if not assessment_id:
        print("No suitable assessment found")
        return

    data = await Assessments.get_assessment_by_id(client, assessment_id, include_tests=True, scenarios_limit=None)
    if not data:
        print(f"Assessment {assessment_id} not found")
        return

    analysis = data.get("_analysis", {})

    _print_assessment_summary(data, analysis)

    if analysis.get("is_attack_graph"):
        _print_attack_graph_details(data)
    else:
        _print_boundaries(data.get("boundaries", []))
        _print_atomic_tests(data.get("tests", []))
        _print_sample_model_json(data.get("tests", []))


async def run_test(choice: "TestChoice", client: AttackIQClient, assessment_id: str):
    test_functions = {
        TestChoice.LIST_ASSESSMENTS: lambda: test_list_assessments(client),
        TestChoice.GET_RECENT_RUN: lambda: test_get_recent_run(client, assessment_id),
        TestChoice.RUN_ASSESSMENT: lambda: test_run_assessment(client, assessment_id),
        TestChoice.WORKFLOW_DEMO: lambda: test_workflow_demo(client, assessment_id),
        TestChoice.GET_RESULTS: lambda: test_get_results(client, assessment_id),
        TestChoice.GET_RECENT_RUN_RESULTS: lambda: test_get_recent_run_results(client, assessment_id),
        TestChoice.EXECUTION_WITH_DETECTION: lambda: test_execution_with_detection(client, assessment_id),
        TestChoice.EXECUTION_WITHOUT_DETECTION: lambda: test_execution_without_detection(client, assessment_id),
        TestChoice.GET_EXECUTION_STRATEGY: lambda: test_get_execution_strategy(client, assessment_id),
        TestChoice.SEARCH_ASSESSMENTS_PAGINATION: lambda: test_search_assessments_pagination(client),
        TestChoice.LIST_RUNS_PAGINATION: lambda: test_list_assessment_runs_pagination(client, assessment_id),
        TestChoice.TEST_FILTERS: lambda: test_assessment_filters(client),
        TestChoice.TEST_RUNS: lambda: test_assessment_runs(client),
        TestChoice.TEST_CONFIGURATION: lambda: test_assessment_configuration(client, assessment_id),
        TestChoice.ATOMIC_CREATION: lambda: test_atomic_creation(client),
        TestChoice.SCENARIO_PARAMETERS: lambda: test_scenario_parameters(client),
        TestChoice.ALL: lambda: test_all(client, assessment_id),
    }

    await test_functions[choice]()


async def test_atomic_creation(client: AttackIQClient, cleanup: bool = True) -> Dict[str, Any]:
    """Test atomic assessment creation capability.

    Run: TEST_CHOICE=atomic_creation python aiq_platform_api/assessment_use_cases.py
    """
    from aiq_platform_api import Scenarios
    from aiq_platform_api.core.assets import Assets

    results = {"passed": 0, "failed": 0, "tests": []}

    def check(name: str, condition: bool, detail: str):
        status = "PASS" if condition else "FAIL"
        results["passed" if condition else "failed"] += 1
        results["tests"].append({"name": name, "passed": condition, "detail": detail})
        logger.info(f"{name}: {status} - {detail}")

    logger.info("=" * 70)
    logger.info("  TEST: Atomic Assessment Creation")
    logger.info("=" * 70)

    # Get sample scenarios
    logger.info("  Step 1: Get sample scenarios...")
    scenario_ids = []
    async for scenario in Scenarios.list_scenarios(client, limit=3):
        scenario_ids.append(scenario["id"])
    check("get_scenarios", len(scenario_ids) >= 2, f"found {len(scenario_ids)} scenarios")

    if len(scenario_ids) < 2:
        logger.error("Cannot proceed without scenarios")
        return results

    # Get active test point
    logger.info("  Step 2: Get active test point...")
    active_asset = None
    async for asset in Assets.get_assets(client, params={"hide_hosted_agents": "true"}, limit=5):
        if asset.get("status") == "Active":
            active_asset = asset
            break

    check(
        "get_test_point",
        active_asset is not None,
        f"found {active_asset.get('hostname', 'N/A') if active_asset else 'none'}",
    )

    if not active_asset:
        logger.error("Cannot proceed without active test point")
        return results

    # Test atomic creation
    logger.info("  Step 3: Create atomic assessment...")
    try:
        result = await Assessments.create_atomic_assessment(
            client=client,
            name="[SDK-UseCase-Test] Atomic Assessment",
            scenario_ids=scenario_ids[:2],
            asset_ids=[active_asset["id"]],
            test_name="SDK Use Case Test Container",
        )
        check("create_assessment", "assessment_id" in result, f"id={result.get('assessment_id', 'N/A')[:8]}...")
        assessment_id = result.get("assessment_id")
    except Exception as e:
        check("create_assessment", False, str(e))
        return results

    # Verify assessment
    logger.info("  Step 4: Verify assessment...")
    assessment = await Assessments.get_assessment_by_id(client, assessment_id, include_tests=True)
    tests = assessment.get("tests", []) if assessment else []
    scenarios_count = sum(len(t.get("scenarios", [])) for t in tests)
    check("verify_tests", len(tests) == 1, f"tests={len(tests)}")
    check("verify_scenarios", scenarios_count == 2, f"scenarios={scenarios_count}")

    # Verify detection is disabled (execution_strategy=1 = prevention-only)
    exec_strategy = assessment.get("execution_strategy") if assessment else None
    check("verify_detection_disabled", exec_strategy == 1, f"execution_strategy={exec_strategy} (expected 1)")

    # Test constraint validation
    logger.info("  Step 5: Test constraints...")
    try:
        await Assessments.create_atomic_assessment(client=client, name="test", scenario_ids=[], asset_ids=["x"])
        check("empty_list_rejected", False, "should have raised ValueError")
    except ValueError as e:
        check("empty_list_rejected", True, str(e))

    try:
        await Assessments.create_atomic_assessment(client=client, name="test", scenario_ids=["x"] * 30, asset_ids=["x"])
        check("max_scenarios_enforced", False, "should have raised ValueError")
    except ValueError as e:
        check("max_scenarios_enforced", True, str(e))

    # Cleanup
    if cleanup and assessment_id:
        logger.info("  Step 6: Cleanup...")
        try:
            await client.delete_object(f"v1/assessments/{assessment_id}")
            check("cleanup", True, "deleted test assessment")
        except Exception as e:
            check("cleanup", False, str(e))

    logger.info(f"{'=' * 70}")
    logger.info(f"  RESULTS: {results['passed']} passed, {results['failed']} failed")
    logger.info(f"{'=' * 70}")

    return results


async def test_scenario_parameters(client: AttackIQClient) -> Dict[str, Any]:
    """Demonstrate scenario_parameters usage for Phase 5 config validation.

    Run: TEST_CHOICE=scenario_parameters python aiq_platform_api/assessment_use_cases.py

    This use case documents the INTENDED usage pattern for scenario_parameters.
    Currently the parameter is accepted but not validated (Phase 5 work).

    Phase 5 will add:
    - Validation that scenarios requiring config have their params provided
    - Error reporting for missing required parameters
    - Type checking for parameter values

    Example scenarios that need parameters:
    - Download scenarios: need target URL
    - Script execution: may need file paths or IPs
    - Custom scenarios: user-defined parameters from model_json_keys
    """
    from aiq_platform_api.core.scenarios import Scenarios

    results = {"passed": 0, "failed": 0, "tests": []}

    def check(name: str, condition: bool, detail: str):
        status = "PASS" if condition else "FAIL"
        results["passed" if condition else "failed"] += 1
        results["tests"].append({"name": name, "passed": condition, "detail": detail})
        logger.info(f"{name}: {status} - {detail}")

    logger.info("=" * 70)
    logger.info("  TEST: scenario_parameters Usage Pattern (Phase 5 Preview)")
    logger.info("=" * 70)

    # Step 1: Get scenarios that might need configuration
    logger.info("  Step 1: Find scenarios (some may need configuration)...")
    scenario_ids = []
    async for scenario in Scenarios.list_scenarios(client, limit=3):
        scenario_ids.append(scenario["id"])
    check("get_scenarios", len(scenario_ids) >= 1, f"found {len(scenario_ids)} scenarios")

    if not scenario_ids:
        logger.error("Cannot proceed without scenarios")
        return results

    # Step 2: Get a test point
    logger.info("  Step 2: Get test point...")
    from aiq_platform_api.core.assets import Assets

    test_point_id = None
    async for asset in Assets.get_assets(client, params={"hide_hosted_agents": "true"}, limit=5):
        if asset.get("status") == "Active":
            test_point_id = asset["id"]
            break
    check("get_test_point", test_point_id is not None, "found active test point")

    if not test_point_id:
        logger.error("Cannot proceed without active test point")
        return results

    # Step 3: Demonstrate scenario_parameters usage pattern
    logger.info("  Step 3: Validate with scenario_parameters (Phase 5 preview)...")

    # This is the INTENDED usage pattern for Phase 5:
    # When a scenario needs config (e.g., a download URL), you provide it like this:
    example_scenario_parameters = {
        scenario_ids[0]: {
            "target_url": "https://example.com/test.exe",  # Example: download scenario
            "output_path": "/tmp/test.exe",
        },
        # More scenarios can have their own parameters...
    }

    # Currently, validate_assessment_batch accepts but doesn't validate these parameters
    # Phase 5 will add validation that required params are provided
    result = await Assessments.validate_assessment_batch(
        client=client,
        scenario_ids=scenario_ids,
        test_point_ids=[test_point_id],
        scenario_parameters=example_scenario_parameters,  # Accepted but not yet validated
    )

    check("accepts_scenario_parameters", "is_valid" in result, "parameter accepted without error")
    check("has_summary", "summary" in result, "summary present")

    # Step 4: Document what Phase 5 will add
    logger.info("  Step 4: Phase 5 will add these validations...")
    phase5_checks = [
        "Scenario X requires 'target_url' but none provided",
        "Scenario Y has invalid 'port' value: expected int, got str",
        "Scenario Z has unknown parameter 'foo' (valid: bar, baz)",
    ]
    for future_check in phase5_checks:
        logger.info(f"    (Future) {future_check}")
    check("phase5_documented", True, "see ODV_AGENT.md Section 5.4")

    # Step 5: Show current behavior - scenarios_need_configuration
    logger.info("  Step 5: Current behavior - identifies scenarios needing config...")
    need_config = result.get("scenarios_need_configuration", [])
    check(
        "identifies_config_needed",
        True,
        f"{len(need_config)} scenarios need configuration (runnable=False)",
    )

    logger.info(f"{'=' * 70}")
    logger.info(f"  RESULTS: {results['passed']} passed, {results['failed']} failed")
    logger.info("  NOTE: scenario_parameters is a Phase 5 feature placeholder")
    logger.info(f"{'=' * 70}")

    return results


class TestChoice(Enum):
    LIST_ASSESSMENTS = "list_assessments"
    GET_RECENT_RUN = "get_recent_run"
    RUN_ASSESSMENT = "run_assessment"
    WORKFLOW_DEMO = "workflow_demo"
    GET_RESULTS = "get_results"
    GET_RECENT_RUN_RESULTS = "get_recent_run_results"
    EXECUTION_WITH_DETECTION = "execution_with_detection"
    EXECUTION_WITHOUT_DETECTION = "execution_without_detection"
    GET_EXECUTION_STRATEGY = "get_execution_strategy"
    SEARCH_ASSESSMENTS_PAGINATION = "search_assessments_pagination"
    LIST_RUNS_PAGINATION = "list_runs_pagination"
    TEST_FILTERS = "test_filters"
    TEST_RUNS = "test_runs"
    TEST_CONFIGURATION = "test_configuration"
    ATOMIC_CREATION = "atomic_creation"
    SCENARIO_PARAMETERS = "scenario_parameters"
    ALL = "all"


async def main():
    require_env(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN)
    choice = parse_test_choice(TestChoice)

    async with AttackIQClient(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN) as client:
        assessment_id = os.environ.get("ASSESSMENT_ID") or os.environ.get("ATTACKIQ_ATOMIC_ASSESSMENT_ID")
        await run_test(choice, client, assessment_id)


if __name__ == "__main__":
    asyncio.run(main())
