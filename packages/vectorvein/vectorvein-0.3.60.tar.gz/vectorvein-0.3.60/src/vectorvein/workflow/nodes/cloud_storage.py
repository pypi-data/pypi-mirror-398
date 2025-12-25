from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


class CloudStorageManageFile(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="CloudStorageManageFile",
            category="cloudStorage",
            task_name="cloud_storage.cloud_storage_manage_file",
            node_id=id,
            ports={
                "action": InputPort(
                    name="action",
                    port_type=PortType.SELECT,
                    value="move",
                    options=[
                        {"label": "move", "value": "move"},
                        {"label": "rename", "value": "rename"},
                        {"label": "delete", "value": "delete"},
                        {"label": "set_tags", "value": "set_tags"},
                        {"label": "add_tags", "value": "add_tags"},
                        {"label": "remove_tags", "value": "remove_tags"},
                        {"label": "clear_tags", "value": "clear_tags"},
                    ],
                    show=True,
                ),
                "multiple": InputPort(
                    name="multiple",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "file_path": InputPort(
                    name="file_path",
                    port_type=PortType.INPUT,
                    value="",
                    required=False,
                    show=True,
                ),
                "file_paths": InputPort(
                    name="file_paths",
                    port_type=PortType.LIST,
                    value=[],
                    required=False,
                ),
                "dest_folder_path": InputPort(
                    name="dest_folder_path",
                    port_type=PortType.INPUT,
                    value="",
                    required=False,
                ),
                "new_name": InputPort(
                    name="new_name",
                    port_type=PortType.INPUT,
                    value="",
                    required=False,
                ),
                "all_versions": InputPort(
                    name="all_versions",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "cloud_tag_ids": InputPort(
                    name="cloud_tag_ids",
                    port_type=PortType.LIST,
                    value=[],
                    required=False,
                ),
                "apply_to_all_versions": InputPort(
                    name="apply_to_all_versions",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class CloudStorageReadFile(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="CloudStorageReadFile",
            category="cloudStorage",
            task_name="cloud_storage.cloud_storage_read_file",
            node_id=id,
            ports={
                "file_path": InputPort(
                    name="file_path",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                    has_tooltip=True,
                ),
                "output": OutputPort(),
            },
        )


class CloudStorageSemanticSearch(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="CloudStorageSemanticSearch",
            category="cloudStorage",
            task_name="cloud_storage.cloud_storage_semantic_search",
            node_id=id,
            ports={
                "query": InputPort(
                    name="query",
                    port_type=PortType.TEXTAREA,
                    value="",
                    show=True,
                ),
                "search_mode": InputPort(
                    name="search_mode",
                    port_type=PortType.SELECT,
                    value="hybrid",
                    options=[{"label": "hybrid", "value": "hybrid"}, {"label": "vector", "value": "vector"}, {"label": "bm25", "value": "bm25"}],
                    required=False,
                ),
                "limit": InputPort(
                    name="limit",
                    port_type=PortType.NUMBER,
                    value=10,
                    required=False,
                    min=1,
                    max=50,
                ),
                "file_multiple": InputPort(
                    name="file_multiple",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "file_path": InputPort(
                    name="file_path",
                    port_type=PortType.INPUT,
                    value="",
                    required=False,
                ),
                "file_paths": InputPort(
                    name="file_paths",
                    port_type=PortType.LIST,
                    value=[],
                    required=False,
                ),
                "folder_multiple": InputPort(
                    name="folder_multiple",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "folder_path": InputPort(
                    name="folder_path",
                    port_type=PortType.INPUT,
                    value="",
                    required=False,
                ),
                "folder_paths": InputPort(
                    name="folder_paths",
                    port_type=PortType.LIST,
                    value=[],
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class CloudStorageUploadFile(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="CloudStorageUploadFile",
            category="cloudStorage",
            task_name="cloud_storage.cloud_storage_upload_file",
            node_id=id,
            ports={
                "file_path": InputPort(
                    name="file_path",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                    has_tooltip=True,
                ),
                "file_content": InputPort(
                    name="file_content",
                    port_type=PortType.TEXTAREA,
                    value="",
                    show=True,
                ),
            },
        )
