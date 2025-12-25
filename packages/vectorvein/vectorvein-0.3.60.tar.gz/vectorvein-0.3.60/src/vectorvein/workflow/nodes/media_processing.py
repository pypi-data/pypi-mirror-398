from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


class ClaudeVision(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="ClaudeVision",
            category="mediaProcessing",
            task_name="media_processing.claude_vision",
            node_id=id,
            ports={
                "text_prompt": InputPort(
                    name="text_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="claude-sonnet-4-5-20250929",
                    options=[
                        {"value": "claude-sonnet-4-5-20250929-thinking", "label": "claude-sonnet-4-5-20250929-thinking"},
                        {"value": "claude-sonnet-4-5-20250929", "label": "claude-sonnet-4-5-20250929"},
                        {"value": "claude-haiku-4-5-20251001", "label": "claude-haiku-4-5-20251001"},
                        {"value": "claude-opus-4-20250514-thinking", "label": "claude-opus-4-20250514-thinking"},
                        {"value": "claude-opus-4-20250514", "label": "claude-opus-4-20250514"},
                        {"value": "claude-sonnet-4-20250514-thinking", "label": "claude-sonnet-4-20250514-thinking"},
                        {"value": "claude-sonnet-4-20250514", "label": "claude-sonnet-4-20250514"},
                        {"value": "claude-3-7-sonnet-thinking", "label": "claude-3-7-sonnet-thinking"},
                        {"value": "claude-3-7-sonnet", "label": "claude-3-7-sonnet"},
                        {"value": "claude-3-5-sonnet", "label": "claude-3-5-sonnet"},
                        {"value": "claude-3-opus", "label": "claude-3-opus"},
                        {"value": "claude-3-sonnet", "label": "claude-3-sonnet"},
                        {"value": "claude-3-haiku", "label": "claude-3-haiku"},
                    ],
                    required=False,
                ),
                "multiple_input": InputPort(
                    name="multiple_input",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                ),
                "images_or_urls": InputPort(
                    name="images_or_urls",
                    port_type=PortType.RADIO,
                    value="images",
                    options=[{"value": "images", "label": "images"}, {"value": "urls", "label": "urls"}],
                    required=False,
                ),
                "images": InputPort(
                    name="images",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    support_file_types=[".jpg", ".jpeg", ".png", ".webp"],
                    condition="return fieldsData.images_or_urls.value == 'images'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "images",
                ),
                "urls": InputPort(
                    name="urls",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.images_or_urls.value == 'urls'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "urls",
                ),
                "output": OutputPort(),
                "reasoning_content": OutputPort(
                    name="reasoning_content",
                    condition="return fieldsData.llm_model.value.endsWith('-thinking')",
                    condition_python=lambda ports: ports["llm_model"].value.endswith("-thinking"),
                ),
            },
        )


class DeepseekVl(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="DeepseekVl",
            category="mediaProcessing",
            task_name="media_processing.deepseek_vl",
            node_id=id,
            ports={
                "text_prompt": InputPort(
                    name="text_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="deepseek-vl2",
                    options=[{"value": "deepseek-vl2", "label": "deepseek-vl2"}],
                    required=False,
                ),
                "images_or_urls": InputPort(
                    name="images_or_urls",
                    port_type=PortType.RADIO,
                    value="images",
                    options=[{"value": "images", "label": "images"}, {"value": "urls", "label": "urls"}],
                    required=False,
                ),
                "images": InputPort(
                    name="images",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    support_file_types=[".jpg", ".jpeg", ".png", ".webp"],
                    condition="return fieldsData.images_or_urls.value == 'images'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "images",
                ),
                "urls": InputPort(
                    name="urls",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.images_or_urls.value == 'urls'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "urls",
                ),
                "output": OutputPort(),
            },
        )


