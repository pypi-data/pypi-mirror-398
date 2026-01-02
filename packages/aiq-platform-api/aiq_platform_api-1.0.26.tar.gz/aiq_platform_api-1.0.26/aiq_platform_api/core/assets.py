from typing import Optional, Dict, Any, AsyncGenerator, List

from aiq_platform_api.core.async_utils import async_islice
from aiq_platform_api.core.client import AttackIQClient
from aiq_platform_api.core.constants import AssetStatus
from aiq_platform_api.core.logger import AttackIQLogger
from aiq_platform_api.core.tags import TaggedItems

logger = AttackIQLogger.get_logger(__name__)

# Max test points to consider for recommendation (prevents unbounded queries)
MAX_TEST_POINTS_FOR_RECOMMENDATION = 25


def normalize_platform(platform: str) -> str:
    """Normalize platform names for matching.

    Scenarios report specific distros (ubuntu, centos, redhat, amazon, debian).
    Test points have generic tags (linux, windows, osx).
    This function normalizes both to common keys for matching.
    """
    p = platform.lower().strip()
    if p in ("macos", "darwin"):
        return "osx"
    if p in ("win", "win32", "win64"):
        return "windows"
    if p in ("ubuntu", "centos", "debian", "redhat", "amazon", "rhel", "fedora", "suse", "oracle"):
        return "linux"
    return p


def get_asset_platforms(asset: dict) -> set:
    """Extract platform from asset tags, with product_name fallback.

    Priority:
    1. Tags: Platform adds 'windows', 'linux', 'osx' tags automatically
    2. Fallback: Parse product_name (e.g., "Microsoft Windows 11 Pro" → windows)
    """
    platforms = set()

    # Try tags first (preferred - explicitly set by platform)
    for tag in asset.get("tags", []):
        name = tag.get("name", "").lower()
        if name in ("windows", "linux", "osx", "macos"):
            platforms.add(normalize_platform(name))

    # Fallback: parse product_name if no platform tags found
    if not platforms:
        product_name = asset.get("product_name", "").lower()
        if "windows" in product_name:
            platforms.add("windows")
        elif "mac" in product_name or "darwin" in product_name or "osx" in product_name:
            platforms.add("osx")
        elif any(
            d in product_name for d in ("linux", "ubuntu", "centos", "debian", "redhat", "rhel", "fedora", "amazon")
        ):
            platforms.add("linux")

    return platforms


