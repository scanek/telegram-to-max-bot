import logging
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class GreenApiClient:
    def __init__(
        self,
        host: Optional[str] = None,
        instance_id: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        self.host = (host or settings.GREEN_API_HOST).rstrip("/")
        self.instance_id = instance_id or settings.MAX_INSTANCE_ID
        self.api_token = api_token or settings.MAX_API_TOKEN
        self.base_url = f"{self.host}/waInstance{self.instance_id}"

    async def send_message(self, chat_id: str, text: str) -> dict:
        """Sends text message to target chat via GREEN-API."""
        url = f"{self.base_url}/sendMessage/{self.api_token}"
        payload = {
            "chatId": chat_id,
            "message": text,
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                logger.info(f"GREEN-API message sent successfully to {chat_id}: {data}")
                return data
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"GREEN-API HTTP error {e.response.status_code}: {e.response.text}"
                )
                raise
            except Exception as e:
                logger.error(f"Failed to send message via GREEN-API: {e}")
                raise

    async def send_file_by_upload(
        self,
        chat_id: str,
        file_bytes: bytes,
        file_name: str,
        caption: Optional[str] = None,
    ) -> dict:
        """Sends file (uploading bytes) to target chat via GREEN-API."""
        import mimetypes
        content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        url = f"{self.base_url}/sendFileByUpload/{self.api_token}"
        data = {
            "chatId": chat_id,
            "fileName": file_name,
        }
        if caption:
            data["caption"] = caption

        files = {
            "file": (file_name, file_bytes, content_type),
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, data=data, files=files)
                response.raise_for_status()
                res_data = response.json()
                logger.info(f"GREEN-API file {file_name} sent successfully to {chat_id}: {res_data}")
                return res_data
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"GREEN-API file upload HTTP error {e.response.status_code}: {e.response.text}"
                )
                raise
            except Exception as e:
                logger.error(f"Failed to upload file via GREEN-API: {e}")
                raise

    async def send_file_by_url(
        self,
        chat_id: str,
        url_file: str,
        file_name: str,
        caption: Optional[str] = None,
    ) -> dict:
        """Sends file by public URL to target chat via GREEN-API."""
        url = f"{self.base_url}/sendFileByUrl/{self.api_token}"
        payload = {
            "chatId": chat_id,
            "urlFile": url_file,
            "fileName": file_name,
        }
        if caption:
            payload["caption"] = caption

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                logger.info(f"GREEN-API file by URL sent successfully to {chat_id}: {data}")
                return data
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"GREEN-API file-by-url HTTP error {e.response.status_code}: {e.response.text}"
                )
                raise
            except Exception as e:
                logger.error(f"Failed to send file by URL via GREEN-API: {e}")
                raise


green_api_client = GreenApiClient()
