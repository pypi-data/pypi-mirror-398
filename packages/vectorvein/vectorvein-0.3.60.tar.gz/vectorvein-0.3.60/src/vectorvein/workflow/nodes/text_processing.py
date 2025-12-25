from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


class ListRender(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="ListRender",
            category="textProcessing",
            task_name="text_processing.list_render",
            node_id=id,
            ports={
                "list": InputPort(
                    name="list",
                    port_type=PortType.LIST,
                    value=[],
                ),
                "separator": InputPort(
                    name="separator",
                    port_type=PortType.INPUT,
                    value="\\n\\n",
                    required=False,
                    condition="return fieldsData.output_type.value == 'text'",
                    condition_python=lambda ports: ports["output_type"].value == "text",
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


class MarkdownToHtml(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="MarkdownToHtml",
            category="textProcessing",
            task_name="text_processing.markdown_to_html",
            node_id=id,
            ports={
                "markdown": InputPort(
                    name="markdown",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "html": OutputPort(name="html"),
            },
        )


class RegexExtract(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="RegexExtract",
            category="textProcessing",
            task_name="text_processing.regex_extract",
            node_id=id,
            ports={
                "text": InputPort(
                    name="text",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "pattern": InputPort(
                    name="pattern",
                    port_type=PortType.INPUT,
                    value="```.*?\\n(.*?)\\n```",
                    has_tooltip=True,
                ),
                "first_match": InputPort(
                    name="first_match",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                    has_tooltip=True,
                ),
                "output_original_on_no_match": InputPort(
                    name="output_original_on_no_match",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                    has_tooltip=True,
                ),
                "output": OutputPort(list=True),
            },
        )


class TemplateCompose(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="TemplateCompose",
            category="textProcessing",
            task_name="text_processing.template_compose",
            node_id=id,
            can_add_input_ports=True,
            ports={
                "template": InputPort(
                    name="template",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "output": OutputPort(),
            },
        )


class TextInOut(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="TextInOut",
            category="textProcessing",
            task_name="text_processing.text_in_out",
            node_id=id,
            ports={
                "text": InputPort(
                    name="text",
                    port_type=PortType.TEXTAREA,
                    value="",
                    show=True,
                ),
                "input_type": InputPort(
                    name="input_type",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "text"}, {"value": "number", "label": "number"}],
                ),
                "output": OutputPort(),
            },
        )


class TextReplace(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="TextReplace",
            category="textProcessing",
            task_name="text_processing.text_replace",
            node_id=id,
            ports={
                "text": InputPort(
                    name="text",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "replace_items": InputPort(
                    name="replace_items",
                    port_type=PortType.INPUT,
                    value=[],
                ),
                "output": OutputPort(),
            },
        )


class TextSplitters(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="TextSplitters",
            category="textProcessing",
            task_name="text_processing.text_splitters",
            node_id=id,
            ports={
                "text": InputPort(
                    name="text",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "split_method": InputPort(
                    name="split_method",
                    port_type=PortType.SELECT,
                    value="general",
                    options=[{"value": "general", "label": "general"}, {"value": "delimiter", "label": "delimiter"}, {"value": "markdown", "label": "markdown"}],
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
                "output": OutputPort(list=True),
            },
        )


class TextTruncation(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="TextTruncation",
            category="textProcessing",
            task_name="text_processing.text_truncation",
            node_id=id,
            ports={
                "text": InputPort(
                    name="text",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "truncate_method": InputPort(
                    name="truncate_method",
                    port_type=PortType.SELECT,
                    value="general",
                    options=[{"value": "general", "label": "general"}, {"value": "markdown", "label": "markdown"}],
                ),
                "truncate_length": InputPort(
                    name="truncate_length",
                    port_type=PortType.NUMBER,
                    value=2000,
                ),
                "floating_range": InputPort(
                    name="floating_range",
                    port_type=PortType.NUMBER,
                    value=100,
                ),
                "output": OutputPort(list=True),
            },
        )
