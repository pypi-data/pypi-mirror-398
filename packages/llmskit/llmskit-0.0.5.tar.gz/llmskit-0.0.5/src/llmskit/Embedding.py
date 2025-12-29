# -*- coding: UTF-8 -*-
# @Time : 2025/12/15 23:18 
# @Author : 刘洪波

from __future__ import annotations
import httpx
from typing import List, Optional
from functools import lru_cache
from openai import OpenAI, APIError, RateLimitError, APIConnectionError, InternalServerError, AsyncOpenAI
from tenacity import retry, AsyncRetrying, stop_after_attempt, wait_random_exponential, retry_if_exception_type, before_sleep_log, retry_if_exception
import logging


__all__ = ["OpenAIEmbeddings", "AsyncOpenAIEmbeddings"]


def _should_retry(exc: Exception) -> bool:
    # 明确不可重试的错误（即使属于 APIError）
    if isinstance(exc, APIError):
        err_code = getattr(exc, 'code', None) or ""
        err_type = getattr(exc, 'type', "") or ""
        # 如：context_length_exceeded / invalid_request_error / auth error 都不该重试
        if err_code in ("context_length_exceeded", "invalid_request_error") or "auth" in err_type:
            return False
    # 兜底：对已知可恢复错误重试
    return isinstance(exc, (RateLimitError, APIConnectionError, InternalServerError, httpx.TimeoutException, httpx.NetworkError))


