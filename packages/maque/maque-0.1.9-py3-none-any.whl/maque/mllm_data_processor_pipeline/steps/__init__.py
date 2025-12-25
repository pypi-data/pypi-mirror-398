"""
Pipeline处理步骤实现
"""

from .data_loader import DataLoaderStep
from .data_alignment import DataAlignmentStep
from .data_validation import DataValidationStep
from .mllm_annotation import MllmAnnotationStep
from .mllm_refinement import MllmRefinementStep
from .format_conversion import FormatConversionStep
from .result_validation import ResultValidationStep

# 所有可用的步骤类
ALL_STEPS = [
    DataLoaderStep,
    DataAlignmentStep,
    DataValidationStep,
    MllmAnnotationStep,
    MllmRefinementStep,
    FormatConversionStep,
    ResultValidationStep
]

def get_all_steps():
    """获取所有可用的步骤类"""
    return ALL_STEPS

def create_step_from_config(step_config: dict):
    """根据配置创建步骤实例"""
    step_name = step_config.get("name")
    step_type = step_config.get("type")
    step_params = step_config.get("params", {})
    
    # 根据类型查找对应的步骤类
    step_class = None
    for cls in ALL_STEPS:
        if cls.__name__ == step_type:
            step_class = cls
            break
    
    if not step_class:
        raise ValueError(f"未知的步骤类型: {step_type}")
    
    return step_class(name=step_name, config=step_params)

__all__ = [
    "DataLoaderStep",
    "DataAlignmentStep", 
    "DataValidationStep",
    "MllmAnnotationStep",
    "MllmRefinementStep",
    "FormatConversionStep",
    "ResultValidationStep",
    "get_all_steps",
    "create_step_from_config"
]