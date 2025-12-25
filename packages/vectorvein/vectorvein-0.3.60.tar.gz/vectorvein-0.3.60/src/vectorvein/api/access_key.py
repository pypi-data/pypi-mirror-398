"""Access Key API functionality"""

from typing import Literal

from .exceptions import AccessKeyError, VectorVeinAPIError
from .models import AccessKey, AccessKeyListResponse


class AccessKeySyncMixin:
    """Synchronous access key API methods"""

    def get_access_keys(self, access_keys: list[str] | None = None, get_type: Literal["selected", "all"] = "selected") -> list[AccessKey]:
        """Get access key information

        Args:
            access_keys: Access key list
            get_type: Get type, optional values: 'selected' or 'all'

        Returns:
            List[AccessKey]: Access key information list

        Raises:
            AccessKeyError: Access key does not exist or has expired
        """
        params = {"get_type": get_type}
        if access_keys:
            params["access_keys"] = ",".join(access_keys)

        try:
            result = self._request("GET", "vapp/access-key/get", params=params)
            return [AccessKey(**key) for key in result["data"]]
        except VectorVeinAPIError as e:
            if e.status_code == 404:
                raise AccessKeyError("Access key does not exist") from e
            elif e.status_code == 403:
                raise AccessKeyError("Access key has expired") from e
            raise

    def create_access_keys(
        self,
        access_key_type: Literal["O", "M", "L"],
        app_id: str | None = None,
        app_ids: list[str] | None = None,
        count: int = 1,
        expire_time: str | None = None,
        max_credits: int | None = None,
        max_use_count: int | None = None,
        description: str | None = None,
    ) -> list[AccessKey]:
        """Create access key

        Args:
            access_key_type: Key type, optional values: 'O'(one-time)、'M'(multiple)、'L'(long-term)
            app_id: Single application ID
            app_ids: Multiple application ID list
            count: Create quantity
            expire_time: Expiration time
            max_credits: Maximum credit limit
            max_use_count: Maximum use count
            description: Description information

        Returns:
            List[AccessKey]: Created access key list

        Raises:
            AccessKeyError: Failed to create access key, such as invalid type, application does not exist, etc.
        """
        if access_key_type not in ["O", "M", "L"]:
            raise AccessKeyError("Invalid access key type, must be 'O'(one-time)、'M'(multiple) or 'L'(long-term)")

        if app_id and app_ids:
            raise AccessKeyError("Cannot specify both app_id and app_ids")

        payload = {"access_key_type": access_key_type, "count": count}

        if app_id:
            payload["app_id"] = app_id
        if app_ids:
            payload["app_ids"] = app_ids
        if expire_time:
            payload["expire_time"] = expire_time
        if max_credits is not None:
            payload["max_credits"] = max_credits
        if max_use_count is not None:
            payload["max_use_count"] = max_use_count
        if description:
            payload["description"] = description

        try:
            result = self._request("POST", "vapp/access-key/create", json=payload)
            return [AccessKey(**key) for key in result["data"]]
        except VectorVeinAPIError as e:
            if e.status_code == 404:
                raise AccessKeyError("The specified application does not exist") from e
            elif e.status_code == 403:
                raise AccessKeyError("No permission to create access key") from e
            raise

    def list_access_keys(
        self,
        page: int = 1,
        page_size: int = 10,
        sort_field: str = "create_time",
        sort_order: str = "descend",
        app_id: str | None = None,
        status: list[str] | None = None,
        access_key_type: Literal["O", "M", "L"] | None = None,
    ) -> AccessKeyListResponse:
        """List access keys

        Args:
            page: Page number
            page_size: Number of items per page
            sort_field: Sort field
            sort_order: Sort order
            app_id: Application ID
            status: Status list
            access_key_type: Key type list, optional values: 'O'(one-time)、'M'(multiple)、'L'(long-term)

        Returns:
            AccessKeyListResponse: Access key list response
        """
        payload = {"page": page, "page_size": page_size, "sort_field": sort_field, "sort_order": sort_order}

        if app_id:
            payload["app_id"] = app_id
        if status:
            payload["status"] = status
        if access_key_type:
            payload["access_key_type"] = access_key_type

        result = self._request("POST", "vapp/access-key/list", json=payload)
        return AccessKeyListResponse(**result["data"])

    def delete_access_keys(self, app_id: str, access_keys: list[str]) -> None:
        """Delete access key

        Args:
            app_id: Application ID
            access_keys: List of access keys to delete
        """
        payload = {"app_id": app_id, "access_keys": access_keys}
        self._request("POST", "vapp/access-key/delete", json=payload)

    def update_access_keys(
        self,
        access_key: str | None = None,
        access_keys: list[str] | None = None,
        app_id: str | None = None,
        app_ids: list[str] | None = None,
        expire_time: str | None = None,
        max_use_count: int | None = None,
        max_credits: int | None = None,
        description: str | None = None,
        access_key_type: Literal["O", "M", "L"] | None = None,
    ) -> None:
        """Update access key

        Args:
            access_key: Single access key
            access_keys: Multiple access key list
            app_id: Single application ID
            app_ids: Multiple application ID list
            expire_time: Expiration time
            max_use_count: Maximum use count
            max_credits: Maximum credit limit
            description: Description information
            access_key_type: Key type, optional values: 'O'(one-time)、'M'(multiple)、'L'(long-term)
        """
        payload = {}
        if access_key:
            payload["access_key"] = access_key
        if access_keys:
            payload["access_keys"] = access_keys
        if app_id:
            payload["app_id"] = app_id
        if app_ids:
            payload["app_ids"] = app_ids
        if expire_time:
            payload["expire_time"] = expire_time
        if max_use_count is not None:
            payload["max_use_count"] = max_use_count
        if max_credits is not None:
            payload["max_credits"] = max_credits
        if description:
            payload["description"] = description
        if access_key_type:
            payload["access_key_type"] = access_key_type

        self._request("POST", "vapp/access-key/update", json=payload)

    def add_apps_to_access_keys(self, access_keys: list[str], app_ids: list[str]) -> None:
        """Add applications to access keys

        Args:
            access_keys: Access key list
            app_ids: List of application IDs to add
        """
        payload = {"access_keys": access_keys, "app_ids": app_ids}
        self._request("POST", "vapp/access-key/add-apps", json=payload)

    def remove_apps_from_access_keys(self, access_keys: list[str], app_ids: list[str]) -> None:
        """Remove applications from access keys

        Args:
            access_keys: Access key list
            app_ids: List of application IDs to remove
        """
        payload = {"access_keys": access_keys, "app_ids": app_ids}
        self._request("POST", "vapp/access-key/remove-apps", json=payload)


