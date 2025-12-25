from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


class Audio(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Audio",
            category="outputs",
            task_name="output.audio",
            node_id=id,
            ports={
                "audio_type": InputPort(
                    name="audio_type",
                    port_type=PortType.SELECT,
                    value="play_audio",
                    options=[{"value": "text_to_speech", "label": "text_to_speech"}, {"value": "play_audio", "label": "play_audio"}],
                    required=False,
                ),
                "file_link": InputPort(
                    name="file_link",
                    port_type=PortType.TEXTAREA,
                    value="",
                    condition="return fieldsData.audio_type.value == 'play_audio'",
                    condition_python=lambda ports: ports["audio_type"].value == "play_audio",
                ),
                "is_midi": InputPort(
                    name="is_midi",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    condition="return fieldsData.audio_type.value == 'play_audio'",
                    condition_python=lambda ports: ports["audio_type"].value == "play_audio",
                ),
                "content": InputPort(
                    name="content",
                    port_type=PortType.TEXTAREA,
                    value="",
                    condition="return fieldsData.audio_type.value == 'text_to_speech'",
                    condition_python=lambda ports: ports["audio_type"].value == "text_to_speech",
                ),
                "show_player": InputPort(
                    name="show_player",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="markdown",
                    options=[{"value": "only_link", "label": "only_link"}, {"value": "markdown", "label": "markdown"}, {"value": "html", "label": "html"}],
                    required=False,
                ),
                "output": OutputPort(port_type=PortType.INPUT, required=False),
            },
        )


