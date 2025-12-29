# -*- coding: UTF-8 -*-
# @Time : 2025/12/24 16:15 
# @Author : 刘洪波
from __future__ import annotations

import abc
import logging
import httpx
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional, Union, Callable
from openai import (
    OpenAI,
    AsyncOpenAI,
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
    InternalServerError,
)
from tenacity import (
    Retrying,
    AsyncRetrying,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception,
    before_sleep_log,
)

__all__ = [
    "ChatLLM", "AsyncChatLLM", "OpenAIClient", "AsyncOpenAIClient", "AzureOpenAIClient", "AsyncAzureOpenAIClient"
]


Message = Dict[str, str]


# =========================
# Message builder
# =========================

def build_messages(user_input: str, system_prompt: Optional[str] = None, history: Optional[List[Message]] = None) -> List[Message]:
    """
    组装messages
    :param user_input: 用户输入
    :param system_prompt: 系统提示词
    :param history: 历史对话
    :return:
    """

    def _safe_text(text: Optional[str]) -> str:
        if not text:
            return ""
        if not isinstance(text, str):
            text = str(text)
        return text

    messages: List[Message] = []

    if system_prompt:
        messages.append(
            {"role": "system", "content": _safe_text(system_prompt)}
        )

    if history:
        for m in history:
            messages.append(
                {
                    "role": m.get("role", "user"),
                    "content": _safe_text(m.get("content")),
                }
            )

    messages.append({"role": "user", "content": _safe_text(user_input)})
    return messages


# =========================
# Retry decision
# =========================

def _should_retry(exc: Exception) -> bool:
    """
    明确区分可重试 / 不可重试异常
    """
    if isinstance(exc, APIError):
        err_code = getattr(exc, "code", "") or ""
        err_type = getattr(exc, "type", "") or ""
        # 明确不可恢复错误
        if err_code in ("invalid_request_error", "context_length_exceeded") or "auth" in err_type:
            return False

    return isinstance(
        exc,
        (
            RateLimitError,
            APIConnectionError,
            APITimeoutError,
            InternalServerError,
            httpx.TimeoutException,
            httpx.NetworkError,
        ),
    )


# =========================
# Async Base Abstraction
# =========================

class AsyncLLMClient(abc.ABC):
    """async LLM Client 抽象基类"""

    @abc.abstractmethod
    async def complete(
            self,
            messages: List[Message],
            **kwargs: Any,
    ) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    async def stream(
            self,
            messages: List[Message],
            **kwargs: Any,
    ) -> AsyncIterator[str]:
        raise NotImplementedError


# =========================
# Async OpenAI / Compatible Client
# =========================

class AsyncOpenAIClient(AsyncLLMClient):
    def __init__(
            self,
            *,
            model: str,
            api_key: str = "EMPTY",
            base_url: Optional[str] = None,
            client: Optional[AsyncOpenAI] = None,
            logger: Optional[logging.Logger] = None,
            max_retries: int = 3,
            retry_delay: float = 1.0,
            max_retry_delay: int = 10,
    ):
        """
        初始化异步 OpenAI 客户端。

        :param model: 要使用的 OpenAI 模型名称，例如 "gpt-4", "gpt-3.5-turbo"
        :param api_key: OpenAI API key，用于身份验证
        :param base_url: 可选的 OpenAI API 基础 URL，默认使用官方 API
        :param client: 可选的自定义 AsyncOpenAI 客户端实例，如果提供则复用
        :param logger: 可选的日志对象，用于记录请求和重试日志
        :param max_retries: 最大重试次数，当请求失败或异常时最多重试次数，默认为 3
        :param retry_delay: 重试延迟的基础时间（秒），用于指数退避策略， 默认为 1.0
        :param max_retry_delay: 重试延迟的最大值（秒），避免等待时间无限增长， 默认为 10
        """
        self.model = model
        self.logger = logger or logging.getLogger(__name__)

        self.client = client or AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        self.retry_config = dict(
            stop=stop_after_attempt(max_retries),
            wait=wait_random_exponential(
                multiplier=retry_delay, max=max_retry_delay
            ),
            retry=retry_if_exception(_should_retry),
            before_sleep=before_sleep_log(self.logger, logging.INFO),
            reraise=True,
        )

        self.logger.info(
            f"✅ OpenAIClient initialized (model={model}, base_url={base_url})"
        )

    async def complete(self, messages: List[Message], **kwargs: Any) -> str:
        async for attempt in AsyncRetrying(**self.retry_config):
            with attempt:
                resp = await self.client.chat.completions.create(model=self.model, messages=messages, **kwargs)
                content = resp.choices[0].message.content
                if not content:
                    raise RuntimeError("Empty LLM response")
                return content

        raise RuntimeError("Unreachable")

    async def stream(
            self,
            messages: List[Message],
            **kwargs: Any,
    ) -> AsyncIterator[str]:
        async for attempt in AsyncRetrying(**self.retry_config):
            with attempt:
                resp = await self.client.chat.completions.create(model=self.model, messages=messages, stream=True, **kwargs)
                async for chunk in resp:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
                return


