#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文本 Embedding - 支持 vLLM/OpenAI 兼容的 API
"""

import asyncio
import time
from typing import List, Optional, Union, Literal
from dataclasses import dataclass, field

import aiohttp
import requests

from .base import BaseEmbedding

# jina-embeddings-v3 支持的任务类型
TaskType = Literal[
    "text-matching",      # 语义相似度、对称检索
    "retrieval.query",    # 非对称检索 - 查询端
    "retrieval.passage",  # 非对称检索 - 文档端
    "classification",     # 分类任务
    "separation",         # 聚类、重排序
]

@dataclass
class EmbeddingResult:
    """Embedding 结果"""

    index: int
    embedding: List[float]
    text: str = ""


@dataclass
class EmbeddingResponse:
    """Embedding 响应"""

    embeddings: List[EmbeddingResult]
    model: str
    usage: dict = field(default_factory=dict)


class TextEmbedding(BaseEmbedding):
    """
    文本 Embedding 客户端
    支持 vLLM 和 OpenAI 兼容的 API (jina-v3, bge-m3 等)
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "EMPTY",
        task: Optional[TaskType] = None,
        dimensions: Optional[int] = None,
        local_truncate: bool = False,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        """
        初始化文本 Embedding 客户端

        Args:
            base_url: API 基础 URL，如 http://localhost:8000
            model: 模型名称，如 jinaai/jina-embeddings-v3
            api_key: API 密钥，vLLM 默认不需要
            task: 任务类型 (jina-v3 支持)
            dimensions: 输出维度 (Matryoshka)
            local_truncate: 是否本地截取维度（适用于服务端不支持 dimensions 参数的情况）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.task = task
        self._dimensions = dimensions
        self.local_truncate = local_truncate
        self.timeout = timeout
        self.max_retries = max_retries
        self._actual_dimension: Optional[int] = None

    def _get_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _build_payload(
        self,
        texts: List[str],
        task: Optional[TaskType] = None,
        dimensions: Optional[int] = None,
        include_dimensions: bool = True,
    ) -> dict:
        """构建请求 payload"""
        payload = {
            "model": self.model,
            "input": texts,
        }
        task = task or self.task
        dimensions = dimensions or self._dimensions

        if task:
            payload["task"] = task
        if dimensions and include_dimensions:
            payload["dimensions"] = dimensions

        return payload

    def _parse_response(
        self, data: dict, texts: List[str], truncate_to: Optional[int] = None
    ) -> EmbeddingResponse:
        """解析 API 响应

        Args:
            data: API 响应数据
            texts: 原始文本列表
            truncate_to: 本地截取维度（MRL 模式用）
        """
        results = []
        for item in data["data"]:
            embedding = item["embedding"]
            # 本地截取（MRL 模式）
            if truncate_to and len(embedding) > truncate_to:
                embedding = embedding[:truncate_to]
            results.append(
                EmbeddingResult(
                    index=item["index"],
                    embedding=embedding,
                    text=texts[item["index"]] if item["index"] < len(texts) else "",
                )
            )

        # 记录实际维度（截取后的维度）
        if results and not self._actual_dimension:
            self._actual_dimension = len(results[0].embedding)

        return EmbeddingResponse(
            embeddings=sorted(results, key=lambda x: x.index),
            model=data.get("model", self.model),
            usage=data.get("usage", {}),
        )

    # ========== 实现 BaseEmbedding 接口 ==========

    def embed(
        self,
        inputs: Union[str, List[str]],
        task: Optional[TaskType] = None,
        dimensions: Optional[int] = None,
    ) -> List[List[float]]:
        """
        向量化文本

        Args:
            inputs: 文本或文本列表
            task: 任务类型
            dimensions: 输出维度

        Returns:
            向量列表
        """
        response = self.embed_with_response(inputs, task, dimensions)
        return [r.embedding for r in response.embeddings]

    async def aembed(
        self,
        inputs: Union[str, List[str]],
        task: Optional[TaskType] = None,
        dimensions: Optional[int] = None,
    ) -> List[List[float]]:
        """异步向量化文本"""
        response = await self.aembed_with_response(inputs, task, dimensions)
        return [r.embedding for r in response.embeddings]

    @property
    def dimension(self) -> int:
        """向量维度"""
        if self._dimensions:
            return self._dimensions
        if self._actual_dimension:
            return self._actual_dimension
        # 默认维度，实际调用后会更新
        return 1024

    @property
    def supports_image(self) -> bool:
        return False

    # ========== 扩展方法 ==========

    def embed_with_response(
        self,
        texts: Union[str, List[str]],
        task: Optional[TaskType] = None,
        dimensions: Optional[int] = None,
    ) -> EmbeddingResponse:
        """
        同步获取 embedding，返回完整响应

        Args:
            texts: 单个文本或文本列表
            task: 任务类型
            dimensions: 输出维度

        Returns:
            EmbeddingResponse 对象
        """
        if isinstance(texts, str):
            texts = [texts]

        url = f"{self.base_url}/v1/embeddings"
        target_dim = dimensions or self._dimensions
        # local_truncate=True 时不发送 dimensions 参数，获取完整向量后本地截取
        include_dimensions = not self.local_truncate
        payload = self._build_payload(texts, task, dimensions, include_dimensions=include_dimensions)

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()

                # 本地截取模式
                truncate_to = target_dim if self.local_truncate else None
                return self._parse_response(data, texts, truncate_to=truncate_to)

            except requests.RequestException:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(0.5 * (attempt + 1))

    async def aembed_with_response(
        self,
        texts: Union[str, List[str]],
        task: Optional[TaskType] = None,
        dimensions: Optional[int] = None,
    ) -> EmbeddingResponse:
        """异步获取 embedding，返回完整响应"""
        if isinstance(texts, str):
            texts = [texts]

        url = f"{self.base_url}/v1/embeddings"
        target_dim = dimensions or self._dimensions
        include_dimensions = not self.local_truncate
        payload = self._build_payload(texts, task, dimensions, include_dimensions=include_dimensions)

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for attempt in range(self.max_retries):
                try:
                    async with session.post(
                        url,
                        json=payload,
                        headers=self._get_headers(),
                    ) as response:
                        response.raise_for_status()
                        data = await response.json()

                        truncate_to = target_dim if self.local_truncate else None
                        return self._parse_response(data, texts, truncate_to=truncate_to)

                except aiohttp.ClientError:
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(0.5 * (attempt + 1))

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        task: Optional[TaskType] = None,
        dimensions: Optional[int] = None,
    ) -> List[List[float]]:
        """同步批量获取 embedding"""
        return asyncio.run(
            self.aembed_batch(texts, batch_size, task, dimensions)
        )

    async def aembed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        task: Optional[TaskType] = None,
        dimensions: Optional[int] = None,
    ) -> List[List[float]]:
        """批量异步获取 embedding，自动分批处理"""
        all_embeddings = [None] * len(texts)

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            vectors = await self.aembed(batch, task, dimensions)
            for j, vec in enumerate(vectors):
                all_embeddings[i + j] = vec

        return all_embeddings

    def __repr__(self) -> str:
        return f"TextEmbedding(base_url={self.base_url!r}, model={self.model!r})"


# 向后兼容别名
EmbeddingClient = TextEmbedding
