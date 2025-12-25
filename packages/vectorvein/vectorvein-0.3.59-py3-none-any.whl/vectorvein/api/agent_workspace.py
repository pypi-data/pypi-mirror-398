"""Agent Workspace API functionality"""

from typing import Any

from .models import (
    AgentWorkspace,
    AgentWorkspaceListResponse,
    WorkspaceFileListResponse,
    WorkspaceFileContent,
    WorkspaceFile,
    User,
)


def _create_agent_workspace_from_response(data: dict) -> AgentWorkspace:
    """Create AgentWorkspace object from API response"""
    # Create User object
    user_data = data.get("user", {})
    user = User(nickname=user_data.get("nickname", ""), avatar=user_data.get("avatar", ""))

    # Create WorkspaceFile objects for latest_files
    latest_files = []
    if data.get("latest_files"):
        for file_data in data["latest_files"]:
            latest_files.append(WorkspaceFile(key=file_data["key"], size=file_data["size"], etag=file_data["etag"], last_modified=file_data["last_modified"]))

    return AgentWorkspace(
        workspace_id=data["workspace_id"],
        agent_task_id=data["agent_task_id"],
        user=user,
        oss_bucket=data["oss_bucket"],
        base_storage_path=data["base_storage_path"],
        created_at=data["created_at"],
        last_accessed=data["last_accessed"],
        latest_files=latest_files,
        file_count=data["file_count"],
    )


def _create_agent_workspace_list_response(data: dict) -> AgentWorkspaceListResponse:
    """Create AgentWorkspaceListResponse from API response"""
    workspaces = [_create_agent_workspace_from_response(ws_data) for ws_data in data["workspaces"]]
    return AgentWorkspaceListResponse(
        workspaces=workspaces,
        total=data["total"],
        page=data["page"],
        page_size=data["page_size"],
        page_count=data["page_count"],
    )


