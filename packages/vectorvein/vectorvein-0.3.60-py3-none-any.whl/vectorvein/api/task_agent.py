"""Task Agent API functionality"""

from dataclasses import asdict
from typing import Any

from .models import (
    Agent,
    AgentListResponse,
    AgentTask,
    AgentTaskListResponse,
    AgentCycle,
    AgentCycleListResponse,
    TaskInfo,
    AgentDefinition,
    AgentSettings,
    AttachmentDetail,
    User,
    WaitingQuestion,
)


def _to_dict(obj):
    """Convert dataclass to dict, handling nested dataclasses"""
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return obj


def _create_agent_from_response(data: dict) -> Agent:
    """Create Agent object from API response, handling missing/extra fields"""
    # Create User object
    user_data = data.get("user", {})
    user = User(nickname=user_data.get("nickname", ""), avatar=user_data.get("avatar", ""))

    # Create Agent with all available fields, using defaults for missing ones
    return Agent(
        agent_id=data["agent_id"],
        user=user,
        name=data["name"],
        avatar=data.get("avatar"),
        description=data.get("description"),
        system_prompt=data["system_prompt"],
        default_model_name=data.get("default_model_name"),
        default_backend_type=data.get("default_backend_type"),
        default_max_cycles=data["default_max_cycles"],
        default_allow_interruption=data["default_allow_interruption"],
        default_use_workspace=data["default_use_workspace"],
        default_compress_memory_after_characters=data["default_compress_memory_after_characters"],
        shared=data["shared"],
        is_public=data["is_public"],
        used_count=data["used_count"],
        is_official=data.get("is_official", False),
        official_order=data.get("official_order", 0),
        is_owner=data["is_owner"],
        create_time=data["create_time"],
        update_time=data["update_time"],
        # Optional additional fields
        name_display=data.get("name_display"),
        avatar_display=data.get("avatar_display"),
        usage_hint=data.get("usage_hint"),
        default_agent_type=data.get("default_agent_type"),
        default_workspace_files=data.get("default_workspace_files"),
        default_sub_agent_ids=data.get("default_sub_agent_ids"),
        tags=data.get("tags"),
        available_workflows=data.get("available_workflows"),
        available_workflow_templates=data.get("available_workflow_templates"),
    )


def _create_agent_list_response(data: dict) -> AgentListResponse:
    """Create AgentListResponse from API response"""
    agents = [_create_agent_from_response(agent_data) for agent_data in data["agents"]]
    return AgentListResponse(
        agents=agents,
        total=data["total"],
        page=data["page"],
        page_size=data["page_size"],
        page_count=data["page_count"],
    )


def _create_agent_task_from_response(data: dict) -> AgentTask:
    """Create AgentTask object from API response, handling missing/extra fields"""
    # Create User object if present
    user = None
    if data.get("user"):
        user_data = data["user"]
        if isinstance(user_data, dict):
            user = User(nickname=user_data.get("nickname", ""), avatar=user_data.get("avatar", ""))
        # If user_data is not a dict (e.g., just an ID), create a minimal User object
        else:
            user = User(nickname="", avatar="")

    # Create WaitingQuestion if present
    waiting_question = None
    if data.get("waiting_question"):
        wq_data = data["waiting_question"]
        waiting_question = WaitingQuestion(cycle_id=wq_data["cycle_id"], tool_call_id=wq_data["tool_call_id"], question=wq_data["question"])

    return AgentTask(
        task_id=data["task_id"],
        user=user,
        source_agent_id=data.get("source_agent_id"),
        source_agent_name=data.get("source_agent_name"),
        source_agent_avatar=data.get("source_agent_avatar"),
        title=data.get("title"),
        task_info=data.get("task_info"),
        agent_definition=data.get("agent_definition"),
        status=data.get("status"),
        max_cycles=data.get("max_cycles"),
        workspace_id=data.get("workspace_id"),
        current_cycle_index=data.get("current_cycle_index"),
        result=data.get("result"),
        total_prompt_tokens=data.get("total_prompt_tokens"),
        total_completion_tokens=data.get("total_completion_tokens"),
        used_credits=data.get("used_credits"),
        error_reason_title=data.get("error_reason_title"),
        shared=data.get("shared"),
        is_public=data.get("is_public"),
        shared_meta=data.get("shared_meta"),
        create_time=data.get("create_time"),
        update_time=data.get("update_time"),
        complete_time=data.get("complete_time"),
        waiting_question=waiting_question,
        cycles=data.get("cycles"),
    )