class GeminiVision(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="GeminiVision",
            category="mediaProcessing",
            task_name="media_processing.gemini_vision",
            node_id=id,
            ports={
                "text_prompt": InputPort(
                    name="text_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="gemini-3-pro",
                    options=[
                        {"label": "gemini-3-pro", "value": "gemini-3-pro"},
                        {"label": "gemini-2.5-pro", "value": "gemini-2.5-pro"},
                        {"label": "gemini-2.5-flash", "value": "gemini-2.5-flash"},
                    ],
                    required=False,
                ),
                "multiple_input": InputPort(
                    name="multiple_input",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                ),
                "images_or_urls": InputPort(
                    name="images_or_urls",
                    port_type=PortType.RADIO,
                    value="images",
                    options=[{"value": "images", "label": "images"}, {"value": "urls", "label": "urls"}],
                    required=False,
                ),
                "images": InputPort(
                    name="images",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    support_file_types=[".jpg", ".jpeg", ".png", ".webp"],
                    condition="return fieldsData.images_or_urls.value == 'images'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "images",
                ),
                "urls": InputPort(
                    name="urls",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.images_or_urls.value == 'urls'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "urls",
                ),
                "output": OutputPort(),
            },
        )


class GlmVision(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="GlmVision",
            category="mediaProcessing",
            task_name="media_processing.glm_vision",
            node_id=id,
            ports={
                "text_prompt": InputPort(
                    name="text_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="glm-4.6v",
                    options=[
                        {"value": "glm-4.6v", "label": "glm-4.6v"},
                        {"value": "glm-4.5v", "label": "glm-4.5v"},
                        {"value": "glm-4v-plus", "label": "glm-4v-plus"},
                        {"value": "glm-4v-flash", "label": "glm-4v-flash"},
                    ],
                    required=False,
                ),
                "multiple_input": InputPort(
                    name="multiple_input",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                ),
                "images_or_urls": InputPort(
                    name="images_or_urls",
                    port_type=PortType.RADIO,
                    value="images",
                    options=[{"value": "images", "label": "images"}, {"value": "urls", "label": "urls"}],
                    required=False,
                ),
                "images": InputPort(
                    name="images",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    support_file_types=[".jpg", ".jpeg", ".png", ".webp", ".mp4"],
                    condition="return fieldsData.images_or_urls.value == 'images'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "images",
                ),
                "urls": InputPort(
                    name="urls",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.images_or_urls.value == 'urls'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "urls",
                ),
                "output": OutputPort(),
            },
        )


