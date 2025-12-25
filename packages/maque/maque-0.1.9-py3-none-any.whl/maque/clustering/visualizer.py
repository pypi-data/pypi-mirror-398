# -*- coding: utf-8 -*-
"""
聚类可视化工具

支持多种降维算法：UMAP、t-SNE、PCA
"""

from pathlib import Path
from typing import Literal, Optional, Tuple, Union

import numpy as np
from loguru import logger

# 设置 matplotlib 后端（服务器环境兼容）
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.manifold import TSNE
from sklearn.decomposition import PCA

DimReductionMethod = Literal["umap", "tsne", "pca"]


class ClusterVisualizer:
    """
    聚类结果可视化器

    支持多种降维算法：
    - UMAP: 速度快，保持全局结构（推荐）
    - t-SNE: 保持局部结构，适合小数据集
    - PCA: 最快，线性降维

    Example:
        >>> visualizer = ClusterVisualizer(method="umap")
        >>> visualizer.plot(embeddings, labels, "clusters.png")
    """

    def __init__(
        self,
        method: DimReductionMethod = "umap",
        figsize: Tuple[int, int] = (12, 8),
        dpi: int = 150,
        random_state: int = 42,
        # UMAP 参数
        n_neighbors: int = 15,
        min_dist: float = 0.1,
        # t-SNE 参数
        perplexity: int = 30,
    ):
        """
        Args:
            method: 降维方法 ("umap", "tsne", "pca")
            figsize: 图片大小
            dpi: 图片分辨率
            random_state: 随机种子
            n_neighbors: UMAP 邻居数
            min_dist: UMAP 最小距离
            perplexity: t-SNE perplexity 参数
        """
        self.method = method
        self.figsize = figsize
        self.dpi = dpi
        self.random_state = random_state
        self.n_neighbors = n_neighbors
        self.min_dist = min_dist
        self.perplexity = perplexity

    def reduce_dimensions(self, embeddings: np.ndarray) -> np.ndarray:
        """
        将高维向量降维到 2D

        Args:
            embeddings: 向量矩阵 (n_samples, n_features)

        Returns:
            2D 坐标矩阵 (n_samples, 2)
        """
        if self.method == "umap":
            return self._reduce_umap(embeddings)

        elif self.method == "tsne":
            return self._reduce_tsne(embeddings)

        elif self.method == "pca":
            return self._reduce_pca(embeddings)

        else:
            raise ValueError(f"未知降维方法: {self.method}")

    def _reduce_umap(self, embeddings: np.ndarray) -> np.ndarray:
        """UMAP 降维"""
        try:
            import umap
        except ImportError:
            raise ImportError("UMAP 需要: pip install umap-learn")

        logger.info(f"使用 UMAP 降维 (n_neighbors={self.n_neighbors}, min_dist={self.min_dist})...")
        reducer = umap.UMAP(
            n_components=2,
            n_neighbors=min(self.n_neighbors, len(embeddings) - 1),
            min_dist=self.min_dist,
            random_state=self.random_state,
            metric='cosine',
        )
        return reducer.fit_transform(embeddings)

    def _reduce_tsne(self, embeddings: np.ndarray) -> np.ndarray:
        """t-SNE 降维"""
        logger.info(f"使用 t-SNE 降维 (perplexity={self.perplexity})...")
        tsne = TSNE(
            n_components=2,
            random_state=self.random_state,
            perplexity=min(self.perplexity, len(embeddings) - 1),
        )
        return tsne.fit_transform(embeddings)

    def _reduce_pca(self, embeddings: np.ndarray) -> np.ndarray:
        """PCA 降维"""
        logger.info("使用 PCA 降维...")
        pca = PCA(n_components=2, random_state=self.random_state)
        return pca.fit_transform(embeddings)

    def plot(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray,
        output_path: Union[str, Path],
        title: Optional[str] = None,
        embeddings_2d: Optional[np.ndarray] = None,
    ) -> bool:
        """
        绘制聚类可视化图

        Args:
            embeddings: 向量矩阵（如果提供 embeddings_2d 则忽略）
            labels: 聚类标签
            output_path: 输出文件路径
            title: 图片标题
            embeddings_2d: 预计算的 2D 坐标（可选）

        Returns:
            bool: 是否成功生成图片
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 降维
        if embeddings_2d is None:
            embeddings_2d = self.reduce_dimensions(embeddings)

        # 绘图
        logger.info("生成可视化图...")
        plt.figure(figsize=self.figsize)

        unique_labels = sorted(set(labels))
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)

        # 根据簇数量选择颜色方案
        if n_clusters <= 20:
            colors = plt.cm.tab20(np.linspace(0, 1, 20))
        else:
            # 簇数 > 20 时使用连续色图
            colors = plt.cm.gist_ncar(np.linspace(0.05, 0.95, n_clusters))

        color_idx = 0
        for label in unique_labels:
            mask = labels == label
            if label == -1:
                plt.scatter(
                    embeddings_2d[mask, 0],
                    embeddings_2d[mask, 1],
                    c='gray',
                    alpha=0.3,
                    s=10,
                    label='Noise'
                )
            else:
                if n_clusters <= 20:
                    color = colors[label % 20]
                else:
                    color = colors[color_idx]
                    color_idx += 1
                plt.scatter(
                    embeddings_2d[mask, 0],
                    embeddings_2d[mask, 1],
                    c=[color],
                    alpha=0.6,
                    s=15,
                    label=f'Cluster {label}'
                )

        if n_clusters <= 10:
            plt.legend(loc='best', fontsize=8)

        method_name = self.method.upper()
        plt.title(title or f'Cluster Visualization ({method_name}, n={n_clusters})')
        plt.xlabel(f'{method_name} dim 1')
        plt.ylabel(f'{method_name} dim 2')
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.dpi)
        plt.close()

        logger.info(f"可视化图片保存到: {output_path}")
        return True
