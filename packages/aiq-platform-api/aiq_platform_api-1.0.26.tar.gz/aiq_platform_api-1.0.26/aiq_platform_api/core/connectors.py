from typing import Optional, Dict, Any, AsyncGenerator

from aiq_platform_api.core.async_utils import async_islice
from aiq_platform_api.core.client import AttackIQClient
from aiq_platform_api.core.logger import AttackIQLogger

logger = AttackIQLogger.get_logger(__name__)


class Connectors:
    """Utilities for working with company connectors.

    API Endpoint: /v1/company_connectors
    """

    ENDPOINT = "v1/company_connectors"

    @staticmethod
    async def get_connectors(
        client: AttackIQClient, params: dict = None, limit: Optional[int] = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """List connectors, optionally filtered and limited."""
        generator = client.get_all_objects(Connectors.ENDPOINT, params=params)
        async for connector in async_islice(generator, 0, limit):
            yield connector

    @staticmethod
    async def get_connector_by_id(client: AttackIQClient, connector_id: str):
        """Get a specific connector by its ID."""
        return await client.get_object(f"{Connectors.ENDPOINT}/{connector_id}")
