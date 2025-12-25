from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


class AddData(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="AddData",
            category="vectorDb",
            task_name="vector_db.add_data",
            node_id=id,
            ports={
                "text": InputPort(
                    name="text",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "content_title": InputPort(
                    name="content_title",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "source_url": InputPort(
                    name="source_url",
                    port_type=PortType.INPUT,
                    value="",
                    required=False,
                ),
                "database": InputPort(
                    name="database",
                    port_type=PortType.SELECT,
                    value="",
                    options=[],
                ),
                "data_type": InputPort(
                    name="data_type",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "TEXT", "label": "Text"}],
                ),
                "split_method": InputPort(
                    name="split_method",
                    port_type=PortType.SELECT,
                    value="general",
                    options=[
                        {"value": "general", "label": "general"},
                        {"value": "delimiter", "label": "delimiter"},
                        {"value": "markdown", "label": "markdown"},
                        {"value": "table", "label": "table"},
                    ],
                    condition="return fieldsData.data_type.value == 'text'",
                    condition_python=lambda ports: ports["data_type"].value == "text",
                ),
                "chunk_length": InputPort(
                    name="chunk_length",
                    port_type=PortType.NUMBER,
                    value=500,
                    condition="return ['general', 'markdown'].includes(fieldsData.split_method.value)",
                    condition_python=lambda ports: ports["split_method"].value in ["general", "markdown"],
                ),
                "chunk_overlap": InputPort(
                    name="chunk_overlap",
                    port_type=PortType.NUMBER,
                    value=30,
                    condition="return ['general', 'markdown'].includes(fieldsData.split_method.value)",
                    condition_python=lambda ports: ports["split_method"].value in ["general", "markdown"],
                ),
                "delimiter": InputPort(
                    name="delimiter",
                    port_type=PortType.INPUT,
                    value="\\n",
                    required=False,
                    condition="return fieldsData.split_method.value == 'delimiter'",
                    condition_python=lambda ports: ports["split_method"].value == "delimiter",
                ),
                "remove_url_and_email": InputPort(
                    name="remove_url_and_email",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                ),
                "wait_for_processing": InputPort(
                    name="wait_for_processing",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "object_id": OutputPort(name="object_id"),
            },
        )


class DeleteData(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="DeleteData",
            category="vectorDb",
            task_name="vector_db.delete_data",
            node_id=id,
            ports={
                "object_id": InputPort(
                    name="object_id",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "database": InputPort(
                    name="database",
                    port_type=PortType.SELECT,
                    value="",
                    options=[],
                ),
                "delete_success": OutputPort(name="delete_success"),
            },
        )


class Search(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Search",
            category="vectorDb",
            task_name="vector_db.search_data",
            node_id=id,
            ports={
                "search_text": InputPort(
                    name="search_text",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "data_type": InputPort(
                    name="data_type",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}],
                ),
                "database": InputPort(
                    name="database",
                    port_type=PortType.SELECT,
                    value="",
                    options=[],
                    show=True,
                ),
                "count": InputPort(
                    name="count",
                    port_type=PortType.NUMBER,
                    value=5,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}, {"value": "list", "label": "List"}],
                ),
                "output": OutputPort(),
            },
        )
