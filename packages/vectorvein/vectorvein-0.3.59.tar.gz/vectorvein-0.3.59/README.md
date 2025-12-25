# VectorVein Python SDK

[![PyPI version](https://badge.fury.io/py/vectorvein.svg)](https://badge.fury.io/py/vectorvein)
[![Python versions](https://img.shields.io/pypi/pyversions/vectorvein.svg)](https://pypi.org/project/vectorvein/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

VectorVein Python SDK 是一个功能强大的 Python 库，提供了对向量脉络(VectorVein)平台的完整访问能力。它包含两大核心功能：
1. **向量脉络 API 客户端** - 用于调用向量脉络的工作流和VApp功能
2. **多模型聊天客户端** - 统一的接口支持多种大语言模型（Claude、OpenAI、通义千问、智谱AI等）
3. **工作流设计框架** - 用于构建和设计复杂的AI工作流

## 🚀 快速开始

### 安装

```bash
pip install vectorvein
```

### 基本使用

#### 1. VectorVein API 客户端

```python
from vectorvein.api import VectorVeinClient, WorkflowInputField

# 创建客户端实例
client = VectorVeinClient(api_key="YOUR_API_KEY")

# 准备工作流输入字段
input_fields = [
    WorkflowInputField(
        node_id="8fc6eceb-8599-46a7-87fe-58bf7c0b633e",
        field_name="商品名称",
        value="测试商品"
    )
]

# 异步运行工作流
rid = client.run_workflow(
    wid="abcde0985736457aa72cc667f17bfc89",
    input_fields=input_fields,
    wait_for_completion=False
)
print(f"工作流运行ID: {rid}")

# 同步运行工作流
result = client.run_workflow(
    wid="abcde0985736457aa72cc667f17bfc89",
    input_fields=input_fields,
    wait_for_completion=True
)
print(f"工作流运行结果: {result}")
```

#### 2. 聊天客户端

```python
from vectorvein.chat_clients import create_chat_client, BackendType
from vectorvein.settings import settings

# 加载设置（包含API密钥等配置）
settings.load({
    "rate_limit": {
        "enabled": True,
        "backend": "redis",  # 或 "diskcache"
        "redis": {
            "host": "127.0.0.1",
            "port": 6379,
            "db": 0,
        },
        "default_rpm": 60,
        "default_tpm": 1000000,
    },
    "endpoints": [
        {
            "id": "anthropic-default",
            "api_base": "https://api.anthropic.com",
            "api_key": "your_claude_api_key",
            "rpm": 60,
            "tpm": 1000000
        },
        {
            "id": "openai-default", 
            "api_base": "https://api.openai.com/v1",
            "api_key": "your_openai_api_key",
            "rpm": 3500,
            "tpm": 90000
        }
    ],
    "anthropic": {
        "models": {
            "claude-3-7-sonnet-20250219": {
                "id": "claude-3-7-sonnet-20250219",
                "endpoints": ["anthropic-default"],
                "context_length": 200000,
                "max_output_tokens": 8192,
                "function_call_available": True,
                "native_multimodal": True
            }
        }
    },
    "openai": {
        "models": {
            "gpt-4o": {
                "id": "gpt-4o", 
                "endpoints": ["openai-default"],
                "context_length": 128000,
                "max_output_tokens": 16384,
                "function_call_available": True,
                "response_format_available": True,
                "native_multimodal": True
            }
        }
    }
})

# 创建 Claude 客户端
client = create_chat_client(BackendType.Anthropic, model="claude-3-7-sonnet-20250219")

# 发送消息
response = client.create_completion([
    {"role": "user", "content": "你好，请介绍一下人工智能的发展历程"}
])
print(response.content)

# 创建 OpenAI 客户端
openai_client = create_chat_client(BackendType.OpenAI, model="gpt-4o")

# 流式响应
for chunk in openai_client.create_stream([
    {"role": "user", "content": "写一首关于春天的诗"}
]):
    print(chunk.content, end="", flush=True)
```

#### 3. 工作流设计

```python
from vectorvein.workflow.graph.workflow import Workflow
from vectorvein.workflow.nodes.llms import Claude
from vectorvein.workflow.nodes.text_processing import TemplateCompose
from vectorvein.workflow.nodes.output import Text

# 创建工作流
workflow = Workflow()

# 创建节点
template = TemplateCompose()
template.add_port(name="用户输入", port_type="textarea", show=True)
template.ports["template"].value = "请回答以下问题：{{用户输入}}"

claude = Claude()
claude.ports["llm_model"].value = "claude-3-7-sonnet-20250219"
claude.ports["temperature"].value = 0.7

output = Text()
output.ports["output_title"].value = "AI回答"

# 添加节点到工作流
workflow.add_nodes([template, claude, output])

# 连接节点
workflow.connect(template, "output", claude, "prompt")
workflow.connect(claude, "output", output, "text")

# 布局和导出
workflow.layout()
print(workflow.to_json())
```

## 📚 功能特性

### VectorVein API 客户端

- **工作流管理**: 运行工作流、检查状态、管理执行
- **访问密钥管理**: 创建、获取、列表、更新、删除访问密钥
- **VApp 集成**: 生成VApp访问链接
- **异步支持**: 完整的异步API支持
- **错误处理**: 详细的异常类型和错误信息

### 聊天客户端

#### 支持的模型提供商

- **Anthropic**: Claude-3, Claude-3.5, Claude-4, Claude Opus 等
- **OpenAI**: GPT-3.5, GPT-4, GPT-4o, o1, o3 系列
- **阿里云**: 通义千问 Qwen2.5, Qwen3, QVQ 等
- **智谱AI**: GLM-4, GLM-4.5, GLM-Z1 等
- **DeepSeek**: DeepSeek-Chat, DeepSeek-Reasoner
- **月之暗面**: Kimi, Moonshot 系列
- **Google**: Gemini 1.5, Gemini 2.0, Gemini 2.5
- **百川智能**: Baichuan3, Baichuan4
- **零一万物**: Yi-Lightning, Yi-Vision
- **MiniMax**: MiniMax-Text, MiniMax-M1
- **Mistral**: Mistral Large, Codestral
- **Groq**: Llama3, Mixtral 等
- **XAI**: Grok-2, Grok-3, Grok-4
- **百度文心**: ERNIE 系列
- **阶跃星辰**: Step-1, Step-2 系列
- **本地模型**: 支持本地部署的模型

#### 核心功能

- **统一接口**: 所有模型使用相同的API接口
- **流式响应**: 支持实时流式输出
- **多模态**: 支持图像、音频输入的模型
- **工具调用**: 支持Function Calling的模型
- **上下文管理**: 自动处理上下文长度限制
- **令牌统计**: 精确的令牌计数和使用统计
- **速率限制**: 内置速率限制和重试机制
- **响应格式**: 支持JSON模式等结构化输出

### 工作流设计框架

- **可视化节点**: 丰富的预置节点库
- **灵活连接**: 节点间的数据流连接
- **批量处理**: 支持列表输入的批量处理
- **代码执行**: 内置Python代码执行节点
- **文件处理**: 文档读取、图像处理、音频处理
- **数据输出**: 表格、文档、图表等多种输出格式

## 🔧 安装和配置

### 依赖要求

- Python 3.10+
- 各模型API密钥（按需配置）

### 可选依赖

```bash
# 服务器功能
pip install vectorvein[server]

# Redis缓存
pip install vectorvein[redis]

# 磁盘缓存
pip install vectorvein[diskcache]

# Google Vertex AI
pip install vectorvein[vertex]

# AWS Bedrock
pip install vectorvein[bedrock]
```

### 设置配置

```python
from vectorvein.settings import settings

# 通过字典配置（v2 版本）
settings_dict = {
    "rate_limit": {
        "enabled": True,
        "backend": "redis",  # 或 "diskcache"
        "redis": {
            "host": "127.0.0.1",
            "port": 6379,
            "db": 0,
        },
        "diskcache": {
            "cache_dir": ".rate_limit_cache",
        },
        "default_rpm": 60,
        "default_tpm": 1000000,
    },
    "endpoints": [
        {
            "id": "anthropic-default",
            "api_base": "https://api.anthropic.com",
            "api_key": "sk-ant-...",
            "rpm": 60,
            "tpm": 1000000,
            "concurrent_requests": 5
        },
        {
            "id": "openai-default",
            "api_base": "https://api.openai.com/v1", 
            "api_key": "sk-...",
            "rpm": 3500,
            "tpm": 90000,
            "concurrent_requests": 10
        },
        {
            "id": "qwen-default",
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": "sk-...",
            "rpm": 100,
            "tpm": 1000000
        },
        {
            "id": "azure-openai",
            "region": "East US",
            "api_base": "https://your-resource.openai.azure.com",
            "api_key": "your-azure-key",
            "rpm": 900,
            "tpm": 150000,
            "is_azure": True
        },
        {
            "id": "vertex-anthropic",
            "region": "europe-west1",
            "api_base": "https://europe-west1-aiplatform.googleapis.com",
            "credentials": {
                "token": "...",
                "refresh_token": "...",
                "client_id": "...",
                "client_secret": "...",
                "quota_project_id": "your-project-id"
            },
            "is_vertex": True
        }
    ],
    "anthropic": {
        "models": {
            "claude-3-7-sonnet-20250219": {
                "id": "claude-3-7-sonnet-20250219",
                "endpoints": ["anthropic-default"],
                "context_length": 200000,
                "max_output_tokens": 8192,
                "function_call_available": True,
                "native_multimodal": True
            },
            "claude-3-5-sonnet-20240620": {
                "id": "claude-3-5-sonnet@20240620",
                "endpoints": ["vertex-anthropic"],
                "context_length": 200000,
                "max_output_tokens": 8192,
                "function_call_available": True,
                "native_multimodal": True
            }
        }
    },
    "openai": {
        "models": {
            "gpt-4o": {
                "id": "gpt-4o",
                "endpoints": ["openai-default", "azure-openai"],
                "context_length": 128000,
                "max_output_tokens": 16384,
                "function_call_available": True,
                "response_format_available": True,
                "native_multimodal": True
            },
            "gpt-4o-mini": {
                "id": "gpt-4o-mini",
                "endpoints": ["openai-default"],
                "context_length": 128000,
                "max_output_tokens": 16384,
                "function_call_available": True,
                "response_format_available": True,
                "native_multimodal": True
            }
        }
    },
    "qwen": {
        "models": {
            "qwen3-32b": {
                "id": "qwen3-32b", 
                "endpoints": ["qwen-default"],
                "context_length": 32768,
                "max_output_tokens": 8192,
                "function_call_available": True,
                "response_format_available": True,
                "native_multimodal": False
            },
            "qwen2.5-72b-instruct": {
                "id": "qwen2.5-72b-instruct",
                "endpoints": ["qwen-default"],
                "context_length": 131072,
                "max_output_tokens": 8192,
                "function_call_available": True,
                "response_format_available": True,
                "native_multimodal": False
            }
        }
    }
}
settings.load(settings_dict)

# 或通过文件配置
settings.load_from_file("config.json")
```

## 📖 详细文档

### API 客户端详细使用

#### 访问密钥管理

```python
from vectorvein.api import VectorVeinClient

client = VectorVeinClient(api_key="YOUR_API_KEY")

# 创建访问密钥
keys = client.create_access_keys(
    access_key_type="L",  # L: 长期, M: 多次, O: 一次性
    app_id="YOUR_APP_ID",
    count=1,
    max_credits=500,
    description="测试密钥"
)

# 获取访问密钥信息
keys_info = client.get_access_keys(["ACCESS_KEY_1", "ACCESS_KEY_2"])

# 列出访问密钥
response = client.list_access_keys(
    page=1,
    page_size=10,
    sort_field="create_time",
    sort_order="descend"
)

# 更新访问密钥
client.update_access_keys(
    access_key="ACCESS_KEY",
    description="更新的描述"
)

# 删除访问密钥
client.delete_access_keys(
    app_id="YOUR_APP_ID",
    access_keys=["ACCESS_KEY_1", "ACCESS_KEY_2"]
)
```

#### 生成VApp访问链接

```python
url = client.generate_vapp_url(
    app_id="YOUR_APP_ID",
    access_key="YOUR_ACCESS_KEY",
    key_id="YOUR_KEY_ID"
)
print(f"VApp访问链接: {url}")
```

### 聊天客户端高级用法

#### 工具调用（Function Calling）

```python
from vectorvein.chat_clients import create_chat_client, BackendType

client = create_chat_client(BackendType.OpenAI, model="gpt-4o")

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取指定城市的天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"}
            },
            "required": ["city"]
        }
    }
}]

response = client.create_completion(
    messages=[{"role": "user", "content": "北京今天天气怎么样？"}],
    tools=tools
)

if response.tool_calls:
    for tool_call in response.tool_calls:
        print(f"调用工具: {tool_call.function.name}")
        print(f"参数: {tool_call.function.arguments}")
```

#### 多模态输入

```python
client = create_chat_client(BackendType.Anthropic, model="claude-3-7-sonnet-20250219")

messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "这张图片里有什么？"},
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": "base64_encoded_image_data"
            }
        }
    ]
}]

response = client.create_completion(messages)
```

#### 结构化输出

```python
client = create_chat_client(BackendType.OpenAI, model="gpt-4o")

response = client.create_completion(
    messages=[{"role": "user", "content": "分析以下数据并返回JSON格式"}],
    response_format={"type": "json_object"}
)
```

### 工作流节点参考

#### LLM 节点

```python
from vectorvein.workflow.nodes.llms import Claude, OpenAI, AliyunQwen

# Claude 节点
claude = Claude()
claude.ports["llm_model"].value = "claude-3-7-sonnet-20250219"
claude.ports["temperature"].value = 0.7
claude.ports["prompt"].show = True

# OpenAI 节点
openai = OpenAI()
openai.ports["llm_model"].value = "gpt-4o"
openai.ports["response_format"].value = "json_object"

# 通义千问节点
qwen = AliyunQwen()
qwen.ports["llm_model"].value = "qwen3-32b"
```

#### 文本处理节点

```python
from vectorvein.workflow.nodes.text_processing import (
    TemplateCompose, TextSplitters, TextReplace
)

# 文本合成
template = TemplateCompose()
template.add_port(name="标题", port_type="text", show=True)
template.add_port(name="内容", port_type="textarea", show=True)
template.ports["template"].value = "# {{标题}}\n\n{{内容}}"

# 文本分割
splitter = TextSplitters()
splitter.ports["split_method"].value = "delimiter"
splitter.ports["delimiter"].value = "\n"
splitter.ports["text"].show = True

# 文本替换
replacer = TextReplace()
replacer.ports["old_text"].value = "旧文本"
replacer.ports["new_text"].value = "新文本"
replacer.ports["text"].show = True
```

#### 文件处理节点

```python
from vectorvein.workflow.nodes.file_processing import FileLoader

loader = FileLoader()
loader.ports["parse_quality"].value = "high"  # 高质量解析
loader.ports["files"].show = True  # 显示文件上传界面
```

#### 输出节点

```python
from vectorvein.workflow.nodes.output import Text, Table, Document

# 文本输出
text_output = Text()
text_output.ports["output_title"].value = "结果"

# 表格输出
table_output = Table()

# 文档输出
doc_output = Document()
doc_output.ports["file_name"].value = "报告"
doc_output.ports["export_type"].value = ".xlsx"
```

## 🔍 异常处理

```python
from vectorvein.api import (
    VectorVeinAPIError, APIKeyError, WorkflowError, 
    AccessKeyError, RequestError, TimeoutError
)

try:
    result = client.run_workflow(wid="invalid", input_fields=[])
except APIKeyError as e:
    print(f"API密钥错误: {e}")
except WorkflowError as e:
    print(f"工作流错误: {e}")
except TimeoutError as e:
    print(f"请求超时: {e}")
except VectorVeinAPIError as e:
    print(f"API错误: {e.message}, 状态码: {e.status_code}")
```

## 🧪 测试

```bash
# 安装开发依赖
pip install -e .[dev]

# 运行测试
pytest tests/

# 运行特定测试
pytest tests/test_simple.py -v

# 生成覆盖率报告
pytest --cov=vectorvein tests/
```

## 📝 开发指南

### 项目结构

```
src/vectorvein/
├── api/                 # VectorVein API客户端
│   ├── client.py       # 主要客户端类
│   ├── models.py       # 数据模型
│   └── exceptions.py   # 异常定义
├── chat_clients/        # 聊天客户端
│   ├── __init__.py     # 客户端工厂函数
│   ├── base_client.py  # 基础客户端类
│   ├── anthropic_client.py  # Claude客户端
│   ├── openai_client.py     # OpenAI客户端
│   └── ...             # 其他模型客户端
├── workflow/           # 工作流设计框架
│   ├── graph/          # 图结构定义
│   ├── nodes/          # 节点定义
│   └── utils/          # 工具函数
├── settings/           # 配置管理
├── types/              # 类型定义
└── utilities/          # 实用工具
```

### 贡献代码

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范

- 使用 `ruff` 进行代码格式化和检查
- 遵循 Python 类型提示
- 编写测试用例覆盖新功能
- 更新相关文档

## 🤝 社区和支持

- **文档**: [官方文档](https://docs.vectorvein.com)
- **问题反馈**: [GitHub Issues](https://github.com/vectorvein/python-vectorvein/issues)
- **讨论**: [GitHub Discussions](https://github.com/vectorvein/python-vectorvein/discussions)
- **更新日志**: [CHANGELOG.md](CHANGELOG.md)

## 📜 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有为 VectorVein Python SDK 做出贡献的开发者和用户。

---

**注意事项**：
1. 请妥善保管您的API密钥，不要将其泄露给他人
2. API调用有速率限制，请合理使用
3. 建议在生产环境中使用异步方式运行工作流
4. 不同模型支持的功能可能有所差异，请参考具体模型文档