class AgentWorkspaceSyncMixin:
    """Synchronous agent workspace API methods"""

    def list_agent_workspaces(
        self,
        page: int = 1,
        page_size: int = 10,
    ) -> AgentWorkspaceListResponse:
        """List user's agent workspaces

        Args:
            page: Page number
            page_size: Page size

        Returns:
            AgentWorkspaceListResponse: Workspace list response

        Raises:
            VectorVeinAPIError: List error
        """
        payload = {"page": page, "page_size": page_size}
        response = self._request("POST", "agent-workspace/list", json=payload)
        return _create_agent_workspace_list_response(response["data"])

    def get_agent_workspace(self, workspace_id: str) -> AgentWorkspace:
        """Get agent workspace details

        Args:
            workspace_id: Workspace ID

        Returns:
            AgentWorkspace: Workspace details

        Raises:
            VectorVeinAPIError: Workspace not found or access denied
        """
        payload = {"workspace_id": workspace_id}
        response = self._request("POST", "agent-workspace/get", json=payload)
        return _create_agent_workspace_from_response(response["data"])

    def list_workspace_files(
        self,
        workspace_id: str,
        prefix: str | None = None,
        tree_view: bool = False,
    ) -> WorkspaceFileListResponse:
        """List files in workspace

        Args:
            workspace_id: Workspace ID
            prefix: Path prefix filter
            tree_view: Whether to return tree structure

        Returns:
            WorkspaceFileListResponse: File list response

        Raises:
            VectorVeinAPIError: List error
        """
        payload = {"workspace_id": workspace_id, "tree_view": tree_view}
        if prefix:
            payload["prefix"] = prefix

        response = self._request("POST", "agent-workspace/list-files", json=payload)
        return WorkspaceFileListResponse(**response["data"])

    def read_workspace_file(
        self,
        workspace_id: str,
        file_path: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> WorkspaceFileContent:
        """Read workspace file content

        Args:
            workspace_id: Workspace ID
            file_path: File path within workspace
            start_line: Start line (1-based)
            end_line: End line (1-based, inclusive)

        Returns:
            WorkspaceFileContent: File content and info

        Raises:
            VectorVeinAPIError: Read error
        """
        payload = {"workspace_id": workspace_id, "file_path": file_path}
        if start_line is not None:
            payload["start_line"] = start_line
        if end_line is not None:
            payload["end_line"] = end_line

        response = self._request("POST", "agent-workspace/read-file", json=payload)
        return WorkspaceFileContent(**response["data"])

    def download_workspace_file(self, workspace_id: str, file_path: str) -> str:
        """Get workspace file download URL

        Args:
            workspace_id: Workspace ID
            file_path: File path within workspace

        Returns:
            str: Temporary download URL

        Raises:
            VectorVeinAPIError: Download error
        """
        payload = {"workspace_id": workspace_id, "file_path": file_path}
        response = self._request("POST", "agent-workspace/download-file", json=payload)
        return response["data"]["file_url"]

    def write_workspace_file(self, workspace_id: str, file_path: str, content: str) -> dict[str, Any]:
        """Write file to workspace

        Args:
            workspace_id: Workspace ID
            file_path: File path within workspace
            content: File content

        Returns:
            dict: Write result

        Raises:
            VectorVeinAPIError: Write error
        """
        payload = {
            "workspace_id": workspace_id,
            "file_path": file_path,
            "content": content,
        }
        response = self._request("POST", "agent-workspace/write-file", json=payload)
        return response["data"]

    def delete_workspace_file(self, workspace_id: str, file_path: str) -> dict[str, Any]:
        """Delete file from workspace

        Args:
            workspace_id: Workspace ID
            file_path: File path within workspace

        Returns:
            dict: Delete result

        Raises:
            VectorVeinAPIError: Delete error
        """
        payload = {"workspace_id": workspace_id, "file_path": file_path}
        response = self._request("POST", "agent-workspace/delete-file", json=payload)
        return response["data"]


class AgentWorkspaceAsyncMixin:
    """Asynchronous agent workspace API methods"""

    async def list_agent_workspaces(
        self,
        page: int = 1,
        page_size: int = 10,
    ) -> AgentWorkspaceListResponse:
        """Async list user's agent workspaces

        Args:
            page: Page number
            page_size: Page size

        Returns:
            AgentWorkspaceListResponse: Workspace list response

        Raises:
            VectorVeinAPIError: List error
        """
        payload = {"page": page, "page_size": page_size}
        response = await self._request("POST", "agent-workspace/list", json=payload)
        return _create_agent_workspace_list_response(response["data"])

    async def get_agent_workspace(self, workspace_id: str) -> AgentWorkspace:
        """Async get agent workspace details

        Args:
            workspace_id: Workspace ID

        Returns:
            AgentWorkspace: Workspace details

        Raises:
            VectorVeinAPIError: Workspace not found or access denied
        """
        payload = {"workspace_id": workspace_id}
        response = await self._request("POST", "agent-workspace/get", json=payload)
        return _create_agent_workspace_from_response(response["data"])

    async def list_workspace_files(
        self,
        workspace_id: str,
        prefix: str | None = None,
        tree_view: bool = False,
    ) -> WorkspaceFileListResponse:
        """Async list files in workspace

        Args:
            workspace_id: Workspace ID
            prefix: Path prefix filter
            tree_view: Whether to return tree structure

        Returns:
            WorkspaceFileListResponse: File list response

        Raises:
            VectorVeinAPIError: List error
        """
        payload = {"workspace_id": workspace_id, "tree_view": tree_view}
        if prefix:
            payload["prefix"] = prefix

        response = await self._request("POST", "agent-workspace/list-files", json=payload)
        return WorkspaceFileListResponse(**response["data"])

    async def read_workspace_file(
        self,
        workspace_id: str,
        file_path: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> WorkspaceFileContent:
        """Async read workspace file content

        Args:
            workspace_id: Workspace ID
            file_path: File path within workspace
            start_line: Start line (1-based)
            end_line: End line (1-based, inclusive)

        Returns:
            WorkspaceFileContent: File content and info

        Raises:
            VectorVeinAPIError: Read error
        """
        payload = {"workspace_id": workspace_id, "file_path": file_path}
        if start_line is not None:
            payload["start_line"] = start_line
        if end_line is not None:
            payload["end_line"] = end_line

        response = await self._request("POST", "agent-workspace/read-file", json=payload)
        return WorkspaceFileContent(**response["data"])

    async def download_workspace_file(self, workspace_id: str, file_path: str) -> str:
        """Async get workspace file download URL

        Args:
            workspace_id: Workspace ID
            file_path: File path within workspace

        Returns:
            str: Temporary download URL

        Raises:
            VectorVeinAPIError: Download error
        """
        payload = {"workspace_id": workspace_id, "file_path": file_path}
        response = await self._request("POST", "agent-workspace/download-file", json=payload)
        return response["data"]["file_url"]

    async def write_workspace_file(self, workspace_id: str, file_path: str, content: str) -> dict[str, Any]:
        """Async write file to workspace

        Args:
            workspace_id: Workspace ID
            file_path: File path within workspace
            content: File content

        Returns:
            dict: Write result

        Raises:
            VectorVeinAPIError: Write error
        """
        payload = {
            "workspace_id": workspace_id,
            "file_path": file_path,
            "content": content,
        }
        response = await self._request("POST", "agent-workspace/write-file", json=payload)
        return response["data"]

    async def delete_workspace_file(self, workspace_id: str, file_path: str) -> dict[str, Any]:
        """Async delete file from workspace

        Args:
            workspace_id: Workspace ID
            file_path: File path within workspace

        Returns:
            dict: Delete result

        Raises:
            VectorVeinAPIError: Delete error
        """
        payload = {"workspace_id": workspace_id, "file_path": file_path}
        response = await self._request("POST", "agent-workspace/delete-file", json=payload)
        return response["data"]
