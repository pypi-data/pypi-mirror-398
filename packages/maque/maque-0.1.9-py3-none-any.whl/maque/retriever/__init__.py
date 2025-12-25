#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Retriever 模块 - 提供向量检索功能

支持 ChromaDB 和 Milvus 两种向量数据库后端，可独立使用。
"""

from .document import Document, SearchResult, Modality
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chroma import ChromaRetriever
    from .milvus import MilvusRetriever


def __getattr__(name: str):
    """延迟导入，避免未使用的依赖"""
    if name == "ChromaRetriever":
        from .chroma import ChromaRetriever
        return ChromaRetriever
    elif name == "MilvusRetriever":
        from .milvus import MilvusRetriever
        return MilvusRetriever
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Document",
    "SearchResult",
    "Modality",
    "ChromaRetriever",
    "MilvusRetriever",
]
