from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


class AliyunQwen(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="AliyunQwen",
            category="llms",
            task_name="llms.aliyun_qwen",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="qwen3-32b",
                    options=[
                        {"value": "qwen3-max-preview", "label": "qwen3-max-preview"},
                        {"value": "qwen3-235b-a22b-instruct-2507", "label": "qwen3-235b-a22b-instruct-2507"},
                        {"value": "qwen3-coder-480b-a35b-instruct", "label": "qwen3-coder-480b-a35b-instruct"},
                        {"value": "qwen3-235b-a22b", "label": "qwen3-235b-a22b"},
                        {"value": "qwen3-235b-a22b-thinking", "label": "qwen3-235b-a22b-thinking"},
                        {"value": "qwen3-next-80b-a3b-thinking", "label": "qwen3-next-80b-a3b-thinking"},
                        {"value": "qwen3-next-80b-a3b-instruct", "label": "qwen3-next-80b-a3b-instruct"},
                        {"value": "qwen3-32b", "label": "qwen3-32b"},
                        {"value": "qwen3-32b-thinking", "label": "qwen3-32b-thinking"},
                        {"value": "qwen3-30b-a3b", "label": "qwen3-30b-a3b"},
                        {"value": "qwen3-30b-a3b-thinking", "label": "qwen3-30b-a3b-thinking"},
                        {"value": "qwen3-14b", "label": "qwen3-14b"},
                        {"value": "qwen3-14b-thinking", "label": "qwen3-14b-thinking"},
                        {"value": "qwen3-8b", "label": "qwen3-8b"},
                        {"value": "qwen3-8b-thinking", "label": "qwen3-8b-thinking"},
                        {"value": "qwen3-4b", "label": "qwen3-4b"},
                        {"value": "qwen3-4b-thinking", "label": "qwen3-4b-thinking"},
                        {"value": "qwen3-1.7b", "label": "qwen3-1.7b"},
                        {"value": "qwen3-1.7b-thinking", "label": "qwen3-1.7b-thinking"},
                        {"value": "qwen3-0.6b", "label": "qwen3-0.6b"},
                        {"value": "qwen3-0.6b-thinking", "label": "qwen3-0.6b-thinking"},
                        {"value": "qwen2.5-72b-instruct", "label": "qwen2.5-72b-instruct"},
                        {"value": "qwen2.5-32b-instruct", "label": "qwen2.5-32b-instruct"},
                        {"value": "qwen2.5-coder-32b-instruct", "label": "qwen2.5-coder-32b-instruct"},
                        {"value": "qwq-32b", "label": "qwq-32b"},
                        {"value": "qwen2.5-14b-instruct", "label": "qwen2.5-14b-instruct"},
                        {"value": "qwen2.5-7b-instruct", "label": "qwen2.5-7b-instruct"},
                        {"value": "qwen2.5-coder-7b-instruct", "label": "qwen2.5-coder-7b-instruct"},
                    ],
                    required=False,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "system_prompt": InputPort(
                    name="system_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "response_format": InputPort(
                    name="response_format",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}, {"value": "json_object", "label": "JSON"}],
                    required=False,
                ),
                "output": OutputPort(),
                "reasoning_content": OutputPort(
                    name="reasoning_content",
                    condition='return fieldsData.llm_model.value.includes("-thinking")',
                    condition_python=lambda ports: "-thinking" in ports["llm_model"].value,
                ),
            },
        )


