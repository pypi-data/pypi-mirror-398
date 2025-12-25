# @Author: Bi Ying
# @Date:   2024-07-26 14:48:55
import re
import json
from functools import cached_property
from collections.abc import Generator, AsyncGenerator, Iterable
from typing import Any, TYPE_CHECKING, overload, Literal

import httpx
from openai import OpenAI, AsyncOpenAI, AzureOpenAI, AsyncAzureOpenAI
from openai._types import Headers, Query, Body
from openai.types.shared_params.metadata import Metadata
from openai.types.completion_usage import PromptTokensDetails
from openai.types.chat.completion_create_params import ResponseFormat
from openai.types.chat.chat_completion_modality import ChatCompletionModality
from openai.types.chat.chat_completion_audio_param import ChatCompletionAudioParam
from openai.types.chat.chat_completion_reasoning_effort import ChatCompletionReasoningEffort
from openai.types.chat.chat_completion_stream_options_param import ChatCompletionStreamOptionsParam
from openai.types.chat.chat_completion_prediction_content_param import ChatCompletionPredictionContentParam
from openai.types.responses.function_tool_param import FunctionToolParam as ResponsesFunctionToolParam
from anthropic.types.thinking_config_param import ThinkingConfigParam

from .base_client import BaseChatClient, BaseAsyncChatClient
from .utils import (
    cutoff_messages,
    get_message_token_counts,
    ToolCallContentProcessor,
    generate_tool_use_system_prompt,
)
from ..types import defaults as defs
from ..types.enums import ContextLengthControlType, BackendType
from ..types.llm_parameters import (
    NotGiven,
    NOT_GIVEN,
    OPENAI_NOT_GIVEN,
    ToolParam,
    ToolChoice,
    OpenAINotGiven,
    AnthropicNotGiven,
    Usage,
    ChatCompletionMessage,
    ChatCompletionDeltaMessage,
)

if TYPE_CHECKING:
    from ..settings import Settings
    from ..types.settings import SettingsDict


def is_gemini_3_model(model_id: str | None, backend: BackendType) -> bool:
    """Check if the current model is a Gemini 3 series model."""
    return backend == BackendType.Gemini and bool(model_id and str(model_id).startswith("gemini-3"))


def get_thinking_tags(backend: BackendType) -> tuple[str, str]:
    """Get the appropriate thinking tags for the given backend.

    Args:
        backend: The backend type

    Returns:
        Tuple of (start_tag, end_tag) for thinking content
    """
    if backend == BackendType.Gemini:
        return ("<thought>", "</thought>")
    else:
        return ("<think>", "</think>")


def process_thinking_content(buffer: str, in_reasoning: bool, start_tag: str, end_tag: str) -> tuple[str, str, str, bool]:
    """Process buffer content to extract thinking tags.

    Args:
        buffer: Content buffer to process
        in_reasoning: Whether currently inside thinking tags
        start_tag: Opening thinking tag
        end_tag: Closing thinking tag

    Returns:
        Tuple of (remaining_buffer, output_content, reasoning_content, new_in_reasoning_state)
    """
    current_output_content = ""
    current_reasoning_content = ""

    while buffer:
        if not in_reasoning:
            start_pos = buffer.find(start_tag)
            if start_pos != -1:
                # Found start tag
                if start_pos > 0:
                    current_output_content += buffer[:start_pos]
                buffer = buffer[start_pos + len(start_tag) :]
                in_reasoning = True
            else:
                # No start tag found, output all content
                current_output_content += buffer
                buffer = ""
        else:
            end_pos = buffer.find(end_tag)
            if end_pos != -1:
                # Found end tag
                current_reasoning_content += buffer[:end_pos]
                buffer = buffer[end_pos + len(end_tag) :]
                in_reasoning = False
            else:
                # No end tag found, accumulate as reasoning content
                current_reasoning_content += buffer
                buffer = ""

    return buffer, current_output_content, current_reasoning_content, in_reasoning


def tool_schema_for_response_api(tool: ToolParam) -> ResponsesFunctionToolParam:
    return {
        "name": tool["function"]["name"],
        "description": tool["function"]["description"],
        "parameters": tool["function"]["parameters"],
        "strict": tool["function"].get("strict", False),
        "type": "function",
    }


