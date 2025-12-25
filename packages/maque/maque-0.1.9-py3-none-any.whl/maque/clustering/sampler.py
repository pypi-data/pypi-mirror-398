# -*- coding: utf-8 -*-
"""
聚类样本采样器
"""

from dataclasses import dataclass
from typing import List, Literal, Optional, Union

import numpy as np
from loguru import logger


@dataclass
class ClusterSample:
    """单个簇的样本信息"""
    label: Union[int, str]
    count: int
    sample_indices: List[int]
    sample_ids: Optional[List[str]] = None
    sample_docs: Optional[List[str]] = None


class CentroidSampler:
    """
    基于质心的样本采样器

    从每个簇中选择距离质心最近的样本，这些样本最能代表簇的特征。

    Example:
        >>> sampler = CentroidSampler(n_samples=5, metric="cosine")
        >>> samples = sampler.sample(embeddings, labels)
        >>> for s in samples:
        ...     print(f"Cluster {s.label}: {s.count} samples")
    """

    def __init__(
        self,
        n_samples: int = 5,
        max_doc_length: int = 500,
        metric: Literal["euclidean", "cosine"] = "cosine",
    ):
        """
        Args:
            n_samples: 每个簇采样的样本数
            max_doc_length: 文档截断长度
            metric: 距离度量方式，"euclidean" 或 "cosine"（推荐用于文本嵌入）
        """
        self.n_samples = n_samples
        self.max_doc_length = max_doc_length
        self.metric = metric

    def sample(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray,
        ids: Optional[List[str]] = None,
        documents: Optional[List[str]] = None,
    ) -> List[ClusterSample]:
        """
        从每个簇中采样距离质心最近的样本

        Args:
            embeddings: 向量矩阵
            labels: 聚类标签
            ids: 样本 ID 列表
            documents: 文档内容列表

        Returns:
            list[ClusterSample]: 每个簇的样本信息
        """
        unique_labels = sorted(set(labels))
        samples = []

        logger.debug(f"从 {len(unique_labels)} 个簇中采样...")

        for label in unique_labels:
            mask = labels == label
            cluster_indices = np.where(mask)[0]
            cluster_embeddings = embeddings[mask]

            if label == -1:
                # 噪声点：取前 n 个
                selected_indices = cluster_indices[:self.n_samples].tolist()
            else:
                # 计算质心并选择最近的样本
                centroid = cluster_embeddings.mean(axis=0)
                distances = self._compute_distances(cluster_embeddings, centroid)
                nearest_indices = np.argsort(distances)[:self.n_samples]
                selected_indices = cluster_indices[nearest_indices].tolist()

            # 构建样本信息
            sample = ClusterSample(
                label="noise" if label == -1 else label,
                count=int(mask.sum()),
                sample_indices=selected_indices,
            )

            if ids is not None:
                sample.sample_ids = [ids[i] for i in selected_indices]

            if documents is not None:
                sample.sample_docs = [
                    self._truncate(documents[i]) for i in selected_indices
                ]

            samples.append(sample)

        return samples

    def _compute_distances(self, embeddings: np.ndarray, centroid: np.ndarray) -> np.ndarray:
        """
        计算样本到质心的距离

        Args:
            embeddings: 样本向量矩阵 (n, dim)
            centroid: 质心向量 (dim,)

        Returns:
            距离数组 (n,)
        """
        if self.metric == "cosine":
            # 余弦距离 = 1 - 余弦相似度
            norm_emb = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10)
            norm_cen = centroid / (np.linalg.norm(centroid) + 1e-10)
            return 1 - np.dot(norm_emb, norm_cen)
        else:
            # 欧氏距离
            return np.linalg.norm(embeddings - centroid, axis=1)

    def _truncate(self, text: str) -> str:
        """截断文本"""
        if len(text) > self.max_doc_length:
            return text[:self.max_doc_length] + "..."
        return text