class AccessKeyAsyncMixin:
    """Asynchronous access key API methods"""

    async def get_access_keys(self, access_keys: list[str] | None = None, get_type: Literal["selected", "all"] = "selected") -> list[AccessKey]:
        """Async get access key information

        Args:
            access_keys: Access key list
            get_type: Get type, optional values: 'selected' or 'all'

        Returns:
            List[AccessKey]: Access key information list

        Raises:
            AccessKeyError: Access key does not exist or has expired
        """
        params = {"get_type": get_type}
        if access_keys:
            params["access_keys"] = ",".join(access_keys)

        try:
            result = await self._request("GET", "vapp/access-key/get", params=params)
            return [AccessKey(**key) for key in result["data"]]
        except VectorVeinAPIError as e:
            if e.status_code == 404:
                raise AccessKeyError("Access key does not exist") from e
            elif e.status_code == 403:
                raise AccessKeyError("Access key has expired") from e
            raise

    async def create_access_keys(
        self,
        access_key_type: Literal["O", "M", "L"],
        app_id: str | None = None,
        app_ids: list[str] | None = None,
        count: int = 1,
        expire_time: str | None = None,
        max_credits: int | None = None,
        max_use_count: int | None = None,
        description: str | None = None,
    ) -> list[AccessKey]:
        """Async create access key

        Args:
            access_key_type: Key type, optional values: 'O'(one-time)、'M'(multiple)、'L'(long-term)
            app_id: Single application ID
            app_ids: Multiple application ID list
            count: Create quantity
            expire_time: Expiration time
            max_credits: Maximum credit limit
            max_use_count: Maximum use count
            description: Description

        Returns:
            List[AccessKey]: Created access key list

        Raises:
            AccessKeyError: Failed to create access key, such as invalid type, application does not exist, etc.
        """
        if access_key_type not in ["O", "M", "L"]:
            raise AccessKeyError("Invalid access key type, must be 'O'(one-time) or 'M'(multiple) or 'L'(long-term)")

        if app_id and app_ids:
            raise AccessKeyError("Cannot specify both app_id and app_ids")

        payload = {"access_key_type": access_key_type, "count": count}

        if app_id:
            payload["app_id"] = app_id
        if app_ids:
            payload["app_ids"] = app_ids
        if expire_time:
            payload["expire_time"] = expire_time
        if max_credits is not None:
            payload["max_credits"] = max_credits
        if max_use_count is not None:
            payload["max_use_count"] = max_use_count
        if description:
            payload["description"] = description

        try:
            result = await self._request("POST", "vapp/access-key/create", json=payload)
            return [AccessKey(**key) for key in result["data"]]
        except VectorVeinAPIError as e:
            if e.status_code == 404:
                raise AccessKeyError("The specified application does not exist") from e
            elif e.status_code == 403:
                raise AccessKeyError("No permission to create access key") from e
            raise

    async def list_access_keys(
        self,
        page: int = 1,
        page_size: int = 10,
        sort_field: str = "create_time",
        sort_order: str = "descend",
        app_id: str | None = None,
        status: list[str] | None = None,
        access_key_type: Literal["O", "M", "L"] | None = None,
    ) -> AccessKeyListResponse:
        """Async list access keys

        Args:
            page: Page number
            page_size: Number of items per page
            sort_field: Sort field
            sort_order: Sort order
            app_id: Application ID
            status: Status list
            access_key_type: Key type list, optional values: 'O'(one-time)、'M'(multiple)、'L'(long-term)

        Returns:
            AccessKeyListResponse: Access key list response
        """
        payload = {"page": page, "page_size": page_size, "sort_field": sort_field, "sort_order": sort_order}

        if app_id:
            payload["app_id"] = app_id
        if status:
            payload["status"] = status
        if access_key_type:
            payload["access_key_type"] = access_key_type

        result = await self._request("POST", "vapp/access-key/list", json=payload)
        return AccessKeyListResponse(**result["data"])

    async def delete_access_keys(self, app_id: str, access_keys: list[str]) -> None:
        """Async delete access key

        Args:
            app_id: Application ID
            access_keys: List of access keys to delete
        """
        payload = {"app_id": app_id, "access_keys": access_keys}
        await self._request("POST", "vapp/access-key/delete", json=payload)

    async def update_access_keys(
        self,
        access_key: str | None = None,
        access_keys: list[str] | None = None,
        app_id: str | None = None,
        app_ids: list[str] | None = None,
        expire_time: str | None = None,
        max_use_count: int | None = None,
        max_credits: int | None = None,
        description: str | None = None,
        access_key_type: Literal["O", "M", "L"] | None = None,
    ) -> None:
        """Async update access key

        Args:
            access_key: Single access key
            access_keys: Multiple access key list
            app_id: Single application ID
            app_ids: Multiple application ID list
            expire_time: Expiration time
            max_use_count: Maximum use count
            max_credits: Maximum credit limit
            description: Description
            access_key_type: Key type, optional values: 'O'(one-time)、'M'(multiple)、'L'(long-term)
        """
        payload = {}
        if access_key:
            payload["access_key"] = access_key
        if access_keys:
            payload["access_keys"] = access_keys
        if app_id:
            payload["app_id"] = app_id
        if app_ids:
            payload["app_ids"] = app_ids
        if expire_time:
            payload["expire_time"] = expire_time
        if max_use_count is not None:
            payload["max_use_count"] = max_use_count
        if max_credits is not None:
            payload["max_credits"] = max_credits
        if description:
            payload["description"] = description
        if access_key_type:
            payload["access_key_type"] = access_key_type

        await self._request("POST", "vapp/access-key/update", json=payload)

    async def add_apps_to_access_keys(self, access_keys: list[str], app_ids: list[str]) -> None:
        """Async add applications to access keys

        Args:
            access_keys: Access key list
            app_ids: List of application IDs to add
        """
        payload = {"access_keys": access_keys, "app_ids": app_ids}
        await self._request("POST", "vapp/access-key/add-apps", json=payload)

    async def remove_apps_from_access_keys(self, access_keys: list[str], app_ids: list[str]) -> None:
        """Async remove applications from access keys

        Args:
            access_keys: Access key list
            app_ids: List of application IDs to remove
        """
        payload = {"access_keys": access_keys, "app_ids": app_ids}
        await self._request("POST", "vapp/access-key/remove-apps", json=payload)