class Assets:
    """Utilities for working with assets a.k.a Test Points

    API Endpoint: /v1/assets, /v1/asset_jobs
    """

    ENDPOINT = "v1/assets"
    ASSET_JOBS_ENDPOINT = "v1/asset_jobs"
    JOB_NAME_DESTROY_SELF = "06230502-890c-4dca-aab1-296706758fd9"

    @staticmethod
    async def get_assets(
        client: AttackIQClient,
        params: dict = None,
        limit: Optional[int] = 10,
        offset: Optional[int] = 0,
        ordering: Optional[str] = "-modified",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """List assets with minimal fields (63.3% reduction: 30 -> 11 fields), ordering, and offset support.

        Args:
            ordering: Sort order (default: -modified for most recent first)
                     Use '-' prefix for descending (e.g., '-modified', '-created')
                     Omit '-' for ascending (e.g., 'modified', 'created', 'hostname')
        """
        request_params = params.copy() if params else {}
        request_params["minimal"] = "true"
        if "ordering" not in request_params and ordering:
            request_params["ordering"] = ordering
        logger.info(f"Listing assets with params: {request_params}, limit: {limit}, offset: {offset}")
        generator = client.get_all_objects(Assets.ENDPOINT, params=request_params)
        stop = offset + limit if limit is not None else None
        async for asset in async_islice(generator, offset, stop):
            yield asset

    @staticmethod
    async def get_asset_by_id(client: AttackIQClient, asset_id: str):
        """Get a specific asset by its ID."""
        return await client.get_object(f"{Assets.ENDPOINT}/{asset_id}")

    @staticmethod
    async def get_asset_by_hostname(client: AttackIQClient, hostname: str) -> Optional[Dict[str, Any]]:
        """Get a specific asset by its hostname."""
        params = {"hostname": hostname}
        assets = [asset async for asset in client.get_all_objects(Assets.ENDPOINT, params=params)]
        return assets[0] if assets else None

    @staticmethod
    async def search_assets(
        client: AttackIQClient,
        query: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        ordering: Optional[str] = "-modified",
    ) -> dict:
        """Search or list assets.
        - With query: Search by keyword
        - Without query: List all assets (paginated)
        Returns {"count": total, "results": [...]}

        Args:
            status: Filter by status ('Active', 'Inactive')
            ordering: Sort order (default: -modified for most recent first)
                     Use '-' prefix for descending (e.g., '-modified', '-created')
                     Omit '-' for ascending (e.g., 'modified', 'created', 'hostname')
        """
        logger.info(f"Searching assets with query: '{query}', status: {status}, limit: {limit}, offset: {offset}")
        params = {"minimal": "true", "limit": limit, "offset": offset}
        if query:
            params["search"] = query
        if status:
            params["status"] = status
        if "ordering" not in params and ordering:
            params["ordering"] = ordering
        url = client._build_url(Assets.ENDPOINT, params)
        data = await client._make_request(url, method="get", json=None)
        total_count = data.get("count", 0)
        results = data.get("results", [])
        logger.info(f"Found {total_count} total assets matching '{query}', returning {len(results)}")
        return {"count": total_count, "results": results}

    @staticmethod
    async def uninstall_asset(client: AttackIQClient, asset_id: str) -> bool:
        """Submit a job to uninstall an asset."""
        logger.info(f"Uninstalling asset with ID: {asset_id}")
        payload = {
            "asset": asset_id,
            "job_name": Assets.JOB_NAME_DESTROY_SELF,
            "one_way": True,
        }
        try:
            response = await client.post_object(Assets.ASSET_JOBS_ENDPOINT, data=payload)
            if response:
                logger.info(f"Asset {asset_id} uninstall job submitted successfully")
                return True
            logger.error(f"Failed to submit uninstall job for asset {asset_id}")
            return False
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error while uninstalling asset {asset_id}: {str(e)}")
            return False

    @staticmethod
    async def add_tag(client: AttackIQClient, asset_id: str, tag_id: str) -> str:
        """Add a tag to an asset."""
        return await TaggedItems.create_tagged_item(client, "asset", asset_id, tag_id)

    @staticmethod
    async def get_total_assets(client: AttackIQClient) -> Optional[int]:
        """Get the total number of assets."""
        logger.info("Fetching total number of assets...")
        return await client.get_total_objects_count(Assets.ENDPOINT)

    @staticmethod
    async def get_assets_count_by_status(client: AttackIQClient, status: AssetStatus) -> Optional[int]:
        """Get the count of assets with a specific status."""
        logger.info(f"Fetching count of assets with status: {status.value}...")
        params = {"status": status.value}
        return await client.get_total_objects_count(Assets.ENDPOINT, params=params)

    @staticmethod
    async def get_active_assets_with_details(
        client: AttackIQClient, limit: Optional[int] = 10, offset: Optional[int] = 0
    ) -> list:
        """Get active assets with OS and agent details with pagination support."""
        params = {"status": AssetStatus.ACTIVE.value}
        assets = []

        async for asset in Assets.get_assets(client, params=params, limit=limit, offset=offset):
            assets.append(
                {
                    "id": asset.get("id"),
                    "hostname": asset.get("hostname"),
                    "product_name": asset.get("product_name", "unknown"),
                    "agent_version": asset.get("agent_version", "unknown"),
                    "ipv4_address": asset.get("ipv4_address"),
                    "ipv6_address": asset.get("ipv6_address"),
                    "mac_address": asset.get("mac_address"),
                    "domain_name": asset.get("domain_name"),
                    "processor_arch": asset.get("processor_arch"),
                    "status": asset.get("status"),
                    "deployment_state": asset.get("deployment_state"),
                    "modified": asset.get("modified"),
                }
            )

        logger.info(f"Retrieved {len(assets)} active assets")
        return assets

    @staticmethod
    async def recommend_test_points(
        client: AttackIQClient,
        scenario_ids: List[str],
    ) -> Dict[str, Any]:
        """Recommend test points for a set of scenarios.

        Finds Active test points compatible with scenario platform requirements.
        Uses platform's `status` field for liveness (computed server-side).

        Args:
            client: AttackIQ client
            scenario_ids: List of scenario UUIDs to run

        Returns:
            {
                "recommended_test_points": [...],
                "scenarios_by_platform": {...},
                "summary": {...}
            }
        """
        # Import here to avoid circular import
        from aiq_platform_api.core.scenarios import Scenarios

        logger.info(f"Recommending test points for {len(scenario_ids)} scenarios")

        # Step 1: Analyze scenario requirements
        scenario_analysis = await Scenarios.analyze_scenario_requirements(client, scenario_ids)
        by_platform = scenario_analysis.get("by_platform", {})

        # Build scenarios_by_platform output (normalize keys)
        scenarios_by_platform = Assets._build_scenarios_by_platform(by_platform)

        # Step 2: Fetch Active test points using server-side filtering
        result = await Assets.search_assets(client, status="Active", limit=MAX_TEST_POINTS_FOR_RECOMMENDATION)
        active_assets = result.get("results", [])

        # Step 3: Evaluate compatibility
        recommended: List[Dict[str, Any]] = []
        all_scenario_ids = set(scenario_ids)

        for asset in active_assets:
            tp = Assets._evaluate_test_point(asset, scenarios_by_platform, all_scenario_ids)
            recommended.append(tp)

        # Step 4: Sort by compatible_scenario_count desc
        recommended.sort(key=lambda x: -x["compatible_scenario_count"])

        summary = {
            "total_scenarios": len(scenario_ids),
            "active_test_points": len(active_assets),
            "platforms_needed": list(scenarios_by_platform.keys()),
        }

        logger.info(f"Recommended {len(recommended)} active test points")

        return {
            "recommended_test_points": recommended,
            "scenarios_by_platform": scenarios_by_platform,
            "summary": summary,
        }

    @staticmethod
    def _build_scenarios_by_platform(by_platform: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Normalize platform keys and identify multi-platform scenarios.

        Uses sets internally to prevent duplicate counting when multiple distros
        (e.g., ubuntu, centos, redhat) normalize to the same platform (linux).
        """
        # Use sets to deduplicate scenarios per platform
        scenarios_by_platform_sets: Dict[str, set] = {}
        for platform, sids in by_platform.items():
            norm_platform = normalize_platform(platform)
            scenarios_by_platform_sets.setdefault(norm_platform, set()).update(sids)

        # Find multi-platform scenarios (appear in multiple normalized platform sets)
        scenario_platform_count: Dict[str, int] = {}
        for sids in scenarios_by_platform_sets.values():
            for sid in sids:
                scenario_platform_count[sid] = scenario_platform_count.get(sid, 0) + 1

        # Convert sets to lists for output, add multi_platform list
        scenarios_by_platform: Dict[str, List[str]] = {k: list(v) for k, v in scenarios_by_platform_sets.items()}
        scenarios_by_platform["multi_platform"] = [sid for sid, count in scenario_platform_count.items() if count > 1]
        return scenarios_by_platform

    @staticmethod
    def _evaluate_test_point(
        asset: Dict[str, Any],
        scenarios_by_platform: Dict[str, List[str]],
        all_scenario_ids: set,
    ) -> Dict[str, Any]:
        """Evaluate a single test point for platform compatibility.

        Uses a set to deduplicate scenarios that appear in multiple platform buckets,
        preventing double-counting for multi-platform scenarios on multi-platform assets.
        """
        asset_platforms = get_asset_platforms(asset)
        compatible_scenarios: set = set()
        for platform, sids in scenarios_by_platform.items():
            if platform == "multi_platform":
                continue
            # "universal" scenarios (empty supported_platforms) are compatible with ALL test points
            if platform == "universal" or platform in asset_platforms:
                compatible_scenarios.update(s for s in sids if s in all_scenario_ids)

        return {
            "id": asset.get("id", ""),
            "hostname": asset.get("hostname", ""),
            "product_name": asset.get("product_name", ""),
            "status": asset.get("status", ""),
            "modified": asset.get("modified", ""),
            "platforms": list(asset_platforms),
            "compatible_scenario_count": len(compatible_scenarios),
        }
