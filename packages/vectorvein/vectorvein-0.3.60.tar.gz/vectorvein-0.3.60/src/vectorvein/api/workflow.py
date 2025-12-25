"""Workflow API functionality"""

import time
import asyncio
from typing import Any, Literal, overload

from .exceptions import WorkflowError, TimeoutError, VectorVeinAPIError
from .models import (
    WorkflowInputField,
    WorkflowOutput,
    WorkflowRunResult,
    Workflow,
    WorkflowTag,
)


class WorkflowMixin:
    """Workflow API mixin with shared logic"""

    @staticmethod
    def _create_workflow_response(response: dict[str, Any]) -> Workflow:
        """Parse workflow creation response"""
        workflow_tags = []
        if response["data"].get("tags"):
            for tag_data in response["data"]["tags"]:
                if isinstance(tag_data, dict):
                    workflow_tags.append(WorkflowTag(**tag_data))

        return Workflow(
            wid=response["data"]["wid"],
            title=response["data"]["title"],
            brief=response["data"]["brief"],
            data=response["data"]["data"],
            language=response["data"]["language"],
            images=response["data"]["images"],
            tags=workflow_tags,
            source_workflow=response["data"].get("source_workflow"),
            tool_call_data=response["data"].get("tool_call_data"),
            create_time=response["data"].get("create_time"),
            update_time=response["data"].get("update_time"),
        )

    @staticmethod
    def _parse_workflow_result(response: dict[str, Any], rid: str) -> WorkflowRunResult:
        """Parse workflow run result"""
        if response["status"] in [200, 202]:
            return WorkflowRunResult(
                rid=rid,
                status=response["status"],
                msg=response["msg"],
                data=[WorkflowOutput(**output) for output in response["data"]],
            )
        else:
            raise WorkflowError(f"Workflow execution failed: {response['msg']}")


