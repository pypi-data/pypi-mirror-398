#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多模态 Embedding - 支持文本和图片 (jina-clip-v2 等)
"""

import asyncio
import base64
import time
from pathlib import Path
from typing import List, Optional, Union, Literal

import aiohttp
import requests

from .base import BaseEmbedding


InputType = Literal["text", "image", "auto"]


class MultiModalEmbedding(BaseEmbedding):
    """
    多模态 Embedding 客户端
    支持文本和图片的向量化 (jina-clip-v2 等)
    """

    def __init__(
        self,
        base_url: str,
        model: str = "jinaai/jina-clip-v2",
        api_key: str = "EMPTY",
        dimensions: Optional[int] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        """
        初始化多模态 Embedding 客户端

        Args:
            base_url: API 基础 URL
            model: 模型名称
            api_key: API 密钥
            dimensions: 输出维度 (如果模型支持)
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self._dimensions = dimensions
        self.timeout = timeout
        self.max_retries = max_retries
        self._actual_dimension: Optional[int] = None

    def _get_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _is_image(self, input_str: str) -> bool:
        """判断输入是否为图片"""
        # URL 图片
        if input_str.startswith(("http://", "https://")):
            lower = input_str.lower()
            return any(ext in lower for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"])
        # 本地文件
        if Path(input_str).suffix.lower() in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]:
            return Path(input_str).exists()
        # Base64
        if input_str.startswith("data:image"):
            return True
        return False

    def _encode_image(self, image_path: str) -> str:
        """将本地图片编码为 base64 data URL"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")

        suffix = path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        mime = mime_types.get(suffix, "image/jpeg")

        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")

        return f"data:{mime};base64,{data}"

    def _prepare_input(
        self,
        input_str: str,
        input_type: InputType = "auto",
    ) -> dict:
        """
        准备单个输入，返回 API 格式

        Returns:
            {"text": "..."} 或 {"image": "..."}
        """
        if input_type == "auto":
            is_image = self._is_image(input_str)
        else:
            is_image = input_type == "image"

        if is_image:
            # 本地文件需要编码
            if not input_str.startswith(("http://", "https://", "data:")):
                input_str = self._encode_image(input_str)
            return {"image": input_str}
        else:
            return {"text": input_str}

    def _build_payload(
        self,
        inputs: List[str],
        input_type: InputType = "auto",
        dimensions: Optional[int] = None,
    ) -> dict:
        """构建请求 payload"""
        # 准备输入
        prepared_inputs = [
            self._prepare_input(inp, input_type) for inp in inputs
        ]

        payload = {
            "model": self.model,
            "input": prepared_inputs,
        }

        dimensions = dimensions or self._dimensions
        if dimensions:
            payload["dimensions"] = dimensions

        return payload

    def _parse_response(self, data: dict) -> List[List[float]]:
        """解析 API 响应"""
        results = sorted(data["data"], key=lambda x: x["index"])
        embeddings = [item["embedding"] for item in results]

        # 记录实际维度
        if embeddings and not self._actual_dimension:
            self._actual_dimension = len(embeddings[0])

        return embeddings

    # ========== 实现 BaseEmbedding 接口 ==========

    def embed(
        self,
        inputs: Union[str, List[str]],
        input_type: InputType = "auto",
        dimensions: Optional[int] = None,
    ) -> List[List[float]]:
        """
        向量化输入（文本或图片）

        Args:
            inputs: 输入或输入列表（文本/图片路径/图片URL）
            input_type: 输入类型 "text"/"image"/"auto"
            dimensions: 输出维度

        Returns:
            向量列表
        """
        if isinstance(inputs, str):
            inputs = [inputs]

        url = f"{self.base_url}/v1/embeddings"
        payload = self._build_payload(inputs, input_type, dimensions)

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
                return self._parse_response(data)

            except requests.RequestException:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(0.5 * (attempt + 1))

    async def aembed(
        self,
        inputs: Union[str, List[str]],
        input_type: InputType = "auto",
        dimensions: Optional[int] = None,
    ) -> List[List[float]]:
        """异步向量化输入"""
        if isinstance(inputs, str):
            inputs = [inputs]

        url = f"{self.base_url}/v1/embeddings"
        payload = self._build_payload(inputs, input_type, dimensions)

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
                        return self._parse_response(data)

                except aiohttp.ClientError:
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(0.5 * (attempt + 1))

    @property
    def dimension(self) -> int:
        """向量维度"""
        if self._dimensions:
            return self._dimensions
        if self._actual_dimension:
            return self._actual_dimension
        return 768  # CLIP 默认维度

    @property
    def supports_image(self) -> bool:
        return True

    # ========== 便捷方法 ==========

    def embed_text(
        self,
        texts: Union[str, List[str]],
        dimensions: Optional[int] = None,
    ) -> List[List[float]]:
        """仅向量化文本"""
        return self.embed(texts, input_type="text", dimensions=dimensions)

    def embed_image(
        self,
        images: Union[str, List[str]],
        dimensions: Optional[int] = None,
    ) -> List[List[float]]:
        """仅向量化图片"""
        return self.embed(images, input_type="image", dimensions=dimensions)

    async def aembed_text(
        self,
        texts: Union[str, List[str]],
        dimensions: Optional[int] = None,
    ) -> List[List[float]]:
        """异步仅向量化文本"""
        return await self.aembed(texts, input_type="text", dimensions=dimensions)

    async def aembed_image(
        self,
        images: Union[str, List[str]],
        dimensions: Optional[int] = None,
    ) -> List[List[float]]:
        """异步仅向量化图片"""
        return await self.aembed(images, input_type="image", dimensions=dimensions)

    def embed_batch(
        self,
        inputs: List[str],
        batch_size: int = 16,
        input_type: InputType = "auto",
        dimensions: Optional[int] = None,
    ) -> List[List[float]]:
        """批量向量化"""
        return asyncio.run(
            self.aembed_batch(inputs, batch_size, input_type, dimensions)
        )

    async def aembed_batch(
        self,
        inputs: List[str],
        batch_size: int = 16,
        input_type: InputType = "auto",
        dimensions: Optional[int] = None,
    ) -> List[List[float]]:
        """异步批量向量化"""
        all_embeddings = [None] * len(inputs)

        for i in range(0, len(inputs), batch_size):
            batch = inputs[i : i + batch_size]
            vectors = await self.aembed(batch, input_type, dimensions)
            for j, vec in enumerate(vectors):
                all_embeddings[i + j] = vec

        return all_embeddings

    def __repr__(self) -> str:
        return f"MultiModalEmbedding(base_url={self.base_url!r}, model={self.model!r})"