class Document(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Document",
            category="outputs",
            task_name="output.document",
            node_id=id,
            ports={
                "file_name": InputPort(
                    name="file_name",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "export_type": InputPort(
                    name="export_type",
                    port_type=PortType.SELECT,
                    value=".docx",
                    options=[
                        {"value": ".docx", "label": ".docx"},
                        {"value": ".xlsx", "label": ".xlsx"},
                        {"value": ".txt", "label": ".txt"},
                        {"value": ".md", "label": ".md"},
                        {"value": ".json", "label": ".json"},
                        {"value": ".csv", "label": ".csv"},
                        {"value": ".html", "label": ".html"},
                        {"value": ".srt", "label": ".srt"},
                        {"value": ".pdf", "label": ".pdf"},
                    ],
                    required=False,
                ),
                "content_type": InputPort(
                    name="content_type",
                    port_type=PortType.SELECT,
                    value="markdown",
                    options=[{"value": "markdown", "label": "markdown"}, {"value": "html", "label": "html"}],
                    required=False,
                    condition="return fieldsData.export_type.value == '.pdf'",
                    condition_python=lambda ports: ports["export_type"].value == ".pdf",
                ),
                "content": InputPort(
                    name="content",
                    port_type=PortType.TEXTAREA,
                    value="",
                    has_tooltip=True,
                ),
                "show_download": InputPort(
                    name="show_download",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="markdown",
                    options=[{"value": "only_link", "label": "only_link"}, {"value": "markdown", "label": "markdown"}, {"value": "html", "label": "html"}],
                    required=False,
                ),
                "output": OutputPort(port_type=PortType.INPUT, required=False),
            },
        )


class Echarts(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Echarts",
            category="outputs",
            task_name="output.echarts",
            node_id=id,
            ports={
                "option": InputPort(
                    name="option",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "show_echarts": InputPort(
                    name="show_echarts",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                ),
            },
        )


class Email(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Email",
            category="outputs",
            task_name="output.email",
            node_id=id,
            ports={
                "to_email": InputPort(
                    name="to_email",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                ),
                "subject": InputPort(
                    name="subject",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                ),
                "content_html": InputPort(
                    name="content_html",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "attachments": InputPort(
                    name="attachments",
                    port_type=PortType.INPUT,
                    value="",
                    required=False,
                ),
            },
        )


class Html(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Html",
            category="outputs",
            task_name="output.html",
            node_id=id,
            ports={
                "html_code": InputPort(
                    name="html_code",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "output": OutputPort(port_type=PortType.INPUT, required=False),
            },
        )


class Mermaid(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Mermaid",
            category="outputs",
            task_name="output.mermaid",
            node_id=id,
            ports={
                "content": InputPort(
                    name="content",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "show_mermaid": InputPort(
                    name="show_mermaid",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                ),
            },
        )


class Mindmap(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Mindmap",
            category="outputs",
            task_name="output.mindmap",
            node_id=id,
            ports={
                "content": InputPort(
                    name="content",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "show_mind_map": InputPort(
                    name="show_mind_map",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                ),
            },
        )


class MpWeixinTemplateMsg(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="MpWeixinTemplateMsg",
            category="outputs",
            task_name="output.mp_weixin_template_msg",
            node_id=id,
            ports={
                "message": InputPort(
                    name="message",
                    port_type=PortType.INPUT,
                    value="",
                ),
            },
        )


class PictureRender(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="PictureRender",
            category="outputs",
            task_name="output.picture_render",
            node_id=id,
            ports={
                "render_type": InputPort(
                    name="render_type",
                    port_type=PortType.SELECT,
                    value="markdown",
                    options=[
                        {"value": "markdown", "label": "markdown"},
                        {"value": "mindmap", "label": "mindmap"},
                        {"value": "mermaid", "label": "mermaid"},
                        {"value": "pdf", "label": "PDF"},
                        {"value": "url", "label": "url"},
                        {"value": "html_code", "label": "html_code"},
                    ],
                    required=False,
                ),
                "content": InputPort(
                    name="content",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "width": InputPort(
                    name="width",
                    port_type=PortType.NUMBER,
                    value=1200,
                    condition="return ['url', 'html_code', 'markdown', 'mindmap', 'mermaid'].includes(fieldsData.render_type.value)",
                    condition_python=lambda ports: ports["render_type"].value in ["url", "html_code", "markdown", "mindmap", "mermaid"],
                ),
                "height": InputPort(
                    name="height",
                    port_type=PortType.NUMBER,
                    value=800,
                    condition="return ['url', 'html_code', 'markdown', 'mindmap', 'mermaid'].includes(fieldsData.render_type.value) && !fieldsData.is_long_screenshot.value",
                    condition_python=lambda ports: ports["render_type"].value in ["url", "html_code", "markdown", "mindmap", "mermaid"],
                ),
                "is_long_screenshot": InputPort(
                    name="is_long_screenshot",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                    condition="return !['pdf'].includes(fieldsData.render_type.value)",
                    condition_python=lambda ports: ports["render_type"].value in ["pdf"],
                ),
                "base64_encode": InputPort(
                    name="base64_encode",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="markdown",
                    options=[{"value": "only_link", "label": "only_link"}, {"value": "markdown", "label": "markdown"}, {"value": "html", "label": "html"}],
                    required=False,
                ),
                "output": OutputPort(port_type=PortType.INPUT, required=False),
            },
        )


class Presentation(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Presentation",
            category="outputs",
            task_name="output.presentation",
            node_id=id,
            ports={
                "file_name": InputPort(
                    name="file_name",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "content_type": InputPort(
                    name="content_type",
                    port_type=PortType.SELECT,
                    value="html",
                    options=[{"value": "html", "label": "html"}],
                    required=False,
                ),
                "contents": InputPort(
                    name="contents",
                    port_type=PortType.LIST,
                    value=[],
                ),
                "width": InputPort(
                    name="width",
                    port_type=PortType.NUMBER,
                    value=1280,
                ),
                "height": InputPort(
                    name="height",
                    port_type=PortType.NUMBER,
                    value=720,
                ),
                "show_download": InputPort(
                    name="show_download",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="markdown",
                    options=[{"value": "only_link", "label": "only_link"}, {"value": "markdown", "label": "markdown"}, {"value": "html", "label": "html"}],
                    required=False,
                ),
                "output": OutputPort(port_type=PortType.INPUT, required=False),
                "output_htmls": OutputPort(
                    name="output_htmls",
                    port_type=PortType.LIST,
                    list=True,
                ),
            },
        )


class Table(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Table",
            category="outputs",
            task_name="output.table",
            node_id=id,
            ports={
                "content_type": InputPort(
                    name="content_type",
                    port_type=PortType.SELECT,
                    value="csv",
                    options=[{"value": "file_link", "label": "file_link"}, {"value": "csv", "label": "csv"}, {"value": "json", "label": "json"}],
                    required=False,
                ),
                "content": InputPort(
                    name="content",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "bordered": InputPort(
                    name="bordered",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "show_table": InputPort(
                    name="show_table",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class Text(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Text",
            category="outputs",
            task_name="output.text",
            node_id=id,
            ports={
                "text": InputPort(
                    name="text",
                    port_type=PortType.TEXTAREA,
                    value="",
                    show=True,
                ),
                "output_title": InputPort(
                    name="output_title",
                    port_type=PortType.INPUT,
                    value="",
                    has_tooltip=True,
                ),
                "render_markdown": InputPort(
                    name="render_markdown",
                    port_type=PortType.CHECKBOX,
                    value=True,
                ),
                "output": OutputPort(),
            },
        )


class WorkflowInvokeOutput(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="WorkflowInvokeOutput",
            category="outputs",
            task_name="output.workflow_invoke_output",
            node_id=id,
            ports={
                "value": InputPort(
                    name="value",
                    port_type=PortType.TEXTAREA,
                    value="",
                    show=True,
                ),
                "display_name": InputPort(
                    name="display_name",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                ),
            },
        )