class Baichuan(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Baichuan",
            category="llms",
            task_name="llms.baichuan",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="Baichuan3-Turbo",
                    options=[
                        {"value": "Baichuan4", "label": "Baichuan4"},
                        {"value": "Baichuan3-Turbo", "label": "Baichuan3-Turbo"},
                        {"value": "Baichuan3-Turbo-128k", "label": "Baichuan3-Turbo-128k"},
                    ],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "system_prompt": InputPort(
                    name="system_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "response_format": InputPort(
                    name="response_format",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}, {"value": "json_object", "label": "JSON"}],
                    required=False,
                ),
                "use_function_call": InputPort(
                    name="use_function_call",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "functions": InputPort(
                    name="functions",
                    port_type=PortType.SELECT,
                    value=[],
                    required=False,
                ),
                "function_call_mode": InputPort(
                    name="function_call_mode",
                    port_type=PortType.SELECT,
                    value="auto",
                    options=[{"value": "auto", "label": "auto"}, {"value": "none", "label": "none"}],
                    required=False,
                ),
                "output": OutputPort(),
                "function_call_output": OutputPort(
                    name="function_call_output",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
                "function_call_arguments": OutputPort(
                    name="function_call_arguments",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
            },
        )


class BaiduWenxin(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="BaiduWenxin",
            category="llms",
            task_name="llms.baidu_wenxin",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="ernie-3.5",
                    options=[
                        {"value": "ernie-lite", "label": "ernie-lite"},
                        {"value": "ernie-speed", "label": "ernie-speed"},
                        {"value": "ernie-3.5", "label": "ernie-3.5"},
                        {"value": "ernie-4.0", "label": "ernie-4.0"},
                        {"value": "ernie-4.5", "label": "ernie-4.5"},
                    ],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class ChatGLM(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="ChatGLM",
            category="llms",
            task_name="llms.chat_glm",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="glm-4.6",
                    options=[
                        {"value": "glm-4.6", "label": "glm-4.6"},
                        {"value": "glm-4.6-thinking", "label": "glm-4.6-thinking"},
                        {"value": "glm-4.5", "label": "glm-4.5"},
                        {"value": "glm-4.5-thinking", "label": "glm-4.5-thinking"},
                        {"value": "glm-4.5-x", "label": "glm-4.5-x"},
                        {"value": "glm-4.5-air", "label": "glm-4.5-air"},
                        {"value": "glm-4.5-airx", "label": "glm-4.5-airx"},
                        {"value": "glm-4.5-flash", "label": "glm-4.5-flash"},
                        {"value": "glm-4-plus", "label": "glm-4-plus"},
                        {"value": "glm-4-long", "label": "glm-4-long"},
                        {"value": "glm-zero-preview", "label": "glm-zero-preview"},
                        {"value": "glm-z1-air", "label": "glm-z1-air"},
                        {"value": "glm-z1-airx", "label": "glm-z1-airx"},
                        {"value": "glm-z1-flash", "label": "glm-z1-flash"},
                    ],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "system_prompt": InputPort(
                    name="system_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "use_function_call": InputPort(
                    name="use_function_call",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "functions": InputPort(
                    name="functions",
                    port_type=PortType.SELECT,
                    value=[],
                    required=False,
                ),
                "function_call_mode": InputPort(
                    name="function_call_mode",
                    port_type=PortType.SELECT,
                    value="auto",
                    options=[{"value": "auto", "label": "auto"}, {"value": "none", "label": "none"}],
                    required=False,
                ),
                "output": OutputPort(),
                "function_call_output": OutputPort(
                    name="function_call_output",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
                "function_call_arguments": OutputPort(
                    name="function_call_arguments",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
            },
        )


class Claude(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Claude",
            category="llms",
            task_name="llms.claude",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
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
                        {"value": "claude-opus-4-5-20251101-thinking", "label": "claude-opus-4-5-20251101-thinking"},
                        {"value": "claude-opus-4-5-20251101", "label": "claude-opus-4-5-20251101"},
                        {"value": "claude-haiku-4-5-20251001", "label": "claude-haiku-4-5-20251001"},
                        {"value": "claude-opus-4-20250514-thinking", "label": "claude-opus-4-20250514-thinking"},
                        {"value": "claude-opus-4-20250514", "label": "claude-opus-4-20250514"},
                        {"value": "claude-sonnet-4-20250514-thinking", "label": "claude-sonnet-4-20250514-thinking"},
                        {"value": "claude-sonnet-4-20250514", "label": "claude-sonnet-4-20250514"},
                    ],
                    required=False,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "system_prompt": InputPort(
                    name="system_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "output": OutputPort(),
                "reasoning_content": OutputPort(
                    name="reasoning_content",
                    condition="return fieldsData.llm_model.value.endsWith('-thinking')",
                    condition_python=lambda ports: ports["llm_model"].value.endswith("-thinking"),
                ),
            },
        )


class CustomModel(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="CustomModel",
            category="llms",
            task_name="llms.custom_model",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "model_family": InputPort(
                    name="model_family",
                    port_type=PortType.SELECT,
                    value="",
                    options=[],
                    required=False,
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="",
                    options=[],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "system_prompt": InputPort(
                    name="system_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "response_format": InputPort(
                    name="response_format",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}, {"value": "json_object", "label": "JSON"}],
                    required=False,
                ),
                "use_function_call": InputPort(
                    name="use_function_call",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "functions": InputPort(
                    name="functions",
                    port_type=PortType.SELECT,
                    value=[],
                    required=False,
                ),
                "function_call_mode": InputPort(
                    name="function_call_mode",
                    port_type=PortType.SELECT,
                    value="auto",
                    options=[{"value": "auto", "label": "auto"}, {"value": "none", "label": "none"}],
                    required=False,
                ),
                "output": OutputPort(),
                "reasoning_content": OutputPort(
                    name="reasoning_content",
                    condition='return fieldsData.llm_model.value === "deepseek-reasoner" || fieldsData.llm_model.value === "deepseek-r1-distill-qwen-32b"',
                    condition_python=lambda ports: ports["llm_model"].value == "deepseek-reasoner" or ports["llm_model"].value == "deepseek-r1-distill-qwen-32b",
                ),
                "function_call_output": OutputPort(
                    name="function_call_output",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
                "function_call_arguments": OutputPort(
                    name="function_call_arguments",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
            },
        )


class Deepseek(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Deepseek",
            category="llms",
            task_name="llms.deepseek",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="deepseek-chat",
                    options=[{"value": "deepseek-chat", "label": "deepseek-chat"}, {"value": "deepseek-reasoner", "label": "deepseek-r1"}],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "system_prompt": InputPort(
                    name="system_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "response_format": InputPort(
                    name="response_format",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}, {"value": "json_object", "label": "JSON"}],
                    required=False,
                ),
                "use_function_call": InputPort(
                    name="use_function_call",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "functions": InputPort(
                    name="functions",
                    port_type=PortType.SELECT,
                    value=[],
                    required=False,
                ),
                "function_call_mode": InputPort(
                    name="function_call_mode",
                    port_type=PortType.SELECT,
                    value="auto",
                    options=[{"value": "auto", "label": "auto"}, {"value": "none", "label": "none"}],
                    required=False,
                ),
                "output": OutputPort(),
                "reasoning_content": OutputPort(
                    name="reasoning_content",
                    condition='return fieldsData.llm_model.value === "deepseek-reasoner" || fieldsData.llm_model.value === "deepseek-r1-distill-qwen-32b"',
                    condition_python=lambda ports: ports["llm_model"].value == "deepseek-reasoner" or ports["llm_model"].value == "deepseek-r1-distill-qwen-32b",
                ),
                "function_call_output": OutputPort(
                    name="function_call_output",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
                "function_call_arguments": OutputPort(
                    name="function_call_arguments",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
            },
        )


class Gemini(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Gemini",
            category="llms",
            task_name="llms.gemini",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
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
                        {"label": "gemini-2.5-flash-lite", "value": "gemini-2.5-flash-lite"},
                    ],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "system_prompt": InputPort(
                    name="system_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "response_format": InputPort(
                    name="response_format",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}, {"value": "json_object", "label": "JSON"}],
                    required=False,
                ),
                "use_function_call": InputPort(
                    name="use_function_call",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "functions": InputPort(
                    name="functions",
                    port_type=PortType.SELECT,
                    value=[],
                    required=False,
                ),
                "function_call_mode": InputPort(
                    name="function_call_mode",
                    port_type=PortType.SELECT,
                    value="auto",
                    options=[{"value": "auto", "label": "auto"}, {"value": "none", "label": "none"}],
                    required=False,
                ),
                "output": OutputPort(),
                "function_call_output": OutputPort(
                    name="function_call_output",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
                "function_call_arguments": OutputPort(
                    name="function_call_arguments",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
            },
        )


class Groq(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Groq",
            category="llms",
            task_name="llms.groq",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="groq-mixtral-8x7b-32768",
                    options=[
                        {"label": "mixtral-8x7b-32768", "value": "groq-mixtral-8x7b-32768"},
                        {"label": "llama3-70b-8192", "value": "groq-llama3-70b-8192"},
                        {"label": "llama3-8b-8192", "value": "groq-llama3-8b-8192"},
                        {"label": "gemma-7b-it", "value": "groq-gemma-7b-it"},
                    ],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class LingYiWanWu(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="LingYiWanWu",
            category="llms",
            task_name="llms.ling_yi_wan_wu",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="yi-lightning",
                    options=[{"value": "yi-lightning", "label": "yi-lightning"}],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class MiniMax(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="MiniMax",
            category="llms",
            task_name="llms.mini_max",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="MiniMax-M2",
                    options=[{"value": "MiniMax-M2", "label": "MiniMax-M2"}, {"value": "MiniMax-M1", "label": "MiniMax-M1"}],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "system_prompt": InputPort(
                    name="system_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "response_format": InputPort(
                    name="response_format",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}, {"value": "json_object", "label": "JSON"}],
                    required=False,
                ),
                "use_function_call": InputPort(
                    name="use_function_call",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "functions": InputPort(
                    name="functions",
                    port_type=PortType.SELECT,
                    value=[],
                    required=False,
                ),
                "function_call_mode": InputPort(
                    name="function_call_mode",
                    port_type=PortType.SELECT,
                    value="auto",
                    options=[{"value": "auto", "label": "auto"}, {"value": "none", "label": "none"}],
                    required=False,
                ),
                "output": OutputPort(),
                "function_call_output": OutputPort(
                    name="function_call_output",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
                "function_call_arguments": OutputPort(
                    name="function_call_arguments",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
            },
        )


class Moonshot(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Moonshot",
            category="llms",
            task_name="llms.moonshot",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="kimi-k2-0905-preview",
                    options=[
                        {"value": "kimi-k2-thinking", "label": "kimi-k2-thinking"},
                        {"value": "kimi-k2-thinking-turbo", "label": "kimi-k2-thinking-turbo"},
                        {"value": "kimi-k2-0905-preview", "label": "kimi-k2-0905-preview"},
                        {"value": "kimi-latest", "label": "kimi-latest"},
                        {"value": "moonshot-v1-8k", "label": "moonshot-v1-8k"},
                        {"value": "moonshot-v1-32k", "label": "moonshot-v1-32k"},
                        {"value": "moonshot-v1-128k", "label": "moonshot-v1-128k"},
                    ],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "system_prompt": InputPort(
                    name="system_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "response_format": InputPort(
                    name="response_format",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}, {"value": "json_object", "label": "JSON"}],
                    required=False,
                ),
                "use_function_call": InputPort(
                    name="use_function_call",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "functions": InputPort(
                    name="functions",
                    port_type=PortType.SELECT,
                    value=[],
                    required=False,
                ),
                "function_call_mode": InputPort(
                    name="function_call_mode",
                    port_type=PortType.SELECT,
                    value="auto",
                    options=[{"value": "auto", "label": "auto"}, {"value": "none", "label": "none"}],
                    required=False,
                ),
                "output": OutputPort(),
                "function_call_output": OutputPort(
                    name="function_call_output",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
                "function_call_arguments": OutputPort(
                    name="function_call_arguments",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
            },
        )


class OpenAI(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="OpenAI",
            category="llms",
            task_name="llms.open_ai",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="gpt-5.2",
                    options=[
                        {"value": "gpt-5.2", "label": "gpt-5.2"},
                        {"value": "gpt-5.1", "label": "gpt-5.1"},
                        {"value": "gpt-5.1-codex", "label": "gpt-5.1-codex"},
                        {"value": "gpt-5.1-codex-max", "label": "gpt-5.1-codex-max"},
                        {"value": "gpt-5.1-codex-mini", "label": "gpt-5.1-codex-mini"},
                        {"value": "gpt-5.1-chat", "label": "gpt-5.1-chat"},
                        {"value": "gpt-5", "label": "gpt-5"},
                        {"value": "gpt-5-pro", "label": "gpt-5-pro"},
                        {"value": "gpt-5-mini", "label": "gpt-5-mini"},
                        {"value": "gpt-5-nano", "label": "gpt-5-nano"},
                        {"value": "gpt-5-chat-latest", "label": "gpt-5-chat-latest"},
                        {"value": "gpt-5-codex", "label": "gpt-5-codex"},
                        {"value": "o4-mini", "label": "o4-mini"},
                        {"value": "o4-mini-high", "label": "o4-mini-high"},
                        {"value": "gpt-4.1", "label": "gpt-4.1"},
                        {"value": "o3-mini", "label": "o3-mini"},
                        {"value": "o3-mini-high", "label": "o3-mini-high"},
                        {"value": "o1-mini", "label": "o1-mini"},
                        {"value": "o1-preview", "label": "o1-preview"},
                        {"value": "gpt-4o", "label": "gpt-4o"},
                        {"value": "gpt-4", "label": "gpt-4-turbo"},
                        {"value": "gpt-4o-mini", "label": "gpt-4o-mini"},
                    ],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "system_prompt": InputPort(
                    name="system_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "response_format": InputPort(
                    name="response_format",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}, {"value": "json_object", "label": "JSON"}],
                    required=False,
                ),
                "use_function_call": InputPort(
                    name="use_function_call",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "functions": InputPort(
                    name="functions",
                    port_type=PortType.SELECT,
                    value=[],
                    required=False,
                ),
                "function_call_mode": InputPort(
                    name="function_call_mode",
                    port_type=PortType.SELECT,
                    value="auto",
                    options=[{"value": "auto", "label": "auto"}, {"value": "none", "label": "none"}],
                    required=False,
                ),
                "output": OutputPort(),
                "function_call_output": OutputPort(
                    name="function_call_output",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
                "function_call_arguments": OutputPort(
                    name="function_call_arguments",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
            },
        )


class Stepfun(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Stepfun",
            category="llms",
            task_name="llms.stepfun",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="step-1-32k",
                    options=[
                        {"value": "step-3", "label": "step-3"},
                        {"value": "step-2-mini", "label": "step-2-mini"},
                        {"value": "step-1-32k", "label": "step-1-32k"},
                        {"value": "step-1-200k", "label": "step-1-200k"},
                    ],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "output": OutputPort(),
            },
        )


class XAi(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="XAi",
            category="llms",
            task_name="llms.x_ai",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="grok-4",
                    options=[
                        {"value": "grok-4", "label": "grok-4"},
                        {"value": "grok-beta", "label": "grok-beta"},
                        {"value": "grok-3-beta", "label": "grok-3-beta"},
                        {"value": "grok-3-fast-beta", "label": "grok-3-fast-beta"},
                        {"value": "grok-3-mini-beta", "label": "grok-3-mini-beta"},
                        {"value": "grok-3-mini-fast-beta", "label": "grok-3-mini-fast-beta"},
                    ],
                    required=False,
                ),
                "temperature": InputPort(
                    name="temperature",
                    port_type=PortType.TEMPERATURE,
                    value=0.7,
                ),
                "top_p": InputPort(
                    name="top_p",
                    port_type=PortType.NUMBER,
                    value=0.95,
                ),
                "stream": InputPort(
                    name="stream",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "system_prompt": InputPort(
                    name="system_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "response_format": InputPort(
                    name="response_format",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}, {"value": "json_object", "label": "JSON"}],
                    required=False,
                ),
                "use_function_call": InputPort(
                    name="use_function_call",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "functions": InputPort(
                    name="functions",
                    port_type=PortType.SELECT,
                    value=[],
                    required=False,
                ),
                "function_call_mode": InputPort(
                    name="function_call_mode",
                    port_type=PortType.SELECT,
                    value="auto",
                    options=[{"value": "auto", "label": "auto"}, {"value": "none", "label": "none"}],
                    required=False,
                ),
                "output": OutputPort(),
                "function_call_output": OutputPort(
                    name="function_call_output",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
                "function_call_arguments": OutputPort(
                    name="function_call_arguments",
                    condition="return fieldsData.use_function_call.value",
                    condition_python=lambda ports: ports["use_function_call"].value,
                ),
            },
        )
