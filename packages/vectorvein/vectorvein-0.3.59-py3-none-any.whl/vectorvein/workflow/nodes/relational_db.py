from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


class GetTableInfo(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="GetTableInfo",
            category="relationalDb",
            task_name="relational_db.get_table_info",
            node_id=id,
            ports={
                "database": InputPort(
                    name="database",
                    port_type=PortType.SELECT,
                    value="",
                    options=[],
                ),
                "tables": InputPort(
                    name="tables",
                    port_type=PortType.SELECT,
                    value=[],
                    options=[],
                ),
                "output_sql": OutputPort(name="output_sql", has_tooltip=True),
                "output_json": OutputPort(name="output_json"),
            },
        )


class RunSql(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="RunSql",
            category="relationalDb",
            task_name="relational_db.run_sql",
            node_id=id,
            ports={
                "database": InputPort(
                    name="database",
                    port_type=PortType.SELECT,
                    value="",
                    options=[],
                ),
                "sql": InputPort(
                    name="sql",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "read_only": InputPort(
                    name="read_only",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                ),
                "include_column_names": InputPort(
                    name="include_column_names",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                    has_tooltip=True,
                    condition="return fieldsData.output_type.value == 'list'",
                    condition_python=lambda ports: ports["output_type"].value == "list",
                ),
                "max_count": InputPort(
                    name="max_count",
                    port_type=PortType.NUMBER,
                    value=100,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="csv",
                    options=[{"value": "list", "label": "list"}, {"value": "markdown", "label": "markdown"}, {"value": "csv", "label": "csv"}],
                ),
                "output": OutputPort(),
            },
        )


class SmartQuery(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="SmartQuery",
            category="relationalDb",
            task_name="relational_db.smart_query",
            node_id=id,
            ports={
                "query": InputPort(
                    name="query",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "model": InputPort(
                    name="model",
                    port_type=PortType.SELECT,
                    value="OpenAI/gpt-4o-mini",
                    options=[],
                ),
                "database": InputPort(
                    name="database",
                    port_type=PortType.SELECT,
                    value="",
                    options=[],
                ),
                "tables": InputPort(
                    name="tables",
                    port_type=PortType.SELECT,
                    value=[],
                    options=[],
                ),
                "use_sample_data": InputPort(
                    name="use_sample_data",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                ),
                "include_column_names": InputPort(
                    name="include_column_names",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                ),
                "max_count": InputPort(
                    name="max_count",
                    port_type=PortType.NUMBER,
                    value=100,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="csv",
                    options=[{"value": "list", "label": "list"}, {"value": "markdown", "label": "markdown"}, {"value": "csv", "label": "csv"}],
                ),
                "output": OutputPort(),
                "output_query_sql": OutputPort(name="output_query_sql"),
            },
        )
