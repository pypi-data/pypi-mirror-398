#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Embedding 模块 - 提供文本和多模态向量化功能

包含:
- 客户端: TextEmbedding, MultiModalEmbedding
- 服务端: EmbeddingServer, create_server
"""

from .base import BaseEmbedding
from .text import (
    TextEmbedding,
    EmbeddingClient,  # 向后兼容别名
    EmbeddingResult,
    EmbeddingResponse,
    TaskType,
)
from .multimodal import MultiModalEmbedding

# 服务端 (延迟导入，避免强依赖 fastapi)
def __getattr__(name):
    if name in ("EmbeddingServer", "create_server"):
        from .server import EmbeddingServer, create_server
        return {"EmbeddingServer": EmbeddingServer, "create_server": create_server}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # 基类
    "BaseEmbedding",
    # 文本客户端
    "TextEmbedding",
    "EmbeddingClient",  # 向后兼容
    "EmbeddingResult",
    "EmbeddingResponse",
    "TaskType",
    # 多模态客户端
    "MultiModalEmbedding",
    # 服务端
    "EmbeddingServer",
    "create_server",
]
