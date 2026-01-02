import asyncio
import time
from typing import Optional, Dict, Any, List, AsyncGenerator, Tuple

import httpx

from aiq_platform_api.core.async_utils import async_islice
from aiq_platform_api.core.client import AttackIQClient
from aiq_platform_api.core.constants import AssessmentExecutionStrategy
from aiq_platform_api.core.logger import AttackIQLogger

logger = AttackIQLogger.get_logger(__name__)


class Assessments:
    ASSESSMENT_ENDPOINT = "v1/assessments"
    PUBLIC_ENDPOINT = "v1/public/assessment"
    RESULTS_V1_ENDPOINT = "v1/results"
    RESULTS_V2_ENDPOINT = "v2/results"
    RUN_ASSESSMENT_V1_ENDPOINT = "v1/assessments/{}/run_all"
    RUN_ASSESSMENT_V2_ENDPOINT = "v2/assessments/{}/run_all"

    @staticmethod
    async def get_assessments(
        client: AttackIQClient,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 10,
        offset: Optional[int] = 0,
        ordering: Optional[str] = "-modified",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        request_params = params.copy() if params else {}
        if ordering:
            request_params["ordering"] = ordering
        logger.info(f"Listing assessments with params: {request_params}, limit: {limit}, offset: {offset}")
        generator = client.get_all_objects(Assessments.ASSESSMENT_ENDPOINT, params=request_params)
        stop = None if limit is None else offset + limit
        async for assessment in async_islice(generator, offset, stop):
            yield assessment

    @staticmethod
    async def _fetch_atomic_tests(
        client: AttackIQClient,
        assessment_id: str,
        scenarios_limit: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        tests = [test async for test in client.get_all_objects("v1/tests", {"project_id": assessment_id})]

        scenarios_fetched = 0
        limit_reached = False

        for test in tests:
            if limit_reached:
                # Don't fetch more tests once limit is reached
                test["scenarios"] = []
                test["assets"] = []
                continue

            test_id = test["id"]

            # Fetch scenarios with optional limit
            scenarios = []
            async for scenario in client.get_all_objects("v1/test_scenarios", {"scenario_master_job": test_id}):
                # Check limit BEFORE appending so limit=0 fetches nothing
                if scenarios_limit is not None and scenarios_fetched >= scenarios_limit:
                    limit_reached = True
                    break  # Stop fetching scenarios
                scenarios.append(scenario)
                scenarios_fetched += 1
            test["scenarios"] = scenarios

            # Only fetch assets if we fetched scenarios for this test
            if scenarios:
                test["assets"] = [
                    asset async for asset in client.get_all_objects("v1/test_assets", {"scenario_master_job": test_id})
                ]
            else:
                test["assets"] = []

        return tests, scenarios_fetched, limit_reached

    @staticmethod
    def _compute_atomic_analysis(tests: List[Dict], version: int, boundaries: List) -> Dict[str, Any]:
        total_scenarios = sum(len(t.get("scenarios", [])) for t in tests)
        total_assets = sum(len(t.get("assets", [])) for t in tests)
        has_multi_asset = any(
            s.get("scenario", {}).get("is_multi_asset") for t in tests for s in t.get("scenarios", [])
        )
        is_network = bool(boundaries) and has_multi_asset

        if is_network:
            assessment_type = f"v{version} Atomic Network"
            estimated_jobs = total_scenarios * len(boundaries)
        else:
            assessment_type = f"v{version} Atomic Endpoint"
            estimated_jobs = sum(len(t.get("scenarios", [])) * max(len(t.get("assets", [])), 1) for t in tests)

        return {
            "assessment_type": assessment_type,
            "is_attack_graph": False,
            "is_network": is_network,
            "has_multi_asset_scenarios": has_multi_asset,
            "total_scenarios": total_scenarios,
            "total_assets": total_assets,
            "total_boundaries": len(boundaries) if is_network else 0,
            "estimated_jobs": estimated_jobs,
        }

    @staticmethod
    async def _fetch_attack_graph(
        client: AttackIQClient,
        assessment_id: str,
        nodes_limit: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        extra_url = client._build_url("v1/assessments/details", {"project_ids": assessment_id})
        extra = await client._make_request(extra_url, method="get", json=None)
        attack_graph_id = extra.get("results", {}).get(assessment_id, {}).get("attack_graph_id") if extra else None
        if not attack_graph_id:
            return None

        graph = await client.get_object(f"v1/attack_graphs/{attack_graph_id}")
        if not graph or nodes_limit is None:
            return graph

        # Apply nodes limit to the graph
        graph_data = graph.get("graph", {})
        nodes = graph_data.get("graph", {})
        total_nodes = len(nodes)

        if total_nodes > nodes_limit:
            # Keep only first N nodes (by key order)
            limited_keys = list(nodes.keys())[:nodes_limit]
            limited_nodes = {k: nodes[k] for k in limited_keys}
            graph["graph"]["graph"] = limited_nodes
            graph["_truncated"] = True
            graph["_truncation_info"] = {
                "type": "nodes",
                "fetched": nodes_limit,
                "total": total_nodes,
                "limit": nodes_limit,
            }

        return graph

    @staticmethod
    def _compute_attack_graph_analysis(graph: Dict[str, Any]) -> Dict[str, Any]:
        graph_data = graph.get("graph", {})
        nodes = graph_data.get("graph", {})
        stages = graph_data.get("graph_meta", {}).get("stages", {})
        has_multi_asset = any(n.get("is_multi_asset") for n in nodes.values())
        graph_type = "MTAG" if has_multi_asset else "STAG"

        return {
            "assessment_type": f"Attack Graph {graph_type}",
            "is_attack_graph": True,
            "graph_type": graph_type,
            "total_nodes": len(nodes),
            "total_stages": len(stages),
            "has_multi_asset_nodes": has_multi_asset,
            "estimated_jobs": len(nodes),
        }

    @staticmethod
    async def get_assessment_by_id(
        client: AttackIQClient,
        assessment_id: str,
        include_tests: bool = False,
        scenarios_limit: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        endpoint = f"{Assessments.ASSESSMENT_ENDPOINT}/{assessment_id}"
        logger.info(f"Fetching assessment details for ID: {assessment_id}")
        details = await client.get_object(endpoint)

        if not include_tests or details is None:
            return details

        version = details.get("version", 1)
        boundaries = details.get("boundaries", [])

        if details.get("master_job_count", 0) > 0:
            tests, scenarios_fetched, was_truncated = await Assessments._fetch_atomic_tests(
                client, assessment_id, scenarios_limit=scenarios_limit
            )
            details["tests"] = tests
            details["_analysis"] = Assessments._compute_atomic_analysis(tests, version, boundaries)
            # Add truncation metadata
            if was_truncated:
                details["_truncated"] = True
                details["_truncation_info"] = {
                    "type": "scenarios",
                    "fetched": scenarios_fetched,
                    "limit": scenarios_limit,
                    # Note: actual total unknown since we stopped fetching early
                }
        else:
            graph = await Assessments._fetch_attack_graph(client, assessment_id, nodes_limit=scenarios_limit)
            if graph:
                details["attack_graph"] = graph
                analysis = Assessments._compute_attack_graph_analysis(graph)
                details["_analysis"] = analysis
                # Add truncation metadata for attack graphs
                # Note: _analysis describes the truncated data, _truncation_info has full totals
                if graph.get("_truncated"):
                    details["_truncated"] = True
                    details["_truncation_info"] = graph.get("_truncation_info", {})

        return details

    @staticmethod
    async def search_assessments(
        client: AttackIQClient,
        query: Optional[str] = None,
        version: Optional[int] = None,
        created_after: Optional[str] = None,
        modified_after: Optional[str] = None,
        execution_strategy: Optional[int] = None,
        user_id: Optional[str] = None,
        is_attack_graph: Optional[bool] = None,
        project_template_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        ordering: str = "-modified",
    ) -> Dict[str, Any]:
        logger.info(f"Searching assessments: query='{query}', version={version}, limit={limit}, offset={offset}")
        params: Dict[str, Any] = {"page_size": limit, "offset": offset}
        if query:
            params["search"] = query
        if version is not None:
            params["version"] = version
        if created_after:
            params["created_after"] = created_after
        if modified_after:
            params["modified_after"] = modified_after
        if execution_strategy is not None:
            params["execution_strategy"] = execution_strategy
        if user_id:
            params["user_id"] = user_id
        if is_attack_graph is not None:
            params["is_attack_graph"] = str(is_attack_graph).lower()
        if project_template_id:
            params["project_template_id"] = project_template_id
        if ordering:
            params["ordering"] = ordering

        url = client._build_url(Assessments.ASSESSMENT_ENDPOINT, params)
        data = await client._make_request(url, method="get", json=None)
        total_count = data.get("count", 0)
        results = data.get("results", [])
        logger.info(f"Found {total_count} total assessments, returning {len(results)}")
        return {"count": total_count, "results": results}

    @staticmethod
    async def list_assessment_runs(
        client: AttackIQClient,
        assessment_id: str,
        limit: int = 20,
        offset: int = 0,
        ordering: str = "-created",
    ) -> Dict[str, Any]:
        logger.info(f"Listing runs for assessment {assessment_id}: limit={limit}, offset={offset}")
        endpoint = f"{Assessments.PUBLIC_ENDPOINT}/{assessment_id}/runs"
        params: Dict[str, Any] = {}
        if ordering:
            params["ordering"] = ordering

        generator = client.get_all_objects(endpoint, params=params)
        all_runs = [run async for run in generator]
        total_count = len(all_runs)
        results = all_runs[offset : offset + limit]
        logger.info(f"Found {len(results)} runs (total: {total_count}) for assessment {assessment_id}")
        return {"count": total_count, "results": results}

    @staticmethod
    async def search_assessment_runs(
        client: AttackIQClient,
        assessment_id: str,
        limit: int = 20,
        offset: int = 0,
        ordering: str = "-created",
    ) -> Dict[str, Any]:
        return await Assessments.list_assessment_runs(client, assessment_id, limit, offset, ordering)

    @staticmethod
    async def get_run(client: AttackIQClient, assessment_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        endpoint = "v1/widgets/assessment_runs"
        params = {"project_id": assessment_id, "run_id": run_id}
        logger.debug(f"Getting run {run_id} for assessment {assessment_id}")

        try:
            results = await client.get_object(endpoint, params=params)
            if results and isinstance(results, dict):
                runs = results["results"]
                if runs:
                    return runs[0]
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code == 400:
                if "run does not exist" in e.response.text:
                    return None
            raise

        return None

    @staticmethod
    async def get_most_recent_run_status(
        client: AttackIQClient, assessment_id: str, without_detection: bool = True
    ) -> Optional[Dict[str, Any]]:
        logger.info(f"Getting most recent run status for assessment {assessment_id}")

        result = await Assessments.list_assessment_runs(client, assessment_id, limit=1)
        runs = result.get("results", [])
        if runs:
            run = runs[0]
            run_id = run.get("id")
            logger.info(f"Found most recent run: {run_id}")

            status = await Assessments.get_run_status(client, assessment_id, run_id, without_detection)
            if status:
                run.update(status)

            return run

        logger.warning(f"No runs found for assessment {assessment_id}")
        return None

    @staticmethod
    async def get_run_status(
        client: AttackIQClient,
        assessment_id: str,
        run_id: str,
        without_detection: bool = True,
    ) -> Optional[Dict[str, Any]]:
        logger.info(
            f"Checking status for run {run_id} of assessment {assessment_id} without detection: {without_detection}"
        )

        run = await Assessments.get_run(client, assessment_id, run_id)
        if not run:
            logger.warning(f"Run ID {run_id} not found for assessment {assessment_id}")
            return None

        scenario_jobs = run.get("scenario_jobs_in_progress", 0)
        integration_jobs = run.get("integration_jobs_in_progress", 0)

        scenario_jobs = 0 if scenario_jobs is False else scenario_jobs
        integration_jobs = 0 if integration_jobs is False else integration_jobs

        completed = scenario_jobs == 0 if without_detection else (scenario_jobs == 0 and integration_jobs == 0)

        return {
            "scenario_jobs_in_progress": scenario_jobs,
            "integration_jobs_in_progress": integration_jobs,
            "completed": completed,
            "total_count": run.get("total_count", 0),
            "done_count": run.get("done_count", 0),
            "sent_count": run.get("sent_count", 0),
            "pending_count": run.get("pending_count", 0),
            "cancelled_count": run.get("cancelled_count", 0),
        }

    @staticmethod
    async def is_run_complete(
        client: AttackIQClient,
        assessment_id: str,
        run_id: str,
        without_detection: bool = True,
    ) -> bool:
        status = await Assessments.get_run_status(client, assessment_id, run_id, without_detection)
        return status.get("completed", False) if status else False

    @staticmethod
    async def run_assessment(client: AttackIQClient, assessment_id: str, assessment_version: int) -> Optional[str]:
        endpoint = (
            Assessments.RUN_ASSESSMENT_V2_ENDPOINT
            if assessment_version == 2
            else Assessments.RUN_ASSESSMENT_V1_ENDPOINT
        ).format(assessment_id)

        run_result = await client.post_object(endpoint, data={})

        if not run_result:
            logger.error(f"Failed to start assessment {assessment_id}")
            return None

        run_id = run_result["run_id"]
        if not run_id:
            logger.error(f"No run ID in response for assessment {assessment_id}")
            return None

        logger.info(f"Assessment {assessment_id} (v{assessment_version}) started with run ID: {run_id}")
        return run_id

    @staticmethod
    async def get_results_by_run_id(
        client: AttackIQClient,
        run_id: str,
        assessment_version: int,
        limit: Optional[int] = 10,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        endpoint = Assessments.RESULTS_V2_ENDPOINT if assessment_version == 2 else Assessments.RESULTS_V1_ENDPOINT
        params = {"run_id": run_id, "assessment_results": "true"}
        logger.info(f"Fetching results for run ID: {run_id} from {endpoint}")

        generator = client.get_all_objects(endpoint, params=params)
        async for result in async_islice(generator, 0, limit):
            yield result

    @staticmethod
    async def get_result_details(
        client: AttackIQClient, result_id: str, assessment_version: int
    ) -> Optional[Dict[str, Any]]:
        base_endpoint = Assessments.RESULTS_V2_ENDPOINT if assessment_version == 2 else Assessments.RESULTS_V1_ENDPOINT
        endpoint = f"{base_endpoint}/{result_id}"
        logger.info(f"Fetching detailed result for ID: {result_id} from {endpoint}")
        return await client.get_object(endpoint)

    @staticmethod
    async def get_assets_in_assessment(
        client: AttackIQClient,
        assessment_id: str,
        limit: Optional[int] = 10,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        from aiq_platform_api.core.assets import Assets

        params = {"hide_hosted_agents": "true", "project_id": assessment_id}
        logger.info(f"Listing assets for assessment ID: {assessment_id}")
        generator = Assets.get_assets(client, params=params)
        async for asset in async_islice(generator, 0, limit):
            yield asset

    @staticmethod
    async def wait_for_run_completion(
        client: AttackIQClient,
        assessment_id: str,
        run_id: str,
        timeout: int = 600,
        check_interval: int = 10,
        without_detection: bool = True,
    ) -> bool:
        logger.info(
            f"Waiting for run {run_id} of assessment {assessment_id} to complete without detection: {without_detection}"
        )
        start_time = time.time()
        last_status = None

        while time.time() - start_time < timeout:
            run = await Assessments.get_run(client, assessment_id, run_id)
            if not run:
                logger.warning(f"Run {run_id} not found")
                return False

            scenario_jobs = run.get("scenario_jobs_in_progress", 0)
            integration_jobs = run.get("integration_jobs_in_progress", 0)

            total_count = run.get("total_count", 0)
            done_count = run.get("done_count", 0)

            if without_detection:
                is_completed = not scenario_jobs
            else:
                is_completed = not scenario_jobs and not integration_jobs

            if is_completed:
                elapsed_time = round(time.time() - start_time, 2)
                logger.info(f"Run completed in {elapsed_time} seconds")
                return True

            status_msg = f"Progress: {done_count}/{total_count} completed"
            if status_msg != last_status:
                logger.info(f"{status_msg}")
                last_status = status_msg

            await asyncio.sleep(check_interval)

        logger.warning(f"Run did not complete within {timeout} seconds")
        return False

    @staticmethod
    async def get_execution_strategy(client: AttackIQClient, assessment_id: str) -> AssessmentExecutionStrategy:
        endpoint = f"{Assessments.ASSESSMENT_ENDPOINT}/{assessment_id}"
        assessment = await client.get_object(endpoint)
        return AssessmentExecutionStrategy(assessment["execution_strategy"])

    @staticmethod
    async def set_execution_strategy(client: AttackIQClient, assessment_id: str, with_detection: bool) -> bool:
        execution_strategy = (
            AssessmentExecutionStrategy.WITH_DETECTION
            if with_detection
            else AssessmentExecutionStrategy.WITHOUT_DETECTION
        )
        endpoint = f"{Assessments.ASSESSMENT_ENDPOINT}/{assessment_id}"
        result = await client.patch_object(endpoint, {"execution_strategy": execution_strategy.value})
        return result is not None

    # Blank template UUID for atomic assessment creation
    BLANK_TEMPLATE_UUID = "d09d29ba-eed8-4212-bff2-4d1ee11ed80c"
    MAX_SCENARIOS_PER_BATCH = 25

    @staticmethod
    async def create_atomic_assessment(
        client: AttackIQClient,
        name: str,
        scenario_ids: List[str],
        asset_ids: List[str],
        test_name: str = "Test Container 1",
    ) -> Dict[str, Any]:
        """Create an atomic assessment with transaction semantics.

        Orchestrates 5 API calls:
        1. POST /v1/assessments/project_from_template - Create blank assessment
        2. POST /v1/tests - Add test container
        3. POST /v1/tests/{id}/bulk_add_scenarios - Add scenarios
        4. POST /v1/assessments/{id}/update_defaults - Assign test points
        5. PATCH /v1/assessments/{id} - Set execution_strategy to prevention-only

        Detection is disabled by design. Legacy detection validation via API is deprecated.
        Use the platform UI if detection is required. New detection workflow: Atlas project.

        Args:
            client: AttackIQ API client
            name: Assessment name (recommend using [plan_id-batch_id] prefix)
            scenario_ids: List of scenario UUIDs (max 25)
            asset_ids: List of test point (asset) UUIDs - provide at least one per OS
            test_name: Name for the test container

        Returns:
            Dict with assessment_id, test_id, and creation details

        Raises:
            ValueError: If scenario_ids exceeds MAX_SCENARIOS_PER_BATCH, is empty, or asset_ids is empty
            RuntimeError: If any API call fails (assessment is cleaned up)
        """
        if not scenario_ids:
            raise ValueError("At least one scenario_id is required")
        if len(scenario_ids) > Assessments.MAX_SCENARIOS_PER_BATCH:
            raise ValueError(
                f"Cannot add more than {Assessments.MAX_SCENARIOS_PER_BATCH} scenarios per batch, got {len(scenario_ids)}"
            )
        if not asset_ids:
            raise ValueError("At least one asset_id is required")

        assessment_id = None
        test_id = None

        try:
            # Step 1: Create assessment from template
            logger.info(f"Creating assessment '{name}' from blank template")
            create_result = await client.post_object(
                "v1/assessments/project_from_template",
                data={
                    "template": Assessments.BLANK_TEMPLATE_UUID,
                    "project_name": name,
                },
            )
            # API returns "project_id" not "id"
            assessment_id = create_result.get("project_id") if create_result else None
            if not assessment_id:
                raise RuntimeError(f"Failed to create assessment: {create_result}")
            logger.info(f"Created assessment: {assessment_id}")

            # Step 2: Add test container
            logger.info(f"Adding test container '{test_name}' to assessment {assessment_id}")
            test_result = await client.post_object(
                "v1/tests",
                data={
                    "project": assessment_id,  # NOTE: "project" not "project_id"
                    "name": test_name,
                },
            )
            test_id = test_result.get("id") if test_result else None
            if not test_id:
                raise RuntimeError(f"Failed to create test container: {test_result}")
            logger.info(f"Created test container: {test_id}")

            # Step 3: Bulk add scenarios
            logger.info(f"Adding {len(scenario_ids)} scenarios to test {test_id}")
            bulk_result = await client.post_object(
                f"v1/tests/{test_id}/bulk_add_scenarios",
                data={"include": scenario_ids},
            )
            if bulk_result is None:
                raise RuntimeError("Failed to bulk add scenarios")
            logger.info(f"Added {len(scenario_ids)} scenarios")

            # Step 4: Assign test points (assets) - API accepts list
            logger.info(f"Assigning {len(asset_ids)} test points to assessment {assessment_id}")
            defaults_result = await client.post_object(
                f"v1/assessments/{assessment_id}/update_defaults",
                data={"assets": asset_ids},
            )
            if defaults_result is None:
                raise RuntimeError("Failed to assign test points")
            logger.info(f"Assigned test points: {asset_ids}")

            # Step 5: Disable detection (execution_strategy=1 = prevention-only)
            # Legacy detection via API is deprecated. Use platform UI or Atlas project.
            logger.info(f"Disabling detection for assessment {assessment_id}")
            await Assessments.set_execution_strategy(client, assessment_id, with_detection=False)

            return {
                "assessment_id": assessment_id,
                "test_id": test_id,
                "name": name,
                "scenario_count": len(scenario_ids),
                "asset_ids": asset_ids,
            }

        except Exception as e:
            # Transaction rollback: delete assessment if created
            if assessment_id:
                logger.warning(f"Rolling back: deleting assessment {assessment_id} due to error: {e}")
                try:
                    await client.delete_object(f"v1/assessments/{assessment_id}")
                    logger.info(f"Rolled back assessment {assessment_id}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to rollback assessment {assessment_id}: {cleanup_error}")
            raise

    @staticmethod
    async def validate_assessment_batch(
        client: AttackIQClient,
        scenario_ids: List[str],
        test_point_ids: List[str],
        scenario_parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate a batch before creating an assessment.

        Pre-creation guardrail that checks:
        1. Scenario count ≤ 25
        2. All test points exist and have status: Active
        3. OS compatibility: each scenario has ≥1 compatible test point
        4. Multi-asset scenarios are flagged
        5. All scenario IDs exist (anti-hallucination)
        6. (Future) Config completeness: scenarios needing params have them provided

        Args:
            client: AttackIQ API client
            scenario_ids: List of scenario UUIDs to validate
            test_point_ids: List of test point (asset) UUIDs - need at least one per OS
            scenario_parameters: (Phase 5) Dict of {scenario_id: {param: value}} for config validation

        Returns:
            {
                "is_valid": bool,
                "errors": [...],
                "warnings": [...],
                "compatible_scenarios": [...],
                "scenarios_need_configuration": [{id, name, reason}],  # Screams: look at SCENARIO
                "scenarios_need_test_point": [{id, name, required_platforms, reason}],  # Screams: look at TEST POINT LIST
                "multi_asset_scenarios": [{id, name}],
                "not_found_scenarios": [...],
                "test_points": [{id, hostname, status, platforms}, ...],
                "summary": {...}
            }
        """
        from aiq_platform_api.core.assets import Assets, get_asset_platforms, normalize_platform
        from aiq_platform_api.core.scenarios import Scenarios

        errors: List[str] = []
        warnings: List[str] = []
        compatible: List[str] = []
        need_configuration: List[Dict[str, Any]] = []  # Scenarios where runnable=False
        need_test_point: List[Dict[str, Any]] = []  # Scenarios with no compatible test point
        multi_asset: List[Dict[str, Any]] = []
        not_found: List[Dict[str, Any]] = []

        # Check 1: Scenario count
        if not scenario_ids:
            errors.append("No scenarios provided")
        elif len(scenario_ids) > Assessments.MAX_SCENARIOS_PER_BATCH:
            errors.append(f"Too many scenarios: {len(scenario_ids)} exceeds max {Assessments.MAX_SCENARIOS_PER_BATCH}")

        # Check 2: All test points exist and are Active
        if not test_point_ids:
            errors.append("No test points provided")

        test_points_info: List[Dict[str, Any]] = []
        all_test_point_platforms: set = set()  # Union of all platforms across test points

        for tp_id in test_point_ids:
            try:
                tp = await Assets.get_asset_by_id(client, tp_id)
                if tp.get("status") != "Active":
                    errors.append(f"Test point {tp_id} is not Active (status: {tp.get('status')})")

                tp_platforms = get_asset_platforms(tp)
                if not tp_platforms:
                    # Fallback: infer from product_name
                    product_name = (tp.get("product_name") or "").lower()
                    if "windows" in product_name:
                        tp_platforms.add("windows")
                    elif "linux" in product_name or "ubuntu" in product_name or "centos" in product_name:
                        tp_platforms.add("linux")
                    elif "mac" in product_name or "darwin" in product_name:
                        tp_platforms.add("osx")

                all_test_point_platforms.update(tp_platforms)
                test_points_info.append(
                    {
                        "id": tp_id,
                        "hostname": tp.get("hostname"),
                        "status": tp.get("status"),
                        "platforms": list(tp_platforms),
                    }
                )
            except Exception as e:
                errors.append(f"Test point not found: {tp_id} ({str(e)})")

        # Check 3, 4, 5: Scenario validation
        for sid in scenario_ids:
            try:
                req = await Scenarios.get_scenario_requirements(client, sid)

                # Handle None or empty return (scenario not found - SDK returns {} on 404)
                if not req or not req.get("name"):
                    not_found.append({"id": sid, "error": "Scenario not found"})
                    errors.append(f"Scenario not found: {sid}")
                    continue

                # Check multi-asset
                if req.get("is_multi_asset"):
                    multi_asset.append({"id": sid, "name": req.get("name", "")})
                    warnings.append(f"Multi-asset scenario excluded: {req.get('name', sid)}")
                    continue

                # Check not runnable - scenario needs configuration
                if not req.get("runnable", True):
                    need_configuration.append(
                        {
                            "id": sid,
                            "name": req.get("name", ""),
                            "reason": "Scenario is not runnable (needs configuration)",
                        }
                    )
                    continue

                # Check OS compatibility - scenario needs at least one compatible test point
                scenario_platforms = set(normalize_platform(p) for p in req.get("supported_platforms", []))

                if not scenario_platforms:
                    # No platform restriction - compatible with any test point
                    compatible.append(sid)
                elif not all_test_point_platforms:
                    # Unknown test point platforms - warn but allow
                    compatible.append(sid)
                    warnings.append(f"Cannot verify OS compatibility for {sid} (unknown test point platforms)")
                elif scenario_platforms & all_test_point_platforms:
                    # At least one test point has matching platform
                    compatible.append(sid)
                else:
                    # No test point supports this scenario's platforms - need to add test point
                    need_test_point.append(
                        {
                            "id": sid,
                            "name": req.get("name", ""),
                            "required_platforms": list(scenario_platforms),
                            "reason": f"No test point supports platforms {list(scenario_platforms)}",
                        }
                    )

            except Exception as e:
                not_found.append({"id": sid, "error": str(e)})
                errors.append(f"Scenario not found: {sid}")

        # Determine overall validity
        is_valid = (
            len(errors) == 0
            and len(need_configuration) == 0
            and len(need_test_point) == 0
            and len(not_found) == 0
            and len(multi_asset) == 0
        )

        # Count only truly active test points for summary
        active_count = sum(1 for tp in test_points_info if tp.get("status") == "Active")

        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "compatible_scenarios": compatible,
            "scenarios_need_configuration": need_configuration,
            "scenarios_need_test_point": need_test_point,
            "multi_asset_scenarios": multi_asset,
            "not_found_scenarios": not_found,
            "test_points": test_points_info,
            "summary": {
                "total_scenarios": len(scenario_ids),
                "total_test_points": len(test_point_ids),
                "active_test_points": active_count,
                "available_platforms": list(all_test_point_platforms),
                "compatible": len(compatible),
                "need_configuration": len(need_configuration),
                "need_test_point": len(need_test_point),
                "multi_asset": len(multi_asset),
                "not_found": len(not_found),
            },
        }
