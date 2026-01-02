"""
Basic example demonstrating how to use the AttackIQ Platform API utilities.

To use this example:
1. Copy this file to your project
2. Create a .env file with your credentials (see below)
3. Create and source a virtual environment: virtualenv venv && source venv/bin/activate
4. Install required packages: pip install --upgrade aiq-platform-api python-dotenv
5. Run: python basic_usage.py
"""

import asyncio
import os

from dotenv import load_dotenv

from aiq_platform_api import (
    AttackIQClient,
    Assets,
    Tags,
    AttackIQLogger,
    AssetStatus,
)

logger = AttackIQLogger.get_logger(__name__)


async def demonstrate_asset_operations(client: AttackIQClient):
    """Demonstrate basic asset operations."""
    total_assets = await Assets.get_total_assets(client)
    logger.info(f"Total assets: {total_assets}")

    active_assets = await Assets.get_assets_count_by_status(client, AssetStatus.ACTIVE)
    logger.info(f"Active assets: {active_assets}")

    logger.info("Listing first 5 assets:")
    count = 0
    async for asset in Assets.get_assets(client, limit=5):
        count += 1
        logger.info(f"Asset {count}:")
        logger.info(f"  ID: {asset.get('id')}")
        logger.info(f"  Name: {asset.get('name')}")
        logger.info(f"  Type: {asset.get('type')}")
        logger.info("---")


async def demonstrate_tag_operations(client: AttackIQClient):
    """Demonstrate basic tag operations."""
    tag_name = "EXAMPLE_TAG"
    tag_id = await Tags.get_or_create_custom_tag(client, tag_name)
    if tag_id:
        logger.info(f"Created/Found tag '{tag_name}' with ID: {tag_id}")

        if await Tags.delete_tag(client, tag_id):
            logger.info(f"Successfully deleted tag '{tag_name}'")


async def main():
    load_dotenv()

    platform_url = os.getenv("ATTACKIQ_PLATFORM_URL")
    api_token = os.getenv("ATTACKIQ_PLATFORM_API_TOKEN")

    if not platform_url or not api_token:
        logger.error("Missing required environment variables")
        return

    try:
        async with AttackIQClient(platform_url, api_token) as client:
            await demonstrate_asset_operations(client)
            await demonstrate_tag_operations(client)

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
