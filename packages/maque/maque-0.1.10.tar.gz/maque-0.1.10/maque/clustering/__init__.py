# -*- coding: utf-8 -*-
"""
聚类分析模块

提供通用的聚类分析工具，支持多种算法和可视化方法。

聚类算法：
- K-Means: 经典算法，需指定聚类数
- HDBSCAN: 自动确定聚类数，对噪声鲁棒
- DBSCAN: 基于密度，自动确定聚类数
- Agglomerative: 层次聚类

可视化方法：
- UMAP: 速度快，保持全局结构（推荐）
- t-SNE: 保持局部结构
- PCA: 最快，线性降维
"""

from .clusterers import (
    BaseClusterer,
    ClusteringResult,
    ClusterMetrics,
    KMeansClusterer,
    HDBSCANClusterer,
    DBSCANClusterer,
    AgglomerativeClusterer,
    create_clusterer,
)
from .sampler import CentroidSampler, ClusterSample
from .visualizer import ClusterVisualizer, DimReductionMethod
from .analyzer import ClusterAnalyzer, ClusterResult

__all__ = [
    # 聚类器
    "BaseClusterer",
    "ClusteringResult",
    "ClusterMetrics",
    "KMeansClusterer",
    "HDBSCANClusterer",
    "DBSCANClusterer",
    "AgglomerativeClusterer",
    "create_clusterer",
    # 采样器
    "CentroidSampler",
    "ClusterSample",
    # 可视化
    "ClusterVisualizer",
    "DimReductionMethod",
    # 分析器
    "ClusterAnalyzer",
    "ClusterResult",
]
