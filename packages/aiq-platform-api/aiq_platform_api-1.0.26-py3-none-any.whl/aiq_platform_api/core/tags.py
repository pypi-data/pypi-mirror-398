from typing import Optional, Dict, Any, AsyncGenerator

from aiq_platform_api.core.async_utils import async_islice
from aiq_platform_api.core.client import AttackIQClient
from aiq_platform_api.core.logger import AttackIQLogger

logger = AttackIQLogger.get_logger(__name__)


class TagSets:
    """Utilities for working with tag sets.

    API Endpoint: /v1/tag_sets
    """

    ENDPOINT = "v1/tag_sets"

    @staticmethod
    async def get_tag_set_id(client: AttackIQClient, tag_set_name: str) -> Optional[str]:
        """Get the ID of a tag set by its name."""
        logger.info(f"Searching for TagSet: '{tag_set_name}'")
        params = {"name": tag_set_name}
        tag_sets = [tag async for tag in client.get_all_objects(TagSets.ENDPOINT, params=params)]
        if tag_sets:
            tag_set = tag_sets[0]
            logger.info(f"TagSet '{tag_set_name}' found with ID '{tag_set['id']}'")
            return tag_set["id"]
        logger.warning(f"TagSet '{tag_set_name}' not found")
        return None

    @staticmethod
    async def get_custom_tag_set_id(client: AttackIQClient) -> Optional[str]:
        """Get the ID of the 'Custom' tag set."""
        return await TagSets.get_tag_set_id(client, "Custom")


