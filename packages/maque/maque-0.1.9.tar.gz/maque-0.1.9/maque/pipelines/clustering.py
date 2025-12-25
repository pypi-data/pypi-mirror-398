#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
聚类分析流水线

提供向量化 + 聚类的端到端便利接口。
这是可选的高层封装，用户仍可使用底层 API 进行完全自定义。
"""

from pathlib import Path
from typing import List, Optional, Union

import numpy as np
from loguru import logger

try:
    import chromadb
except ImportError:
    chromadb = None

from ..embedding.base import BaseEmbedding
from ..retriever import ChromaRetriever, Document
from ..clustering import ClusterAnalyzer, ClusterResult


class ClusteringPipeline:
    """
    向量化 + 聚类的端到端流水线

    封装常见的工作流：数据加载 → 向量化 → 存储 → 聚类分析

    这是可选的便利层，用户仍可使用底层组件：
    - TextEmbedding: 向量化
    - ChromaRetriever: 向量存储与检索
    - ClusterAnalyzer: 聚类分析

    Example:
        >>> # 基础用法
        >>> from maque.embedding import TextEmbedding
        >>> from maque.pipelines import ClusteringPipeline
        >>> from maque.clustering import ClusterAnalyzer
        >>> from maque.retriever import Document
        >>>
        >>> # 创建流水线
        >>> pipeline = ClusteringPipeline(
        ...     embedding=TextEmbedding(base_url="http://localhost:8000", model="jina-v3"),
        ...     persist_dir="./chroma_db",
        ...     collection_name="my_data",
        ... )
        >>>
        >>> # 向量化文档
        >>> docs = [Document.text(content=text, id=f"doc_{i}") for i, text in enumerate(texts)]
        >>> pipeline.build_vectors(docs, batch_size=32, skip_existing=True)
        >>>
        >>> # 聚类分析
        >>> analyzer = ClusterAnalyzer(algorithm="hdbscan", min_cluster_size=15)
        >>> result = pipeline.analyze(analyzer, output_dir="./results", name="my_cluster")

        >>> # 高级用法：直接访问底层组件
        >>> pipeline.retriever.search("查询文本", top_k=10)  # 使用检索功能
        >>> pipeline.embedding.embed(["文本1", "文本2"])     # 直接向量化
    """

    def __init__(
        self,
        embedding: BaseEmbedding,
        persist_dir: Union[str, Path] = None,
        collection_name: str = "default",
        distance_metric: str = "cosine",
        retriever=None,
    ):
        """
        初始化聚类流水线

        Args:
            embedding: Embedding 实例（TextEmbedding 或 MultiModalEmbedding）
            persist_dir: ChromaDB 持久化目录（当 retriever=None 时必须提供）
            collection_name: 集合名称（当 retriever=None 时使用）
            distance_metric: 距离度量方式 (cosine/l2/ip)（当 retriever=None 时使用）
            retriever: 可选，直接传入 Retriever 实例（ChromaRetriever 或 MilvusRetriever）
                      传入后将忽略 persist_dir, collection_name, distance_metric 参数
        """
        self.embedding = embedding

        # 支持传入 retriever 或自动创建 ChromaRetriever
        if retriever is not None:
            self.retriever = retriever
            self.persist_dir = getattr(retriever, 'persist_dir', None)
            self.collection_name = getattr(retriever, 'collection_name', 'unknown')
            logger.info(f"初始化 ClusteringPipeline: {self.collection_name} (外部 retriever)")
        else:
            if persist_dir is None:
                raise ValueError("persist_dir 必须提供（当 retriever=None 时）")
            self.persist_dir = Path(persist_dir)
            self.collection_name = collection_name
            # 创建 ChromaRetriever（底层组件仍可访问）
            self.retriever = ChromaRetriever(
                embedding=embedding,
                persist_dir=str(persist_dir),
                collection_name=collection_name,
                distance_metric=distance_metric,
            )
            logger.info(f"初始化 ClusteringPipeline: {collection_name} @ {persist_dir}")

    def build_vectors(
        self,
        documents: List[Document],
        batch_size: int = 32,
        skip_existing: bool = True,
        show_progress: bool = True,
    ) -> int:
        """
        向量化并存储文档

        Args:
            documents: 文档列表
            batch_size: 批处理大小
            skip_existing: 是否跳过已存在的文档（增量更新）
            show_progress: 是否显示进度条

        Returns:
            实际插入的文档数量

        Example:
            >>> from maque.retriever import Document
            >>> docs = [Document.text(content=f"text {i}", id=f"doc_{i}") for i in range(100)]
            >>> count = pipeline.build_vectors(docs, skip_existing=True)
            >>> print(f"插入 {count} 个文档")
        """
        logger.info(f"开始向量化 {len(documents)} 个文档...")

        count = self.retriever.upsert_batch(
            documents=documents,
            batch_size=batch_size,
            skip_existing=skip_existing,
            show_progress=show_progress,
        )

        logger.info(f"完成向量化，当前集合共 {self.retriever.count()} 个文档")
        return count

    def analyze(
        self,
        analyzer: ClusterAnalyzer,
        output_dir: Optional[Union[str, Path]] = None,
        name: Optional[str] = None,
        sample_size: Optional[int] = None,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> ClusterResult:
        """
        从 ChromaDB 加载并执行聚类分析

        Args:
            analyzer: ClusterAnalyzer 实例（预配置算法参数）
            output_dir: 输出目录（保存 JSON 和可视化图片）
            name: 结果文件名前缀（默认使用 collection_name）
            sample_size: 限制加载的样本数量（用于大规模数据）
            where: 元数据过滤条件
            where_document: 文档内容过滤条件

        Returns:
            ClusterResult: 聚类分析结果

        Example:
            >>> # HDBSCAN 自动聚类
            >>> analyzer = ClusterAnalyzer(algorithm="hdbscan", min_cluster_size=15)
            >>> result = pipeline.analyze(analyzer, output_dir="./results")

            >>> # K-Means 指定簇数
            >>> analyzer = ClusterAnalyzer(algorithm="kmeans", n_clusters=20)
            >>> result = pipeline.analyze(analyzer, output_dir="./results", sample_size=10000)

            >>> # 过滤特定类别数据
            >>> result = pipeline.analyze(
            ...     analyzer,
            ...     output_dir="./results",
            ...     where={"category": "tech"},
            ... )
        """
        logger.info("开始聚类分析...")

        # 使用 ClusterAnalyzer 的 analyze_chroma 方法
        result = analyzer.analyze_chroma(
            persist_dir=self.persist_dir,
            collection_name=self.collection_name,
            output_dir=output_dir,
            name=name or self.collection_name,
            sample_size=sample_size,
            where=where,
            where_document=where_document,
        )

        logger.info("聚类分析完成")
        return result

    def load_vectors(
        self,
        sample_size: Optional[int] = None,
        where: Optional[dict] = None,
    ) -> tuple[List[str], np.ndarray, List[str]]:
        """
        从 ChromaDB 加载向量数据（供高级用户自定义分析）

        Args:
            sample_size: 限制加载的样本数量
            where: 元数据过滤条件

        Returns:
            (ids, embeddings, documents) 元组

        Example:
            >>> ids, embeddings, docs = pipeline.load_vectors(sample_size=1000)
            >>> print(f"加载 {len(embeddings)} 个向量，维度={embeddings.shape[1]}")
            >>> # 用户可自定义分析逻辑
            >>> from sklearn.cluster import KMeans
            >>> kmeans = KMeans(n_clusters=10)
            >>> labels = kmeans.fit_predict(embeddings)
        """
        if chromadb is None:
            raise ImportError("需要安装 chromadb: pip install chromadb")

        client = chromadb.PersistentClient(path=str(self.persist_dir))
        collection = client.get_collection(self.collection_name)

        query_kwargs = {"include": ["embeddings", "documents", "metadatas"]}
        if sample_size is not None:
            query_kwargs["limit"] = sample_size
        if where is not None:
            query_kwargs["where"] = where

        results = collection.get(**query_kwargs)

        ids = results["ids"]
        embeddings = np.array(results["embeddings"])
        documents = results["documents"]

        logger.info(f"加载 {len(embeddings)} 个向量, 维度={embeddings.shape[1]}")
        return ids, embeddings, documents

    def count(self) -> int:
        """返回集合中的文档数量"""
        return self.retriever.count()

    def __repr__(self) -> str:
        return (
            f"ClusteringPipeline("
            f"collection={self.collection_name!r}, "
            f"count={self.count()}, "
            f"persist_dir={str(self.persist_dir)!r})"
        )
