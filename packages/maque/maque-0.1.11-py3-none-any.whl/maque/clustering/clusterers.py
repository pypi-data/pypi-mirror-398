# -*- coding: utf-8 -*-
"""
聚类算法集合

支持多种聚类算法：
- K-Means: 经典算法，需指定聚类数
- HDBSCAN: 自动确定聚类数，对噪声鲁棒
- DBSCAN: 基于密度，自动确定聚类数
- Agglomerative: 层次聚类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Literal, Optional, Tuple, Union

import numpy as np
from loguru import logger
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

@dataclass
class ClusteringResult:
    """聚类结果"""
    labels: np.ndarray
    n_clusters: int
    algorithm: str
    silhouette: Optional[float] = None
    calinski_harabasz: Optional[float] = None
    davies_bouldin: Optional[float] = None
    n_noise: int = 0
    extra_info: dict = field(default_factory=dict)


@dataclass
class ClusterMetrics:
    """聚类质量指标"""
    silhouette: Optional[float] = None
    calinski_harabasz: Optional[float] = None
    davies_bouldin: Optional[float] = None


class BaseClusterer(ABC):
    """聚类器基类"""

    @abstractmethod
    def fit(self, embeddings: np.ndarray) -> ClusteringResult:
        """执行聚类"""
        pass

    def _compute_metrics(self, embeddings: np.ndarray, labels: np.ndarray) -> ClusterMetrics:
        """
        计算聚类质量指标（排除噪声点）

        指标说明：
        - silhouette: 轮廓系数 [-1, 1]，越大越好
        - calinski_harabasz: CH 指数，越大越好
        - davies_bouldin: DB 指数，越小越好
        """
        valid_mask = labels != -1
        if valid_mask.sum() < 2:
            return ClusterMetrics()

        unique_labels = set(labels[valid_mask])
        if len(unique_labels) < 2:
            return ClusterMetrics()

        valid_embeddings = embeddings[valid_mask]
        valid_labels = labels[valid_mask]

        try:
            silhouette = silhouette_score(valid_embeddings, valid_labels)
            calinski = calinski_harabasz_score(valid_embeddings, valid_labels)
            davies = davies_bouldin_score(valid_embeddings, valid_labels)
            return ClusterMetrics(
                silhouette=round(silhouette, 4),
                calinski_harabasz=round(calinski, 2),
                davies_bouldin=round(davies, 4),
            )
        except Exception as e:
            logger.warning(f"计算聚类指标失败: {e}")
            return ClusterMetrics()


class KMeansClusterer(BaseClusterer):
    """
    K-Means 聚类器

    支持自动选择最优聚类数（轮廓系数法）

    Example:
        >>> clusterer = KMeansClusterer(n_clusters=10)
        >>> result = clusterer.fit(embeddings)
    """

    def __init__(
        self,
        n_clusters: Union[int, Literal["auto"]] = "auto",
        k_range: Tuple[int, int] = (2, 30),
        random_state: int = 42,
        n_init: int = 10,
    ):
        self.n_clusters = n_clusters
        self.k_range = k_range
        self.random_state = random_state
        self.n_init = n_init

    def fit(self, embeddings: np.ndarray) -> ClusteringResult:
        extra_info = {}

        if self.n_clusters == "auto":
            n_clusters, k_scores = self._auto_select_k(embeddings)
            extra_info["k_selection_method"] = "silhouette"
            extra_info["k_scores"] = {str(k): round(v, 4) for k, v in k_scores.items()}
            logger.info(f"自动选择 k={n_clusters}")
        else:
            n_clusters = self.n_clusters

        logger.info(f"执行 K-Means 聚类 (k={n_clusters})...")
        self._model = KMeans(
            n_clusters=n_clusters,
            random_state=self.random_state,
            n_init=self.n_init,
        )
        labels = self._model.fit_predict(embeddings)
        extra_info["inertia"] = round(self._model.inertia_, 2)

        metrics = self._compute_metrics(embeddings, labels)
        if metrics.silhouette:
            logger.info(f"轮廓系数: {metrics.silhouette:.4f}, CH: {metrics.calinski_harabasz:.2f}, DB: {metrics.davies_bouldin:.4f}")

        return ClusteringResult(
            labels=labels,
            n_clusters=n_clusters,
            algorithm="kmeans",
            silhouette=metrics.silhouette,
            calinski_harabasz=metrics.calinski_harabasz,
            davies_bouldin=metrics.davies_bouldin,
            extra_info=extra_info,
        )

    def predict(self, embeddings: np.ndarray) -> np.ndarray:
        """预测新样本的簇标签"""
        if not hasattr(self, '_model'):
            raise RuntimeError("请先调用 fit() 方法")
        return self._model.predict(embeddings)

    def _auto_select_k(self, embeddings: np.ndarray) -> Tuple[int, Dict[int, float]]:
        n_samples = len(embeddings)
        k_min, k_max = self.k_range
        k_max = min(k_max, n_samples - 1)

        if k_min >= k_max:
            return k_min, {}

        logger.info(f"搜索最优 k (范围: {k_min}-{k_max})...")
        scores = {}

        for k in range(k_min, k_max + 1):
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=self.n_init)
            labels = kmeans.fit_predict(embeddings)
            scores[k] = silhouette_score(embeddings, labels)

        best_k = max(scores, key=scores.get)
        return best_k, scores


class HDBSCANClusterer(BaseClusterer):
    """
    HDBSCAN 聚类器

    自动确定聚类数，对噪声鲁棒。适合发现任意形状的簇。

    注意：HDBSCAN 在高维空间（如 >50 维的嵌入向量）效果较差，
    建议开启 reduce_dim 参数先用 UMAP 降维再聚类。

    Example:
        >>> # 高维嵌入向量推荐使用预降维
        >>> clusterer = HDBSCANClusterer(min_cluster_size=15, reduce_dim=20)
        >>> result = clusterer.fit(embeddings)
    """

    def __init__(
        self,
        min_cluster_size: int = 15,
        min_samples: Optional[int] = None,
        cluster_selection_epsilon: float = 0.0,
        metric: str = "euclidean",
        reduce_dim: Union[int, Literal["auto"], None] = None,
        reduce_dim_threshold: int = 50,
    ):
        """
        Args:
            min_cluster_size: 最小簇大小
            min_samples: 核心点的最小邻居数
            cluster_selection_epsilon: 簇选择阈值
            metric: 距离度量
            reduce_dim: 预降维目标维度
                - None: 不降维（默认，适合低维数据）
                - "auto": 当维度 > reduce_dim_threshold 时自动降到 20 维
                - int: 指定降维目标维度
            reduce_dim_threshold: 自动降维的维度阈值（默认 50）
        """
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.cluster_selection_epsilon = cluster_selection_epsilon
        self.metric = metric
        self.reduce_dim = reduce_dim
        self.reduce_dim_threshold = reduce_dim_threshold

    def _reduce_with_umap(self, embeddings: np.ndarray, n_components: int) -> np.ndarray:
        """使用 UMAP 降维"""
        try:
            import umap
        except ImportError:
            raise ImportError("预降维需要 umap-learn: pip install umap-learn")

        logger.info(f"使用 UMAP 预降维: {embeddings.shape[1]}维 -> {n_components}维...")
        reducer = umap.UMAP(
            n_components=n_components,
            n_neighbors=15,
            min_dist=0.0,  # 聚类用途，设为 0 保持局部结构
            metric="cosine",
            random_state=42,
        )
        return reducer.fit_transform(embeddings)

    def fit(self, embeddings: np.ndarray) -> ClusteringResult:
        try:
            import hdbscan
        except ImportError:
            raise ImportError("HDBSCAN 需要: pip install hdbscan")

        original_dim = embeddings.shape[1]
        reduced_dim = None
        extra_info = {
            "min_cluster_size": self.min_cluster_size,
            "min_samples": self.min_samples,
        }

        # 判断是否需要预降维
        if self.reduce_dim == "auto":
            if original_dim > self.reduce_dim_threshold:
                reduced_dim = 20
        elif isinstance(self.reduce_dim, int):
            reduced_dim = self.reduce_dim

        # 执行预降维
        if reduced_dim and reduced_dim < original_dim:
            embeddings_for_cluster = self._reduce_with_umap(embeddings, reduced_dim)
            extra_info["umap_reduced_dim"] = reduced_dim
            extra_info["original_dim"] = original_dim
        else:
            embeddings_for_cluster = embeddings

        logger.info(f"执行 HDBSCAN 聚类 (min_cluster_size={self.min_cluster_size})...")

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            cluster_selection_epsilon=self.cluster_selection_epsilon,
            metric=self.metric,
            cluster_selection_method='eom',
        )
        labels = clusterer.fit_predict(embeddings_for_cluster)

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = (labels == -1).sum()

        logger.info(f"发现 {n_clusters} 个簇, {n_noise} 个噪声点 ({n_noise/len(labels)*100:.1f}%)")

        # 在降维后的空间计算指标
        metrics = self._compute_metrics(embeddings_for_cluster, labels)
        if metrics.silhouette:
            logger.info(f"轮廓系数: {metrics.silhouette:.4f}, CH: {metrics.calinski_harabasz:.2f}, DB: {metrics.davies_bouldin:.4f}")

        return ClusteringResult(
            labels=labels,
            n_clusters=n_clusters,
            algorithm="hdbscan",
            silhouette=metrics.silhouette,
            calinski_harabasz=metrics.calinski_harabasz,
            davies_bouldin=metrics.davies_bouldin,
            n_noise=int(n_noise),
            extra_info=extra_info,
        )


class DBSCANClusterer(BaseClusterer):
    """
    DBSCAN 聚类器

    基于密度的聚类，自动确定聚类数。

    Example:
        >>> clusterer = DBSCANClusterer(eps=0.5, min_samples=5)
        >>> result = clusterer.fit(embeddings)
    """

    def __init__(
        self,
        eps: Union[float, Literal["auto"]] = "auto",
        min_samples: int = 5,
        metric: str = "euclidean",
    ):
        self.eps = eps
        self.min_samples = min_samples
        self.metric = metric

    def fit(self, embeddings: np.ndarray) -> ClusteringResult:
        eps = self.eps
        if eps == "auto":
            eps = self._auto_select_eps(embeddings)
            logger.info(f"自动选择 eps={eps:.4f}")

        logger.info(f"执行 DBSCAN 聚类 (eps={eps:.4f}, min_samples={self.min_samples})...")

        dbscan = DBSCAN(eps=eps, min_samples=self.min_samples, metric=self.metric)
        labels = dbscan.fit_predict(embeddings)

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = (labels == -1).sum()

        logger.info(f"发现 {n_clusters} 个簇, {n_noise} 个噪声点 ({n_noise/len(labels)*100:.1f}%)")

        metrics = self._compute_metrics(embeddings, labels)
        if metrics.silhouette:
            logger.info(f"轮廓系数: {metrics.silhouette:.4f}, CH: {metrics.calinski_harabasz:.2f}, DB: {metrics.davies_bouldin:.4f}")

        return ClusteringResult(
            labels=labels,
            n_clusters=n_clusters,
            algorithm="dbscan",
            silhouette=metrics.silhouette,
            calinski_harabasz=metrics.calinski_harabasz,
            davies_bouldin=metrics.davies_bouldin,
            n_noise=int(n_noise),
            extra_info={"eps": round(eps, 4), "min_samples": self.min_samples},
        )

    def _auto_select_eps(self, embeddings: np.ndarray) -> float:
        """使用 k-距离图自动选择 eps"""
        from sklearn.neighbors import NearestNeighbors

        nn = NearestNeighbors(n_neighbors=self.min_samples)
        nn.fit(embeddings)
        distances, _ = nn.kneighbors(embeddings)
        distances = np.sort(distances[:, -1])

        # 使用二阶差分找拐点
        d1 = np.diff(distances)
        d2 = np.diff(d1)
        knee_idx = np.argmax(d2) + 1
        return float(distances[knee_idx])


class AgglomerativeClusterer(BaseClusterer):
    """
    层次聚类器

    自底向上的层次聚类算法。

    Example:
        >>> clusterer = AgglomerativeClusterer(n_clusters=10)
        >>> result = clusterer.fit(embeddings)
    """

    def __init__(
        self,
        n_clusters: Union[int, Literal["auto"]] = "auto",
        linkage: Literal["ward", "complete", "average", "single"] = "ward",
        distance_threshold: Optional[float] = None,
        k_range: Tuple[int, int] = (2, 30),
    ):
        self.n_clusters = n_clusters
        self.linkage = linkage
        self.distance_threshold = distance_threshold
        self.k_range = k_range

    def fit(self, embeddings: np.ndarray) -> ClusteringResult:
        extra_info = {"linkage": self.linkage}

        if self.distance_threshold is not None:
            logger.info(f"执行层次聚类 (distance_threshold={self.distance_threshold})...")
            agg = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=self.distance_threshold,
                linkage=self.linkage,
            )
            extra_info["distance_threshold"] = self.distance_threshold
        else:
            if self.n_clusters == "auto":
                n_clusters = self._auto_select_k(embeddings)
                logger.info(f"自动选择 k={n_clusters}")
            else:
                n_clusters = self.n_clusters

            logger.info(f"执行层次聚类 (n_clusters={n_clusters}, linkage={self.linkage})...")
            agg = AgglomerativeClustering(n_clusters=n_clusters, linkage=self.linkage)

        labels = agg.fit_predict(embeddings)
        n_clusters = len(set(labels))

        metrics = self._compute_metrics(embeddings, labels)
        if metrics.silhouette:
            logger.info(f"轮廓系数: {metrics.silhouette:.4f}, CH: {metrics.calinski_harabasz:.2f}, DB: {metrics.davies_bouldin:.4f}")

        return ClusteringResult(
            labels=labels,
            n_clusters=n_clusters,
            algorithm="agglomerative",
            silhouette=metrics.silhouette,
            calinski_harabasz=metrics.calinski_harabasz,
            davies_bouldin=metrics.davies_bouldin,
            extra_info=extra_info,
        )

    def _auto_select_k(self, embeddings: np.ndarray) -> int:
        """使用轮廓系数自动选择 k"""
        n_samples = len(embeddings)
        k_min, k_max = self.k_range
        k_max = min(k_max, n_samples - 1)

        logger.info(f"搜索最优 k (范围: {k_min}-{k_max})...")
        best_k, best_score = k_min, -1

        for k in range(k_min, k_max + 1):
            agg = AgglomerativeClustering(n_clusters=k, linkage=self.linkage)
            labels = agg.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            if score > best_score:
                best_k, best_score = k, score

        return best_k


def create_clusterer(
    algorithm: Literal["kmeans", "hdbscan", "dbscan", "agglomerative"] = "kmeans",
    **kwargs
) -> BaseClusterer:
    """
    创建聚类器的工厂函数

    Args:
        algorithm: 聚类算法
        **kwargs: 传递给聚类器的参数

    Returns:
        BaseClusterer: 聚类器实例

    Example:
        >>> clusterer = create_clusterer("hdbscan", min_cluster_size=20)
        >>> result = clusterer.fit(embeddings)
    """
    clusterers = {
        "kmeans": KMeansClusterer,
        "hdbscan": HDBSCANClusterer,
        "dbscan": DBSCANClusterer,
        "agglomerative": AgglomerativeClusterer,
    }

    if algorithm not in clusterers:
        raise ValueError(f"未知算法: {algorithm}, 支持: {list(clusterers.keys())}")

    return clusterers[algorithm](**kwargs)
