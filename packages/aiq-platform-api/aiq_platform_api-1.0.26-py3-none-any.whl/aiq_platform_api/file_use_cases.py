# File endpoint use cases: upload, fetch metadata, download via URL.
import asyncio
import base64
import os
from enum import Enum
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

from aiq_platform_api import (
    AttackIQLogger,
    AttackIQClient,
    FileDownloads,
    FileUploads,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
from aiq_platform_api.core.testing import parse_test_choice, require_env

logger = AttackIQLogger.get_logger(__name__)


async def upload_text_file(client: AttackIQClient, file_name: str, content: str) -> dict:
    logger.info(f"Uploading file {file_name}")
    return await FileUploads.upload_script_file(
        client=client,
        file_name=file_name,
        file_content=content.encode(),
        content_type="text/plain",
    )


async def get_file_metadata(client: AttackIQClient, file_id: str) -> dict:
    meta = await FileUploads.get_file_metadata(client, file_id)
    logger.info(f"Retrieved metadata for file {file_id}")
    return meta


async def download_file(meta: dict, destination: Optional[str] = None) -> Path:
    file_url = meta["file"]
    parsed_name = Path(urlparse(file_url).path).name
    target_path = Path(destination) if destination else Path(parsed_name)
    if target_path.is_dir():
        target_path = target_path / parsed_name
    logger.info(f"Downloading file to {target_path}")
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as http_client:
        response = await http_client.get(file_url)
        response.raise_for_status()
        target_path.write_bytes(response.content)
    return target_path.resolve()


async def test_upload_and_get_metadata(client: AttackIQClient):
    result = await upload_text_file(client, "file_use_case_test.txt", "Hello from file_use_cases")
    file_id = result["id"]
    meta = await get_file_metadata(client, file_id)
    logger.info(f"File path: {result['file_path']}")
    logger.info(f"Metadata keys: {list(meta.keys())}")
    return file_id


async def test_download_file(client: AttackIQClient, destination: Optional[str] = None):
    result = await upload_text_file(client, "file_use_case_download.txt", "Download use case")
    meta = await get_file_metadata(client, result["id"])
    path = await download_file(meta, destination)
    logger.info(f"Downloaded file size: {os.path.getsize(path)} bytes")


async def test_upload_and_download(client: AttackIQClient):
    original_content = "Hello from file_use_case_round_trip"
    uploaded = await upload_text_file(client, "file_use_case_round_trip.txt", original_content)
    file_path = uploaded["file_path"]

    downloaded = await FileDownloads.download_file(client, file_path)
    decoded = base64.b64decode(downloaded["content_base64"]).decode()

    if decoded != original_content:
        raise ValueError("Downloaded content does not match uploaded content")

    logger.info(f"Round-trip download size: {downloaded['size']} bytes")


async def test_download_bytes_with_limit(client: AttackIQClient, max_bytes: int = 300_000):
    """Upload a small file and download via client.download_bytes to exercise retry + size guard."""
    body = "Hello from download_bytes use case"
    uploaded = await upload_text_file(client, "file_use_case_download_bytes.txt", body)
    file_path = uploaded["file_path"]
    endpoint = f"downloads/files/{file_path}"
    content = await client.download_bytes(endpoint)
    decoded = content.decode()
    if decoded != body:
        raise ValueError("download_bytes content mismatch")
    logger.info(f"download_bytes fetched {len(content)} bytes for {file_path}")


async def test_all(client: AttackIQClient):
    """Run all file tests."""
    for choice in TestChoice:
        if choice != TestChoice.ALL:
            await run_test(choice, client)


async def run_test(choice: "TestChoice", client: AttackIQClient):
    """Run the selected test."""
    test_functions = {
        TestChoice.UPLOAD_AND_METADATA: lambda: test_upload_and_get_metadata(client),
        TestChoice.DOWNLOAD_FILE: lambda: test_download_file(client),
        TestChoice.UPLOAD_AND_DOWNLOAD: lambda: test_upload_and_download(client),
        TestChoice.DOWNLOAD_BYTES: lambda: test_download_bytes_with_limit(client),
        TestChoice.ALL: lambda: test_all(client),
    }
    await test_functions[choice]()


class TestChoice(Enum):
    UPLOAD_AND_METADATA = "upload_and_metadata"
    DOWNLOAD_FILE = "download_file"
    UPLOAD_AND_DOWNLOAD = "upload_and_download"
    DOWNLOAD_BYTES = "download_bytes"
    ALL = "all"


async def main():
    require_env(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN)
    choice = parse_test_choice(TestChoice)

    async with AttackIQClient(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN) as client:
        await run_test(choice, client)


if __name__ == "__main__":
    asyncio.run(main())