class Tags:
    """Utilities for managing tags in the AttackIQ platform.

    API Endpoint: /v1/tags
    """

    ENDPOINT = "v1/tags"

    @staticmethod
    async def get_tags(
        client: AttackIQClient, params: dict = None, limit: Optional[int] = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """List tags, optionally filtered and limited."""
        generator = client.get_all_objects(Tags.ENDPOINT, params=params)
        async for tag in async_islice(generator, 0, limit):
            yield tag

    @staticmethod
    async def get_tag_by_id(client: AttackIQClient, tag_id: str):
        """Get a specific tag by its ID."""
        return await client.get_object(f"{Tags.ENDPOINT}/{tag_id}")

    @staticmethod
    async def create_tag(client: AttackIQClient, tag_name: str, tag_set_id: str):
        """Create a new tag."""
        tag_data = {
            "name": tag_name,
            "display_name": tag_name,
            "tag_set": tag_set_id,
            "meta_data": None,
        }
        logger.info(f"Creating tag '{tag_name}' in tag set ID '{tag_set_id}'")
        return await client.post_object(Tags.ENDPOINT, data=tag_data)

    @staticmethod
    async def get_tag_id(client: AttackIQClient, tag_name: str, tag_set_id: str):
        """Get the ID of a tag by name and tag set ID."""
        params = {"name": tag_name, "tag_set": tag_set_id}
        tags = [tag async for tag in client.get_all_objects(Tags.ENDPOINT, params=params)]
        if tags:
            tag = tags[0]
            logger.info(f"Tag '{tag_name}' found with ID '{tag['id']}'")
            return tag["id"]
        logger.info(f"Tag '{tag_name}' not found in custom tag set")
        return None

    @staticmethod
    async def delete_tag(client: AttackIQClient, tag_id: str):
        """Delete a specific tag by its ID."""
        logger.info(f"Deleting tag with ID '{tag_id}'")
        return await client.delete_object(f"{Tags.ENDPOINT}/{tag_id}")

    @staticmethod
    async def get_or_create_tag(client: AttackIQClient, tag_name: str, tag_set_name: str) -> str:
        """Get a tag ID, creating the tag if it doesn't exist."""
        tag_set_id = await TagSets.get_tag_set_id(client, tag_set_name)
        if not tag_set_id:
            logger.error(f"Failed to get TagSet ID for '{tag_set_name}'")
            return ""
        tag_id = await Tags.get_tag_id(client, tag_name, tag_set_id)
        if not tag_id:
            logger.info(f"Tag '{tag_name}' not found. Creating new tag.")
            tag = await Tags.create_tag(client, tag_name, tag_set_id)
            if not tag:
                logger.error(f"Failed to create tag '{tag_name}'")
                return ""
            tag_id = tag["id"]
        return tag_id

    @staticmethod
    async def get_or_create_custom_tag(client: AttackIQClient, tag_name: str) -> str:
        """Get a custom tag ID, creating the tag if it doesn't exist."""
        return await Tags.get_or_create_tag(client, tag_name, "Custom")

    @staticmethod
    async def search_tags(
        client: AttackIQClient,
        search: Optional[str] = None,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        if name:
            params["name"] = name
        if display_name:
            params["display_name"] = display_name
        logger.info(f"Searching tags with params: {params}")
        url = client._build_url(Tags.ENDPOINT, params)
        data = await client._make_request(url, method="get", json=None)
        response = {"count": data["count"], "results": data["results"]}
        if "detail" in data:
            response["detail"] = data["detail"]
        return response

    @staticmethod
    async def search_mitre_tags(
        client: AttackIQClient, technique_id: str, limit: Optional[int] = 20, offset: Optional[int] = 0
    ) -> Dict[str, Any]:
        return await Tags.search_tags(client, search=technique_id, limit=limit, offset=offset)


class TaggedItems:
    """Utilities for working with tagged items in the AttackIQ platform.

    API Endpoint: /v1/tagged_items
    """

    ENDPOINT = "v1/tagged_items"

    @staticmethod
    async def get_tagged_items(
        client: AttackIQClient,
        content_type: str,
        object_id: str,
        limit: Optional[int] = 10,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """List tagged items for an object, optionally limited."""
        logger.info(f"Fetching tagged items for object of type: {content_type} with ID '{object_id}'")
        if content_type not in ["asset", "assessment"]:
            logger.error(f"Unsupported content type '{content_type}'. Supported types: 'asset', 'assessment'")
            return
        params = {"content_type": content_type, "object_id": object_id}
        generator = client.get_all_objects(TaggedItems.ENDPOINT, params=params)
        async for item in async_islice(generator, 0, limit):
            yield item

    @staticmethod
    async def get_tagged_item(client: AttackIQClient, content_type: str, object_id: str, tag_id: str):
        """Get a specific tagged item linking an object and a tag."""
        params = {"content_type": content_type, "object_id": object_id, "tag": tag_id}
        items = [item async for item in client.get_all_objects(TaggedItems.ENDPOINT, params=params)]
        return items[0] if items else None

    @staticmethod
    async def create_tagged_item(client: AttackIQClient, content_type: str, object_id: str, tag_id: str) -> str:
        """Create a tagged item (apply a tag to an object)."""
        logger.info(
            f"Creating tagged item with tag_id '{tag_id}' to object of type: {content_type} with ID '{object_id}'"
        )
        data = {
            "content_type": content_type,
            "object_id": object_id,
            "tag": tag_id,
        }
        tag_item = await client.post_object(TaggedItems.ENDPOINT, data)
        if tag_item:
            tag_item_id = tag_item["id"]
            logger.info(f"Successfully created tagged item with ID {tag_item_id}")
            return tag_item_id
        logger.error(f"Failed to create tag item with tag '{tag_id}' to object with ID '{object_id}'")
        return ""

    @staticmethod
    async def delete_tagged_item(client: AttackIQClient, tagged_item_id: str) -> bool:
        """Delete a tagged item (remove a tag from an object)."""
        logger.info(f"Removing tag item with ID {tagged_item_id}")
        response = await client.delete_object(f"{TaggedItems.ENDPOINT}/{tagged_item_id}")
        if response:
            logger.info(f"Successfully deleted tag item with ID {tagged_item_id}")
            return True
        logger.error(f"Failed to delete tagged item with ID {tagged_item_id}")
        return False
