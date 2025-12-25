"""
第3步：第一轮校验与粗筛（可选）
对数据进行基本校验和粗筛，过滤明显不符合要求的数据
"""

import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from ..core import PipelineStep, StepResult, PipelineConfig
from maque.performance import MeasureTime


class DataValidationStep(PipelineStep):
    """数据校验步骤"""
    
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "skip_validation": {
                "type": "boolean",
                "default": False,
                "description": "是否跳过验证步骤"
            },
            "min_text_length": {
                "type": "integer",
                "default": 10,
                "description": "最小文本长度"
            },
            "max_text_length": {
                "type": "integer", 
                "default": 10000,
                "description": "最大文本长度"
            },
            "require_images": {
                "type": "boolean",
                "default": False,
                "description": "是否要求必须有图像"
            },
            "require_text": {
                "type": "boolean",
                "default": True,
                "description": "是否要求必须有文本"
            },
            "image_extensions": {
                "type": "array",
                "items": {"type": "string"},
                "default": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
                "description": "允许的图像文件扩展名"
            },
            "text_filters": {
                "type": "object",
                "properties": {
                    "forbidden_words": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "禁用词列表"
                    },
                    "required_words": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "必须包含的词列表"
                    },
                    "regex_patterns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "正则表达式模式列表"
                    }
                },
                "default": {}
            },
            "quality_thresholds": {
                "type": "object",
                "properties": {
                    "min_image_size": {
                        "type": "integer",
                        "default": 1024,
                        "description": "最小图像文件大小（字节）"
                    },
                    "max_image_size": {
                        "type": "integer",
                        "default": 10485760,
                        "description": "最大图像文件大小（字节）"
                    }
                },
                "default": {}
            },
            "remove_invalid": {
                "type": "boolean",
                "default": True,
                "description": "是否移除无效数据，否则只标记"
            }
        }
    }
    
    def __init__(self, name: str = "data_validation", config: Dict[str, Any] = None):
        super().__init__(name, config)
    
    async def execute(self, data: pd.DataFrame, config: PipelineConfig, step_config: Dict[str, Any]) -> StepResult:
        """执行数据校验"""
        with MeasureTime(f"步骤 {self.name}"):
            try:
                step_config = self.get_step_config(config)
                
                # 如果跳过验证
                if step_config.get("skip_validation", False):
                    self.logger.info("跳过数据验证步骤")
                    return StepResult(
                        step_name=self.name,
                        success=True,
                        data=data,
                        metadata={"skipped": True}
                    )
                
                data_copy = data.copy()
                
                # 添加验证结果列
                data_copy['__validation_passed'] = True
                data_copy['__validation_errors'] = ''
                
                # 执行各种验证
                await self._validate_text_content(data_copy, step_config)
                await self._validate_image_content(data_copy, step_config)
                await self._validate_data_quality(data_copy, step_config)
                
                # 统计验证结果
                total_rows = len(data_copy)
                valid_rows = len(data_copy[data_copy['__validation_passed']])
                invalid_rows = total_rows - valid_rows
                
                # 是否移除无效数据
                if step_config.get("remove_invalid", True) and invalid_rows > 0:
                    data_copy = data_copy[data_copy['__validation_passed']].copy()
                    self.logger.info(f"移除了 {invalid_rows} 行无效数据")
                
                # 更新处理状态
                data_copy['__processing_status'] = 'validated'
                data_copy['__validated_at'] = pd.Timestamp.now()
                
                metadata = {
                    "total_rows_before": total_rows,
                    "valid_rows": valid_rows,
                    "invalid_rows": invalid_rows,
                    "validation_rate": valid_rows / total_rows if total_rows > 0 else 0,
                    "removed_invalid": step_config.get("remove_invalid", True),
                    "final_rows": len(data_copy)
                }
                
                self.logger.info(f"数据验证完成，有效率: {metadata['validation_rate']:.2%}")
                
                return StepResult(
                    step_name=self.name,
                    success=True,
                    data=data_copy,
                    metadata=metadata
                )
                
            except Exception as e:
                self.logger.error(f"数据验证失败: {e}")
                return StepResult(
                    step_name=self.name,
                    success=False,
                    data=data,
                    metadata={},
                    error=str(e)
                )
    
    async def _validate_text_content(self, data: pd.DataFrame, step_config: Dict[str, Any]):
        """验证文本内容"""
        min_length = step_config.get("min_text_length", 10)
        max_length = step_config.get("max_text_length", 10000)
        require_text = step_config.get("require_text", True)
        text_filters = step_config.get("text_filters", {})
        
        text_col = step_config.get("output_text_column", "text")
        if text_col not in data.columns:
            return
        
        for idx, row in data.iterrows():
            errors = []
            text_content = str(row[text_col]) if pd.notna(row[text_col]) else ""
            
            # 检查是否需要文本
            if require_text and not text_content.strip():
                errors.append("缺少必需的文本内容")
            
            # 检查文本长度
            text_length = len(text_content.strip())
            if text_content.strip() and (text_length < min_length or text_length > max_length):
                errors.append(f"文本长度不符合要求 ({text_length}), 要求 {min_length}-{max_length}")
            
            # 检查禁用词
            forbidden_words = text_filters.get("forbidden_words", [])
            for word in forbidden_words:
                if word.lower() in text_content.lower():
                    errors.append(f"包含禁用词: {word}")
            
            # 检查必需词
            required_words = text_filters.get("required_words", [])
            for word in required_words:
                if word.lower() not in text_content.lower():
                    errors.append(f"缺少必需词: {word}")
            
            # 检查正则表达式
            regex_patterns = text_filters.get("regex_patterns", [])
            for pattern in regex_patterns:
                try:
                    if not re.search(pattern, text_content, re.IGNORECASE):
                        errors.append(f"不符合模式: {pattern}")
                except re.error:
                    self.logger.warning(f"无效的正则表达式: {pattern}")
            
            # 更新验证结果
            if errors:
                data.at[idx, '__validation_passed'] = False
                data.at[idx, '__validation_errors'] = "; ".join(errors)
    
    async def _validate_image_content(self, data: pd.DataFrame, step_config: Dict[str, Any]):
        """验证图像内容"""
        require_images = step_config.get("require_images", False)
        image_extensions = step_config.get("image_extensions", [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"])
        quality_thresholds = step_config.get("quality_thresholds", {})
        
        image_col = step_config.get("output_image_column", "images")
        if image_col not in data.columns:
            return
        
        separator = step_config.get("image_separator", "|")
        
        for idx, row in data.iterrows():
            errors = []
            image_paths_str = str(row[image_col]) if pd.notna(row[image_col]) else ""
            image_paths = [p.strip() for p in image_paths_str.split(separator) if p.strip()]
            
            # 检查是否需要图像
            if require_images and not image_paths:
                errors.append("缺少必需的图像")
            
            # 验证每个图像文件
            for image_path in image_paths:
                path_errors = await self._validate_single_image(image_path, image_extensions, quality_thresholds)
                errors.extend(path_errors)
            
            # 更新验证结果
            if errors:
                current_errors = data.at[idx, '__validation_errors']
                if current_errors:
                    current_errors += "; " + "; ".join(errors)
                else:
                    current_errors = "; ".join(errors)
                data.at[idx, '__validation_errors'] = current_errors
                data.at[idx, '__validation_passed'] = False
    
    async def _validate_single_image(self, image_path: str, allowed_extensions: List[str], quality_thresholds: Dict[str, Any]) -> List[str]:
        """验证单个图像文件"""
        errors = []
        
        try:
            path_obj = Path(image_path)
            
            # 检查文件是否存在
            if not path_obj.exists():
                errors.append(f"图像文件不存在: {image_path}")
                return errors
            
            # 检查文件扩展名
            if allowed_extensions and path_obj.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                errors.append(f"不支持的图像格式: {path_obj.suffix}")
            
            # 检查文件大小
            file_size = path_obj.stat().st_size
            min_size = quality_thresholds.get("min_image_size", 0)
            max_size = quality_thresholds.get("max_image_size", float('inf'))
            
            if file_size < min_size:
                errors.append(f"图像文件太小: {file_size} < {min_size}")
            if file_size > max_size:
                errors.append(f"图像文件太大: {file_size} > {max_size}")
                
        except Exception as e:
            errors.append(f"验证图像时出错: {str(e)}")
        
        return errors
    
    async def _validate_data_quality(self, data: pd.DataFrame, step_config: Dict[str, Any]):
        """验证数据质量"""
        # 检查重复数据
        text_col = step_config.get("output_text_column", "text")
        image_col = step_config.get("output_image_column", "images")
        
        if text_col in data.columns and image_col in data.columns:
            # 基于文本和图像内容查找重复
            content_cols = [text_col, image_col]
            duplicate_mask = data.duplicated(subset=content_cols, keep='first')
            
            for idx in data[duplicate_mask].index:
                current_errors = data.at[idx, '__validation_errors']
                error_msg = "发现重复内容"
                if current_errors:
                    current_errors += "; " + error_msg
                else:
                    current_errors = error_msg
                data.at[idx, '__validation_errors'] = current_errors
                data.at[idx, '__validation_passed'] = False