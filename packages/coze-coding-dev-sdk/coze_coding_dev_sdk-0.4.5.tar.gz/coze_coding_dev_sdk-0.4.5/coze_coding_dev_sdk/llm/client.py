from typing import Any, Dict, Iterator, List, Optional, Union

from coze_coding_utils.runtime_ctx.context import Context, default_headers
from cozeloop.decorator import observe
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    BaseMessageChunk,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI

from ..core.config import Config
from .models import LLMConfig


class LLMClient:
    def __init__(
        self,
        config: Optional[Config] = None,
        ctx: Optional[Context] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        verbose: bool = False,
    ):
        if config is None:
            config = Config()
        self.config = config
        self.ctx = ctx
        self.custom_headers = custom_headers or {}
        self.verbose = verbose
        self.base_url = self.config.base_model_url
        self.api_key = self.config.api_key

    def _create_llm(
        self,
        llm_config: LLMConfig,
        use_caching: bool = False,
        previous_response_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> ChatOpenAI:
        extra_body = {}

        if llm_config.thinking:
            extra_body["thinking"] = {"type": llm_config.thinking}

        if llm_config.caching:
            extra_body["caching"] = {"type": llm_config.caching}

        headers = {}

        if self.ctx is not None:
            ctx_headers = default_headers(self.ctx)
            headers.update(ctx_headers)

        if self.custom_headers:
            headers.update(self.custom_headers)

        config_headers = self.config.get_headers(extra_headers)
        headers.update(config_headers)

        llm = ChatOpenAI(
            model=llm_config.model,
            api_key=self.api_key,
            base_url=self.base_url,
            streaming=llm_config.streaming,
            extra_body=extra_body if extra_body else None,
            temperature=llm_config.temperature,
            frequency_penalty=llm_config.frequency_penalty,
            top_p=llm_config.top_p,
            max_tokens=llm_config.max_tokens,
            max_completion_tokens=llm_config.max_completion_tokens,
            default_headers=headers,
            use_responses_api=use_caching,
            use_previous_response_id=previous_response_id is not None,
        )

        return llm

    @observe(name="llm_stream")
    def stream(
        self,
        messages: List[BaseMessage],
        model: str = "doubao-seed-1-6-251015",
        thinking: Optional[str] = "disabled",
        caching: Optional[str] = "disabled",
        temperature: Optional[float] = 1.0,
        frequency_penalty: Optional[float] = 0,
        top_p: Optional[float] = 0,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        previous_response_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Iterator[BaseMessageChunk]:
        """
        流式调用大语言模型，逐块返回生成的内容

        Args:
            messages: 消息列表，使用 LangChain 消息格式（必需）
                - SystemMessage: 系统提示词，定义 AI 角色和行为
                - HumanMessage: 用户消息
                - AIMessage: AI 回复，用于多轮对话

            model: 模型ID，默认 "doubao-seed-1-6-251015"
                可选模型：
                - "doubao-seed-1-6-251015": 默认模型，平衡性能
                - "doubao-seed-1-6-flash-250615": 快速模型
                - "doubao-seed-1-6-thinking-250715": 思考模型

            thinking: 思考模式，默认 "disabled"
                - "enabled": 启用深度思考，适合复杂推理任务
                - "disabled": 禁用，适合快速响应

            caching: 缓存模式，默认 "disabled"
                - "enabled": 启用缓存，加速重复上下文的响应
                - "disabled": 禁用

            temperature: 温度参数，控制输出随机性，范围 0-2，默认 1.0
                - 0.0-0.3: 确定性输出，适合代码生成、数据分析
                - 0.7-0.9: 平衡创造性，适合通用对话
                - 1.0-2.0: 高创造性，适合创意写作、头脑风暴

            frequency_penalty: 频率惩罚，减少重复内容，范围 -2 到 2，默认 0
                正值减少重复，负值增加重复

            top_p: 核采样参数，控制输出多样性，范围 0-1，默认 0
                值越小输出越确定，值越大输出越多样

            max_tokens: 最大输出 token 数，默认 None（不限制）
                用于限制输出长度或控制成本

            max_completion_tokens: 最大完成 token 数，默认 None
                更精确的长度控制

            previous_response_id: 上一次响应ID，用于缓存场景，默认 None

            extra_headers: 额外的 HTTP 请求头，默认 None

        Returns:
            Iterator[BaseMessageChunk]: 流式返回的消息块，每个块包含：
                - content: 文本内容
                - response_metadata: 响应元数据

        Example:
            >>> from langchain_core.messages import HumanMessage
            >>> client = LLMClient()
            >>> messages = [HumanMessage(content="你好")]
            >>>
            >>> # 最简单用法
            >>> for chunk in client.stream(messages):
            ...     if chunk.content:
            ...         print(chunk.content, end="")
            >>>
            >>> # 调整温度
            >>> for chunk in client.stream(messages, temperature=0.7):
            ...     if chunk.content:
            ...         print(chunk.content, end="")
            >>>
            >>> # 启用思考模式
            >>> for chunk in client.stream(messages, thinking="enabled"):
            ...     if chunk.content:
            ...         print(chunk.content, end="")
        """
        llm_config = LLMConfig(
            model=model,
            thinking=thinking,
            caching=caching,
            temperature=temperature,
            frequency_penalty=frequency_penalty,
            top_p=top_p,
            max_tokens=max_tokens,
            max_completion_tokens=max_completion_tokens,
            streaming=True,
        )

        use_caching = caching == "enabled" or previous_response_id is not None

        if previous_response_id:
            for i in range(len(messages) - 1, -1, -1):
                msg = messages[i]
                if isinstance(msg, AIMessage):
                    msg.response_metadata["id"] = previous_response_id
                    break

        llm = self._create_llm(
            llm_config,
            use_caching=use_caching,
            previous_response_id=previous_response_id,
            extra_headers=extra_headers,
        )

        for chunk in llm.stream(messages):
            yield chunk

    @observe(name="llm_invoke")
    def invoke(
        self,
        messages: List[BaseMessage],
        model: str = "doubao-seed-1-6-251015",
        thinking: Optional[str] = "disabled",
        caching: Optional[str] = "disabled",
        temperature: Optional[float] = 1.0,
        frequency_penalty: Optional[float] = 0,
        top_p: Optional[float] = 0,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        previous_response_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> AIMessage:
        """
        非流式调用大语言模型，返回完整的响应

        内部通过流式调用实现，自动组装完整响应后返回。

        Args:
            messages: 消息列表，使用 LangChain 消息格式（必需）
                - SystemMessage: 系统提示词，定义 AI 角色和行为
                - HumanMessage: 用户消息
                - AIMessage: AI 回复，用于多轮对话

            model: 模型ID，默认 "doubao-seed-1-6-251015"
                可选模型：
                - "doubao-seed-1-6-251015": 默认模型，平衡性能
                - "doubao-seed-1-6-flash-250615": 快速模型
                - "doubao-seed-1-6-thinking-250715": 思考模型

            thinking: 思考模式，默认 "disabled"
                - "enabled": 启用深度思考，适合复杂推理任务
                - "disabled": 禁用，适合快速响应

            caching: 缓存模式，默认 "disabled"
                - "enabled": 启用缓存，加速重复上下文的响应
                - "disabled": 禁用

            temperature: 温度参数，控制输出随机性，范围 0-2，默认 1.0
                - 0.0-0.3: 确定性输出，适合代码生成、数据分析
                - 0.7-0.9: 平衡创造性，适合通用对话
                - 1.0-2.0: 高创造性，适合创意写作、头脑风暴

            frequency_penalty: 频率惩罚，减少重复内容，范围 -2 到 2，默认 0
                正值减少重复，负值增加重复

            top_p: 核采样参数，控制输出多样性，范围 0-1，默认 0
                值越小输出越确定，值越大输出越多样

            max_tokens: 最大输出 token 数，默认 None（不限制）
                用于限制输出长度或控制成本

            max_completion_tokens: 最大完成 token 数，默认 None
                更精确的长度控制

            previous_response_id: 上一次响应ID，用于缓存场景，默认 None

            extra_headers: 额外的 HTTP 请求头，默认 None

        Returns:
            AIMessage: 完整的响应消息，包含：
                - content: 完整的文本内容
                - response_metadata: 响应元数据（模型信息、token 使用量等）

        Example:
            >>> from langchain_core.messages import SystemMessage, HumanMessage
            >>> client = LLMClient()
            >>>
            >>> # 最简单用法
            >>> messages = [HumanMessage(content="你好")]
            >>> response = client.invoke(messages)
            >>> print(response.content)
            >>>
            >>> # 带系统提示词
            >>> messages = [
            ...     SystemMessage(content="你是一个 Python 专家"),
            ...     HumanMessage(content="什么是装饰器？")
            ... ]
            >>> response = client.invoke(messages)
            >>> print(response.content)
            >>>
            >>> # 调整参数
            >>> response = client.invoke(
            ...     messages=messages,
            ...     temperature=0.7,
            ...     max_tokens=500
            ... )
            >>> print(response.content)
            >>> print(f"Token 使用: {response.response_metadata}")
        """
        full_content = ""
        response_metadata = {}

        for chunk in self.stream(
            messages=messages,
            model=model,
            thinking=thinking,
            caching=caching,
            temperature=temperature,
            frequency_penalty=frequency_penalty,
            top_p=top_p,
            max_tokens=max_tokens,
            max_completion_tokens=max_completion_tokens,
            previous_response_id=previous_response_id,
            extra_headers=extra_headers,
        ):
            if chunk.content:
                full_content += chunk.content
            if chunk.response_metadata:
                response_metadata.update(chunk.response_metadata)

        return AIMessage(content=full_content, response_metadata=response_metadata)