def _create_agent_task_list_response(data: dict) -> AgentTaskListResponse:
    """Create AgentTaskListResponse from API response"""
    tasks = [_create_agent_task_from_response(task_data) for task_data in data["tasks"]]
    return AgentTaskListResponse(
        tasks=tasks,
        total=data["total"],
        page=data["page"],
        page_size=data["page_size"],
        page_count=data["page_count"],
    )


class TaskAgentSyncMixin:
    """Synchronous task agent API methods"""

    def create_agent(
        self,
        name: str,
        avatar: str | None = None,
        description: str | None = None,
        system_prompt: str = "You are a helpful assistant.",
        default_model_name: str | None = None,
        default_backend_type: str | None = None,
        default_max_cycles: int = 20,
        default_allow_interruption: bool = True,
        default_use_workspace: bool = True,
        default_compress_memory_after_characters: int = 128000,
        available_workflow_ids: list[str] | None = None,
        available_template_ids: list[str] | None = None,
        shared: bool = False,
        is_public: bool = False,
        is_official: bool = False,
        official_order: int = 0,
    ) -> Agent:
        """Create agent configuration

        Args:
            name: Agent name
            avatar: Agent avatar URL
            description: Agent description
            system_prompt: System prompt
            default_model_name: Default model name
            default_backend_type: Default backend type
            default_max_cycles: Default max cycles
            default_allow_interruption: Default allow interruption
            default_use_workspace: Default use workspace
            default_compress_memory_after_characters: Default compress memory threshold
            available_workflow_ids: Available workflow IDs
            available_template_ids: Available template IDs
            shared: Whether shared
            is_public: Whether public
            is_official: Whether official
            official_order: Official order

        Returns:
            Agent: Created agent configuration

        Raises:
            VectorVeinAPIError: Agent creation error
        """
        payload = {
            "name": name,
            "system_prompt": system_prompt,
            "default_max_cycles": default_max_cycles,
            "default_allow_interruption": default_allow_interruption,
            "default_use_workspace": default_use_workspace,
            "default_compress_memory_after_characters": default_compress_memory_after_characters,
            "shared": shared,
            "is_public": is_public,
            "is_official": is_official,
            "official_order": official_order,
        }

        if avatar:
            payload["avatar"] = avatar
        if description:
            payload["description"] = description
        if default_model_name:
            payload["default_model_name"] = default_model_name
        if default_backend_type:
            payload["default_backend_type"] = default_backend_type
        if available_workflow_ids:
            payload["available_workflow_ids"] = available_workflow_ids
        if available_template_ids:
            payload["available_template_ids"] = available_template_ids

        response = self._request("POST", "task-agent/agent/create", json=payload)
        return _create_agent_from_response(response["data"])

    def get_agent(self, agent_id: str) -> Agent:
        """Get agent configuration details

        Args:
            agent_id: Agent ID

        Returns:
            Agent: Agent configuration details

        Raises:
            VectorVeinAPIError: Agent not found or access denied
        """
        payload = {"agent_id": agent_id}
        response = self._request("POST", "task-agent/agent/get", json=payload)
        return _create_agent_from_response(response["data"])

    def list_agents(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
    ) -> AgentListResponse:
        """List agent configurations

        Args:
            page: Page number
            page_size: Page size
            search: Search keyword

        Returns:
            AgentListResponse: Agent list response

        Raises:
            VectorVeinAPIError: List error
        """
        payload = {"page": page, "page_size": page_size}
        if search:
            payload["search"] = search

        response = self._request("POST", "task-agent/agent/list", json=payload)
        return _create_agent_list_response(response["data"])

    def update_agent(
        self,
        agent_id: str,
        name: str | None = None,
        avatar: str | None = None,
        description: str | None = None,
        system_prompt: str | None = None,
        default_model_name: str | None = None,
        default_backend_type: str | None = None,
        default_max_cycles: int | None = None,
        default_allow_interruption: bool | None = None,
        default_use_workspace: bool | None = None,
        default_compress_memory_after_characters: int | None = None,
        available_workflow_ids: list[str] | None = None,
        available_template_ids: list[str] | None = None,
        shared: bool | None = None,
        is_public: bool | None = None,
        is_official: bool | None = None,
        official_order: int | None = None,
    ) -> Agent:
        """Update agent configuration

        Args:
            agent_id: Agent ID
            name: Agent name
            avatar: Agent avatar URL
            description: Agent description
            system_prompt: System prompt
            default_model_name: Default model name
            default_backend_type: Default backend type
            default_max_cycles: Default max cycles
            default_allow_interruption: Default allow interruption
            default_use_workspace: Default use workspace
            default_compress_memory_after_characters: Default compress memory threshold
            available_workflow_ids: Available workflow IDs
            available_template_ids: Available template IDs
            shared: Whether shared
            is_public: Whether public
            is_official: Whether official
            official_order: Official order

        Returns:
            Agent: Updated agent configuration

        Raises:
            VectorVeinAPIError: Update error
        """
        payload = {"agent_id": agent_id}

        if name is not None:
            payload["name"] = name
        if avatar is not None:
            payload["avatar"] = avatar
        if description is not None:
            payload["description"] = description
        if system_prompt is not None:
            payload["system_prompt"] = system_prompt
        if default_model_name is not None:
            payload["default_model_name"] = default_model_name
        if default_backend_type is not None:
            payload["default_backend_type"] = default_backend_type
        if default_max_cycles is not None:
            payload["default_max_cycles"] = default_max_cycles
        if default_allow_interruption is not None:
            payload["default_allow_interruption"] = default_allow_interruption
        if default_use_workspace is not None:
            payload["default_use_workspace"] = default_use_workspace
        if default_compress_memory_after_characters is not None:
            payload["default_compress_memory_after_characters"] = default_compress_memory_after_characters
        if available_workflow_ids is not None:
            payload["available_workflow_ids"] = available_workflow_ids
        if available_template_ids is not None:
            payload["available_template_ids"] = available_template_ids
        if shared is not None:
            payload["shared"] = shared
        if is_public is not None:
            payload["is_public"] = is_public
        if is_official is not None:
            payload["is_official"] = is_official
        if official_order is not None:
            payload["official_order"] = official_order

        response = self._request("POST", "task-agent/agent/update", json=payload)
        return _create_agent_from_response(response["data"])

    def delete_agent(self, agent_id: str) -> None:
        """Delete agent configuration

        Args:
            agent_id: Agent ID

        Raises:
            VectorVeinAPIError: Delete error
        """
        payload = {"agent_id": agent_id}
        self._request("POST", "task-agent/agent/delete", json=payload)

    def list_public_agents(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        official: bool | None = None,
    ) -> AgentListResponse:
        """List public agent configurations

        Args:
            page: Page number
            page_size: Page size
            search: Search keyword
            official: Filter official agents only

        Returns:
            AgentListResponse: Public agent list response

        Raises:
            VectorVeinAPIError: List error
        """
        payload = {"page": page, "page_size": page_size}
        if search:
            payload["search"] = search
        if official is not None:
            payload["official"] = official

        response = self._request("POST", "task-agent/agent/public-list", json=payload)
        return _create_agent_list_response(response["data"])

    def duplicate_agent(self, agent_id: str, add_templates: bool = False) -> Agent:
        """Duplicate agent configuration

        Args:
            agent_id: Source agent ID
            add_templates: Whether to add templates

        Returns:
            Agent: Duplicated agent configuration

        Raises:
            VectorVeinAPIError: Duplicate error
        """
        payload = {"agent_id": agent_id, "add_templates": add_templates}
        response = self._request("POST", "task-agent/agent/duplicate", json=payload)
        return _create_agent_from_response(response["data"])

    # Agent Task Management
    def create_agent_task(
        self,
        task_info: TaskInfo,
        agent_id_to_start: str | None = None,
        agent_definition_to_start: AgentDefinition | None = None,
        agent_settings: AgentSettings | None = None,
        max_cycles: int | None = None,
        title: str | None = None,
    ) -> AgentTask:
        """Create agent task

        Args:
            task_info: Task information
            agent_id_to_start: Agent ID to start
            agent_definition_to_start: Agent definition to start
            agent_settings: Agent settings override
            max_cycles: Max cycles override
            title: Custom task title

        Returns:
            AgentTask: Created agent task

        Raises:
            VectorVeinAPIError: Task creation error
        """
        payload = {"task_info": _to_dict(task_info)}

        if agent_id_to_start:
            payload["agent_id_to_start"] = agent_id_to_start
        if agent_definition_to_start:
            payload["agent_definition_to_start"] = _to_dict(agent_definition_to_start)
        if agent_settings:
            payload["agent_settings"] = _to_dict(agent_settings)
        if max_cycles is not None:
            payload["max_cycles"] = max_cycles
        if title:
            payload["title"] = title

        response = self._request("POST", "task-agent/agent-task/create", json=payload)
        return _create_agent_task_from_response(response["data"])

    def get_agent_task(self, task_id: str) -> AgentTask:
        """Get agent task details

        Args:
            task_id: Task ID

        Returns:
            AgentTask: Agent task details

        Raises:
            VectorVeinAPIError: Task not found or access denied
        """
        payload = {"task_id": task_id}
        response = self._request("POST", "task-agent/agent-task/get", json=payload)
        return _create_agent_task_from_response(response["data"])

    def list_agent_tasks(
        self,
        page: int = 1,
        page_size: int = 10,
        status: str | list[str] | None = None,
        agent_id: str | None = None,
        search: str | None = None,
    ) -> AgentTaskListResponse:
        """List agent tasks

        Args:
            page: Page number
            page_size: Page size
            status: Task status filter
            agent_id: Agent ID filter
            search: Search keyword

        Returns:
            AgentTaskListResponse: Agent task list response

        Raises:
            VectorVeinAPIError: List error
        """
        payload = {"page": page, "page_size": page_size}
        if status is not None:
            payload["status"] = status
        if agent_id:
            payload["agent_id"] = agent_id
        if search:
            payload["search"] = search

        response = self._request("POST", "task-agent/agent-task/list", json=payload)
        return _create_agent_task_list_response(response["data"])

    def respond_to_agent_task(self, task_id: str, tool_call_id: str, response_content: str) -> AgentTask:
        """Respond to agent task

        Args:
            task_id: Task ID
            tool_call_id: Tool call ID
            response_content: Response content

        Returns:
            AgentTask: Updated agent task

        Raises:
            VectorVeinAPIError: Response error
        """
        payload = {
            "task_id": task_id,
            "tool_call_id": tool_call_id,
            "response_content": response_content,
        }
        response = self._request("POST", "task-agent/agent-task/respond", json=payload)
        return _create_agent_task_from_response(response["data"])

    def update_agent_task_share(
        self,
        task_id: str,
        shared: bool | None = None,
        is_public: bool | None = None,
        shared_meta: dict[str, Any] | None = None,
    ) -> AgentTask:
        """Update agent task share status

        Args:
            task_id: Task ID
            shared: Whether shared
            is_public: Whether public
            shared_meta: Share metadata

        Returns:
            AgentTask: Updated agent task

        Raises:
            VectorVeinAPIError: Update error
        """
        payload = {"task_id": task_id}
        if shared is not None:
            payload["shared"] = shared
        if is_public is not None:
            payload["is_public"] = is_public
        if shared_meta is not None:
            payload["shared_meta"] = shared_meta

        response = self._request("POST", "task-agent/agent-task/update-share", json=payload)
        return _create_agent_task_from_response(response["data"])

    def get_shared_agent_task(self, task_id: str) -> AgentTask:
        """Get shared agent task details

        Args:
            task_id: Task ID

        Returns:
            AgentTask: Shared agent task details with cycles

        Raises:
            VectorVeinAPIError: Task not found or not shared
        """
        payload = {"task_id": task_id}
        response = self._request("POST", "task-agent/agent-task/get-shared", json=payload)
        return _create_agent_task_from_response(response["data"])

    def list_public_shared_agent_tasks(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        sort_field: str = "update_time",
        sort_order: str = "descend",
    ) -> AgentTaskListResponse:
        """List public shared agent tasks

        Args:
            page: Page number
            page_size: Page size
            search: Search keyword
            sort_field: Sort field
            sort_order: Sort order

        Returns:
            AgentTaskListResponse: Public shared agent task list response

        Raises:
            VectorVeinAPIError: List error
        """
        payload = {
            "page": page,
            "page_size": page_size,
            "sort_field": sort_field,
            "sort_order": sort_order,
        }
        if search:
            payload["search"] = search

        response = self._request("POST", "task-agent/agent-task/public-shared-list", json=payload)
        return _create_agent_task_list_response(response["data"])

    def continue_agent_task(
        self,
        task_id: str,
        message: str,
        attachments_detail: list[AttachmentDetail] | None = None,
    ) -> AgentTask:
        """Continue agent task

        Args:
            task_id: Task ID
            message: New message or instruction
            attachments_detail: Attachment details

        Returns:
            AgentTask: Updated agent task

        Raises:
            VectorVeinAPIError: Continue error
        """
        payload = {"task_id": task_id, "message": message}
        if attachments_detail:
            payload["attachments_detail"] = [_to_dict(att) for att in attachments_detail]

        response = self._request("POST", "task-agent/agent-task/continue-task", json=payload)
        return _create_agent_task_from_response(response["data"])

    def pause_agent_task(self, task_id: str) -> AgentTask:
        """Pause agent task

        Args:
            task_id: Task ID

        Returns:
            AgentTask: Updated agent task

        Raises:
            VectorVeinAPIError: Pause error
        """
        payload = {"task_id": task_id}
        response = self._request("POST", "task-agent/agent-task/pause-task", json=payload)
        return _create_agent_task_from_response(response["data"])

    def resume_agent_task(
        self,
        task_id: str,
        message: str | None = None,
        attachments_detail: list[AttachmentDetail] | None = None,
    ) -> AgentTask:
        """Resume agent task

        Args:
            task_id: Task ID
            message: Optional new message
            attachments_detail: Attachment details

        Returns:
            AgentTask: Updated agent task

        Raises:
            VectorVeinAPIError: Resume error
        """
        payload = {"task_id": task_id}
        if message:
            payload["message"] = message
        if attachments_detail:
            payload["attachments_detail"] = [_to_dict(att) for att in attachments_detail]

        response = self._request("POST", "task-agent/agent-task/resume-task", json=payload)
        return _create_agent_task_from_response(response["data"])

    def delete_agent_task(self, task_id: str) -> None:
        """Delete agent task

        Args:
            task_id: Task ID

        Raises:
            VectorVeinAPIError: Delete error
        """
        payload = {"task_id": task_id}
        self._request("POST", "task-agent/agent-task/delete", json=payload)

    # Agent Task Cycle Management
    def list_agent_cycles(
        self,
        task_id: str,
        cycle_index_offset: int = 0,
    ) -> AgentCycleListResponse:
        """List agent task cycles

        Args:
            task_id: Task ID
            cycle_index_offset: Cycle index offset

        Returns:
            AgentCycleListResponse: Agent cycle list response

        Raises:
            VectorVeinAPIError: List error
        """
        payload = {"task_id": task_id, "cycle_index_offset": cycle_index_offset}
        response = self._request("POST", "task-agent/agent-cycle/list", json=payload)
        return AgentCycleListResponse(**response["data"])

    def get_agent_cycle(self, cycle_id: str) -> AgentCycle:
        """Get agent cycle details

        Args:
            cycle_id: Cycle ID

        Returns:
            AgentCycle: Agent cycle details

        Raises:
            VectorVeinAPIError: Cycle not found or access denied
        """
        payload = {"cycle_id": cycle_id}
        response = self._request("POST", "task-agent/agent-cycle/get", json=payload)
        return AgentCycle(**response["data"])


