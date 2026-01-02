from datetime import datetime
from typing import Optional, Dict, Any, AsyncGenerator

from aiq_platform_api.core.async_utils import async_islice
from aiq_platform_api.core.client import AttackIQClient
from aiq_platform_api.core.logger import AttackIQLogger

logger = AttackIQLogger.get_logger(__name__)


class Results:
    """Utilities for working with results in the AttackIQ platform.

    API Endpoint: /v1/results
    """

    ENDPOINT = "v1/results"

    @staticmethod
    async def get_results(
        client: AttackIQClient,
        page: int = 1,
        page_size: int = 10,
        search: str = "",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = 10,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """List results, optionally filtered and limited."""
        params = {
            "page": page,
            "page_size": page_size,
            "search": search,
        }
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        generator = client.get_all_objects(Results.ENDPOINT, params=params)
        async for item in async_islice(generator, 0, limit):
            yield item

    @staticmethod
    async def get_results_by_run_id(
        client: AttackIQClient, run_id: str, limit: Optional[int] = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get assessment result summaries filtered by run ID, optionally limited."""
        endpoint_with_params = f"{Results.ENDPOINT}?run_id={run_id}&assessment_results=true"
        logger.info(f"Fetching result summaries for run_id: {run_id} from constructed URL: {endpoint_with_params}")
        generator = client.get_all_objects(endpoint_with_params, params=None)
        async for result in async_islice(generator, 0, limit):
            yield result

    @staticmethod
    async def get_result_by_id(client: AttackIQClient, result_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed results for a specific result ID."""
        endpoint = f"{Results.ENDPOINT}/{result_id}"
        logger.info(f"Attempting to fetch result details from endpoint: {endpoint}.")
        return await client.get_object(endpoint)


class PhaseResults:
    """Utilities for working with phase results in the AttackIQ platform.

    API Endpoint: /v1/phase_results
    """

    ENDPOINT = "v1/phase_results"

    @staticmethod
    async def get_phase_results(
        client: AttackIQClient,
        assessment_id: str,
        project_run_id: Optional[str] = None,
        result_summary_id: Optional[str] = None,
        limit: Optional[int] = 10,
    ) -> AsyncGenerator[dict, None]:
        """Get phase results, optionally filtered and limited."""
        params = {"project_id": assessment_id}
        if project_run_id:
            params["project_run_id"] = project_run_id  # Backend field name
        if result_summary_id:
            params["result_summary"] = result_summary_id
        generator = client.get_all_objects(PhaseResults.ENDPOINT, params=params)
        async for result in async_islice(generator, 0, limit):
            yield result


class PhaseLogs:
    """Utilities for working with phase logs in the AttackIQ platform.

    API Endpoint: /v1/logs_api/phase_logs (same as UI)
    Note: UI uses node_instance_id as primary filter.
    """

    ENDPOINT = "v1/logs_api/phase_logs"

    @staticmethod
    async def get_phase_logs(
        client: AttackIQClient,
        node_instance_id: Optional[str] = None,
        scenario_job_id: Optional[str] = None,
        phase_number: Optional[int] = None,
        trace_type_id: Optional[str] = None,
        limit: Optional[int] = 10,
    ) -> AsyncGenerator[dict, None]:
        """Get phase logs filtered by node_instance_id or scenario_job_id."""
        params = {}
        if node_instance_id:
            params["node_instance_id"] = node_instance_id
        if scenario_job_id:
            params["scenario_job_id"] = scenario_job_id
        if phase_number:
            params["phase_number"] = phase_number
        if trace_type_id:
            params["trace_type_id"] = trace_type_id
        logger.info(f"Fetching phase logs with params: {params}, limit: {limit}")
        generator = client.get_all_objects(PhaseLogs.ENDPOINT, params=params)
        async for log in async_islice(generator, 0, limit):
            yield log
