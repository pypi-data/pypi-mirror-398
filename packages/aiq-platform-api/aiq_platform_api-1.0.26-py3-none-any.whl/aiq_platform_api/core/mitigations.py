from http import HTTPStatus
from typing import Optional, Dict, Any, AsyncGenerator

from aiq_platform_api.core.async_utils import async_islice
from aiq_platform_api.core.client import AttackIQClient
from aiq_platform_api.core.constants import AnalystVerdict, INTEGRATION_NAMES
from aiq_platform_api.core.logger import AttackIQLogger

logger = AttackIQLogger.get_logger(__name__)


class UnifiedMitigations:
    """Utilities for interacting with Unified Mitigation rules.

    API Endpoint: /v1/unified_mitigations
    """

    ENDPOINT = "v1/unified_mitigations"

    @staticmethod
    async def list_mitigations(
        client: AttackIQClient,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 10,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """List all unified mitigation rules, optionally filtered and limited."""
        logger.info(f"Listing unified mitigations with params: {params}")
        generator = client.get_all_objects(UnifiedMitigations.ENDPOINT, params=params)
        async for mitigation in async_islice(generator, 0, limit):
            yield mitigation

    @staticmethod
    async def get_rules_by_integration_name(
        client: AttackIQClient,
        integration_name: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 10,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get unified mitigation rules filtered by integration name."""
        if integration_name in INTEGRATION_NAMES:
            full_integration_name = INTEGRATION_NAMES[integration_name]
        else:
            full_integration_name = integration_name

        logger.info(f"Getting rules for integration name '{integration_name}' -> '{full_integration_name}'")

        if params is None:
            params = {}
        params["integration_name"] = full_integration_name

        endpoint = "v1/unified_mitigations_with_relations"
        generator = client.get_all_objects(endpoint, params=params)
        async for rule in async_islice(generator, 0, limit):
            yield rule

    @staticmethod
    async def get_mitigation(client: AttackIQClient, mitigation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific unified mitigation rule by its ID."""
        endpoint = f"{UnifiedMitigations.ENDPOINT}/{mitigation_id}"
        logger.info(f"Getting unified mitigation: {mitigation_id}")
        return await client.get_object(endpoint)

    @staticmethod
    async def create_mitigation(client: AttackIQClient, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new unified mitigation rule."""
        logger.info(f"Creating unified mitigation with data: {data}")
        return await client.post_object(UnifiedMitigations.ENDPOINT, data=data)

    @staticmethod
    async def update_mitigation(
        client: AttackIQClient, mitigation_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing unified mitigation rule (PUT)."""
        endpoint = f"{UnifiedMitigations.ENDPOINT}/{mitigation_id}"
        logger.info(f"Updating unified mitigation {mitigation_id} with data: {data}")
        url = client._build_url(endpoint)
        return await client._make_request(url, method="put", json=data)

    @staticmethod
    async def partial_update_mitigation(
        client: AttackIQClient, mitigation_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Partially update an existing unified mitigation rule (PATCH)."""
        endpoint = f"{UnifiedMitigations.ENDPOINT}/{mitigation_id}"
        logger.info(f"Partially updating unified mitigation {mitigation_id} with data: {data}")
        url = client._build_url(endpoint)
        return await client._make_request(url, method="patch", json=data)

    @staticmethod
    async def delete_mitigation(client: AttackIQClient, mitigation_id: str) -> bool:
        """Delete a unified mitigation rule."""
        endpoint = f"{UnifiedMitigations.ENDPOINT}/{mitigation_id}"
        logger.info(f"Deleting unified mitigation: {mitigation_id}")
        response = await client.delete_object(endpoint)
        return response is not None and response.get("status_code") == HTTPStatus.NO_CONTENT

    @staticmethod
    async def get_detection_results(
        client: AttackIQClient,
        mitigation_id: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 10,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get detection results for a specific mitigation rule across all runs."""
        logger.info(f"Getting detection results for mitigation {mitigation_id}")
        endpoint = f"v1/unified_mitigations_with_relations/{mitigation_id}"
        rule = await client.get_object(endpoint)
        if not rule:
            return
        detection_results = rule["detection_results"]
        for idx, result in enumerate(detection_results):
            if limit is not None and idx >= limit:
                break
            yield result

    @staticmethod
    def _transform_detection_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Transform detection result to use analyst_verdict instead of detection_outcome."""
        if "detection_outcome" in result:
            result["analyst_verdict"] = result.pop("detection_outcome")
        return result

    @staticmethod
    async def get_latest_detection_result(client: AttackIQClient, mitigation_id: str) -> Optional[Dict[str, Any]]:
        """Get the detection result for the current/latest assessment run."""
        logger.info(f"Getting latest detection result for mitigation {mitigation_id}")

        run_status = await UnifiedMitigations.get_latest_assessment_run_status(client, mitigation_id)
        if not run_status:
            logger.info(f"No assessment runs found for mitigation {mitigation_id}")
            return None

        endpoint = f"v1/unified_mitigations_with_relations/{mitigation_id}"
        rule = await client.get_object(endpoint)
        if not rule:
            return None

        detection_results = rule["detection_results"]
        if not detection_results:
            return None

        latest_result = detection_results[0]
        if latest_result.get("project_run_id") == run_status["id"]:
            return UnifiedMitigations._transform_detection_result(latest_result)
        else:
            logger.info(f"No detection result for current run {run_status['id']}")
            return None

    @staticmethod
    async def get_associated_assessment(client: AttackIQClient, mitigation_id: str) -> Optional[Dict[str, Any]]:
        """Get the assessment associated with a mitigation rule."""
        from aiq_platform_api.core.assessments import Assessments

        logger.info(f"Getting associated assessment for mitigation {mitigation_id}")
        endpoint = f"v1/unified_mitigations_with_relations/{mitigation_id}"
        rule = await client.get_object(endpoint)
        if not rule:
            return None
        projects = rule["projects"]
        if not projects:
            return None
        assessment_id = projects[0]["project_id"]
        return await Assessments.get_assessment_by_id(client, assessment_id, include_tests=False, scenarios_limit=None)

    @staticmethod
    async def get_latest_assessment_run_status(client: AttackIQClient, mitigation_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent run status for a rule's associated assessment."""
        from aiq_platform_api.core.assessments import Assessments

        assessment = await UnifiedMitigations.get_associated_assessment(client, mitigation_id)
        if not assessment:
            logger.info(f"No assessment associated with mitigation {mitigation_id}")
            return None

        assessment_id = assessment["id"]
        run_status = await Assessments.get_most_recent_run_status(client, assessment_id, without_detection=True)
        if not run_status:
            logger.info(f"No runs found for assessment {assessment_id}")
            return None

        return run_status

    @staticmethod
    async def set_detection_status(
        client: AttackIQClient,
        mitigation_id: str,
        detection_status: str,
        detection_outcome: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Set detection status for the most recent assessment run of a mitigation rule."""
        run_status = await UnifiedMitigations.get_latest_assessment_run_status(client, mitigation_id)
        if not run_status:
            logger.warning(f"No assessment runs found for mitigation {mitigation_id}")
            return None

        latest_result = await UnifiedMitigations.get_latest_detection_result(client, mitigation_id)

        if latest_result and latest_result.get("project_run_id") == run_status["id"]:
            logger.info(f"Updating detection result for mitigation {mitigation_id}, run {run_status['id']}")
            endpoint = f"v1/unified_mitigation_detection_results/{latest_result['id']}"
            patch_data = {"detection_status": detection_status}
            if detection_outcome:
                patch_data["detection_outcome"] = detection_outcome
            if metadata:
                patch_data["metadata"] = metadata
            result = await client.patch_object(endpoint, patch_data)
            return UnifiedMitigations._transform_detection_result(result) if result else None

        logger.info(f"Creating detection result for mitigation {mitigation_id}, run {run_status['id']}")
        data = {
            "unified_mitigation": mitigation_id,
            "project_run_id": run_status["id"],
            "detection_status": detection_status,
        }
        if detection_outcome:
            data["detection_outcome"] = detection_outcome
        if metadata:
            data["metadata"] = metadata
        result = await client.post_object("v1/unified_mitigation_detection_results", data)
        return UnifiedMitigations._transform_detection_result(result) if result else None

    @staticmethod
    async def set_analyst_verdict(
        client: AttackIQClient,
        mitigation_id: str,
        analyst_verdict: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Set analyst verdict (human judgment) for the most recent detection result."""
        latest_result = await UnifiedMitigations.get_latest_detection_result(client, mitigation_id)

        if not latest_result:
            logger.warning(
                f"No detection results found for mitigation {mitigation_id}. "
                "Run assessment first before setting analyst verdict."
            )
            return None

        endpoint = f"v1/unified_mitigation_detection_results/{latest_result['id']}"
        data = {"detection_outcome": analyst_verdict}

        if metadata:
            existing_metadata = latest_result.get("metadata", {})
            existing_metadata.update(metadata)
            data["metadata"] = existing_metadata

        logger.info(f"Setting analyst verdict for mitigation {mitigation_id}: {analyst_verdict}")
        return await client.patch_object(endpoint, data)

    @staticmethod
    async def get_analyst_verdict(client: AttackIQClient, mitigation_id: str) -> Optional[str]:
        """Get the analyst verdict for the most recent detection result."""
        latest_result = await UnifiedMitigations.get_latest_detection_result(client, mitigation_id)

        if not latest_result:
            return None

        verdict = latest_result.get("analyst_verdict")
        if verdict:
            logger.info(f"Current analyst verdict for {mitigation_id}: {verdict}")
        return verdict

    @staticmethod
    async def mark_true_positive(client: AttackIQClient, mitigation_id: str) -> bool:
        """Mark detection as true positive - real threat correctly detected."""
        result = await UnifiedMitigations.set_analyst_verdict(
            client,
            mitigation_id,
            AnalystVerdict.TRUE_POSITIVE.value,
            metadata={"analyst": "api", "reason": "Real threat correctly detected"},
        )
        return result is not None

    @staticmethod
    async def mark_false_positive(client: AttackIQClient, mitigation_id: str) -> bool:
        """Mark detection as false positive - benign activity incorrectly flagged."""
        result = await UnifiedMitigations.set_analyst_verdict(
            client,
            mitigation_id,
            AnalystVerdict.FALSE_POSITIVE.value,
            metadata={"analyst": "api", "reason": "Benign activity incorrectly flagged"},
        )
        return result is not None

    @staticmethod
    async def mark_true_negative(client: AttackIQClient, mitigation_id: str) -> bool:
        """Mark detection as true negative - benign activity correctly ignored."""
        result = await UnifiedMitigations.set_analyst_verdict(
            client,
            mitigation_id,
            AnalystVerdict.TRUE_NEGATIVE.value,
            metadata={"analyst": "api", "reason": "Benign activity correctly ignored"},
        )
        return result is not None

    @staticmethod
    async def mark_false_negative(client: AttackIQClient, mitigation_id: str) -> bool:
        """Mark detection as false negative - real threat missed."""
        result = await UnifiedMitigations.set_analyst_verdict(
            client,
            mitigation_id,
            AnalystVerdict.FALSE_NEGATIVE.value,
            metadata={"analyst": "api", "reason": "Real threat missed"},
        )
        return result is not None


class UnifiedMitigationProjects:
    """Utilities for interacting with Unified Mitigation Project associations.

    API Endpoint: /v1/unified_mitigation_projects
    """

    ENDPOINT = "v1/unified_mitigation_projects"

    @staticmethod
    async def list_associations(
        client: AttackIQClient,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 10,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """List all unified mitigation project associations, optionally filtered and limited."""
        logger.info(f"Listing unified mitigation project associations with params: {params}")
        generator = client.get_all_objects(UnifiedMitigationProjects.ENDPOINT, params=params)
        async for association in async_islice(generator, 0, limit):
            yield association

    @staticmethod
    async def get_association(client: AttackIQClient, association_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific unified mitigation project association by its ID."""
        endpoint = f"{UnifiedMitigationProjects.ENDPOINT}/{association_id}"
        logger.info(f"Getting unified mitigation project association: {association_id}")
        return await client.get_object(endpoint)

    @staticmethod
    async def create_association(client: AttackIQClient, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new unified mitigation project association."""
        logger.info(f"Creating unified mitigation project association with data: {data}")
        return await client.post_object(UnifiedMitigationProjects.ENDPOINT, data=data)

    @staticmethod
    async def partial_update_association(
        client: AttackIQClient, association_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Partially update an existing unified mitigation project association (PATCH)."""
        endpoint = f"{UnifiedMitigationProjects.ENDPOINT}/{association_id}"
        logger.info(f"Partially updating unified mitigation project association {association_id} with data: {data}")
        url = client._build_url(endpoint)
        return await client._make_request(url, method="patch", json=data)

    @staticmethod
    async def delete_association(client: AttackIQClient, association_id: str) -> bool:
        """Delete a unified mitigation project association."""
        endpoint = f"{UnifiedMitigationProjects.ENDPOINT}/{association_id}"
        logger.info(f"Deleting unified mitigation project association: {association_id}")
        response = await client.delete_object(endpoint)
        return response is not None and response.get("status_code") == HTTPStatus.NO_CONTENT


class UnifiedMitigationWithRelations:
    """Utilities for read-only access to Unified Mitigations with related data.

    API Endpoint: /v1/unified_mitigations_with_relations
    """

    ENDPOINT = "v1/unified_mitigations_with_relations"

    @staticmethod
    async def list_mitigations_with_relations(
        client: AttackIQClient,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 10,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """List all unified mitigations with relations, optionally filtered and limited."""
        logger.info(f"Listing unified mitigations with relations, params: {params}")
        generator = client.get_all_objects(UnifiedMitigationWithRelations.ENDPOINT, params=params)
        async for mitigation in async_islice(generator, 0, limit):
            yield mitigation

    @staticmethod
    async def get_mitigation_with_relations(client: AttackIQClient, mitigation_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific unified mitigation with relations by its ID."""
        endpoint = f"{UnifiedMitigationWithRelations.ENDPOINT}/{mitigation_id}"
        logger.info(f"Getting unified mitigation with relations: {mitigation_id}")
        return await client.get_object(endpoint)

    @staticmethod
    async def get_overview(client: AttackIQClient, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Get the overview data for unified mitigations with relations."""
        endpoint = f"{UnifiedMitigationWithRelations.ENDPOINT}/overview"
        logger.info(f"Getting unified mitigation overview with params: {params}")
        return await client.get_object(endpoint, params=params)

    @staticmethod
    async def get_integration_options(client: AttackIQClient) -> Optional[Dict[str, Any]]:
        """Fetch integration filter options (integration_types, integration_names) for unified mitigations."""
        endpoint = f"{UnifiedMitigationWithRelations.ENDPOINT}/integration_options"
        logger.info("Getting unified mitigation integration options")
        return await client.get_object(endpoint)


class UnifiedMitigationReporting:
    """Utilities for Unified Mitigation reporting endpoints.

    API Endpoint: /v3/reporting/unified_mitigation_detection_performance_timeline
    """

    ENDPOINT = "v3/reporting/unified_mitigation_detection_performance_timeline"

    @staticmethod
    async def get_detection_performance_timeline(
        client: AttackIQClient, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get detection performance timeline data, optionally filtering."""
        logger.info(f"Getting detection performance timeline with params: {params}")
        return await client.get_object(UnifiedMitigationReporting.ENDPOINT, params=params)