class OpenAICompatibleChatClient(BaseChatClient):
    DEFAULT_MODEL: str = ""
    BACKEND_NAME: BackendType

    def __init__(
        self,
        model: str = "",
        stream: bool = True,
        temperature: float | None | NotGiven = NOT_GIVEN,
        context_length_control: ContextLengthControlType = defs.CONTEXT_LENGTH_CONTROL,
        random_endpoint: bool = True,
        endpoint_id: str = "",
        http_client: httpx.Client | None = None,
        backend_name: str | None = None,
        settings: "Settings | SettingsDict | None" = None,  # Use default settings if not provided
    ):
        super().__init__(
            model,
            stream,
            temperature,
            context_length_control,
            random_endpoint,
            endpoint_id,
            http_client,
            backend_name,
            settings,
        )
        self.model_id = None
        self.endpoint = None

    @cached_property
    def raw_client(self) -> OpenAI | AzureOpenAI:
        self.endpoint, self.model_id = self._set_endpoint()

        if self.endpoint.proxy and self.http_client is None:
            self.http_client = httpx.Client(proxy=self.endpoint.proxy)

        if self.endpoint.is_azure or self.endpoint.endpoint_type == "openai_azure":
            if self.endpoint.api_base is None:
                raise ValueError("Azure endpoint is not set")
            return AzureOpenAI(
                azure_endpoint=self.endpoint.api_base,
                api_key=self.endpoint.api_key,
                api_version="2025-04-01-preview",
                http_client=self.http_client,
            )
        else:
            return OpenAI(
                api_key=self.endpoint.api_key,
                base_url=self.endpoint.api_base,
                http_client=self.http_client,
            )

    @overload
    def create_completion(
        self,
        *,
        messages: list,
        model: str | None = None,
        stream: Literal[False] = False,
        temperature: float | None | NotGiven = NOT_GIVEN,
        max_tokens: int | None | NotGiven = None,
        tools: Iterable[ToolParam] | NotGiven = NOT_GIVEN,
        tool_choice: ToolChoice | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        stream_options: ChatCompletionStreamOptionsParam | NotGiven = NOT_GIVEN,
        top_p: float | NotGiven | None = NOT_GIVEN,
        skip_cutoff: bool = False,
        audio: ChatCompletionAudioParam | OpenAINotGiven | None = NOT_GIVEN,
        frequency_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        logit_bias: dict[str, int] | OpenAINotGiven | None = NOT_GIVEN,
        logprobs: bool | OpenAINotGiven | None = NOT_GIVEN,
        max_completion_tokens: int | OpenAINotGiven | None = NOT_GIVEN,
        metadata: Metadata | OpenAINotGiven | None = NOT_GIVEN,
        modalities: list[ChatCompletionModality] | OpenAINotGiven | None = NOT_GIVEN,
        n: int | OpenAINotGiven | None = NOT_GIVEN,
        parallel_tool_calls: bool | OpenAINotGiven = NOT_GIVEN,
        prediction: ChatCompletionPredictionContentParam | OpenAINotGiven | None = NOT_GIVEN,
        presence_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        reasoning_effort: ChatCompletionReasoningEffort | OpenAINotGiven | None = NOT_GIVEN,
        thinking: ThinkingConfigParam | None | NotGiven = NOT_GIVEN,
        seed: int | OpenAINotGiven | None = NOT_GIVEN,
        service_tier: Literal["auto", "default"] | OpenAINotGiven | None = NOT_GIVEN,
        stop: str | list[str] | OpenAINotGiven | None = NOT_GIVEN,
        store: bool | OpenAINotGiven | None = NOT_GIVEN,
        top_logprobs: int | OpenAINotGiven | None = NOT_GIVEN,
        user: str | OpenAINotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | OpenAINotGiven = NOT_GIVEN,
    ) -> ChatCompletionMessage:
        pass

    @overload
    def create_completion(
        self,
        *,
        messages: list,
        model: str | None = None,
        stream: Literal[True],
        temperature: float | None | NotGiven = NOT_GIVEN,
        max_tokens: int | None | NotGiven = None,
        tools: Iterable[ToolParam] | NotGiven = NOT_GIVEN,
        tool_choice: ToolChoice | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        stream_options: ChatCompletionStreamOptionsParam | NotGiven = NOT_GIVEN,
        top_p: float | NotGiven | None = NOT_GIVEN,
        skip_cutoff: bool = False,
        audio: ChatCompletionAudioParam | OpenAINotGiven | None = NOT_GIVEN,
        frequency_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        logit_bias: dict[str, int] | OpenAINotGiven | None = NOT_GIVEN,
        logprobs: bool | OpenAINotGiven | None = NOT_GIVEN,
        max_completion_tokens: int | OpenAINotGiven | None = NOT_GIVEN,
        metadata: Metadata | OpenAINotGiven | None = NOT_GIVEN,
        modalities: list[ChatCompletionModality] | OpenAINotGiven | None = NOT_GIVEN,
        n: int | OpenAINotGiven | None = NOT_GIVEN,
        parallel_tool_calls: bool | OpenAINotGiven = NOT_GIVEN,
        prediction: ChatCompletionPredictionContentParam | OpenAINotGiven | None = NOT_GIVEN,
        presence_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        reasoning_effort: ChatCompletionReasoningEffort | OpenAINotGiven | None = NOT_GIVEN,
        thinking: ThinkingConfigParam | None | NotGiven = NOT_GIVEN,
        seed: int | OpenAINotGiven | None = NOT_GIVEN,
        service_tier: Literal["auto", "default"] | OpenAINotGiven | None = NOT_GIVEN,
        stop: str | list[str] | OpenAINotGiven | None = NOT_GIVEN,
        store: bool | OpenAINotGiven | None = NOT_GIVEN,
        top_logprobs: int | OpenAINotGiven | None = NOT_GIVEN,
        user: str | OpenAINotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | OpenAINotGiven = NOT_GIVEN,
    ) -> Generator[ChatCompletionDeltaMessage, Any, None]:
        pass

    @overload
    def create_completion(
        self,
        *,
        messages: list,
        model: str | None = None,
        stream: bool,
        temperature: float | None | NotGiven = NOT_GIVEN,
        max_tokens: int | None | NotGiven = None,
        tools: Iterable[ToolParam] | NotGiven = NOT_GIVEN,
        tool_choice: ToolChoice | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        stream_options: ChatCompletionStreamOptionsParam | NotGiven = NOT_GIVEN,
        top_p: float | NotGiven | None = NOT_GIVEN,
        skip_cutoff: bool = False,
        audio: ChatCompletionAudioParam | OpenAINotGiven | None = NOT_GIVEN,
        frequency_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        logit_bias: dict[str, int] | OpenAINotGiven | None = NOT_GIVEN,
        logprobs: bool | OpenAINotGiven | None = NOT_GIVEN,
        max_completion_tokens: int | OpenAINotGiven | None = NOT_GIVEN,
        metadata: Metadata | OpenAINotGiven | None = NOT_GIVEN,
        modalities: list[ChatCompletionModality] | OpenAINotGiven | None = NOT_GIVEN,
        n: int | OpenAINotGiven | None = NOT_GIVEN,
        parallel_tool_calls: bool | OpenAINotGiven = NOT_GIVEN,
        prediction: ChatCompletionPredictionContentParam | OpenAINotGiven | None = NOT_GIVEN,
        presence_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        reasoning_effort: ChatCompletionReasoningEffort | OpenAINotGiven | None = NOT_GIVEN,
        thinking: ThinkingConfigParam | None | NotGiven = NOT_GIVEN,
        seed: int | OpenAINotGiven | None = NOT_GIVEN,
        service_tier: Literal["auto", "default"] | OpenAINotGiven | None = NOT_GIVEN,
        stop: str | list[str] | OpenAINotGiven | None = NOT_GIVEN,
        store: bool | OpenAINotGiven | None = NOT_GIVEN,
        top_logprobs: int | OpenAINotGiven | None = NOT_GIVEN,
        user: str | OpenAINotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | OpenAINotGiven = NOT_GIVEN,
    ) -> ChatCompletionMessage | Generator[ChatCompletionDeltaMessage, Any, None]:
        pass

    def create_completion(
        self,
        *,
        messages: list,
        model: str | None = None,
        stream: Literal[False] | Literal[True] = False,
        temperature: float | None | NotGiven = NOT_GIVEN,
        max_tokens: int | None | NotGiven = None,
        tools: Iterable[ToolParam] | NotGiven = NOT_GIVEN,
        tool_choice: ToolChoice | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        stream_options: ChatCompletionStreamOptionsParam | NotGiven = NOT_GIVEN,
        top_p: float | NotGiven | None = NOT_GIVEN,
        skip_cutoff: bool = False,
        audio: ChatCompletionAudioParam | OpenAINotGiven | None = NOT_GIVEN,
        frequency_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        logit_bias: dict[str, int] | OpenAINotGiven | None = NOT_GIVEN,
        logprobs: bool | OpenAINotGiven | None = NOT_GIVEN,
        max_completion_tokens: int | OpenAINotGiven | None = NOT_GIVEN,
        metadata: Metadata | OpenAINotGiven | None = NOT_GIVEN,
        modalities: list[ChatCompletionModality] | OpenAINotGiven | None = NOT_GIVEN,
        n: int | OpenAINotGiven | None = NOT_GIVEN,
        parallel_tool_calls: bool | OpenAINotGiven = NOT_GIVEN,
        prediction: ChatCompletionPredictionContentParam | OpenAINotGiven | None = NOT_GIVEN,
        presence_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        reasoning_effort: ChatCompletionReasoningEffort | OpenAINotGiven | None = NOT_GIVEN,
        thinking: ThinkingConfigParam | None | NotGiven = NOT_GIVEN,
        seed: int | OpenAINotGiven | None = NOT_GIVEN,
        service_tier: Literal["auto", "default"] | OpenAINotGiven | None = NOT_GIVEN,
        stop: str | list[str] | OpenAINotGiven | None = NOT_GIVEN,
        store: bool | OpenAINotGiven | None = NOT_GIVEN,
        top_logprobs: int | OpenAINotGiven | None = NOT_GIVEN,
        user: str | OpenAINotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | OpenAINotGiven = NOT_GIVEN,
    ):
        if model is not None:
            self.model = model
        if stream is not None:
            self.stream = stream
        if isinstance(temperature, AnthropicNotGiven):
            temperature = NOT_GIVEN
        if temperature is not None:
            self.temperature = temperature
        if isinstance(top_p, AnthropicNotGiven):
            top_p = NOT_GIVEN
        if isinstance(max_tokens, AnthropicNotGiven):
            max_tokens = NOT_GIVEN
        if isinstance(stream_options, AnthropicNotGiven):
            stream_options = NOT_GIVEN

        raw_client = self.raw_client  # 调用完 self.raw_client 后，self.model_id 会被赋值
        self.model_setting = self.backend_settings.models[self.model]
        if self.model_id is None:
            self.model_id = self.model_setting.id

        is_gemini3 = is_gemini_3_model(self.model_id, self.backend_name)

        # Get thinking tags for the current backend
        start_tag, end_tag = get_thinking_tags(self.backend_name)

        if not skip_cutoff and self.context_length_control == ContextLengthControlType.Latest:
            messages = cutoff_messages(
                messages,
                max_count=self.model_setting.context_length,
                backend=self.BACKEND_NAME,
                model=self.model,
            )

        if tools:
            if self.model_setting.function_call_available:
                _tools = tools
                if self.BACKEND_NAME.value == BackendType.MiniMax.value:  # MiniMax 就非要搞特殊
                    _tools = []
                    for tool in tools:
                        _tools.append(
                            {
                                "type": "function",
                                "function": {
                                    "name": tool["function"]["name"],
                                    "description": tool["function"].get("description", ""),
                                    "parameters": json.dumps(tool["function"].get("parameters", {})),
                                },
                            }
                        )
                tools_params = {"tools": _tools, "tool_choice": tool_choice}
            else:
                tools_str = json.dumps(tools, ensure_ascii=False, indent=None)
                additional_system_prompt = generate_tool_use_system_prompt(tools=tools_str)
                if messages and messages[0].get("role") == "system":
                    messages[0]["content"] += "\n\n" + additional_system_prompt
                else:
                    messages.insert(0, {"role": "system", "content": additional_system_prompt})
                tools_params = {}
        else:
            tools_params = {}

        # 只有 None 的时候才自动计算，否则就设置为 NOT_GIVEN
        if max_tokens is None and not max_completion_tokens:
            max_output_tokens = self.model_setting.max_output_tokens
            native_multimodal = self.model_setting.native_multimodal
            token_counts = get_message_token_counts(messages=messages, tools=tools, model=self.model, native_multimodal=native_multimodal)
            if max_output_tokens is not None:
                max_tokens = self.model_setting.context_length - token_counts - 64
                max_tokens = min(max(max_tokens, 1), max_output_tokens)
            else:
                max_tokens = self.model_setting.context_length - token_counts - 64

        if "o3-mini" in self.model_id or "o4-mini" in self.model_id or "gpt-5" in self.model_id:
            max_completion_tokens = max_tokens
            max_tokens = NOT_GIVEN

        self._acquire_rate_limit(self.endpoint, self.model, messages)

        # When endpoint is configured to use the new Responses API
        if self.endpoint.response_api:
            # Compute max_output_tokens for Responses API
            req_max_output_tokens = None
            if max_completion_tokens is not NOT_GIVEN and max_completion_tokens is not None:
                req_max_output_tokens = max_completion_tokens  # type: ignore[assignment]
            elif max_tokens is not NOT_GIVEN and max_tokens is not None:
                req_max_output_tokens = max_tokens  # type: ignore[assignment]

            if tools_params.get("tools", []):
                tools_params["tools"] = [tool_schema_for_response_api(tool) for tool in tools_params["tools"]]

            if self.stream:
                # Streaming via Responses API
                def generator():
                    stream_ctx = raw_client.responses.stream(
                        model=self.model_id,
                        input=messages,
                        temperature=None if self.temperature is NOT_GIVEN else self.temperature,
                        top_p=None if top_p is NOT_GIVEN else top_p,
                        max_output_tokens=req_max_output_tokens,
                        **tools_params,  # type: ignore[arg-type]
                    )

                    usage = None
                    final_tool_calls: dict[int, dict] = {}
                    with stream_ctx as stream_response:
                        for event in stream_response:
                            et = event.type

                            if et == "response.output_text.delta":
                                if event.delta:
                                    yield ChatCompletionDeltaMessage(content=event.delta)
                                continue

                            if et == "response.output_item.added":
                                item = event.item
                                output_index = event.output_index
                                if item and item.type == "function_call" and output_index is not None:
                                    extra_content = getattr(item, "extra_content", None)
                                    final_tool_calls[output_index] = {
                                        "id": item.id,
                                        "call_id": item.call_id,
                                        "name": item.name,
                                        "arguments": item.arguments or "",
                                        "extra_content": extra_content,
                                    }
                                    yield ChatCompletionDeltaMessage(
                                        tool_calls=[
                                            {
                                                "index": output_index,
                                                "id": item.id,
                                                "type": "function",
                                                "function": {
                                                    "name": item.name,
                                                    "arguments": "",
                                                },
                                            }
                                        ]
                                    )
                                continue

                            if et == "response.function_call_arguments.delta":
                                output_index = event.output_index
                                delta = event.delta
                                if output_index is not None and delta is not None:
                                    if output_index in final_tool_calls:
                                        final_tool_calls[output_index]["arguments"] += delta
                                        call_id = final_tool_calls[output_index].get("id")
                                    else:
                                        call_id = None
                                    yield ChatCompletionDeltaMessage(
                                        tool_calls=[
                                            {
                                                "index": output_index,
                                                "id": call_id,
                                                "type": "function",
                                                "function": {"arguments": delta},
                                            }
                                        ]
                                    )
                                continue

                            if et == "response.function_call_arguments.done":
                                output_index = event.output_index
                                if output_index is not None and output_index in final_tool_calls:
                                    f = final_tool_calls[output_index]
                                    raw_content = None
                                    if is_gemini3:
                                        extra_content = f.get("extra_content")
                                        if isinstance(extra_content, dict) and extra_content.get("google"):
                                            raw_content = {"google": extra_content["google"]}
                                    yield ChatCompletionDeltaMessage(
                                        tool_calls=[
                                            {
                                                "index": output_index,
                                                "id": f.get("id"),
                                                "type": "function",
                                                "function": {
                                                    "name": f.get("name"),
                                                    "arguments": f.get("arguments", ""),
                                                },
                                            }
                                        ],
                                        raw_content=raw_content,
                                    )
                                continue

                            if et == "response.output_item.done":
                                item = event.item
                                output_index = event.output_index
                                if item and item.type == "function_call" and output_index is not None:
                                    yield ChatCompletionDeltaMessage(
                                        tool_calls=[
                                            {
                                                "index": output_index,
                                                "id": item.id,
                                                "type": "function",
                                                "function": {
                                                    "name": item.name,
                                                    "arguments": item.arguments,
                                                },
                                            }
                                        ]
                                    )
                                continue

                            if et == "response.completed":
                                final_resp = event.response
                                if final_resp and final_resp.usage:
                                    u = final_resp.usage
                                    usage = Usage(
                                        completion_tokens=u.output_tokens or 0,
                                        prompt_tokens=u.input_tokens or 0,
                                        total_tokens=(u.input_tokens or 0) + (u.output_tokens or 0),
                                    )
                                continue

                            if et in ("response.error", "error"):
                                # surface the error message if present
                                raise RuntimeError(f"Responses stream error: {event.error}")

                        if usage:
                            yield ChatCompletionDeltaMessage(usage=usage)

                return generator()
            else:
                # Non-streaming via Responses API
                response = raw_client.responses.create(
                    model=self.model_id,
                    input=messages,
                    temperature=None if self.temperature is NOT_GIVEN else self.temperature,
                    top_p=None if top_p is NOT_GIVEN else top_p,
                    max_output_tokens=req_max_output_tokens,
                    **tools_params,  # type: ignore[arg-type]
                )

                # Build ChatCompletion-like message
                content_text = response.output_text
                tool_calls = []
                for item in (response.output or []):
                    if item.type == "function_call":
                        tool_calls.append(
                            {
                                "id": item.call_id or item.id,
                                "type": "function",
                                "function": {
                                    "name": item.name,
                                    "arguments": item.arguments,
                                },
                            }
                        )

                usage = None
                if response.usage:
                    u = response.usage
                    usage = Usage(
                        completion_tokens=u.output_tokens or 0,
                        prompt_tokens=u.input_tokens or 0,
                        total_tokens=(u.input_tokens or 0) + (u.output_tokens or 0),
                    )

                result = {
                    "content": content_text,
                    "tool_calls": tool_calls or None,
                    "usage": usage,
                }
                return ChatCompletionMessage(**result)

        if self.stream:
            stream_response = raw_client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                stream=True,
                temperature=self.temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                audio=audio,
                frequency_penalty=frequency_penalty,
                logit_bias=logit_bias,
                logprobs=logprobs,
                max_completion_tokens=max_completion_tokens,
                metadata=metadata,
                modalities=modalities,
                n=n,
                parallel_tool_calls=parallel_tool_calls,
                prediction=prediction,
                presence_penalty=presence_penalty,
                reasoning_effort=reasoning_effort,
                seed=seed,
                service_tier=service_tier,
                stop=stop,
                store=store,
                top_logprobs=top_logprobs,
                user=user,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                stream_options=stream_options,
                response_format=response_format if response_format and self.model_setting.response_format_available else OPENAI_NOT_GIVEN,
                **tools_params,  # type: ignore
            )

            def generator():
                full_content = ""
                result = {}
                usage = None
                buffer = ""
                in_reasoning = False
                accumulated_reasoning = []
                accumulated_content = []

                for chunk in stream_response:
                    if chunk.usage and chunk.usage.total_tokens:
                        if getattr(chunk.usage, "cached_tokens", None):  # noqa: B009
                            if getattr(chunk.usage, "prompt_tokens_details", None):  # noqa: B009
                                chunk.usage.prompt_tokens_details.cached_tokens = chunk.usage.cached_tokens  # type: ignore
                            else:
                                chunk.usage.prompt_tokens_details = PromptTokensDetails(
                                    cached_tokens=chunk.usage.cached_tokens  # type: ignore
                                )
                        usage = Usage(
                            completion_tokens=chunk.usage.completion_tokens or 0,
                            prompt_tokens=chunk.usage.prompt_tokens or 0,
                            total_tokens=chunk.usage.total_tokens or 0,
                            prompt_tokens_details=chunk.usage.prompt_tokens_details,
                            completion_tokens_details=chunk.usage.completion_tokens_details,
                        )

                    if not chunk.choices or len(chunk.choices) == 0 or not chunk.choices[0].delta:
                        if usage:
                            yield ChatCompletionDeltaMessage(usage=usage)
                        continue

                    if self.model_setting.function_call_available:
                        if chunk.choices[0].delta.tool_calls:
                            for index, tool_call in enumerate(chunk.choices[0].delta.tool_calls):
                                tool_call.index = index
                                tool_call.type = "function"  # 也是 MiniMax 的不规范导致的问题

                        # 即使支持 function call，也要处理思考标签
                        message = chunk.choices[0].delta.model_dump()
                        if is_gemini3 and chunk.choices[0].delta.tool_calls:
                            google_extras: list[dict] = []
                            for tool_call in chunk.choices[0].delta.tool_calls:
                                extra_content = getattr(tool_call, "extra_content", None)
                                if isinstance(extra_content, dict) and extra_content.get("google"):
                                    google_extras.append(extra_content["google"])
                            if google_extras:
                                message["raw_content"] = {"google": google_extras}
                        delta_content = message.get("content", "")
                        if delta_content:
                            buffer += delta_content

                            # 处理缓冲区中的内容，提取思考标签
                            buffer, current_output_content, current_reasoning_content, in_reasoning = process_thinking_content(buffer, in_reasoning, start_tag, end_tag)

                            # 累积内容
                            if current_output_content:
                                accumulated_content.append(current_output_content)
                            if current_reasoning_content:
                                accumulated_reasoning.append(current_reasoning_content)

                            # 只要有内容变化就产生 delta
                            if current_output_content or current_reasoning_content:
                                if current_output_content:
                                    message["content"] = current_output_content
                                elif current_reasoning_content:
                                    message["reasoning_content"] = current_reasoning_content
                                    message["content"] = ""  # 推理时不输出普通内容
                            else:
                                # 处理后没有产生任何内容（如仅包含 </thought> 标签）
                                # 清空 content 避免标签泄露到输出
                                message["content"] = ""
                                if not message.get("tool_calls"):
                                    # 如果没有任何内容且没有 tool_calls，则跳过这个消息
                                    continue

                        yield ChatCompletionDeltaMessage(**message, usage=usage)
                    else:
                        message = chunk.choices[0].delta.model_dump()
                        delta_content = message.get("content", "")
                        if delta_content:
                            buffer += delta_content

                        # 处理缓冲区中的内容，提取思考标签
                        buffer, current_output_content, current_reasoning_content, in_reasoning = process_thinking_content(buffer, in_reasoning, start_tag, end_tag)

                        # 累积内容
                        if current_output_content:
                            accumulated_content.append(current_output_content)
                        if current_reasoning_content:
                            accumulated_reasoning.append(current_reasoning_content)

                        # 只要有内容变化就产生 delta
                        if current_output_content or current_reasoning_content:
                            if current_output_content:
                                message["content"] = current_output_content
                            elif current_reasoning_content:
                                message["reasoning_content"] = current_reasoning_content
                                message["content"] = ""  # 推理时不输出普通内容

                            if tools:
                                full_content += current_output_content
                                tool_call_data = ToolCallContentProcessor(full_content).tool_calls
                                if tool_call_data:
                                    message["tool_calls"] = tool_call_data["tool_calls"]

                            if full_content in ("<", "<|", "<|▶", "<|▶|") or full_content.startswith("<|▶|>"):
                                message["content"] = ""
                                result = message
                                continue

                            yield ChatCompletionDeltaMessage(**message, usage=usage)
                        elif delta_content:
                            # 有原始内容但处理后没有产生任何内容（如仅包含 </thought> 标签）
                            # 清空并跳过，避免标签泄露到输出
                            pass

                # 处理最后剩余的缓冲区内容
                if buffer:
                    if in_reasoning:
                        accumulated_reasoning.append(buffer)
                    else:
                        accumulated_content.append(buffer)

                    final_message = {}
                    if accumulated_content:
                        final_content = "".join(accumulated_content)
                        if final_content.strip():  # 只有当内容非空时才输出
                            final_message["content"] = final_content

                    if accumulated_reasoning:
                        final_reasoning = "".join(accumulated_reasoning)
                        if final_reasoning.strip():  # 只有当推理内容非空时才输出
                            final_message["reasoning_content"] = final_reasoning

                    if final_message:
                        yield ChatCompletionDeltaMessage(**final_message, usage=usage)

                if result:
                    yield ChatCompletionDeltaMessage(**result, usage=usage)

            return generator()
        else:
            response = raw_client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                stream=False,
                temperature=self.temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                audio=audio,
                frequency_penalty=frequency_penalty,
                logit_bias=logit_bias,
                logprobs=logprobs,
                max_completion_tokens=max_completion_tokens,
                metadata=metadata,
                modalities=modalities,
                n=n,
                parallel_tool_calls=parallel_tool_calls,
                prediction=prediction,
                presence_penalty=presence_penalty,
                reasoning_effort=reasoning_effort,
                seed=seed,
                service_tier=service_tier,
                stop=stop,
                store=store,
                top_logprobs=top_logprobs,
                user=user,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                stream_options=stream_options,
                response_format=response_format if response_format and self.model_setting.response_format_available else OPENAI_NOT_GIVEN,
                **tools_params,  # type: ignore
            )

            if not response.choices:
                raise ValueError(f"No response choices: {response}")

            if response.usage and getattr(response.usage, "cached_tokens", None):  # noqa: B009
                if getattr(response.usage, "prompt_tokens_details", None):  # noqa: B009
                    response.usage.prompt_tokens_details.cached_tokens = response.usage.cached_tokens  # type: ignore
                else:
                    response.usage.prompt_tokens_details = PromptTokensDetails(
                        cached_tokens=response.usage.cached_tokens  # type: ignore
                    )

            result = {
                "content": response.choices[0].message.content,
                "reasoning_content": getattr(response.choices[0].message, "reasoning_content", None),
                "usage": response.usage.model_dump() if response.usage else None,
            }

            if not result["reasoning_content"] and result["content"]:
                # Create dynamic regex pattern based on backend
                think_pattern = f"{re.escape(start_tag)}(.*?){re.escape(end_tag)}"
                think_match = re.search(think_pattern, result["content"], re.DOTALL)
                if think_match:
                    result["reasoning_content"] = think_match.group(1)
                    result["content"] = result["content"].replace(think_match.group(0), "", 1)

            if tools:
                if self.model_setting.function_call_available:
                    if response.choices[0].message.tool_calls:
                        result["tool_calls"] = [{**tool_call.model_dump(), "type": "function"} for tool_call in response.choices[0].message.tool_calls]
                else:
                    tool_call_content_processor = ToolCallContentProcessor(result["content"])
                    tool_call_data = tool_call_content_processor.tool_calls
                    if tool_call_data:
                        result["tool_calls"] = tool_call_data["tool_calls"]
                        result["content"] = tool_call_content_processor.non_tool_content

            # 对 Gemini 3 模型保留 Google 扩展信息（如 thought_signature），以便上层可以按文档转发
            if is_gemini3 and getattr(response.choices[0].message, "tool_calls", None):
                google_extras: list[dict] = []
                for tool_call in response.choices[0].message.tool_calls:
                    extra_content = getattr(tool_call, "extra_content", None)
                    if isinstance(extra_content, dict) and extra_content.get("google"):
                        google_extras.append(extra_content["google"])
                if google_extras:
                    result["raw_content"] = [{"google": google_extras}]

            return ChatCompletionMessage(**result)


