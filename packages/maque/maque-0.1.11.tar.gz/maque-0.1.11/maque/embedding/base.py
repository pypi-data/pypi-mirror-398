#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Embedding 抽象基类
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class BaseEmbedding(ABC):
    """Embedding 抽象基类，定义统一接口"""

    @abstractmethod
    def embed(
        self,
        inputs: List[str],
        **kwargs,
    ) -> List[List[float]]:
        """
        向量化接口

        Args:
            inputs: 输入列表（文本或图片路径/URL）
            **kwargs: 额外参数

        Returns:
            向量列表
        """
        pass

    @abstractmethod
    async def aembed(
        self,
        inputs: List[str],
        **kwargs,
    ) -> List[List[float]]:
        """异步向量化接口"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度"""
        pass

    @property
    def supports_image(self) -> bool:
        """是否支持图片模态"""
        return False

    @property
    def model_name(self) -> str:
        """模型名称"""
        return getattr(self, "model", "unknown")