class GptVision(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="GptVision",
            category="mediaProcessing",
            task_name="media_processing.gpt_vision",
            node_id=id,
            ports={
                "text_prompt": InputPort(
                    name="text_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="gpt-5",
                    options=[
                        {"value": "gpt-5", "label": "gpt-5"},
                        {"value": "gpt-5-codex", "label": "gpt-5-codex"},
                        {"value": "gpt-5-mini", "label": "gpt-5-mini"},
                        {"value": "gpt-5-nano", "label": "gpt-5-nano"},
                        {"value": "gpt-4o", "label": "gpt-4o"},
                        {"value": "gpt-4o-mini", "label": "gpt-4o-mini"},
                        {"value": "o4-mini", "label": "o4-mini"},
                        {"value": "o4-mini-high", "label": "o4-mini-high"},
                        {"value": "gpt-4.1", "label": "gpt-4.1"},
                    ],
                    required=False,
                ),
                "multiple_input": InputPort(
                    name="multiple_input",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                ),
                "images_or_urls": InputPort(
                    name="images_or_urls",
                    port_type=PortType.RADIO,
                    value="images",
                    options=[{"value": "images", "label": "images"}, {"value": "urls", "label": "urls"}],
                    required=False,
                ),
                "images": InputPort(
                    name="images",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    support_file_types=[".jpg", ".jpeg", ".png", ".webp"],
                    condition="return fieldsData.images_or_urls.value == 'images'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "images",
                ),
                "urls": InputPort(
                    name="urls",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.images_or_urls.value == 'urls'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "urls",
                ),
                "detail_type": InputPort(
                    name="detail_type",
                    port_type=PortType.SELECT,
                    value="auto",
                    options=[{"value": "auto", "label": "auto"}, {"value": "low", "label": "low"}, {"value": "high", "label": "high"}],
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class InternVision(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="InternVision",
            category="mediaProcessing",
            task_name="media_processing.intern_vision",
            node_id=id,
            ports={
                "text_prompt": InputPort(
                    name="text_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="internvl2-26b",
                    options=[{"value": "internvl2-26b", "label": "internvl2-26b"}, {"value": "internvl2-8b", "label": "internvl2-8b"}],
                    required=False,
                ),
                "images_or_urls": InputPort(
                    name="images_or_urls",
                    port_type=PortType.RADIO,
                    value="images",
                    options=[{"value": "images", "label": "images"}, {"value": "urls", "label": "urls"}],
                    required=False,
                ),
                "images": InputPort(
                    name="images",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    support_file_types=[".jpg", ".jpeg", ".png", ".webp"],
                    condition="return fieldsData.images_or_urls.value == 'images'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "images",
                ),
                "urls": InputPort(
                    name="urls",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.images_or_urls.value == 'urls'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "urls",
                ),
                "output": OutputPort(),
            },
        )


class MoonshotVision(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="MoonshotVision",
            category="mediaProcessing",
            task_name="media_processing.moonshot_vision",
            node_id=id,
            ports={
                "text_prompt": InputPort(
                    name="text_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="moonshot-v1-8k-vision-preview",
                    options=[
                        {"value": "moonshot-v1-8k-vision-preview", "label": "moonshot-v1-8k-vision-preview"},
                        {"value": "moonshot-v1-32k-vision-preview", "label": "moonshot-v1-32k-vision-preview"},
                        {"value": "moonshot-v1-128k-vision-preview", "label": "moonshot-v1-128k-vision-preview"},
                    ],
                    required=False,
                ),
                "images_or_urls": InputPort(
                    name="images_or_urls",
                    port_type=PortType.RADIO,
                    value="images",
                    options=[{"value": "images", "label": "images"}, {"value": "urls", "label": "urls"}],
                    required=False,
                ),
                "images": InputPort(
                    name="images",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    support_file_types=[".jpg", ".jpeg", ".png", ".webp"],
                    condition="return fieldsData.images_or_urls.value == 'images'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "images",
                ),
                "urls": InputPort(
                    name="urls",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.images_or_urls.value == 'urls'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "urls",
                ),
                "output": OutputPort(),
            },
        )


class Ocr(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Ocr",
            category="mediaProcessing",
            task_name="media_processing.ocr",
            node_id=id,
            ports={
                "ocr_type": InputPort(
                    name="ocr_type",
                    port_type=PortType.SELECT,
                    value="general",
                    options=[{"value": "general", "label": "general"}, {"value": "table", "label": "table"}, {"value": "business_license", "label": "business_license"}],
                    required=False,
                ),
                "images_or_urls": InputPort(
                    name="images_or_urls",
                    port_type=PortType.RADIO,
                    value="images",
                    options=[{"value": "images", "label": "images"}, {"value": "urls", "label": "urls"}],
                    required=False,
                ),
                "images": InputPort(
                    name="images",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    support_file_types=[".jpg", ".jpeg", ".png", ".webp"],
                    condition="return fieldsData.images_or_urls.value == 'images'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "images",
                ),
                "urls": InputPort(
                    name="urls",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.images_or_urls.value == 'urls'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "urls",
                ),
                "output_table": OutputPort(
                    name="output_table",
                    has_tooltip=True,
                    condition="return fieldsData.ocr_type.value == 'table'",
                    condition_python=lambda ports: ports["ocr_type"].value == "table",
                ),
                "output_content": OutputPort(
                    name="output_content",
                    condition="return ['general', 'business_license'].includes(fieldsData.ocr_type.value)",
                    condition_python=lambda ports: ports["ocr_type"].value in ["general", "business_license"],
                ),
                "output_words_info": OutputPort(
                    name="output_words_info",
                    has_tooltip=True,
                    condition="return ['general', 'business_license'].includes(fieldsData.ocr_type.value)",
                    condition_python=lambda ports: ports["ocr_type"].value in ["general", "business_license"],
                ),
            },
        )


class QwenVision(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="QwenVision",
            category="mediaProcessing",
            task_name="media_processing.qwen_vision",
            node_id=id,
            ports={
                "text_prompt": InputPort(
                    name="text_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="qwen3-vl-30b-a3b-instruct",
                    options=[
                        {"value": "qwen3-vl-30b-a3b-thinking", "label": "qwen3-vl-30b-a3b-thinking"},
                        {"value": "qwen3-vl-30b-a3b-instruct", "label": "qwen3-vl-30b-a3b-instruct"},
                        {"value": "qwen3-vl-8b-thinking", "label": "qwen3-vl-8b-thinking"},
                        {"value": "qwen3-vl-8b-instruct", "label": "qwen3-vl-8b-instruct"},
                        {"value": "qwen3-vl-flash", "label": "qwen3-vl-flash"},
                        {"value": "qwen3-vl-plus", "label": "qwen3-vl-plus"},
                        {"value": "qwen3-vl-235b-a22b-thinking", "label": "qwen3-vl-235b-a22b-thinking"},
                        {"value": "qwen3-vl-235b-a22b-instruct", "label": "qwen3-vl-235b-a22b-instruct"},
                        {"value": "qvq-72b-preview", "label": "qvq-72b-preview"},
                        {"value": "qwen2.5-vl-72b-instruct", "label": "qwen2.5-vl-72b-instruct"},
                        {"value": "qwen2.5-vl-7b-instruct", "label": "qwen2.5-vl-7b-instruct"},
                        {"value": "qwen2.5-vl-3b-instruct", "label": "qwen2.5-vl-3b-instruct"},
                        {"value": "qwen2-vl-72b-instruct", "label": "qwen2-vl-72b-instruct"},
                        {"value": "qwen2-vl-7b-instruct", "label": "qwen2-vl-7b-instruct"},
                        {"value": "qwen-vl-max", "label": "qwen-vl-max"},
                        {"value": "qwen-vl-plus", "label": "qwen-vl-plus"},
                    ],
                    required=False,
                ),
                "multiple_input": InputPort(
                    name="multiple_input",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                ),
                "images_or_urls": InputPort(
                    name="images_or_urls",
                    port_type=PortType.RADIO,
                    value="images",
                    options=[{"value": "images", "label": "images"}, {"value": "urls", "label": "urls"}],
                    required=False,
                ),
                "images": InputPort(
                    name="images",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    support_file_types=[".jpg", ".jpeg", ".png", ".webp", ".mp4"],
                    condition="return fieldsData.images_or_urls.value == 'images'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "images",
                ),
                "urls": InputPort(
                    name="urls",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.images_or_urls.value == 'urls'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "urls",
                ),
                "output": OutputPort(),
            },
        )


class SpeechRecognition(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="SpeechRecognition",
            category="mediaProcessing",
            task_name="media_processing.speech_recognition",
            node_id=id,
            ports={
                "files_or_urls": InputPort(
                    name="files_or_urls",
                    port_type=PortType.RADIO,
                    value="files",
                    options=[{"value": "files", "label": "files"}, {"value": "urls", "label": "urls"}],
                    required=False,
                ),
                "files": InputPort(
                    name="files",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    support_file_types=[".wav", ".mp3", ".mp4", ".m4a", ".wma", ".aac", ".ogg", ".amr", ".flac"],
                    condition="return fieldsData.files_or_urls.value == 'files'",
                    condition_python=lambda ports: ports["files_or_urls"].value == "files",
                ),
                "urls": InputPort(
                    name="urls",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.files_or_urls.value == 'urls'",
                    condition_python=lambda ports: ports["files_or_urls"].value == "urls",
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "text"}, {"value": "list", "label": "list"}, {"value": "srt", "label": "srt"}],
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class YiVision(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="YiVision",
            category="mediaProcessing",
            task_name="media_processing.yi_vision",
            node_id=id,
            ports={
                "text_prompt": InputPort(
                    name="text_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="yi-vision-v2",
                    options=[{"value": "yi-vision-v2", "label": "yi-vision-v2"}],
                    required=False,
                ),
                "images_or_urls": InputPort(
                    name="images_or_urls",
                    port_type=PortType.RADIO,
                    value="images",
                    options=[{"value": "images", "label": "images"}, {"value": "urls", "label": "urls"}],
                    required=False,
                ),
                "images": InputPort(
                    name="images",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    support_file_types=[".jpg", ".jpeg", ".png", ".webp"],
                    condition="return fieldsData.images_or_urls.value == 'images'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "images",
                ),
                "urls": InputPort(
                    name="urls",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.images_or_urls.value == 'urls'",
                    condition_python=lambda ports: ports["images_or_urls"].value == "urls",
                ),
                "output": OutputPort(),
            },
        )
