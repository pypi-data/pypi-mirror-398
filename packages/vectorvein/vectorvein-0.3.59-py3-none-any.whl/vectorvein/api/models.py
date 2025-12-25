"""VectorVein API data model definitions"""

from dataclasses import dataclass
from typing import Any


@dataclass
class VApp:
    """VApp information"""

    app_id: str
    title: str
    description: str
    info: dict[str, Any]
    images: list[str]


@dataclass
class AccessKey:
    """Access key information"""

    access_key: str
    access_key_type: str  # O: one-time, M: multiple, L: long-term
    use_count: int
    max_use_count: int | None
    max_credits: int | None
    used_credits: int
    v_app: VApp | None
    v_apps: list[VApp]
    records: list[Any]
    status: str  # AC: valid, IN: invalid, EX: expired, US: used
    access_scope: str  # S: single application, M: multiple applications
    description: str
    create_time: str
    expire_time: str
    last_use_time: str | None


@dataclass
class WorkflowInputField:
    """Workflow input field"""

    node_id: str
    field_name: str
    value: Any


@dataclass
class WorkflowOutput:
    """Workflow output result"""

    type: str
    title: str
    value: Any


@dataclass
class WorkflowRunResult:
    """Workflow run result"""

    rid: str
    status: int
    msg: str
    data: list[WorkflowOutput]


@dataclass
class AccessKeyListResponse:
    """Access key list response"""

    access_keys: list[AccessKey]
    total: int
    page_size: int
    page: int


@dataclass
class WorkflowTag:
    """Workflow tag"""

    tid: str
    name: str


@dataclass
class Workflow:
    """Workflow information"""

    wid: str
    title: str
    brief: str
    data: dict[str, Any]
    language: str
    images: list[str]
    tags: list[WorkflowTag]
    source_workflow: str | None = None
    tool_call_data: dict[str, Any] | None = None
    create_time: str | None = None
    update_time: str | None = None


@dataclass
class WorkflowCreateRequest:
    """Workflow creation request data"""

    title: str = "New workflow"
    brief: str = ""
    images: list[str] | None = None
    tags: list[dict[str, str]] | None = None
    data: dict[str, Any] | None = None
    language: str = "zh-CN"
    tool_call_data: dict[str, Any] | None = None
    source_workflow_wid: str | None = None


# File Upload Models
@dataclass
class FileUploadResult:
    """File upload result"""

    oss_path: str
    original_filename: str
    file_size: int
    content_type: str


# Task Agent Models
@dataclass
class AttachmentDetail:
    """Attachment detail"""

    name: str
    url: str


@dataclass
class OssAttachmentDetail:
    """Attachment detail"""

    name: str
    oss_key: str


@dataclass
class TaskInfo:
    """Task information"""

    text: str
    attachments_detail: list[AttachmentDetail | OssAttachmentDetail] | None = None
    model_preference: str = "default"  # default, high_performance, low_cost, custom
    custom_backend_type: str | None = None
    custom_model_name: str | None = None


@dataclass
class AgentDefinition:
    """Agent definition"""

    system_prompt: str
    model_name: str
    backend_type: str
    allow_interruption: bool
    use_workspace: bool
    compress_memory_after_characters: int
    tools: list[dict[str, Any]]


@dataclass
class AgentSettings:
    """Agent settings override"""

    model_name: str | None = None
    backend_type: str | None = None
    use_workspace: bool | None = None
    allow_interruption: bool | None = None
    compress_memory_after_characters: int | None = None


@dataclass
class User:
    """User information"""

    nickname: str
    avatar: str


@dataclass
class Agent:
    """Agent configuration"""

    agent_id: str
    user: User
    name: str
    avatar: str | None
    description: str | None
    system_prompt: str
    default_model_name: str | None
    default_backend_type: str | None
    default_max_cycles: int
    default_allow_interruption: bool
    default_use_workspace: bool
    default_compress_memory_after_characters: int
    shared: bool
    is_public: bool
    used_count: int
    is_official: bool
    official_order: int
    is_owner: bool
    create_time: str
    update_time: str
    # Additional fields that may be present in API responses
    name_display: str | None = None
    avatar_display: str | None = None
    usage_hint: dict[str, Any] | None = None
    default_agent_type: str | None = None
    default_workspace_files: list[str] | None = None
    default_sub_agent_ids: list[str] | None = None
    tags: list[str] | None = None
    available_workflows: list[str] | None = None
    available_workflow_templates: list[str] | None = None


@dataclass
class AgentListResponse:
    """Agent list response"""

    agents: list[Agent]
    total: int
    page: int
    page_size: int
    page_count: int


@dataclass
class WaitingQuestion:
    """Waiting question information"""

    cycle_id: str
    tool_call_id: str
    question: str


@dataclass
class AgentTask:
    """Agent task"""

    task_id: str
    user: User | None = None
    source_agent_id: str | None = None
    source_agent_name: str | None = None
    source_agent_avatar: str | None = None
    title: str | None = None
    task_info: dict[str, Any] | None = None
    agent_definition: dict[str, Any] | None = None
    status: str | None = None
    max_cycles: int | None = None
    workspace_id: str | None = None
    current_cycle_index: int | None = None
    result: str | None = None
    total_prompt_tokens: int | None = None
    total_completion_tokens: int | None = None
    used_credits: int | None = None
    error_reason_title: str | None = None
    shared: bool | None = None
    is_public: bool | None = None
    shared_meta: dict[str, Any] | None = None
    create_time: str | None = None
    update_time: str | None = None
    complete_time: str | None = None
    waiting_question: WaitingQuestion | None = None
    cycles: list[Any] | None = None


@dataclass
class AgentTaskListResponse:
    """Agent task list response"""

    tasks: list[AgentTask]
    total: int
    page: int
    page_size: int
    page_count: int


@dataclass
class AgentCycle:
    """Agent task cycle"""

    cycle_id: str
    agent_task_id: str
    cycle_index: int
    status: str
    title: str | None
    messages: list[dict[str, Any]] | None = None
    ai_response: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_responses: list[dict[str, Any]] | None = None
    memory_compressed: bool | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    used_credits: int | None = None
    start_time: str | None = None
    complete_time: str | None = None


@dataclass
class AgentCycleListResponse:
    """Agent cycle list response"""

    cycles: list[AgentCycle]
    total: int


# Agent Workspace Models
@dataclass
class WorkspaceFile:
    """Workspace file information"""

    key: str
    size: int
    etag: str
    last_modified: str


@dataclass
class WorkspaceFileListResponse:
    """Workspace file list response"""

    files: list[WorkspaceFile] | dict[str, Any]  # Can be list or tree structure
    tree_view: bool


@dataclass
class WorkspaceFileContent:
    """Workspace file content"""

    content: str
    file_info: WorkspaceFile
    file_path: str
    start_line: int | None = None
    end_line: int | None = None
    meta_data: dict[str, Any] | None = None
    download_url: str | None = None


@dataclass
class AgentWorkspace:
    """Agent workspace"""

    workspace_id: str
    agent_task_id: str
    user: User
    oss_bucket: str
    base_storage_path: str
    created_at: str
    last_accessed: str
    latest_files: list[WorkspaceFile]
    file_count: int


@dataclass
class AgentWorkspaceListResponse:
    """Agent workspace list response"""

    workspaces: list[AgentWorkspace]
    total: int
    page: int
    page_size: int
    page_count: int
