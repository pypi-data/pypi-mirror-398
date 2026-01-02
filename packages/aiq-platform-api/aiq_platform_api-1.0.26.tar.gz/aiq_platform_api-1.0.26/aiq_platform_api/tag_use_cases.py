import asyncio
from enum import Enum
from typing import Optional

from aiq_platform_api import (
    AttackIQClient,
    AttackIQLogger,
    Tags,
    TagSets,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
from aiq_platform_api.core.testing import parse_test_choice, require_env

logger = AttackIQLogger.get_logger(__name__)


async def list_tags(client: AttackIQClient, limit: Optional[int] = 10) -> int:
    logger.info(f"Listing up to {limit} tags...")
    tag_count = 0

    async for tag in Tags.get_tags(client, limit=limit):
        tag_count += 1
        logger.info(f"Tag {tag_count}:")
        logger.info(f"  ID: {tag.get('id', 'N/A')}")
        logger.info(f"  Name: {tag.get('name', 'N/A')}")
        logger.info(f"  Display Name: {tag.get('display_name', 'N/A')}")
        logger.info(f"  Tag Set ID: {tag.get('tag_set_id', 'N/A')}")
        logger.info("---")

    logger.info(f"Total tags listed: {tag_count}")
    return tag_count


async def add_custom_tag(client: AttackIQClient, tag_name: str) -> Optional[str]:
    logger.info(f"Adding new tag: {tag_name} to Custom tag set")
    try:
        tag_set_id = await TagSets.get_tag_set_id(client, "Custom")
        if not tag_set_id:
            logger.error("TagSet 'Custom' not found. Cannot add tag.")
            return None
        tag_id = await Tags.get_tag_id(client, tag_name, tag_set_id)
        if tag_id:
            logger.info(f"Tag already exists with ID: {tag_id}")
            return tag_id
        tag = await Tags.create_tag(client, tag_name, tag_set_id)
        logger.info(f"New tag added: {tag}")
        return tag["id"]
    except Exception as e:
        logger.error(f"Failed to add tag: {str(e)}")
        return None


async def remove_tag(client: AttackIQClient, tag_id: str) -> bool:
    logger.info(f"Removing tag with ID: {tag_id}")
    try:
        result = await Tags.delete_tag(client, tag_id)
        if result:
            logger.info(f"Tag {tag_id} removed successfully")
            return True
        else:
            logger.error(f"Failed to remove tag {tag_id}")
            return False
    except Exception as e:
        logger.error(f"Error while removing tag {tag_id}: {str(e)}")
        return False


async def test_list_tags(client: AttackIQClient):
    """Test listing tags."""
    await list_tags(client, limit=5)


async def test_tag_lifecycle(client: AttackIQClient):
    """Test creating and removing a tag."""
    new_tag_id = await add_custom_tag(client, "NEW_TEST_TAG1")
    if new_tag_id:
        await remove_tag(client, new_tag_id)


async def test_all(client: AttackIQClient):
    """Run all tag tests."""
    for choice in TestChoice:
        if choice != TestChoice.ALL:
            await run_test(choice, client)


async def run_test(choice: "TestChoice", client: AttackIQClient):
    """Run the selected test."""
    test_functions = {
        TestChoice.LIST_TAGS: lambda: test_list_tags(client),
        TestChoice.TAG_LIFECYCLE: lambda: test_tag_lifecycle(client),
        TestChoice.ALL: lambda: test_all(client),
    }

    await test_functions[choice]()


class TestChoice(Enum):
    LIST_TAGS = "list_tags"
    TAG_LIFECYCLE = "tag_lifecycle"
    ALL = "all"


async def main():
    require_env(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN)
    choice = parse_test_choice(TestChoice)

    async with AttackIQClient(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN) as client:
        await run_test(choice, client)


if __name__ == "__main__":
    asyncio.run(main())