class OpenAIEmbeddings:
    """OpenAI 兼容的嵌入模型封装类（支持 vLLM / LocalAI / Ollama / 其他 OpenAI 兼容服务）

    特性：
      - 批量处理 + 指数退避重试
      - 输入截断与警告
      - 维度探测缓存
      - 支持同步/异步扩展（本版本为同步）
    """

    def __init__(self, base_url: str, model_name: str, api_key: str = None, batch_size: int = 32, max_retries: int = 3,
        retry_delay: float = 1.0, max_retry_delay: int = 10, *, client: Optional[OpenAI] = None,
        max_input_length: int = 8191,  logger: Optional[logging.Logger] = None):
        """
        init
        :param base_url: 链接地址
        :param api_key: 密钥
        :param model_name: 模型名
        :param batch_size: 批次大小
        :param max_retries: 最大重试次数
        :param retry_delay: 重试延迟值，支持浮点秒数，使用指数退避策略
        :param max_retry_delay: 最大重试延迟值，必须为整数
        :param client: 外部传入client    # 允许注入已有 client（提升测试性）
        :param max_input_length:  模型最大输入长度，截断的依据  # OpenAI 官方上限为 8191 tokens，但按字符截更安全
        :param logger: 可传入 自定义logger
        """
        if not base_url:
            raise ValueError("base_url 不能为空")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key if api_key else ""
        self.model_name = model_name
        self.batch_size = max(1, batch_size)
        self.max_retries = max(0, max_retries)
        self.retry_delay = max(0.1, retry_delay)  # 至少 0.1s
        self.max_retry_delay = max(1, max_retry_delay)  # 至少 1s
        self.max_input_length = max_input_length

        self.logger = logger or logging.getLogger(__name__)
        # 客户端注入或新建
        self.client = client or OpenAI(base_url=self.base_url, api_key=self.api_key)

        self.logger.info(f"✅ 初始化 OpenAIEmbeddings: model={model_name!r}, endpoint={self.base_url}")

        # 定义重试策略
        self.retry_policy = {
                "stop": stop_after_attempt(self.max_retries),
                "wait": wait_random_exponential(multiplier=self.retry_delay, max=self.max_retry_delay),
                "retry": retry_if_exception(_should_retry),
                "before_sleep": before_sleep_log(self.logger, logging.INFO),
                "reraise": True,
            }
        self.logger.info(f'重试策略: {self.retry_policy}')


    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入文档列表（同步）"""
        if not texts:
            return []
        if not isinstance(texts, list):
            raise TypeError("texts must be a list")
        return self.batch_embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询"""
        if not text:
            text = ""
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        return self.batch_embed_documents([text])[0]

    def _request_embeddings(self, texts: List[str]) -> List[List[float]]:
        """带专业重试的嵌入请求, 核心：用 @retry 装饰"""
        @retry(**self.retry_policy)
        def cell():
            if not texts:
                return []
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            if len(response.data) != len(texts):
                raise ValueError(f"响应长度 {len(response.data)} ≠ 输入 {len(texts)}")

            return [[float(x) for x in item.embedding] for item in response.data]
        return cell()

    # ====== 3. 批处理逻辑大幅简化 ======
    def batch_embed_documents(self, texts: List[str], *, batch_size: Optional[int] = None) -> List[List[float]]:
        if not texts:
            return []

        batch_size = batch_size or self.batch_size
        all_embeddings: List[List[float]] = []

        self.logger.info(f"📦 开始嵌入 {len(texts)} 文本 (batch_size={batch_size})")

        for i in range(0, len(texts), batch_size):
            batch = texts[i: i + batch_size]
            safe_batch = self._prepare_texts(batch)
            batch_embeddings = self._request_embeddings(safe_batch)
            all_embeddings.extend(batch_embeddings)

            processed = min(i + len(batch), len(texts))
            self.logger.info(f"📈 进度: {processed}/{len(texts)} ({processed / len(texts) * 100:.1f}%)")

        self.logger.info(f"✅ 批量嵌入完成: {len(all_embeddings)} 向量")
        return all_embeddings

    def _prepare_texts(self, texts: List[str]) -> List[str]:
        """预处理文本：截断 + 警告"""
        prepared = []
        for text in texts:
            if not isinstance(text, str):
                text = str(text)
            if len(text) > self.max_input_length:
                self.logger.warning(f"文本长度 ({len(text)}) > max_input_length ({self.max_input_length})，已截断")
                text = text[: self.max_input_length]
            prepared.append(text)
        return prepared

    @lru_cache(maxsize=1)
    def get_embedding_dimension(self) -> int:
        """探测并缓存嵌入维度（线程安全）"""
        try:
            test_emb = self.embed_query("维度探测文本")
            dim = len(test_emb)
            self.logger.info(f"🔍 探测到嵌入维度: {dim}")
            return dim
        except Exception as e:
            self.logger.error(f"维度探测失败: {e}")
            raise RuntimeError("无法确定嵌入维度") from e


    def __repr__(self) -> str:
        return (
            f"OpenAIEmbeddings(model={self.model_name!r}, "
            f"endpoint={self.base_url}, batch_size={self.batch_size})"
        )


