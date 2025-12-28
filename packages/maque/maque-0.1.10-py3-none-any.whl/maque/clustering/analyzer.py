# -*- coding: utf-8 -*-
"""
聚类分析器

整合聚类、采样、可视化等功能的高级分析器。
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

import numpy as np
from loguru import logger

from .clusterers import (
    BaseClusterer,
    ClusteringResult,
    KMeansClusterer,
    HDBSCANClusterer,
    DBSCANClusterer,
    AgglomerativeClusterer,
    create_clusterer,
)
from .sampler import CentroidSampler, ClusterSample
from .visualizer import ClusterVisualizer, DimReductionMethod


AlgorithmType = Literal["kmeans", "hdbscan", "dbscan", "agglomerative"]


@dataclass
class ClusterResult:
    """聚类分析结果"""
    n_samples: int
    embedding_dim: int
    n_clusters: int
    algorithm: str
    silhouette: Optional[float]
    calinski_harabasz: Optional[float]
    davies_bouldin: Optional[float]
    n_noise: int
    clusters: List[ClusterSample]
    algorithm_info: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "n_samples": self.n_samples,
            "embedding_dim": self.embedding_dim,
            "n_clusters": self.n_clusters,
            "algorithm": self.algorithm,
            "metrics": {
                "silhouette": self.silhouette,
                "calinski_harabasz": self.calinski_harabasz,
                "davies_bouldin": self.davies_bouldin,
            },
            "n_noise": self.n_noise,
            "algorithm_info": self.algorithm_info,
            "clusters": {
                str(c.label): {
                    "count": c.count,
                    "sample_ids": c.sample_ids,
                    "sample_docs": c.sample_docs,
                }
                for c in self.clusters
            },
        }

    def save(self, path: Union[str, Path]) -> None:
        """保存结果到 JSON 文件"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"结果保存到: {path}")


