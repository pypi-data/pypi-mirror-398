"""
多模态大模型训练数据处理pipeline

一个灵活的、模块化的数据处理流水线，支持Web界面交互和断点续传。
"""

from .core import DataProcessorPipeline, PipelineStep, PipelineConfig
from .steps import *
from .web_app import WebApp

__version__ = "0.1.0"
__all__ = [
    "DataProcessorPipeline", 
    "PipelineStep", 
    "PipelineConfig",
    "WebApp"
]