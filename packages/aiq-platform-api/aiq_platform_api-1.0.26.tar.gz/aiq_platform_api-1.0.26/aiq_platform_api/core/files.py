import base64
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import httpx

from aiq_platform_api.core.client import AttackIQClient
from aiq_platform_api.core.logger import AttackIQLogger

logger = AttackIQLogger.get_logger(__name__)


class FileUploads:
    ENDPOINT = "v1/files"

    @staticmethod
    def _normalize_file_path(file_path: str) -> str:
        if not file_path or not file_path.strip():
            raise ValueError("file_path is required")

        parsed = urlparse(file_path.strip())
        path = parsed.path.lstrip("/") if parsed.scheme else file_path.strip().lstrip("/")

        path = path.removeprefix("downloads/").removeprefix("files/")

        parts = path.split("/", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("file_path must be in 'uuid/filename' format")

        return path

    @staticmethod
    async def upload_script_file(
        client: AttackIQClient,
        file_name: str,
        file_content: bytes,
        content_type: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        upload_response = await client.upload_file(
            endpoint=FileUploads.ENDPOINT,
            file_name=file_name,
            file_content=file_content,
            content_type=content_type,
            headers=headers,
        )
        file_url = upload_response["file"]
        file_path = FileUploads._extract_path(file_url)
        return {**upload_response, "file_path": file_path}

    @staticmethod
    async def get_file_metadata(client: AttackIQClient, file_id: str) -> Dict[str, Any]:
        """Get file metadata by ID."""
        endpoint = f"{FileUploads.ENDPOINT}/{file_id}"
        return await client.get_object(endpoint)

    @staticmethod
    def _extract_path(file_url: Optional[str]) -> str:
        if not file_url:
            raise ValueError("Upload response missing file URL")
        return FileUploads._normalize_file_path(file_url)


class FileDownloads:
    @staticmethod
    async def download_file(client: AttackIQClient, file_path: str, max_bytes: int = 300_000) -> Dict[str, Any]:
        normalized = FileUploads._normalize_file_path(file_path)
        url = f"{client.platform_url}/downloads/files/{normalized}"

        async with client.http_client.stream("GET", url, headers=client.headers) as response:
            try:
                response.raise_for_status()
            except httpx.RequestError as e:
                logger.error(
                    f"download_file failed \n"
                    f"\turl: {url} \n"
                    f"\tstatus: {response.status_code if response else 'n/a'} \n"
                    f"\tcontent: {response.text if response and response.content else 'n/a'} \n"
                    f"\texception: {e}"
                )
                raise

            content_length = response.headers.get("Content-Length")
            if content_length is not None and int(content_length) > max_bytes:
                raise ValueError(f"File too large: {content_length} bytes exceeds limit {max_bytes}")

            content = await response.aread()

        if len(content) > max_bytes:
            raise ValueError(f"File too large after download: {len(content)} bytes exceeds limit {max_bytes}")

        content_type = response.headers.get("Content-Type", "application/octet-stream")
        filename = normalized.split("/", 1)[1]

        return {
            "filename": filename,
            "content_type": content_type,
            "size": len(content),
            "content_base64": base64.b64encode(content).decode("ascii"),
        }