class AsyncOpenAICompatibleChatClient(BaseAsyncChatClient):
    DEFAULT_MODEL: str = ""
    BACKEND_NAME: BackendType

    def __init__(
        self,
        model: str = "",
        stream: bool = True,
        temperature: float | None | NotGiven = NOT_GIVEN,
        context_length_control: ContextLengthControlType = defs.CONTEXT_LENGTH_CONTROL,
        random_endpoint: bool = True,
        endpoint_id: str = "",
        http_client: httpx.AsyncClient | None = None,
        backend_name: str | None = None,
        settings: "Settings | SettingsDict | None" = None,  # Use default settings if not provided
    ):
        super().__init__(
            model,
            stream,
            temperature,
            context_length_control,
            random_endpoint,
            endpoint_id,
            http_client,
            backend_name,
            settings,
        )
        self.model_id = None
        self.endpoint = None

    @cached_property
    def raw_client(self):
        self.endpoint, self.model_id = self._set_endpoint()

        if self.endpoint.proxy and self.http_client is None:
            self.http_client = httpx.AsyncClient(proxy=self.endpoint.proxy)

        if self.endpoint.is_azure or self.endpoint.endpoint_type == "openai_azure":
            if self.endpoint.api_base is None:
                raise ValueError("Azure endpoint is not set")
            return AsyncAzureOpenAI(
                azure_endpoint=self.endpoint.api_base,
                api_key=self.endpoint.api_key,
                api_version="2025-04-01-preview",
                http_client=self.http_client,
            )
        else:
            return AsyncOpenAI(
                api_key=self.endpoint.api_key,
                base_url=self.endpoint.api_base,
                http_client=self.http_client,
            )

    @overload
    async def create_completion(
        self,
        *,
        messages: list,
        model: str | None = None,
        stream: Literal[False] = False,
        temperature: float | None | NotGiven = NOT_GIVEN,
        max_tokens: int | None | NotGiven = None,
        tools: Iterable[ToolParam] | NotGiven = NOT_GIVEN,
        tool_choice: ToolChoice | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        stream_options: ChatCompletionStreamOptionsParam | NotGiven = NOT_GIVEN,
        top_p: float | NotGiven | None = NOT_GIVEN,
        skip_cutoff: bool = False,
        audio: ChatCompletionAudioParam | OpenAINotGiven | None = NOT_GIVEN,
        frequency_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        logit_bias: dict[str, int] | OpenAINotGiven | None = NOT_GIVEN,
        logprobs: bool | OpenAINotGiven | None = NOT_GIVEN,
        max_completion_tokens: int | OpenAINotGiven | None = NOT_GIVEN,
        metadata: Metadata | OpenAINotGiven | None = NOT_GIVEN,
        modalities: list[ChatCompletionModality] | OpenAINotGiven | None = NOT_GIVEN,
        n: int | OpenAINotGiven | None = NOT_GIVEN,
        parallel_tool_calls: bool | OpenAINotGiven = NOT_GIVEN,
        prediction: ChatCompletionPredictionContentParam | OpenAINotGiven | None = NOT_GIVEN,
        presence_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        reasoning_effort: ChatCompletionReasoningEffort | OpenAINotGiven | None = NOT_GIVEN,
        thinking: ThinkingConfigParam | None | NotGiven = NOT_GIVEN,
        seed: int | OpenAINotGiven | None = NOT_GIVEN,
        service_tier: Literal["auto", "default"] | OpenAINotGiven | None = NOT_GIVEN,
        stop: str | list[str] | OpenAINotGiven | None = NOT_GIVEN,
        store: bool | OpenAINotGiven | None = NOT_GIVEN,
        top_logprobs: int | OpenAINotGiven | None = NOT_GIVEN,
        user: str | OpenAINotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | OpenAINotGiven = NOT_GIVEN,
    ) -> ChatCompletionMessage:
        pass

    @overload
    async def create_completion(
        self,
        *,
        messages: list,
        model: str | None = None,
        stream: Literal[True],
        temperature: float | None | NotGiven = NOT_GIVEN,
        max_tokens: int | None | NotGiven = None,
        tools: Iterable[ToolParam] | NotGiven = NOT_GIVEN,
        tool_choice: ToolChoice | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        stream_options: ChatCompletionStreamOptionsParam | NotGiven = NOT_GIVEN,
        top_p: float | NotGiven | None = NOT_GIVEN,
        skip_cutoff: bool = False,
        audio: ChatCompletionAudioParam | OpenAINotGiven | None = NOT_GIVEN,
        frequency_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        logit_bias: dict[str, int] | OpenAINotGiven | None = NOT_GIVEN,
        logprobs: bool | OpenAINotGiven | None = NOT_GIVEN,
        max_completion_tokens: int | OpenAINotGiven | None = NOT_GIVEN,
        metadata: Metadata | OpenAINotGiven | None = NOT_GIVEN,
        modalities: list[ChatCompletionModality] | OpenAINotGiven | None = NOT_GIVEN,
        n: int | OpenAINotGiven | None = NOT_GIVEN,
        parallel_tool_calls: bool | OpenAINotGiven = NOT_GIVEN,
        prediction: ChatCompletionPredictionContentParam | OpenAINotGiven | None = NOT_GIVEN,
        presence_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        reasoning_effort: ChatCompletionReasoningEffort | OpenAINotGiven | None = NOT_GIVEN,
        thinking: ThinkingConfigParam | None | NotGiven = NOT_GIVEN,
        seed: int | OpenAINotGiven | None = NOT_GIVEN,
        service_tier: Literal["auto", "default"] | OpenAINotGiven | None = NOT_GIVEN,
        stop: str | list[str] | OpenAINotGiven | None = NOT_GIVEN,
        store: bool | OpenAINotGiven | None = NOT_GIVEN,
        top_logprobs: int | OpenAINotGiven | None = NOT_GIVEN,
        user: str | OpenAINotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | OpenAINotGiven = NOT_GIVEN,
    ) -> AsyncGenerator[ChatCompletionDeltaMessage, Any]:
        pass

    @overload
    async def create_completion(
        self,
        *,
        messages: list,
        model: str | None = None,
        stream: bool,
        temperature: float | None | NotGiven = NOT_GIVEN,
        max_tokens: int | None | NotGiven = None,
        tools: Iterable[ToolParam] | NotGiven = NOT_GIVEN,
        tool_choice: ToolChoice | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        stream_options: ChatCompletionStreamOptionsParam | NotGiven = NOT_GIVEN,
        top_p: float | NotGiven | None = NOT_GIVEN,
        skip_cutoff: bool = False,
        audio: ChatCompletionAudioParam | OpenAINotGiven | None = NOT_GIVEN,
        frequency_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        logit_bias: dict[str, int] | OpenAINotGiven | None = NOT_GIVEN,
        logprobs: bool | OpenAINotGiven | None = NOT_GIVEN,
        max_completion_tokens: int | OpenAINotGiven | None = NOT_GIVEN,
        metadata: Metadata | OpenAINotGiven | None = NOT_GIVEN,
        modalities: list[ChatCompletionModality] | OpenAINotGiven | None = NOT_GIVEN,
        n: int | OpenAINotGiven | None = NOT_GIVEN,
        parallel_tool_calls: bool | OpenAINotGiven = NOT_GIVEN,
        prediction: ChatCompletionPredictionContentParam | OpenAINotGiven | None = NOT_GIVEN,
        presence_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        reasoning_effort: ChatCompletionReasoningEffort | OpenAINotGiven | None = NOT_GIVEN,
        thinking: ThinkingConfigParam | None | NotGiven = NOT_GIVEN,
        seed: int | OpenAINotGiven | None = NOT_GIVEN,
        service_tier: Literal["auto", "default"] | OpenAINotGiven | None = NOT_GIVEN,
        stop: str | list[str] | OpenAINotGiven | None = NOT_GIVEN,
        store: bool | OpenAINotGiven | None = NOT_GIVEN,
        top_logprobs: int | OpenAINotGiven | None = NOT_GIVEN,
        user: str | OpenAINotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | OpenAINotGiven = NOT_GIVEN,
    ) -> ChatCompletionMessage | AsyncGenerator[ChatCompletionDeltaMessage, Any]:
        pass

    async def create_completion(
        self,
        *,
        messages: list,
        model: str | None = None,
        stream: Literal[False] | Literal[True] = False,
        temperature: float | None | NotGiven = NOT_GIVEN,
        max_tokens: int | None | NotGiven = None,
        tools: Iterable[ToolParam] | NotGiven = NOT_GIVEN,
        tool_choice: ToolChoice | NotGiven = NOT_GIVEN,
        response_format: ResponseFormat | NotGiven = NOT_GIVEN,
        stream_options: ChatCompletionStreamOptionsParam | NotGiven = NOT_GIVEN,
        top_p: float | NotGiven | None = NOT_GIVEN,
        skip_cutoff: bool = False,
        audio: ChatCompletionAudioParam | OpenAINotGiven | None = NOT_GIVEN,
        frequency_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        logit_bias: dict[str, int] | OpenAINotGiven | None = NOT_GIVEN,
        logprobs: bool | OpenAINotGiven | None = NOT_GIVEN,
        max_completion_tokens: int | OpenAINotGiven | None = NOT_GIVEN,
        metadata: Metadata | OpenAINotGiven | None = NOT_GIVEN,
        modalities: list[ChatCompletionModality] | OpenAINotGiven | None = NOT_GIVEN,
        n: int | OpenAINotGiven | None = NOT_GIVEN,
        parallel_tool_calls: bool | OpenAINotGiven = NOT_GIVEN,
        prediction: ChatCompletionPredictionContentParam | OpenAINotGiven | None = NOT_GIVEN,
        presence_penalty: float | OpenAINotGiven | None = NOT_GIVEN,
        reasoning_effort: ChatCompletionReasoningEffort | OpenAINotGiven | None = NOT_GIVEN,
        thinking: ThinkingConfigParam | None | NotGiven = NOT_GIVEN,
        seed: int | OpenAINotGiven | None = NOT_GIVEN,
        service_tier: Literal["auto", "default"] | OpenAINotGiven | None = NOT_GIVEN,
        stop: str | list[str] | OpenAINotGiven | None = NOT_GIVEN,
        store: bool | OpenAINotGiven | None = NOT_GIVEN,
        top_logprobs: int | OpenAINotGiven | None = NOT_GIVEN,
        user: str | OpenAINotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | OpenAINotGiven = NOT_GIVEN,
    ) -> ChatCompletionMessage | AsyncGenerator[ChatCompletionDeltaMessage, Any]:
        if model is not None:
            self.model = model
        if stream is not None:
            self.stream = stream
        if isinstance(temperature, AnthropicNotGiven):
            temperature = NOT_GIVEN
        if temperature is not None:
            self.temperature = temperature
        if isinstance(top_p, AnthropicNotGiven):
            top_p = NOT_GIVEN
        if isinstance(max_tokens, AnthropicNotGiven):
            max_tokens = NOT_GIVEN
        if isinstance(stream_options, AnthropicNotGiven):
            stream_options = NOT_GIVEN

        raw_client = self.raw_client  # 调用完 self.raw_client 后，self.model_id 会被赋值
        self.model_setting = self.backend_settings.models[self.model]
        if self.model_id is None:
            self.model_id = self.model_setting.id

        is_gemini3 = is_gemini_3_model(self.model_id, self.backend_name)

        # Get thinking tags for the current backend
        start_tag, end_tag = get_thinking_tags(self.backend_name)

        if not skip_cutoff and self.context_length_control == ContextLengthControlType.Latest:
            messages = cutoff_messages(
                messages,
                max_count=self.model_setting.context_length,
                backend=self.BACKEND_NAME,
                model=self.model,
            )

        if tools:
            if self.model_setting.function_call_available:
                _tools = tools
                if self.BACKEND_NAME.value == BackendType.MiniMax.value:
                    _tools = []
                    for tool in tools:
                        _tools.append(
                            {
                                "type": "function",
                                "function": {
                                    "name": tool["function"]["name"],
                                    "description": tool["function"].get("description", ""),
                                    "parameters": json.dumps(tool["function"].get("parameters", {})),
                                },
                            }
                        )
                tools_params = {"tools": _tools, "tool_choice": tool_choice}
            else:
                tools_str = json.dumps(tools, ensure_ascii=False, indent=None)
                additional_system_prompt = generate_tool_use_system_prompt(tools=tools_str)
                if messages and messages[0].get("role") == "system":
                    messages[0]["content"] += "\n\n" + additional_system_prompt
                else:
                    messages.insert(0, {"role": "system", "content": additional_system_prompt})
                tools_params = {}
        else:
            tools_params = {}

        # 只有 None 的时候才自动计算，否则就设置为 NOT_GIVEN
        if max_tokens is None and not max_completion_tokens:
            max_output_tokens = self.model_setting.max_output_tokens
            native_multimodal = self.model_setting.native_multimodal
            token_counts = get_message_token_counts(messages=messages, tools=tools, model=self.model, native_multimodal=native_multimodal)
            if max_output_tokens is not None:
                max_tokens = self.model_setting.context_length - token_counts - 64
                max_tokens = min(max(max_tokens, 1), max_output_tokens)
            else:
                max_tokens = self.model_setting.context_length - token_counts - 64

        if "o3-mini" in self.model_id or "o4-mini" in self.model_id or "gpt-5" in self.model_id:
            max_completion_tokens = max_tokens
            max_tokens = NOT_GIVEN

        await self._acquire_rate_limit(self.endpoint, self.model, messages)

        # When endpoint is configured to use the new Responses API
        if self.endpoint.response_api:
            req_max_output_tokens = None
            if max_completion_tokens is not NOT_GIVEN and max_completion_tokens is not None:
                req_max_output_tokens = max_completion_tokens  # type: ignore[assignment]
            elif max_tokens is not NOT_GIVEN and max_tokens is not None:
                req_max_output_tokens = max_tokens  # type: ignore[assignment]

            if tools_params.get("tools", []):
                try:
                    tools_params["tools"] = [tool_schema_for_response_api(tool) for tool in tools_params["tools"]]
                except Exception:
                    pass

            if self.stream:

                async def _generator():
                    usage = None
                    final_tool_calls: dict[int, dict] = {}
                    try:
                        # Async streaming via Responses API
                        async with raw_client.responses.stream(
                            model=self.model_id,
                            input=messages,
                            temperature=None if self.temperature is NOT_GIVEN else self.temperature,
                            top_p=None if top_p is NOT_GIVEN else top_p,
                            max_output_tokens=req_max_output_tokens,
                            **tools_params,  # type: ignore[arg-type]
                        ) as stream_response:
                            async for event in stream_response:
                                et = event.type

                                if et == "response.output_text.delta":
                                    if event.delta:
                                        yield ChatCompletionDeltaMessage(content=event.delta)
                                    continue

                                if et == "response.output_item.added":
                                    item = event.item
                                    output_index = event.output_index
                                    if item and item.type == "function_call" and output_index is not None:
                                        extra_content = getattr(item, "extra_content", None)
                                        final_tool_calls[output_index] = {
                                            "id": item.id,
                                            "call_id": item.call_id,
                                            "name": item.name,
                                            "arguments": item.arguments or "",
                                            "extra_content": extra_content,
                                        }
                                        yield ChatCompletionDeltaMessage(
                                            tool_calls=[
                                                {
                                                    "index": output_index,
                                                    "id": item.id,
                                                    "type": "function",
                                                    "function": {
                                                        "name": item.name,
                                                        "arguments": "",
                                                    },
                                                }
                                            ]
                                        )
                                    continue

                                if et == "response.function_call_arguments.delta":
                                    output_index = event.output_index
                                    delta = event.delta
                                    if output_index is not None and delta is not None:
                                        if output_index in final_tool_calls:
                                            final_tool_calls[output_index]["arguments"] += delta
                                            call_id = final_tool_calls[output_index].get("id")
                                        else:
                                            call_id = None
                                        yield ChatCompletionDeltaMessage(
                                            tool_calls=[
                                                {
                                                    "index": output_index,
                                                    "id": call_id,
                                                    "type": "function",
                                                    "function": {"arguments": delta},
                                                }
                                            ]
                                        )
                                    continue

                                if et == "response.function_call_arguments.done":
                                    output_index = event.output_index
                                    if output_index is not None and output_index in final_tool_calls:
                                        f = final_tool_calls[output_index]
                                        raw_content = None
                                        if is_gemini3:
                                            extra_content = f.get("extra_content")
                                            if isinstance(extra_content, dict) and extra_content.get("google"):
                                                raw_content = {"google": extra_content["google"]}
                                        yield ChatCompletionDeltaMessage(
                                            tool_calls=[
                                                {
                                                    "index": output_index,
                                                    "id": f.get("id"),
                                                    "type": "function",
                                                    "function": {
                                                        "name": f.get("name"),
                                                        "arguments": f.get("arguments", ""),
                                                    },
                                                }
                                            ],
                                            raw_content=raw_content,
                                        )
                                    continue

                                if et == "response.output_item.done":
                                    item = event.item
                                    output_index = event.output_index
                                    if item and item.type == "function_call" and output_index is not None:
                                        yield ChatCompletionDeltaMessage(
                                            tool_calls=[
                                                {
                                                    "index": output_index,
                                                    "id": item.id,
                                                    "type": "function",
                                                    "function": {
                                                        "name": item.name,
                                                        "arguments": item.arguments,
                                                    },
                                                }
                                            ]
                                        )
                                    continue

                                if et == "response.completed":
                                    final_resp = event.response
                                    if final_resp and final_resp.usage:
                                        u = final_resp.usage
                                        usage = Usage(
                                            completion_tokens=u.output_tokens or 0,
                                            prompt_tokens=u.input_tokens or 0,
                                            total_tokens=(u.input_tokens or 0) + (u.output_tokens or 0),
                                        )
                                    continue

                                if et in ("response.error", "error"):
                                    raise RuntimeError(f"Responses stream error: {event.error}")

                    finally:
                        if usage:
                            yield ChatCompletionDeltaMessage(usage=usage)

                return _generator()
            else:
                response = await raw_client.responses.create(
                    model=self.model_id,
                    input=messages,
                    temperature=None if self.temperature is NOT_GIVEN else self.temperature,
                    top_p=None if top_p is NOT_GIVEN else top_p,
                    max_output_tokens=req_max_output_tokens,
                    **tools_params,  # type: ignore[arg-type]
                )

                content_text = response.output_text
                tool_calls = []
                for item in (response.output or []):
                    if item.type == "function_call":
                        tool_calls.append(
                            {
                                "id": item.call_id or item.id,
                                "type": "function",
                                "function": {
                                    "name": item.name,
                                    "arguments": item.arguments,
                                },
                            }
                        )

                usage = None
                if response.usage:
                    u = response.usage
                    usage = Usage(
                        completion_tokens=u.output_tokens or 0,
                        prompt_tokens=u.input_tokens or 0,
                        total_tokens=(u.input_tokens or 0) + (u.output_tokens or 0),
                    )

                result = {
                    "content": content_text,
                    "tool_calls": tool_calls or None,
                    "usage": usage,
                }
                return ChatCompletionMessage(**result)

        if self.stream:
            stream_response = await raw_client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                stream=self.stream,
                temperature=self.temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                audio=audio,
                frequency_penalty=frequency_penalty,
                logit_bias=logit_bias,
                logprobs=logprobs,
                max_completion_tokens=max_completion_tokens,
                metadata=metadata,
                modalities=modalities,
                n=n,
                parallel_tool_calls=parallel_tool_calls,
                prediction=prediction,
                presence_penalty=presence_penalty,
                reasoning_effort=reasoning_effort,
                seed=seed,
                service_tier=service_tier,
                stop=stop,
                store=store,
                top_logprobs=top_logprobs,
                user=user,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                stream_options=stream_options,
                response_format=response_format if response_format and self.model_setting.response_format_available else OPENAI_NOT_GIVEN,
                **tools_params,  # type: ignore
            )

            async def _generator():
                full_content = ""
                result = {}
                usage = None
                buffer = ""
                in_reasoning = False
                accumulated_reasoning = []
                accumulated_content = []

                async for chunk in stream_response:
                    if chunk.usage and chunk.usage.total_tokens:
                        if getattr(chunk.usage, "cached_tokens", None):  # noqa: B009
                            if getattr(chunk.usage, "prompt_tokens_details", None):  # noqa: B009
                                chunk.usage.prompt_tokens_details.cached_tokens = chunk.usage.cached_tokens  # type: ignore
                            else:
                                chunk.usage.prompt_tokens_details = PromptTokensDetails(
                                    cached_tokens=chunk.usage.cached_tokens  # type: ignore
                                )
                        usage = Usage(
                            completion_tokens=chunk.usage.completion_tokens or 0,
                            prompt_tokens=chunk.usage.prompt_tokens or 0,
                            total_tokens=chunk.usage.total_tokens or 0,
                            completion_tokens_details=chunk.usage.completion_tokens_details,
                            prompt_tokens_details=chunk.usage.prompt_tokens_details,
                        )

                    if not chunk.choices or len(chunk.choices) == 0 or not chunk.choices[0].delta:
                        if usage:
                            yield ChatCompletionDeltaMessage(usage=usage)
                        continue

                    if self.model_setting.function_call_available:
                        if chunk.choices[0].delta.tool_calls:
                            for index, tool_call in enumerate(chunk.choices[0].delta.tool_calls):
                                tool_call.index = index
                                tool_call.type = "function"

                        # 即使支持 function call，也要处理思考标签
                        message = chunk.choices[0].delta.model_dump()
                        if is_gemini3 and chunk.choices[0].delta.tool_calls:
                            google_extras: list[dict] = []
                            for tool_call in chunk.choices[0].delta.tool_calls:
                                extra_content = getattr(tool_call, "extra_content", None)
                                if isinstance(extra_content, dict) and extra_content.get("google"):
                                    google_extras.append(extra_content["google"])
                            if google_extras:
                                message["raw_content"] = {"google": google_extras}
                        delta_content = message.get("content", "")
                        if delta_content:
                            buffer += delta_content

                            # 处理缓冲区中的内容，提取思考标签
                            buffer, current_output_content, current_reasoning_content, in_reasoning = process_thinking_content(buffer, in_reasoning, start_tag, end_tag)

                            # 累积内容
                            if current_output_content:
                                accumulated_content.append(current_output_content)
                            if current_reasoning_content:
                                accumulated_reasoning.append(current_reasoning_content)

                            # 只要有内容变化就产生 delta
                            if current_output_content or current_reasoning_content:
                                if current_output_content:
                                    message["content"] = current_output_content
                                elif current_reasoning_content:
                                    message["reasoning_content"] = current_reasoning_content
                                    message["content"] = ""  # 推理时不输出普通内容
                            else:
                                # 处理后没有产生任何内容（如仅包含 </thought> 标签）
                                # 清空 content 避免标签泄露到输出
                                message["content"] = ""
                                if not message.get("tool_calls"):
                                    # 如果没有任何内容且没有 tool_calls，则跳过这个消息
                                    continue

                        yield ChatCompletionDeltaMessage(**message, usage=usage)
                    else:
                        message = chunk.choices[0].delta.model_dump()
                        delta_content = message.get("content", "")
                        if delta_content:
                            buffer += delta_content

                        # 处理缓冲区中的内容，提取思考标签
                        buffer, current_output_content, current_reasoning_content, in_reasoning = process_thinking_content(buffer, in_reasoning, start_tag, end_tag)

                        # 累积内容
                        if current_output_content:
                            accumulated_content.append(current_output_content)
                        if current_reasoning_content:
                            accumulated_reasoning.append(current_reasoning_content)

                        # 只要有内容变化就产生 delta
                        if current_output_content or current_reasoning_content:
                            if current_output_content:
                                message["content"] = current_output_content
                            elif current_reasoning_content:
                                message["reasoning_content"] = current_reasoning_content
                                message["content"] = ""  # 推理时不输出普通内容

                            if tools:
                                full_content += current_output_content
                                tool_call_data = ToolCallContentProcessor(full_content).tool_calls
                                if tool_call_data:
                                    message["tool_calls"] = tool_call_data["tool_calls"]

                            if full_content in ("<", "<|", "<|▶", "<|▶|") or full_content.startswith("<|▶|>"):
                                message["content"] = ""
                                result = message
                                continue

                            yield ChatCompletionDeltaMessage(**message, usage=usage)
                        elif delta_content:
                            # 有原始内容但处理后没有产生任何内容（如仅包含 </thought> 标签）
                            # 清空并跳过，避免标签泄露到输出
                            pass

                # 处理最后剩余的缓冲区内容
                if buffer:
                    if in_reasoning:
                        accumulated_reasoning.append(buffer)
                    else:
                        accumulated_content.append(buffer)

                    final_message = {}
                    if accumulated_content:
                        final_content = "".join(accumulated_content)
                        if final_content.strip():  # 只有当内容非空时才输出
                            final_message["content"] = final_content

                    if accumulated_reasoning:
                        final_reasoning = "".join(accumulated_reasoning)
                        if final_reasoning.strip():  # 只有当推理内容非空时才输出
                            final_message["reasoning_content"] = final_reasoning

                    if final_message:
                        yield ChatCompletionDeltaMessage(**final_message, usage=usage)

                if result:
                    yield ChatCompletionDeltaMessage(**result, usage=usage)

            return _generator()
        else:
            response = await raw_client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                stream=self.stream,
                temperature=self.temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                audio=audio,
                frequency_penalty=frequency_penalty,
                logit_bias=logit_bias,
                logprobs=logprobs,
                max_completion_tokens=max_completion_tokens,
                metadata=metadata,
                modalities=modalities,
                n=n,
                parallel_tool_calls=parallel_tool_calls,
                prediction=prediction,
                presence_penalty=presence_penalty,
                reasoning_effort=reasoning_effort,
                seed=seed,
                service_tier=service_tier,
                stop=stop,
                store=store,
                top_logprobs=top_logprobs,
                user=user,
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                stream_options=stream_options,
                response_format=response_format if response_format and self.model_setting.response_format_available else OPENAI_NOT_GIVEN,
                **tools_params,  # type: ignore
            )

            if not response.choices:
                raise ValueError(f"No response choices: {response}")

            if response.usage and getattr(response.usage, "cached_tokens", None):  # noqa: B009
                if getattr(response.usage, "prompt_tokens_details", None):  # noqa: B009
                    response.usage.prompt_tokens_details.cached_tokens = response.usage.cached_tokens  # type: ignore
                else:
                    response.usage.prompt_tokens_details = PromptTokensDetails(
                        cached_tokens=response.usage.cached_tokens  # type: ignore
                    )

            result = {
                "content": response.choices[0].message.content,
                "reasoning_content": getattr(response.choices[0].message, "reasoning_content", None),
                "usage": response.usage.model_dump() if response.usage else None,
            }

            if not result["reasoning_content"] and result["content"]:
                # Create dynamic regex pattern based on backend
                think_pattern = f"{re.escape(start_tag)}(.*?){re.escape(end_tag)}"
                think_match = re.search(think_pattern, result["content"], re.DOTALL)
                if think_match:
                    result["reasoning_content"] = think_match.group(1)
                    result["content"] = result["content"].replace(think_match.group(0), "", 1)

            if tools:
                if self.model_setting.function_call_available:
                    if response.choices[0].message.tool_calls:
                        result["tool_calls"] = [{**tool_call.model_dump(), "type": "function"} for tool_call in response.choices[0].message.tool_calls]
                else:
                    tool_call_content_processor = ToolCallContentProcessor(result["content"])
                    tool_call_data = tool_call_content_processor.tool_calls
                    if tool_call_data:
                        result["tool_calls"] = tool_call_data["tool_calls"]
                        result["content"] = tool_call_content_processor.non_tool_content

            # 对 Gemini 3 模型保留 Google 扩展信息（如 thought_signature），以便上层可以按文档转发
            if is_gemini3 and getattr(response.choices[0].message, "tool_calls", None):
                google_extras: list[dict] = []
                for tool_call in response.choices[0].message.tool_calls:
                    extra_content = getattr(tool_call, "extra_content", None)
                    if isinstance(extra_content, dict) and extra_content.get("google"):
                        google_extras.append(extra_content["google"])
                if google_extras:
                    result["raw_content"] = [{"google": google_extras}]

            return ChatCompletionMessage(**result)
