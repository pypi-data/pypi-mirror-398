#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档数据结构
"""

import hashlib
from dataclasses import dataclass, field
from typing import Literal, Optional


Modality = Literal["text", "image"]


def _content_hash(content: str) -> str:
    """基于内容生成确定性 ID"""
    return hashlib.md5(content.encode()).hexdigest()


@dataclass
class Document:
    """
    通用文档结构，支持文本和图片
    """

    id: str
    content: str                    # 文本内容 或 图片路径/URL
    modality: Modality = "text"
    metadata: dict = field(default_factory=dict)

    @property
    def is_text(self) -> bool:
        return self.modality == "text"

    @property
    def is_image(self) -> bool:
        return self.modality == "image"

    @classmethod
    def text(
        cls,
        content: str,
        id: Optional[str] = None,
        **metadata,
    ) -> "Document":
        """
        创建文本文档

        Args:
            content: 文本内容
            id: 文档 ID（可选，基于 content 自动生成确定性 ID）
            **metadata: 元数据

        Returns:
            Document 实例
        """
        return cls(
            id=id or _content_hash(content),
            content=content,
            modality="text",
            metadata=metadata,
        )

    @classmethod
    def image(
        cls,
        path_or_url: str,
        id: Optional[str] = None,
        **metadata,
    ) -> "Document":
        """
        创建图片文档

        Args:
            path_or_url: 图片路径或 URL
            id: 文档 ID（可选，基于路径自动生成确定性 ID）
            **metadata: 元数据

        Returns:
            Document 实例
        """
        return cls(
            id=id or _content_hash(path_or_url),
            content=path_or_url,
            modality="image",
            metadata=metadata,
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "modality": self.modality,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        """从字典创建"""
        return cls(
            id=data["id"],
            content=data["content"],
            modality=data.get("modality", "text"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SearchResult:
    """
    检索结果
    """

    id: str
    content: str
    score: float
    modality: Modality = "text"
    metadata: dict = field(default_factory=dict)

    @property
    def document(self) -> Document:
        """转换为 Document"""
        return Document(
            id=self.id,
            content=self.content,
            modality=self.modality,
            metadata=self.metadata,
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "modality": self.modality,
            "metadata": self.metadata,
        }
