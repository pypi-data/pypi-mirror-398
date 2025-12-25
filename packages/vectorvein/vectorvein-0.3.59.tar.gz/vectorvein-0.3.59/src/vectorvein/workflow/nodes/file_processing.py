from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


class DocumentConvert(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="DocumentConvert",
            category="fileProcessing",
            task_name="file_processing.document_convert",
            node_id=id,
            ports={
                "files": InputPort(
                    name="files",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    multiple=True,
                    support_file_types=[".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".rtf"],
                ),
                "output_format": InputPort(
                    name="output_format",
                    port_type=PortType.SELECT,
                    value="pdf",
                    options=[
                        {"label": "PDF", "value": "pdf"},
                        {"label": "DOCX", "value": "docx"},
                        {"label": "DOC", "value": "doc"},
                        {"label": "XLSX", "value": "xlsx"},
                        {"label": "XLS", "value": "xls"},
                        {"label": "PPTX", "value": "pptx"},
                        {"label": "PPT", "value": "ppt"},
                        {"label": "ODT", "value": "odt"},
                        {"label": "ODS", "value": "ods"},
                        {"label": "ODP", "value": "odp"},
                        {"label": "RTF", "value": "rtf"},
                        {"label": "TXT", "value": "txt"},
                        {"label": "CSV", "value": "csv"},
                    ],
                ),
                "output": OutputPort(),
            },
        )


class FileLoader(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="FileLoader",
            category="fileProcessing",
            task_name="file_processing.file_loader",
            node_id=id,
            ports={
                "files": InputPort(
                    name="files",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    multiple=True,
                ),
                "parse_quality": InputPort(
                    name="parse_quality",
                    port_type=PortType.SELECT,
                    value="default",
                    options=[{"label": "default", "value": "default"}, {"label": "high", "value": "high"}],
                    required=False,
                    has_tooltip=True,
                ),
                "remove_image": InputPort(
                    name="remove_image",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                    condition="return fieldsData.parse_quality.value === 'default'",
                    condition_python=lambda ports: ports["parse_quality"].value == "default",
                ),
                "remove_url_and_email": InputPort(
                    name="remove_url_and_email",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                    condition="return fieldsData.parse_quality.value === 'default'",
                    condition_python=lambda ports: ports["parse_quality"].value == "default",
                ),
                "parse_table": InputPort(
                    name="parse_table",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                    condition="return fieldsData.parse_quality.value === 'high'",
                    condition_python=lambda ports: ports["parse_quality"].value == "high",
                ),
                "parse_formula": InputPort(
                    name="parse_formula",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    condition="return fieldsData.parse_quality.value === 'high'",
                    condition_python=lambda ports: ports["parse_quality"].value == "high",
                ),
                "multiple": InputPort(
                    name="multiple",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                    has_tooltip=True,
                ),
                "output": OutputPort(),
            },
        )


class FileUpload(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="FileUpload",
            category="fileProcessing",
            task_name="file_processing.file_upload",
            node_id=id,
            ports={
                "files": InputPort(
                    name="files",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    multiple=True,
                    support_file_types=["*/*"],
                ),
                "unzip_files": InputPort(
                    name="unzip_files",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "unzip_output_format": InputPort(
                    name="unzip_output_format",
                    port_type=PortType.SELECT,
                    value="list",
                    options=[{"label": "list", "value": "list"}, {"label": "dict", "value": "dict"}],
                    required=False,
                    condition="return fieldsData.unzip_files.value",
                    condition_python=lambda ports: ports["unzip_files"].value,
                ),
                "allowed_file_types": InputPort(
                    name="allowed_file_types",
                    port_type=PortType.INPUT,
                    value="*/*",
                    required=False,
                    has_tooltip=True,
                ),
                "multiple": InputPort(
                    name="multiple",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                    has_tooltip=True,
                ),
                "output": OutputPort(),
            },
        )