# =========================
# Async Azure OpenAI Client
# =========================

class AsyncAzureOpenAIClient(AsyncOpenAIClient):
    """
    Azure OpenAI 是 OpenAI-compatible
    差异：
    - model -> deployment
    - endpoint + api-version
    """

    def __init__(
            self,
            *,
            deployment: str,
            api_key: str,
            endpoint: str,
            api_version: str = "2024-02-01",
            **kwargs: Any,
    ):
        super().__init__(
            model=deployment,
            api_key=api_key,
            base_url=f"{endpoint}/openai/deployments/{deployment}?api-version={api_version}",
            **kwargs,
        )


# =========================
# AsyncChatLLM
# =========================

class AsyncChatLLM:
    """
    Async 对话统一入口
    """

    def __init__(
            self,
            client: AsyncLLMClient,
            *,
            max_tokens: int = None,
            recorder: Optional[Union[Callable[[str, dict], None], Any]] = None,
            logger: Optional[logging.Logger] = None,
    ):
        """
        初始化 ChatLLM 对象，用于统一管理对话调用。

        :param client: LLM 客户端实例，用于实际调用模型生成结果
        :param max_tokens: 可选参数，限制每次生成的最大 token 数
        :param recorder: 可选的记录器，用于记录对话内容和元信息。
                         可以是一个函数，接受 (prompt: str, result: dict) 参数，
                         或者是任何实现了相应接口的对象
        :param logger: 可选的日志记录器，用于输出调试信息
        """
        self.client = client
        self.max_tokens = max_tokens
        self.recorder = recorder
        self.logger = logger or logging.getLogger(__name__)

    async def complete(
            self,
            user_input: str,
            system_prompt: Optional[str] = None,
            history: Optional[List[Message]] = None,
            trace_id: Optional[str] = None,
            log_input: bool = False,
            log_output: bool = False,
            **kwargs: Any,
    ) -> str:
        """
        非流式调用 LLM 完成一次对话生成，返回模型生成的文本。

        :param user_input: 用户输入的文本内容
        :param system_prompt: 可选系统提示，用于引导模型生成风格或角色
        :param history: 可选历史消息列表，用于上下文连续对话
        :param trace_id: 可选的唯一标识，用于跟踪本次请求（可用于日志或监控）
        :param log_input: 是否记录用户输入到日志
        :param log_output: 是否记录模型输出到日志
        :param kwargs: 其他可选参数，直接传递给 LLM 客户端（如 max_tokens、temperature 等）
        :return: 模型生成的文本结果
        """
        if not trace_id:
            trace_id = str(uuid.uuid4())
        self.logger.info(f"LLM complete request，trace_id: {trace_id}")
        if self.recorder:
            record_data = {'user_input': user_input, "system_prompt": system_prompt,
                           "history": history, 'stream': False}
            if callable(self.recorder):
                self.recorder(trace_id, record_data)
            elif hasattr(self.recorder, "record"):
                self.recorder.record(trace_id, record_data)
        elif log_input:
            self.logger.info(f"user_input: {user_input}")
            self.logger.info(f"system_prompt: {system_prompt}")
            self.logger.info(f"history: {history}")
        messages = build_messages(user_input, system_prompt, history)

        output = await self.client.complete(messages, **kwargs)

        # 调用 recorder
        if self.recorder:
            record_data = {'stream': False, 'output': output}
            if callable(self.recorder):
                self.recorder(trace_id, record_data)
            elif hasattr(self.recorder, "record"):
                self.recorder.record(trace_id, record_data)
        elif log_output:
            self.logger.info(f"output: {output}")

        self.logger.info(f"LLM completed request，trace_id: {trace_id} ")
        return output

    async def stream(
            self,
            user_input: str,
            system_prompt: Optional[str] = None,
            history: Optional[List[Message]] = None,
            trace_id: Optional[str] = None,
            log_input: bool = False,
            log_output: bool = False,
            **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        流式调用 LLM 完成一次对话生成，返回模型生成的文本。

        :param user_input: 用户输入的文本内容
        :param system_prompt: 可选系统提示，用于引导模型生成风格或角色
        :param history: 可选历史消息列表，用于上下文连续对话
        :param trace_id: 可选的唯一标识，用于跟踪本次请求（可用于日志或监控）
        :param log_input: 是否记录用户输入到日志
        :param log_output: 是否记录模型输出到日志
        :param kwargs: 其他可选参数，直接传递给 LLM 客户端（如 max_tokens、temperature 等）
        :return: 模型生成的文本结果
        """
        if not trace_id:
            trace_id = str(uuid.uuid4())

        self.logger.info(f"LLM stream request，trace_id: {trace_id}")
        if self.recorder:
            record_data = {'user_input': user_input, "system_prompt": system_prompt,
                           "history": history, 'stream': True}
            if callable(self.recorder):
                self.recorder(trace_id, record_data)
            elif hasattr(self.recorder, "record"):
                self.recorder.record(trace_id, record_data)
        elif log_input:
            self.logger.info(f"user_input: {user_input}")
            self.logger.info(f"system_prompt: {system_prompt}")
            self.logger.info(f"history: {history}")

        messages = build_messages(user_input, system_prompt, history)
        buffer = ""
        async for chunk in self.client.stream(messages, **kwargs):
            buffer += chunk
            yield chunk

        # 调用 recorder
        if self.recorder:
            record_data = {'stream': True, 'output': buffer}
            if callable(self.recorder):
                self.recorder(trace_id, record_data)
            elif hasattr(self.recorder, "record"):
                self.recorder.record(trace_id, record_data)
        elif log_output:
            self.logger.info(f"output: {buffer}")

        self.logger.info(f"LLM completed stream request，trace_id: {trace_id} ")


# =========================
# Base Abstraction
# =========================

class LLMClient(abc.ABC):
    @abc.abstractmethod
    def complete(self, messages: List[Message], **kwargs: Any) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def stream(self, messages: List[Message], **kwargs: Any):
        raise NotImplementedError


# =========================
# OpenAI / Compatible Client
# =========================

class OpenAIClient(LLMClient):
    def __init__(self, *, model: str, api_key: str = "EMPTY", base_url: Optional[str] = None, client: Optional[OpenAI] = None,
                 logger: Optional[logging.Logger] = None, max_retries: int = 3, retry_delay: float = 1.0, max_retry_delay: int = 10):
        """
        初始化同步 OpenAI 客户端。

        :param model: 要使用的 OpenAI 模型名称，例如 "gpt-4", "gpt-3.5-turbo"
        :param api_key: OpenAI API key，用于身份验证
        :param base_url: 可选的 OpenAI API 基础 URL，默认使用官方 API
        :param client: 可选的自定义 AsyncOpenAI 客户端实例，如果提供则复用
        :param logger: 可选的日志对象，用于记录请求和重试日志
        :param max_retries: 最大重试次数，当请求失败或异常时最多重试次数，默认为 3
        :param retry_delay: 重试延迟的基础时间（秒），用于指数退避策略， 默认为 1.0
        :param max_retry_delay: 重试延迟的最大值（秒），避免等待时间无限增长， 默认为 10
        """

        self.model = model
        self.logger = logger or logging.getLogger(__name__)
        self.client = client or OpenAI(api_key=api_key, base_url=base_url)

        self.retry_config = dict(
            stop=stop_after_attempt(max_retries),
            wait=wait_random_exponential(multiplier=retry_delay, max=max_retry_delay),
            retry=retry_if_exception(_should_retry),
            before_sleep=before_sleep_log(self.logger, logging.INFO),
            reraise=True,
        )

        self.logger.info(f"✅ OpenAIClient initialized (model={model}, base_url={base_url})")

    def complete(self, messages: List[Message], **kwargs: Any) -> str:
        for attempt in Retrying(**self.retry_config):
            with attempt:
                resp = self.client.chat.completions.create(model=self.model, messages=messages, **kwargs)
                content = resp.choices[0].message.content
                if not content:
                    raise RuntimeError("Empty LLM response")
                return content
        raise RuntimeError("Unreachable")

    def stream(self, messages: List[Message], **kwargs: Any):
        for attempt in Retrying(**self.retry_config):
            with attempt:
                resp = self.client.chat.completions.create(model=self.model, messages=messages, stream=True, **kwargs)
                for chunk in resp:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
                return


# =========================
# Azure OpenAI Client
# =========================

class AzureOpenAIClient(OpenAIClient):
    def __init__(self, *, deployment: str, api_key: str, endpoint: str, api_version: str = "2024-02-01", **kwargs: Any):
        super().__init__(model=deployment, api_key=api_key,
                         base_url=f"{endpoint}/openai/deployments/{deployment}?api-version={api_version}", **kwargs)


# =========================
# ChatLLM
# =========================

class ChatLLM:
    def __init__(self, client: LLMClient, *, max_tokens: int = None,
                 recorder: Optional[Union[Callable[[str, dict], None], Any]] = None,
                 logger: Optional[logging.Logger] = None):
        """
        初始化 ChatLLM 对象，用于统一管理对话调用。

        :param client: LLM 客户端实例，用于实际调用模型生成结果
        :param max_tokens: 可选参数，限制每次生成的最大 token 数
        :param recorder: 可选的记录器，用于记录对话内容和元信息。
                         可以是一个函数，接受 (prompt: str, result: dict) 参数，
                         或者是任何实现了相应接口的对象
        :param logger: 可选的日志记录器，用于输出调试信息
        """
        self.client = client
        self.max_tokens = max_tokens
        self.recorder = recorder
        self.logger = logger or logging.getLogger(__name__)

    def complete(self, user_input: str, system_prompt: Optional[str] = None, history: Optional[List[Message]] = None,
                 trace_id: Optional[str] = None, log_input: bool = False, log_output: bool = False, **kwargs: Any) -> str:
        """
        非流式调用 LLM 完成一次对话生成，返回模型生成的文本。

        :param user_input: 用户输入的文本内容
        :param system_prompt: 可选系统提示，用于引导模型生成风格或角色
        :param history: 可选历史消息列表，用于上下文连续对话
        :param trace_id: 可选的唯一标识，用于跟踪本次请求（可用于日志或监控）
        :param log_input: 是否记录用户输入到日志
        :param log_output: 是否记录模型输出到日志
        :param kwargs: 其他可选参数，直接传递给 LLM 客户端（如 max_tokens、temperature 等）
        :return: 模型生成的文本结果
        """
        if not trace_id:
            trace_id = str(uuid.uuid4())
        self.logger.info(f"LLM complete request，trace_id: {trace_id}")

        if self.recorder:
            record_data = {'user_input': user_input, "system_prompt": system_prompt,
                           "history": history, 'stream': False}
            if callable(self.recorder):
                self.recorder(trace_id, record_data)
            elif hasattr(self.recorder, "record"):
                self.recorder.record(trace_id, record_data)
        elif log_input:
            self.logger.info(f"user_input: {user_input}")
            self.logger.info(f"system_prompt: {system_prompt}")
            self.logger.info(f"history: {history}")

        messages = build_messages(user_input, system_prompt, history)
        output = self.client.complete(messages, **kwargs)

        if self.recorder:
            record_data = {'stream': False, 'output': output}
            if callable(self.recorder):
                self.recorder(trace_id, record_data)
            elif hasattr(self.recorder, "record"):
                self.recorder.record(trace_id, record_data)
        elif log_output:
            self.logger.info(f"output: {output}")

        self.logger.info(f"LLM completed request，trace_id: {trace_id} ")
        return output

    def stream(self, user_input: str, system_prompt: Optional[str] = None, history: Optional[List[Message]] = None,
               trace_id: Optional[str] = None, log_input: bool = False, log_output: bool = False, **kwargs: Any):
        """
        流式调用 LLM 完成一次对话生成，返回模型生成的文本。

        :param user_input: 用户输入的文本内容
        :param system_prompt: 可选系统提示，用于引导模型生成风格或角色
        :param history: 可选历史消息列表，用于上下文连续对话
        :param trace_id: 可选的唯一标识，用于跟踪本次请求（可用于日志或监控）
        :param log_input: 是否记录用户输入到日志
        :param log_output: 是否记录模型输出到日志
        :param kwargs: 其他可选参数，直接传递给 LLM 客户端（如 max_tokens、temperature 等）
        :return: 模型生成的文本结果
        """
        if not trace_id:
            trace_id = str(uuid.uuid4())
        self.logger.info(f"LLM stream request，trace_id: {trace_id}")

        if self.recorder:
            record_data = {'user_input': user_input, "system_prompt": system_prompt,
                           "history": history, 'stream': True}
            if callable(self.recorder):
                self.recorder(trace_id, record_data)
            elif hasattr(self.recorder, "record"):
                self.recorder.record(trace_id, record_data)
        elif log_input:
            self.logger.info(f"user_input: {user_input}")
            self.logger.info(f"system_prompt: {system_prompt}")
            self.logger.info(f"history: {history}")

        messages = build_messages(user_input, system_prompt, history)
        buffer = ""
        for chunk in self.client.stream(messages, **kwargs):
            buffer += chunk
            yield chunk

        if self.recorder:
            record_data = {'stream': True, 'output': buffer}
            if callable(self.recorder):
                self.recorder(trace_id, record_data)
            elif hasattr(self.recorder, "record"):
                self.recorder.record(trace_id, record_data)
        elif log_output:
            self.logger.info(f"output: {buffer}")

        self.logger.info(f"LLM completed stream request，trace_id: {trace_id} ")
