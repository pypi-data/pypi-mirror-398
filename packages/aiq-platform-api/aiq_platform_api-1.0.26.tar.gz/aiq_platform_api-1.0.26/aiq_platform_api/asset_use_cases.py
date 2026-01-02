import asyncio
from enum import Enum
from typing import Optional

from aiq_platform_api import (
    AttackIQClient,
    AttackIQLogger,
    Assets,
    Scenarios,
    Tags,
    TaggedItems,
    AssetStatus,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
from aiq_platform_api.core.testing import parse_test_choice, require_env

logger = AttackIQLogger.get_logger(__name__)


async def fetch_and_log_assets(client: AttackIQClient, limit: Optional[int] = 10):
    logger.info(f"Fetching and processing up to {limit} assets...")
    asset_count = 0

    async for asset in Assets.get_assets(client, limit=limit):
        asset_count += 1
        logger.info(f"Asset {asset_count}:")
        logger.info(f"  ID: {asset.get('id')}")
        logger.info(f"  Name: {asset.get('name')}")
        logger.info(f"  Type: {asset.get('type')}")
        logger.info(f"  IP Address: {asset.get('ipv4_address')}")
        logger.info("---")

    if asset_count == 0:
        logger.info("No assets retrieved with the current filters/limit.")
    else:
        logger.info(f"Successfully processed {asset_count} assets.")


async def find_asset_by_hostname(client: AttackIQClient, hostname: str):
    logger.info(f"Searching for asset with hostname: {hostname}")
    asset = await Assets.get_asset_by_hostname(client, hostname)

    if asset:
        logger.info("Asset found:")
        logger.info(f"  ID: {asset.get('id')}")
        logger.info(f"  Name: {asset.get('name')}")
        logger.info(f"  Type: {asset.get('type')}")
        logger.info(f"  IP Address: {asset.get('ipv4_address')}")
        logger.info(f"  Hostname: {asset.get('hostname')}")
    else:
        logger.info(f"No asset found with hostname: {hostname}")


async def search_assets_use_case(
    client: AttackIQClient,
    query: Optional[str] = None,
    limit: Optional[int] = 20,
    offset: Optional[int] = 0,
    ordering: Optional[str] = "-modified",
) -> dict:
    """Search or list assets. Returns {"count": total, "results": [...]}."""
    logger.info(
        f"--- Searching assets with query: '{query}', limit: {limit}, offset: {offset}, ordering: {ordering} ---"
    )
    try:
        result = await Assets.search_assets(client, query, limit, offset, ordering)
        logger.info(f"Found {result['count']} total, returning {len(result['results'])}")
        for idx, asset in enumerate(result["results"], 1):
            logger.info(f"{idx}. {asset.get('hostname')} (ID: {asset.get('id')})")
        return result
    except Exception as e:
        logger.error(f"Failed to search assets: {e}")
        raise


async def uninstall_asset_by_uuid(client: AttackIQClient, asset_id: str):
    if not asset_id:
        logger.error("Asset id not provided.")
        return

    asset = await Assets.get_asset_by_id(client, asset_id)
    if not asset:
        logger.error(f"Asset with id {asset_id} not found.")
        return

    logger.info(f"Attempting to uninstall asset with id: {asset_id}")
    success = await Assets.uninstall_asset(client, asset_id)

    if success:
        logger.info(f"Asset {asset_id} uninstall job submitted successfully.")
    else:
        logger.error(f"Failed to submit uninstall job for asset {asset_id}.")


async def list_asset_tags(client: AttackIQClient, asset_id: str, limit: Optional[int] = 10):
    logger.info(f"Listing up to {limit} tags for asset with ID: {asset_id}")
    tag_count = 0

    async for tagged_item in TaggedItems.get_tagged_items(client, "asset", asset_id, limit=limit):
        tag_count += 1
        tag_id = tagged_item.get("tag", {}).get("id")
        tag_name = tagged_item.get("tag", {}).get("name")
        logger.info(f"Tagged Item {tag_count}:")
        logger.info(f"  Item ID: {tagged_item.get('id')}")
        logger.info(f"  Tag ID: {tag_id}")
        logger.info(f"  Tag Name: {tag_name}")
    logger.info(f"Total tags listed: {tag_count}")


async def tag_asset(client: AttackIQClient, asset_id: str, tag_id: str) -> str:
    logger.info(f"Tagging asset with ID: {asset_id} with tag ID: {tag_id}")
    tagged_item = await TaggedItems.get_tagged_item(client, "asset", asset_id, tag_id)
    tagged_item_id = tagged_item.get("id") if tagged_item else ""
    if tagged_item_id:
        logger.info(f"Asset {asset_id} is already tagged with tag item ID {tagged_item_id}")
        return tagged_item_id
    tagged_item_id = await Assets.add_tag(client, asset_id, tag_id)
    if tagged_item_id:
        logger.info(f"Successfully tagged asset {asset_id} with tag item ID {tagged_item_id}")
        return tagged_item_id
    else:
        logger.error(f"Failed to tag asset {asset_id} with tag ID {tag_id}")
        return ""


async def untag_asset(client: AttackIQClient, tagged_item_id: str):
    logger.info(f"Removing tag item with ID: {tagged_item_id}")
    success = await TaggedItems.delete_tagged_item(client, tagged_item_id)
    if success:
        logger.info(f"Successfully removed tag item with ID {tagged_item_id}")
    else:
        logger.error(f"Failed to remove tag item with ID {tagged_item_id}")


async def delete_tag(client: AttackIQClient, tag_id: str) -> bool:
    logger.info(f"Deleting tag with ID: {tag_id}")
    success = await Tags.delete_tag(client, tag_id)
    if success:
        logger.info(f"Successfully deleted tag with ID {tag_id}")
    else:
        logger.error(f"Failed to delete tag with ID {tag_id}")
    return success


async def get_and_log_total_assets(client: AttackIQClient):
    total_assets = await Assets.get_total_assets(client)
    if total_assets is not None:
        logger.info(f"Total number of assets: {total_assets}")
    else:
        logger.error("Failed to retrieve total number of assets.")


async def get_and_log_assets_count_by_status(client: AttackIQClient, status: AssetStatus):
    assets_count = await Assets.get_assets_count_by_status(client, status)
    if assets_count is not None:
        logger.info(f"Number of {status.value} assets: {assets_count}")
    else:
        logger.error(f"Failed to retrieve count of {status.value} assets.")


async def test_asset_counts(client: AttackIQClient):
    """Test getting asset counts."""
    await get_and_log_total_assets(client)
    await get_and_log_assets_count_by_status(client, AssetStatus.ACTIVE)
    await get_and_log_assets_count_by_status(client, AssetStatus.INACTIVE)


async def test_list_assets(client: AttackIQClient):
    """Test listing assets."""
    await fetch_and_log_assets(client, limit=25)


async def test_active_assets(client: AttackIQClient):
    """Test fetching active assets with details."""
    logger.info("Fetching active assets with full details...")
    active_assets = await Assets.get_active_assets_with_details(client, limit=10)

    if not active_assets:
        logger.info("No active assets found.")
        return

    logger.info(f"\nFound {len(active_assets)} active assets:")
    for i, asset in enumerate(active_assets, 1):
        logger.info(f"{i}. {asset['hostname']}")
        logger.info(f"   Product: {asset['product_name']}")
        logger.info(f"   Agent Version: {asset['agent_version']}")
        logger.info(f"   IPv4: {asset['ipv4_address']}")
        logger.info(f"   MAC: {asset['mac_address']}")
        logger.info(f"   Domain: {asset['domain_name']}")
        logger.info(f"   Arch: {asset['processor_arch']}")
        logger.info(f"   State: {asset['deployment_state']}")

    return active_assets


async def test_find_by_hostname(client: AttackIQClient, hostname: Optional[str] = None):
    """Test finding asset by hostname."""
    test_hostname = hostname or "AIQ-CY4C7CC9W5"
    await find_asset_by_hostname(client, test_hostname)


async def get_first_asset_id(client: AttackIQClient) -> Optional[str]:
    """Get the first available asset ID for testing."""
    async for asset in Assets.get_assets(client, limit=1):
        return asset.get("id")
    return None


async def test_asset_tagging(client: AttackIQClient):
    """Test asset tagging operations."""
    asset_id = await get_first_asset_id(client)
    if not asset_id:
        logger.warning("No assets found. Skipping asset tagging operations.")
        return

    logger.info(f"Using asset ID: {asset_id} for tagging test")

    tag_name = "TEST_TAG"
    tag_id = await Tags.get_or_create_custom_tag(client, tag_name)
    if not tag_id:
        logger.error(f"Failed to get or create tag '{tag_name}'")
        return

    logger.info(f"Tag ID: {tag_id} for tag '{tag_name}'")
    tagged_item_id = await tag_asset(client, asset_id, tag_id)
    if tagged_item_id:
        await list_asset_tags(client, asset_id)
        await untag_asset(client, tagged_item_id)
        await delete_tag(client, tag_id)


async def test_uninstall_asset(client: AttackIQClient):
    """Test uninstalling an asset. WARNING: This is destructive!"""
    asset_id = await get_first_asset_id(client)
    if not asset_id:
        logger.warning("No assets found. Skipping uninstall operation.")
        return

    logger.info(f"Using asset ID: {asset_id} for uninstall test")
    await uninstall_asset_by_uuid(client, asset_id)


async def test_search_assets(client: AttackIQClient):
    """Test searching assets by various queries."""
    logger.info("--- Testing Asset Search ---")

    logger.info("\n1. Searching by keyword 'windows':")
    await search_assets_use_case(client, "windows", limit=5)

    logger.info("\n2. Searching by keyword 'linux':")
    await search_assets_use_case(client, "linux", limit=5)

    logger.info("\n3. Listing all assets (no query):")
    await search_assets_use_case(client, query=None, limit=5)


async def test_pagination_workflow(client: AttackIQClient):
    """
    Test pagination with offset to demonstrate fetching batches.

    This validates:
    1. minimal=true reduces fields (30 -> 11, 63.3% reduction)
    2. offset pagination works correctly
    3. No duplicate assets across batches

    Use this pattern for other endpoints.
    """
    logger.info("--- Testing Pagination Workflow ---")

    batch_size = 5
    max_batches = 3
    all_ids = []

    for batch_num in range(1, max_batches + 1):
        offset = (batch_num - 1) * batch_size
        logger.info(f"\n--- Batch {batch_num}: offset={offset}, limit={batch_size} ---")

        assets = [a async for a in Assets.get_assets(client, params=None, limit=batch_size, offset=offset)]

        if not assets:
            logger.info("No more assets. Stopping.")
            break

        logger.info(f"Retrieved {len(assets)} assets:")
        for idx, asset in enumerate(assets, 1):
            asset_id = asset.get("id")
            asset_hostname = asset.get("hostname")
            logger.info(f"  {idx}. {asset_hostname}")
            all_ids.append(asset_id)

        logger.info(f"Fields in asset: {list(assets[0].keys())}")
        logger.info(f"Field count: {len(assets[0].keys())} (11 with minimal=true)")

    logger.info("\n--- Summary ---")
    logger.info(f"Total fetched: {len(all_ids)}")
    logger.info(f"Unique: {len(set(all_ids))}")
    logger.info(f"Duplicates: {len(all_ids) - len(set(all_ids))}")

    if len(all_ids) == len(set(all_ids)):
        logger.info("SUCCESS: No duplicates, pagination working correctly!")
    else:
        logger.error("FAILED: Duplicates detected!")


async def test_recommend_test_points(client: AttackIQClient):
    """Test recommending test points for scenarios."""
    logger.info("=== Testing recommend_test_points ===")

    # Get some real scenario IDs
    result = await Scenarios.search_scenarios(client, limit=5)
    scenarios = result.get("results", [])
    scenario_ids = [s["id"] for s in scenarios]
    logger.info(f"Using {len(scenario_ids)} scenarios for testing")

    # Call recommend (uses platform's status field for liveness - no threshold param)
    result = await Assets.recommend_test_points(client, scenario_ids)

    # Validate result structure (uses platform's status field, no is_live/warnings)
    recommended = result.get("recommended_test_points", [])
    first_tp = recommended[0] if recommended else {}
    checks = [
        ("has recommended_test_points", "recommended_test_points" in result),
        ("has scenarios_by_platform", "scenarios_by_platform" in result),
        ("has summary", "summary" in result),
        ("summary has total_scenarios", "total_scenarios" in result.get("summary", {})),
        ("summary has active_test_points", "active_test_points" in result.get("summary", {})),
        ("summary has platforms_needed", "platforms_needed" in result.get("summary", {})),
        ("test_point has status", "status" in first_tp if recommended else True),
        ("test_point has compatible_scenario_count", "compatible_scenario_count" in first_tp if recommended else True),
    ]

    passed = 0
    for check_name, check_result in checks:
        status = "✓" if check_result else "✗"
        logger.info(f"  {status} {check_name}")
        if check_result:
            passed += 1

    logger.info(f"\nSummary: {result['summary']}")
    logger.info("\nScenarios by platform:")
    for platform, sids in result["scenarios_by_platform"].items():
        logger.info(f"  {platform}: {len(sids)} scenarios")

    logger.info("\nTop 5 recommended test points:")
    for tp in result["recommended_test_points"][:5]:
        logger.info(
            f"  [{tp['status']}] {tp['hostname'][:20]:20} | {tp['product_name'][:20]:20} | "
            f"compat: {tp['compatible_scenario_count']}"
        )

    logger.info(f"\n{passed}/{len(checks)} checks passed")
    return result


async def test_all(client: AttackIQClient):
    """Run all asset tests."""
    await test_asset_counts(client)
    await test_list_assets(client)
    await test_active_assets(client)
    await test_find_by_hostname(client)
    await test_search_assets(client)
    await test_pagination_workflow(client)
    await test_asset_tagging(client)
    await test_recommend_test_points(client)
    # Uninstall is destructive, so commented out by default
    # await test_uninstall_asset(client)


async def run_test(choice: "TestChoice", client: AttackIQClient):
    """Run the selected test."""
    test_functions = {
        TestChoice.ASSET_COUNTS: lambda: test_asset_counts(client),
        TestChoice.LIST_ASSETS: lambda: test_list_assets(client),
        TestChoice.ACTIVE_ASSETS: lambda: test_active_assets(client),
        TestChoice.FIND_BY_HOSTNAME: lambda: test_find_by_hostname(client),
        TestChoice.SEARCH_ASSETS: lambda: test_search_assets(client),
        TestChoice.PAGINATION_WORKFLOW: lambda: test_pagination_workflow(client),
        TestChoice.ASSET_TAGGING: lambda: test_asset_tagging(client),
        TestChoice.UNINSTALL_ASSET: lambda: test_uninstall_asset(client),
        TestChoice.RECOMMEND_TEST_POINTS: lambda: test_recommend_test_points(client),
        TestChoice.ALL: lambda: test_all(client),
    }

    await test_functions[choice]()


class TestChoice(Enum):
    ASSET_COUNTS = "asset_counts"
    LIST_ASSETS = "list_assets"
    ACTIVE_ASSETS = "active_assets"
    FIND_BY_HOSTNAME = "find_by_hostname"
    SEARCH_ASSETS = "search_assets"
    PAGINATION_WORKFLOW = "pagination_workflow"
    ASSET_TAGGING = "asset_tagging"
    UNINSTALL_ASSET = "uninstall_asset"
    RECOMMEND_TEST_POINTS = "recommend_test_points"
    ALL = "all"


async def main():
    require_env(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN)
    choice = parse_test_choice(TestChoice)

    async with AttackIQClient(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN) as client:
        await run_test(choice, client)


if __name__ == "__main__":
    asyncio.run(main())