class WorkflowSyncMixin(WorkflowMixin):
    """Synchronous workflow API methods"""

    @overload
    def run_workflow(
        self,
        wid: str,
        input_fields: list[WorkflowInputField],
        output_scope: Literal["all", "output_fields_only"] = "output_fields_only",
        wait_for_completion: Literal[False] = False,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        timeout: int = 30,
    ) -> str: ...

    @overload
    def run_workflow(
        self,
        wid: str,
        input_fields: list[WorkflowInputField],
        output_scope: Literal["all", "output_fields_only"] = "output_fields_only",
        wait_for_completion: Literal[True] = True,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        timeout: int = 30,
    ) -> WorkflowRunResult: ...

    def run_workflow(
        self,
        wid: str,
        input_fields: list[WorkflowInputField],
        output_scope: Literal["all", "output_fields_only"] = "output_fields_only",
        wait_for_completion: bool = False,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        timeout: int = 30,
    ) -> str | WorkflowRunResult:
        """Run workflow

        Args:
            wid: Workflow ID
            input_fields: Input fields list
            output_scope: Output scope, optional values: 'all' or 'output_fields_only'
            wait_for_completion: Whether to wait for completion
            api_key_type: Key type, optional values: 'WORKFLOW' or 'VAPP'
            timeout: Timeout (seconds)

        Returns:
            Union[str, WorkflowRunResult]: Workflow run ID or run result

        Raises:
            WorkflowError: Workflow run error
            TimeoutError: Timeout error
        """
        payload = {
            "wid": wid,
            "output_scope": output_scope,
            "wait_for_completion": wait_for_completion,
            "input_fields": [{"node_id": field.node_id, "field_name": field.field_name, "value": field.value} for field in input_fields],
        }

        result = self._request("POST", "workflow/run", json=payload, api_key_type=api_key_type)

        if not wait_for_completion:
            return result["data"]["rid"]

        rid = result.get("rid") or (isinstance(result["data"], dict) and result["data"].get("rid")) or ""
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Workflow execution timed out after {timeout} seconds")

            if api_key_type == "WORKFLOW":
                result = self.check_workflow_status(rid, api_key_type=api_key_type)
            else:
                result = self.check_workflow_status(rid, wid=wid, api_key_type=api_key_type)
            if result.status == 200:
                return result
            elif result.status == 500:
                raise WorkflowError(f"Workflow execution failed: {result.msg}")

            time.sleep(5)

    @overload
    def check_workflow_status(self, rid: str, wid: str | None = None, api_key_type: Literal["WORKFLOW"] = "WORKFLOW") -> WorkflowRunResult: ...

    @overload
    def check_workflow_status(self, rid: str, wid: str, api_key_type: Literal["VAPP"] = "VAPP") -> WorkflowRunResult: ...

    def check_workflow_status(self, rid: str, wid: str | None = None, api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW") -> WorkflowRunResult:
        """Check workflow run status

        Args:
            rid: Workflow run record ID
            wid: Workflow ID, not required, required when api_key_type is 'VAPP'
            api_key_type: Key type, optional values: 'WORKFLOW' or 'VAPP'

        Returns:
            WorkflowRunResult: Workflow run result

        Raises:
            VectorVeinAPIError: Workflow error
        """
        payload = {"rid": rid}
        if api_key_type == "VAPP" and not wid:
            raise VectorVeinAPIError("Workflow ID cannot be empty when api_key_type is 'VAPP'")
        if wid:
            payload["wid"] = wid
        response = self._request("POST", "workflow/check-status", json=payload, api_key_type=api_key_type)
        return self._parse_workflow_result(response, rid)

    def create_workflow(
        self,
        title: str = "New workflow",
        brief: str = "",
        images: list[str] | None = None,
        tags: list[dict[str, str]] | None = None,
        data: dict[str, Any] | None = None,
        language: str = "zh-CN",
        tool_call_data: dict[str, Any] | None = None,
        source_workflow_wid: str | None = None,
    ) -> Workflow:
        """Create a new workflow

        Args:
            title: Workflow title, default is "New workflow"
            brief: Workflow brief description
            images: List of image URLs
            tags: List of workflow tags, each tag should have 'tid' field
            data: Workflow data containing nodes and edges, default is {"nodes": [], "edges": []}
            language: Workflow language, default is "zh-CN"
            tool_call_data: Tool call data
            source_workflow_wid: Source workflow ID for copying

        Returns:
            Workflow: Created workflow information

        Raises:
            VectorVeinAPIError: Workflow creation error
        """
        payload = {
            "title": title,
            "brief": brief,
            "images": images or [],
            "tags": tags or [],
            "data": data or {"nodes": [], "edges": []},
            "language": language,
            "tool_call_data": tool_call_data or {},
        }

        if source_workflow_wid:
            payload["source_workflow_wid"] = source_workflow_wid

        response = self._request("POST", "workflow/create", json=payload)
        return self._create_workflow_response(response)


class WorkflowAsyncMixin(WorkflowMixin):
    """Asynchronous workflow API methods"""

    @overload
    async def run_workflow(
        self,
        wid: str,
        input_fields: list[WorkflowInputField],
        output_scope: Literal["all", "output_fields_only"] = "output_fields_only",
        wait_for_completion: Literal[False] = False,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        timeout: int = 30,
    ) -> str: ...

    @overload
    async def run_workflow(
        self,
        wid: str,
        input_fields: list[WorkflowInputField],
        output_scope: Literal["all", "output_fields_only"] = "output_fields_only",
        wait_for_completion: Literal[True] = True,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        timeout: int = 30,
    ) -> WorkflowRunResult: ...

    async def run_workflow(
        self,
        wid: str,
        input_fields: list[WorkflowInputField],
        output_scope: Literal["all", "output_fields_only"] = "output_fields_only",
        wait_for_completion: bool = False,
        api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW",
        timeout: int = 30,
    ) -> str | WorkflowRunResult:
        """Async run workflow

        Args:
            wid: Workflow ID
            input_fields: Input field list
            output_scope: Output scope, optional values: 'all' or 'output_fields_only'
            wait_for_completion: Whether to wait for completion
            api_key_type: Key type, optional values: 'WORKFLOW' or 'VAPP'
            timeout: Timeout (seconds)

        Returns:
            Union[str, WorkflowRunResult]: Workflow run ID or run result

        Raises:
            WorkflowError: Workflow run error
            TimeoutError: Timeout error
        """
        payload = {
            "wid": wid,
            "output_scope": output_scope,
            "wait_for_completion": wait_for_completion,
            "input_fields": [{"node_id": field.node_id, "field_name": field.field_name, "value": field.value} for field in input_fields],
        }

        result = await self._request("POST", "workflow/run", json=payload, api_key_type=api_key_type)

        if not wait_for_completion:
            return result["data"]["rid"]

        rid = result.get("rid") or (isinstance(result["data"], dict) and result["data"].get("rid")) or ""
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Workflow execution timed out after {timeout} seconds")

            if api_key_type == "WORKFLOW":
                result = await self.check_workflow_status(rid, api_key_type=api_key_type)
            else:
                result = await self.check_workflow_status(rid, wid=wid, api_key_type=api_key_type)
            if result.status == 200:
                return result
            elif result.status == 500:
                raise WorkflowError(f"Workflow execution failed: {result.msg}")

            await asyncio.sleep(5)

    @overload
    async def check_workflow_status(self, rid: str, wid: str | None = None, api_key_type: Literal["WORKFLOW"] = "WORKFLOW") -> WorkflowRunResult: ...

    @overload
    async def check_workflow_status(self, rid: str, wid: str, api_key_type: Literal["VAPP"] = "VAPP") -> WorkflowRunResult: ...

    async def check_workflow_status(self, rid: str, wid: str | None = None, api_key_type: Literal["WORKFLOW", "VAPP"] = "WORKFLOW") -> WorkflowRunResult:
        """Async check workflow run status

        Args:
            rid: Workflow run record ID
            wid: Workflow ID, required when api_key_type is 'VAPP'
            api_key_type: Key type, optional values: 'WORKFLOW' or 'VAPP'

        Raises:
            VectorVeinAPIError: Workflow error
        """
        payload = {"rid": rid}
        if api_key_type == "VAPP" and not wid:
            raise VectorVeinAPIError("Workflow ID cannot be empty when api_key_type is 'VAPP'")
        if wid:
            payload["wid"] = wid
        response = await self._request("POST", "workflow/check-status", json=payload, api_key_type=api_key_type)
        return self._parse_workflow_result(response, rid)

    async def create_workflow(
        self,
        title: str = "New workflow",
        brief: str = "",
        images: list[str] | None = None,
        tags: list[dict[str, str]] | None = None,
        data: dict[str, Any] | None = None,
        language: str = "zh-CN",
        tool_call_data: dict[str, Any] | None = None,
        source_workflow_wid: str | None = None,
    ) -> Workflow:
        """Async create a new workflow

        Args:
            title: Workflow title, default is "New workflow"
            brief: Workflow brief description
            images: List of image URLs
            tags: List of workflow tags, each tag should have 'tid' field
            data: Workflow data containing nodes and edges, default is {"nodes": [], "edges": []}
            language: Workflow language, default is "zh-CN"
            tool_call_data: Tool call data
            source_workflow_wid: Source workflow ID for copying

        Returns:
            Workflow: Created workflow information

        Raises:
            VectorVeinAPIError: Workflow creation error
        """
        payload = {
            "title": title,
            "brief": brief,
            "images": images or [],
            "tags": tags or [],
            "data": data or {"nodes": [], "edges": []},
            "language": language,
            "tool_call_data": tool_call_data or {},
        }

        if source_workflow_wid:
            payload["source_workflow_wid"] = source_workflow_wid

        response = await self._request("POST", "workflow/create", json=payload)
        return self._create_workflow_response(response)
