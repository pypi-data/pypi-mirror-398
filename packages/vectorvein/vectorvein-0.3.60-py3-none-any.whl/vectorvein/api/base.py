"""Base client classes with common functionality"""

import time
import base64
from urllib.parse import quote
from typing import Any, Literal

import httpx
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from .exceptions import (
    VectorVeinAPIError,
    APIKeyError,
    RequestError,
)


class BaseClient:
    """Base client with common functionality"""

    API_VERSION = "20240508"
    BASE_URL = "https://vectorvein.com/api/v1/open-api"

    def __init__(self, api_key: str, base_url: str | None = None):
        """Initialize the base client

        Args:
            api_key: API key
            base_url: API base URL, default is https://vectorvein.com/api/v1/open-api

        Raises:
            APIKeyError: API key is empty or not a string
        """
        if not api_key or not isinstance(api_key, str):
            raise APIKeyError("API key cannot be empty and must be a string type")

        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.default_headers = {
            "VECTORVEIN-API-KEY": api_key,
            "VECTORVEIN-API-VERSION": self.API_VERSION,
        }


class BaseSyncClient(BaseClient):
    """Base synchronous client"""

    def __init__(self, api_key: str, base_url: str | None = None):
        super().__init__(api_key, base_url)
        self._client = httpx.Client(timeout=60)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._client.close()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        **kwargs,
    ) -> dict[str, Any]:
        """Send HTTP request

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: URL parameters
            json: JSON request body
            files: Files to upload
            api_key_type: API key type
            **kwargs: Other request parameters

        Returns:
            Dict[str, Any]: API response

        Raises:
            RequestError: Request error
            VectorVeinAPIError: API error
            APIKeyError: API key is invalid or expired
        """
        url = f"{self.base_url}/{endpoint}"
        headers = self.default_headers.copy()
        if api_key_type == "VAPP":
            headers["VECTORVEIN-API-KEY-TYPE"] = "VAPP"

        try:
            response = self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                files=files,
                headers=headers,
                **kwargs,
            )
            result = response.json()

            if result["status"] in [401, 403]:
                raise APIKeyError("API key is invalid or expired")
            if result["status"] != 200 and result["status"] != 202 and result["status"] != 201:
                raise VectorVeinAPIError(message=result.get("msg", "Unknown error"), status_code=result["status"])
            return result
        except httpx.HTTPError as e:
            raise RequestError(f"Request failed: {str(e)}") from e

    def generate_vapp_url(
        self,
        app_id: str,
        access_key: str,
        key_id: str,
        timeout: int = 15 * 60,
        base_url: str = "https://vectorvein.com",
    ) -> str:
        """Generate VApp access link

        Args:
            app_id: VApp ID
            access_key: Access key
            key_id: Key ID
            timeout: Timeout (seconds)
            base_url: Base URL

        Returns:
            str: VApp access link
        """
        timestamp = int(time.time())
        message = f"{app_id}:{access_key}:{timestamp}:{timeout}"
        encryption_key = self.api_key.encode()

        cipher = AES.new(encryption_key, AES.MODE_CBC)
        padded_data = pad(message.encode(), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        final_data = bytes(cipher.iv) + encrypted_data
        token = base64.b64encode(final_data).decode("utf-8")
        quoted_token = quote(token)

        return f"{base_url}/public/v-app/{app_id}?token={quoted_token}&key_id={key_id}"


class BaseAsyncClient(BaseClient):
    """Base asynchronous client"""

    def __init__(self, api_key: str, base_url: str | None = None):
        super().__init__(api_key, base_url)
        self._client = httpx.AsyncClient(timeout=60)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        **kwargs,
    ) -> dict[str, Any]:
        """Send asynchronous HTTP request

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: URL parameters
            json: JSON request body
            files: Files to upload
            api_key_type: API key type
            **kwargs: Other request parameters

        Returns:
            Dict[str, Any]: API response

        Raises:
            RequestError: Request error
            VectorVeinAPIError: API error
            APIKeyError: API key is invalid or expired
        """
        url = f"{self.base_url}/{endpoint}"
        headers = self.default_headers.copy()
        if api_key_type == "VAPP":
            headers["VECTORVEIN-API-KEY-TYPE"] = "VAPP"

        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                files=files,
                headers=headers,
                **kwargs,
            )
            result = response.json()

            if result["status"] in [401, 403]:
                raise APIKeyError("API key is invalid or expired")
            if result["status"] != 200 and result["status"] != 202 and result["status"] != 201:
                raise VectorVeinAPIError(message=result.get("msg", "Unknown error"), status_code=result["status"])
            return result
        except httpx.HTTPError as e:
            raise RequestError(f"Request failed: {str(e)}") from e

    async def generate_vapp_url(
        self,
        app_id: str,
        access_key: str,
        key_id: str,
        timeout: int = 15 * 60,
        base_url: str = "https://vectorvein.com",
    ) -> str:
        """Async generate VApp access link

        Args:
            app_id: VApp ID
            access_key: Access key
            key_id: Key ID
            timeout: Timeout (seconds)
            base_url: Base URL

        Returns:
            str: VApp access link
        """
        timestamp = int(time.time())
        message = f"{app_id}:{access_key}:{timestamp}:{timeout}"
        encryption_key = self.api_key.encode()

        cipher = AES.new(encryption_key, AES.MODE_CBC)
        padded_data = pad(message.encode(), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        final_data = bytes(cipher.iv) + encrypted_data
        token = base64.b64encode(final_data).decode("utf-8")
        quoted_token = quote(token)

        return f"{base_url}/public/v-app/{app_id}?token={quoted_token}&key_id={key_id}"
