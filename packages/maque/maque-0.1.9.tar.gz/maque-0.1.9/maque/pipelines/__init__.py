#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pipeline 模块 - 提供端到端的便利流水线

这些流水线是可选的便利层，封装常见的工作流模式。
用户仍可以使用底层 API (embedding, retriever, clustering) 进行完全自定义。
"""

from .clustering import ClusteringPipeline

__all__ = [
    "ClusteringPipeline",
]