class TaskAgentAsyncMixin:
    """Asynchronous task agent API methods"""

    # Agent Configuration Management
    async def create_agent(
        self,
        name: str,
        avatar: str | None = None,
        description: str | None = None,
        system_prompt: str = "You are a helpful assistant.",
        default_model_name: str | None = None,
        default_backend_type: str | None = None,
        default_max_cycles: int = 20,
        default_allow_interruption: bool = True,
        default_use_workspace: bool = True,
        default_compress_memory_after_characters: int = 128000,
        available_workflow_ids: list[str] | None = None,
        available_template_ids: list[str] | None = None,
        shared: bool = False,
        is_public: bool = False,
        is_official: bool = False,
        official_order: int = 0,
    ) -> Agent:
        """Async create agent configuration"""
        payload = {
            "name": name,
            "system_prompt": system_prompt,
            "default_max_cycles": default_max_cycles,
            "default_allow_interruption": default_allow_interruption,
            "default_use_workspace": default_use_workspace,
            "default_compress_memory_after_characters": default_compress_memory_after_characters,
            "shared": shared,
            "is_public": is_public,
            "is_official": is_official,
            "official_order": official_order,
        }

        if avatar:
            payload["avatar"] = avatar
        if description:
            payload["description"] = description
        if default_model_name:
            payload["default_model_name"] = default_model_name
        if default_backend_type:
            payload["default_backend_type"] = default_backend_type
        if available_workflow_ids:
            payload["available_workflow_ids"] = available_workflow_ids
        if available_template_ids:
            payload["available_template_ids"] = available_template_ids

        response = await self._request("POST", "task-agent/agent/create", json=payload)
        return _create_agent_from_response(response["data"])

    async def get_agent(self, agent_id: str) -> Agent:
        """Async get agent configuration details"""
        payload = {"agent_id": agent_id}
        response = await self._request("POST", "task-agent/agent/get", json=payload)
        return _create_agent_from_response(response["data"])

    async def list_agents(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
    ) -> AgentListResponse:
        """Async list agent configurations"""
        payload = {"page": page, "page_size": page_size}
        if search:
            payload["search"] = search

        response = await self._request("POST", "task-agent/agent/list", json=payload)
        return _create_agent_list_response(response["data"])

    async def update_agent(
        self,
        agent_id: str,
        name: str | None = None,
        avatar: str | None = None,
        description: str | None = None,
        system_prompt: str | None = None,
        default_model_name: str | None = None,
        default_backend_type: str | None = None,
        default_max_cycles: int | None = None,
        default_allow_interruption: bool | None = None,
        default_use_workspace: bool | None = None,
        default_compress_memory_after_characters: int | None = None,
        available_workflow_ids: list[str] | None = None,
        available_template_ids: list[str] | None = None,
        shared: bool | None = None,
        is_public: bool | None = None,
        is_official: bool | None = None,
        official_order: int | None = None,
    ) -> Agent:
        """Async update agent configuration"""
        payload = {"agent_id": agent_id}

        if name is not None:
            payload["name"] = name
        if avatar is not None:
            payload["avatar"] = avatar
        if description is not None:
            payload["description"] = description
        if system_prompt is not None:
            payload["system_prompt"] = system_prompt
        if default_model_name is not None:
            payload["default_model_name"] = default_model_name
        if default_backend_type is not None:
            payload["default_backend_type"] = default_backend_type
        if default_max_cycles is not None:
            payload["default_max_cycles"] = default_max_cycles
        if default_allow_interruption is not None:
            payload["default_allow_interruption"] = default_allow_interruption
        if default_use_workspace is not None:
            payload["default_use_workspace"] = default_use_workspace
        if default_compress_memory_after_characters is not None:
            payload["default_compress_memory_after_characters"] = default_compress_memory_after_characters
        if available_workflow_ids is not None:
            payload["available_workflow_ids"] = available_workflow_ids
        if available_template_ids is not None:
            payload["available_template_ids"] = available_template_ids
        if shared is not None:
            payload["shared"] = shared
        if is_public is not None:
            payload["is_public"] = is_public
        if is_official is not None:
            payload["is_official"] = is_official
        if official_order is not None:
            payload["official_order"] = official_order

        response = await self._request("POST", "task-agent/agent/update", json=payload)
        return _create_agent_from_response(response["data"])

    async def delete_agent(self, agent_id: str) -> None:
        """Async delete agent configuration"""
        payload = {"agent_id": agent_id}
        await self._request("POST", "task-agent/agent/delete", json=payload)

    async def list_public_agents(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        official: bool | None = None,
    ) -> AgentListResponse:
        """Async list public agent configurations"""
        payload = {"page": page, "page_size": page_size}
        if search:
            payload["search"] = search
        if official is not None:
            payload["official"] = official

        response = await self._request("POST", "task-agent/agent/public-list", json=payload)
        return _create_agent_list_response(response["data"])

    async def duplicate_agent(self, agent_id: str, add_templates: bool = False) -> Agent:
        """Async duplicate agent configuration"""
        payload = {"agent_id": agent_id, "add_templates": add_templates}
        response = await self._request("POST", "task-agent/agent/duplicate", json=payload)
        return _create_agent_from_response(response["data"])

    # Agent Task Management
    async def create_agent_task(
        self,
        task_info: TaskInfo,
        agent_id_to_start: str | None = None,
        agent_definition_to_start: AgentDefinition | None = None,
        agent_settings: AgentSettings | None = None,
        max_cycles: int | None = None,
        title: str | None = None,
    ) -> AgentTask:
        """Async create agent task"""
        payload = {"task_info": _to_dict(task_info)}

        if agent_id_to_start:
            payload["agent_id_to_start"] = agent_id_to_start
        if agent_definition_to_start:
            payload["agent_definition_to_start"] = _to_dict(agent_definition_to_start)
        if agent_settings:
            payload["agent_settings"] = _to_dict(agent_settings)
        if max_cycles is not None:
            payload["max_cycles"] = max_cycles
        if title:
            payload["title"] = title

        response = await self._request("POST", "task-agent/agent-task/create", json=payload)
        return _create_agent_task_from_response(response["data"])

    async def get_agent_task(self, task_id: str) -> AgentTask:
        """Async get agent task details"""
        payload = {"task_id": task_id}
        response = await self._request("POST", "task-agent/agent-task/get", json=payload)
        return _create_agent_task_from_response(response["data"])

    async def list_agent_tasks(
        self,
        page: int = 1,
        page_size: int = 10,
        status: str | list[str] | None = None,
        agent_id: str | None = None,
        search: str | None = None,
    ) -> AgentTaskListResponse:
        """Async list agent tasks"""
        payload = {"page": page, "page_size": page_size}
        if status is not None:
            payload["status"] = status
        if agent_id:
            payload["agent_id"] = agent_id
        if search:
            payload["search"] = search

        response = await self._request("POST", "task-agent/agent-task/list", json=payload)
        return _create_agent_task_list_response(response["data"])

    async def respond_to_agent_task(self, task_id: str, tool_call_id: str, response_content: str) -> AgentTask:
        """Async respond to agent task"""
        payload = {
            "task_id": task_id,
            "tool_call_id": tool_call_id,
            "response_content": response_content,
        }
        response = await self._request("POST", "task-agent/agent-task/respond", json=payload)
        return _create_agent_task_from_response(response["data"])

    async def update_agent_task_share(
        self,
        task_id: str,
        shared: bool | None = None,
        is_public: bool | None = None,
        shared_meta: dict[str, Any] | None = None,
    ) -> AgentTask:
        """Async update agent task share status"""
        payload = {"task_id": task_id}
        if shared is not None:
            payload["shared"] = shared
        if is_public is not None:
            payload["is_public"] = is_public
        if shared_meta is not None:
            payload["shared_meta"] = shared_meta

        response = await self._request("POST", "task-agent/agent-task/update-share", json=payload)
        return _create_agent_task_from_response(response["data"])

    async def get_shared_agent_task(self, task_id: str) -> AgentTask:
        """Async get shared agent task details"""
        payload = {"task_id": task_id}
        response = await self._request("POST", "task-agent/agent-task/get-shared", json=payload)
        return _create_agent_task_from_response(response["data"])

    async def list_public_shared_agent_tasks(
        self,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        sort_field: str = "update_time",
        sort_order: str = "descend",
    ) -> AgentTaskListResponse:
        """Async list public shared agent tasks"""
        payload = {
            "page": page,
            "page_size": page_size,
            "sort_field": sort_field,
            "sort_order": sort_order,
        }
        if search:
            payload["search"] = search

        response = await self._request("POST", "task-agent/agent-task/public-shared-list", json=payload)
        return _create_agent_task_list_response(response["data"])

    async def continue_agent_task(
        self,
        task_id: str,
        message: str,
        attachments_detail: list[AttachmentDetail] | None = None,
    ) -> AgentTask:
        """Async continue agent task"""
        payload = {"task_id": task_id, "message": message}
        if attachments_detail:
            payload["attachments_detail"] = [_to_dict(att) for att in attachments_detail]

        response = await self._request("POST", "task-agent/agent-task/continue-task", json=payload)
        return _create_agent_task_from_response(response["data"])

    async def pause_agent_task(self, task_id: str) -> AgentTask:
        """Async pause agent task"""
        payload = {"task_id": task_id}
        response = await self._request("POST", "task-agent/agent-task/pause-task", json=payload)
        return _create_agent_task_from_response(response["data"])

    async def resume_agent_task(
        self,
        task_id: str,
        message: str | None = None,
        attachments_detail: list[AttachmentDetail] | None = None,
    ) -> AgentTask:
        """Async resume agent task"""
        payload = {"task_id": task_id}
        if message:
            payload["message"] = message
        if attachments_detail:
            payload["attachments_detail"] = [_to_dict(att) for att in attachments_detail]

        response = await self._request("POST", "task-agent/agent-task/resume-task", json=payload)
        return _create_agent_task_from_response(response["data"])

    async def delete_agent_task(self, task_id: str) -> None:
        """Async delete agent task"""
        payload = {"task_id": task_id}
        await self._request("POST", "task-agent/agent-task/delete", json=payload)

    # Agent Task Cycle Management
    async def list_agent_cycles(
        self,
        task_id: str,
        cycle_index_offset: int = 0,
    ) -> AgentCycleListResponse:
        """Async list agent task cycles"""
        payload = {"task_id": task_id, "cycle_index_offset": cycle_index_offset}
        response = await self._request("POST", "task-agent/agent-cycle/list", json=payload)
        return AgentCycleListResponse(**response["data"])

    async def get_agent_cycle(self, cycle_id: str) -> AgentCycle:
        """Async get agent cycle details"""
        payload = {"cycle_id": cycle_id}
        response = await self._request("POST", "task-agent/agent-cycle/get", json=payload)
        return AgentCycle(**response["data"])