class ClusterAnalyzer:
    """
    聚类分析器

    支持多种聚类算法和可视化方法。

    Example:
        >>> # K-Means 聚类 + UMAP 可视化
        >>> analyzer = ClusterAnalyzer(algorithm="kmeans", n_clusters=20, viz_method="umap")
        >>> result = analyzer.analyze(embeddings, ids=ids, documents=docs)

        >>> # HDBSCAN 自动聚类
        >>> analyzer = ClusterAnalyzer(algorithm="hdbscan", min_cluster_size=50)
        >>> result = analyzer.analyze(embeddings)

        >>> # 从 ChromaDB 分析
        >>> result = analyzer.analyze_chroma(
        ...     persist_dir="./chroma_db",
        ...     collection_name="my_collection",
        ... )
    """

    def __init__(
        self,
        algorithm: AlgorithmType = "kmeans",
        viz_method: DimReductionMethod = "umap",
        n_samples: int = 5,
        max_doc_length: int = 500,
        random_state: int = 42,
        # K-Means / Agglomerative 参数
        n_clusters: Union[int, Literal["auto"]] = "auto",
        k_range: Tuple[int, int] = (2, 30),
        # HDBSCAN 参数
        min_cluster_size: int = 15,
        reduce_dim: Union[int, Literal["auto"], None] = "auto",
        # DBSCAN 参数
        eps: Union[float, Literal["auto"]] = "auto",
        min_samples: int = 5,
        # Agglomerative 参数
        linkage: Literal["ward", "complete", "average", "single"] = "ward",
    ):
        """
        Args:
            algorithm: 聚类算法 ("kmeans", "hdbscan", "dbscan", "agglomerative")
            viz_method: 可视化降维方法 ("umap", "tsne", "pca")
            n_samples: 每个簇采样的样本数
            max_doc_length: 文档截断长度
            random_state: 随机种子
            n_clusters: 聚类数 (kmeans/agglomerative)
            k_range: 自动选 k 范围 (kmeans/agglomerative)
            min_cluster_size: 最小簇大小 (hdbscan)
            reduce_dim: HDBSCAN 预降维维度 ("auto"/int/None)
            eps: 邻域半径 (dbscan)
            min_samples: 最小样本数 (dbscan/hdbscan)
            linkage: 链接方式 (agglomerative)
        """
        self.algorithm = algorithm
        self.random_state = random_state

        # 创建聚类器
        if algorithm == "kmeans":
            self.clusterer = KMeansClusterer(
                n_clusters=n_clusters,
                k_range=k_range,
                random_state=random_state,
            )
        elif algorithm == "hdbscan":
            self.clusterer = HDBSCANClusterer(
                min_cluster_size=min_cluster_size,
                min_samples=min_samples,
                reduce_dim=reduce_dim,
            )
        elif algorithm == "dbscan":
            self.clusterer = DBSCANClusterer(
                eps=eps,
                min_samples=min_samples,
            )
        elif algorithm == "agglomerative":
            self.clusterer = AgglomerativeClusterer(
                n_clusters=n_clusters,
                linkage=linkage,
                k_range=k_range,
            )
        else:
            raise ValueError(f"未知算法: {algorithm}")

        self.sampler = CentroidSampler(
            n_samples=n_samples,
            max_doc_length=max_doc_length,
            metric="cosine",  # 文本嵌入推荐使用余弦距离
        )
        self.visualizer = ClusterVisualizer(
            method=viz_method,
            random_state=random_state,
        )

    def analyze(
        self,
        embeddings: np.ndarray,
        ids: Optional[List[str]] = None,
        documents: Optional[List[str]] = None,
        output_dir: Union[str, Path, None] = None,
        name: str = "cluster",
    ) -> ClusterResult:
        """
        执行聚类分析

        Args:
            embeddings: 向量矩阵 (n_samples, n_features)
            ids: 样本 ID 列表
            documents: 文档内容列表
            output_dir: 输出目录（可选）
            name: 结果文件名前缀

        Returns:
            ClusterResult: 聚类分析结果
        """
        n_samples, embedding_dim = embeddings.shape
        logger.info(f"开始聚类分析: {n_samples} 个样本, {embedding_dim} 维向量, 算法={self.algorithm}")

        # 1. 聚类
        cluster_result = self.clusterer.fit(embeddings)

        # 2. 采样
        logger.info("从每个簇中采样代表性样本...")
        samples = self.sampler.sample(
            embeddings, cluster_result.labels,
            ids=ids, documents=documents,
        )

        # 3. 统计簇大小
        self._log_cluster_stats(samples)

        # 4. 构建结果
        result = ClusterResult(
            n_samples=n_samples,
            embedding_dim=embedding_dim,
            n_clusters=cluster_result.n_clusters,
            algorithm=cluster_result.algorithm,
            silhouette=cluster_result.silhouette,
            calinski_harabasz=cluster_result.calinski_harabasz,
            davies_bouldin=cluster_result.davies_bouldin,
            n_noise=cluster_result.n_noise,
            clusters=samples,
            algorithm_info=cluster_result.extra_info,
        )

        # 5. 保存结果
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # 保存 JSON
            result.save(output_dir / f"{name}_{self.algorithm}.json")

            # 保存可视化
            self.visualizer.plot(
                embeddings, cluster_result.labels,
                output_dir / f"{name}_{self.algorithm}.png",
                title=f"{name} ({self.algorithm}, n={cluster_result.n_clusters})",
            )

        logger.info("聚类分析完成")
        return result

    def analyze_chroma(
        self,
        persist_dir: Union[str, Path],
        collection_name: str,
        output_dir: Union[str, Path, None] = None,
        name: Optional[str] = None,
        sample_size: Optional[int] = None,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> ClusterResult:
        """
        从 ChromaDB 加载数据并执行聚类分析

        Args:
            persist_dir: ChromaDB 持久化目录
            collection_name: 集合名称
            output_dir: 输出目录（可选）
            name: 结果文件名前缀（默认使用 collection_name）
            sample_size: 限制加载的样本数量（可选，用于大规模数据）
            where: 元数据过滤条件（可选），例如 {"category": "tech"}
            where_document: 文档内容过滤条件（可选），例如 {"$contains": "python"}

        Returns:
            ClusterResult: 聚类分析结果

        Example:
            >>> # 全量数据分析
            >>> analyzer = ClusterAnalyzer(algorithm="hdbscan")
            >>> result = analyzer.analyze_chroma(
            ...     persist_dir="./chroma_db",
            ...     collection_name="my_data",
            ... )

            >>> # 采样分析（处理大规模数据）
            >>> result = analyzer.analyze_chroma(
            ...     persist_dir="./chroma_db",
            ...     collection_name="my_data",
            ...     sample_size=10000,
            ... )

            >>> # 过滤特定类别的数据
            >>> result = analyzer.analyze_chroma(
            ...     persist_dir="./chroma_db",
            ...     collection_name="my_data",
            ...     where={"category": "tech"},
            ... )
        """
        try:
            import chromadb
        except ImportError:
            raise ImportError("请安装 chromadb: pip install chromadb")

        logger.info(f"从 ChromaDB 加载数据: {collection_name}")

        client = chromadb.PersistentClient(path=str(persist_dir))
        collection = client.get_collection(collection_name)

        # 构建查询参数
        query_kwargs = {
            "include": ["embeddings", "documents", "metadatas"]
        }

        if sample_size is not None:
            query_kwargs["limit"] = sample_size
            logger.info(f"限制加载前 {sample_size} 条数据")

        if where is not None:
            query_kwargs["where"] = where
            logger.info(f"应用元数据过滤: {where}")

        if where_document is not None:
            query_kwargs["where_document"] = where_document
            logger.info(f"应用文档过滤: {where_document}")

        # 加载数据
        results = collection.get(**query_kwargs)

        ids = results["ids"]
        embeddings = np.array(results["embeddings"])
        documents = results["documents"]

        logger.info(f"加载 {len(embeddings)} 个向量, 维度={embeddings.shape[1]}")

        return self.analyze(
            embeddings,
            ids=ids,
            documents=documents,
            output_dir=output_dir,
            name=name or collection_name,
        )

    def _log_cluster_stats(self, samples: List[ClusterSample]) -> None:
        """输出簇大小统计"""
        total = sum(s.count for s in samples)
        sorted_samples = sorted(samples, key=lambda s: -s.count)

        logger.info("簇大小分布:")
        for s in sorted_samples[:10]:
            pct = s.count / total * 100
            label = "Noise" if s.label == "noise" else f"Cluster {s.label}"
            logger.info(f"  {label}: {s.count} ({pct:.1f}%)")

        if len(sorted_samples) > 10:
            logger.info(f"  ... 还有 {len(sorted_samples) - 10} 个簇")