class AsyncOpenAIEmbeddings:
    """
    完全异步 OpenAI 兼容 Embeddings 封装
    - 支持 vLLM / LocalAI / Ollama / OpenAI
    - 批量处理
    - 异步指数退避重试
    """

    def __init__(
        self,
        base_url: str,
        model_name: str,
        api_key: str | None = None,
        batch_size: int = 32,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_retry_delay: int = 10,
        *,
        client: Optional[AsyncOpenAI] = None,
        max_input_length: int = 8191,
        logger: Optional[logging.Logger] = None,
    ):

        """
        init
        :param base_url: 链接地址
        :param api_key: 密钥
        :param model_name: 模型名
        :param batch_size: 批次大小
        :param max_retries: 最大重试次数
        :param retry_delay: 重试延迟值，支持浮点秒数，使用指数退避策略
        :param max_retry_delay: 最大重试延迟值，必须为整数
        :param client: 外部传入client    # 允许注入已有 client（提升测试性）
        :param max_input_length:  模型最大输入长度，截断的依据  # OpenAI 官方上限为 8191 tokens，但按字符截更安全
        :param logger: 可传入 自定义logger
        """
        if not base_url:
            raise ValueError("base_url 不能为空")

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""
        self.model_name = model_name
        self.batch_size = max(1, batch_size)
        self.max_retries = max(0, max_retries)
        self.retry_delay = max(0.1, retry_delay)
        self.max_retry_delay = max(1, max_retry_delay)
        self.max_input_length = max_input_length

        self.logger = logger or logging.getLogger(__name__)

        self.client = client or AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

        self.logger.info(
            f"✅ 初始化 AsyncOpenAIEmbeddings: model={model_name!r}, endpoint={self.base_url}"
        )

        # 定义重试策略
        self.retry_policy = {
            "stop": stop_after_attempt(self.max_retries),
            "wait": wait_random_exponential(multiplier=self.retry_delay, max=self.max_retry_delay),
            "retry": retry_if_exception(_should_retry),
            "before_sleep": before_sleep_log(self.logger, logging.INFO),
            "reraise": True,
        }
        self.logger.info(f'重试策略: {self.retry_policy}')

    # =========================
    # 对外 API
    # =========================
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not isinstance(texts, list):
            raise TypeError("texts must be a list")
        return await self.batch_embed_documents(texts)

    async def embed_query(self, text: str) -> List[float]:
        if not text:
            text = ""
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        return (await self.batch_embed_documents([text]))[0]

    # =========================
    # 核心请求（异步重试）
    # =========================
    async def _request_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        async for attempt in AsyncRetrying(**self.retry_policy):
            with attempt:
                response = await self.client.embeddings.create(
                    model=self.model_name,
                    input=texts,
                )

                if len(response.data) != len(texts):
                    raise ValueError(
                        f"响应长度 {len(response.data)} ≠ 输入 {len(texts)}"
                    )

                return [
                    [float(x) for x in item.embedding]
                    for item in response.data
                ]

        return []

    # =========================
    # 批处理（异步顺序执行）
    # =========================
    async def batch_embed_documents(
        self, texts: List[str], *, batch_size: Optional[int] = None
    ) -> List[List[float]]:
        if not texts:
            return []

        batch_size = batch_size or self.batch_size
        all_embeddings: List[List[float]] = []

        self.logger.info(
            f"📦 开始嵌入 {len(texts)} 文本 (batch_size={batch_size})"
        )

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            safe_batch = self._prepare_texts(batch)

            batch_embeddings = await self._request_embeddings(safe_batch)
            all_embeddings.extend(batch_embeddings)

            processed = min(i + len(batch), len(texts))
            self.logger.info(
                f"📈 进度: {processed}/{len(texts)} "
                f"({processed / len(texts) * 100:.1f}%)"
            )

        self.logger.info(f"✅ 批量嵌入完成: {len(all_embeddings)} 向量")
        return all_embeddings

    # =========================
    # 文本预处理
    # =========================
    def _prepare_texts(self, texts: List[str]) -> List[str]:
        prepared = []
        for text in texts:
            if not isinstance(text, str):
                text = str(text)
            if len(text) > self.max_input_length:
                self.logger.warning(
                    f"文本长度 ({len(text)}) > max_input_length "
                    f"({self.max_input_length})，已截断"
                )
                text = text[: self.max_input_length]
            prepared.append(text)
        return prepared

    # =========================
    # 嵌入维度探测（异步 + 缓存）
    # =========================
    @lru_cache(maxsize=1)
    async def get_embedding_dimension(self) -> int:
        try:
            emb = await self.embed_query("维度探测文本")
            dim = len(emb)
            self.logger.info(f"🔍 探测到嵌入维度: {dim}")
            return dim
        except Exception as e:
            self.logger.error(f"维度探测失败: {e}")
            raise RuntimeError("无法确定嵌入维度") from e

    def __repr__(self) -> str:
        return (
            f"AsyncOpenAIEmbeddings(model={self.model_name!r}, "
            f"endpoint={self.base_url}, batch_size={self.batch_size})"
        )
