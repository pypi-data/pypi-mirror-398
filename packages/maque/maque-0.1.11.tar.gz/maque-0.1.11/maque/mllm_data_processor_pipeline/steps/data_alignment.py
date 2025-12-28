"""
第2步：数据对齐步骤
对齐为所需格式，主要是图像列 将多个图像处理为多个字符串地址的拼接
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Union
from ..core import PipelineStep, StepResult, PipelineConfig
from maque.performance import MeasureTime


class DataAlignmentStep(PipelineStep):
    """数据对齐步骤"""
    
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "image_separator": {
                "type": "string",
                "default": "|",
                "description": "多个图像路径的分隔符"
            },
            "text_separator": {
                "type": "string", 
                "default": "\\n",
                "description": "多个文本的分隔符"
            },
            "output_image_column": {
                "type": "string",
                "default": "images",
                "description": "合并后的图像列名"
            },
            "output_text_column": {
                "type": "string",
                "default": "text", 
                "description": "合并后的文本列名"
            },
            "output_harmful_image_column": {
                "type": "string",
                "default": "harmful_images",
                "description": "合并后的有害图像列名"
            },
            "output_harmful_text_column": {
                "type": "string",
                "default": "harmful_text",
                "description": "合并后的有害文本列名"
            },
            "normalize_paths": {
                "type": "boolean",
                "default": True,
                "description": "是否标准化路径格式"
            },
            "check_image_exists": {
                "type": "boolean",
                "default": True,
                "description": "是否检查图像文件是否存在"
            }
        }
    }
    
    def __init__(self, name: str = "data_alignment", config: Dict[str, Any] = None):
        super().__init__(name, config)
    
    async def execute(self, data: pd.DataFrame, config: PipelineConfig) -> StepResult:
        """执行数据对齐"""
        with MeasureTime(f"步骤 {self.name}"):
            try:
                step_config = self.get_step_config(config)
                data_copy = data.copy()
                
                # 对齐图像列
                aligned_images = await self._align_image_columns(
                    data_copy, config, step_config
                )
                
                # 对齐文本列
                aligned_text = await self._align_text_columns(
                    data_copy, config, step_config
                )
                
                # 对齐有害内容列
                aligned_harmful_images = await self._align_harmful_image_columns(
                    data_copy, config, step_config
                )
                aligned_harmful_text = await self._align_harmful_text_columns(
                    data_copy, config, step_config
                )
                
                # 添加对齐后的列到数据中
                output_image_col = step_config.get("output_image_column", "images")
                output_text_col = step_config.get("output_text_column", "text")
                output_harmful_image_col = step_config.get("output_harmful_image_column", "harmful_images")
                output_harmful_text_col = step_config.get("output_harmful_text_column", "harmful_text")
                
                data_copy[output_image_col] = aligned_images
                data_copy[output_text_col] = aligned_text
                data_copy[output_harmful_image_col] = aligned_harmful_images
                data_copy[output_harmful_text_col] = aligned_harmful_text
                
                # 更新处理状态
                data_copy['__processing_status'] = 'aligned'
                data_copy['__aligned_at'] = pd.Timestamp.now()
                
                # 统计信息
                valid_images = sum(1 for img in aligned_images if img and img.strip())
                valid_texts = sum(1 for txt in aligned_text if txt and txt.strip())
                
                metadata = {
                    "total_rows": len(data_copy),
                    "valid_images": valid_images,
                    "valid_texts": valid_texts,
                    "image_columns_merged": config.image_columns,
                    "text_columns_merged": config.text_columns,
                    "harmful_image_columns_merged": config.harmful_image_columns,
                    "harmful_text_columns_merged": config.harmful_text_columns,
                    "output_columns": {
                        "images": output_image_col,
                        "text": output_text_col,
                        "harmful_images": output_harmful_image_col,
                        "harmful_text": output_harmful_text_col
                    }
                }
                
                self.logger.info(f"数据对齐完成，有效图像: {valid_images}, 有效文本: {valid_texts}")
                
                return StepResult(
                    step_name=self.name,
                    success=True,
                    data=data_copy,
                    metadata=metadata
                )
                
            except Exception as e:
                self.logger.error(f"数据对齐失败: {e}")
                return StepResult(
                    step_name=self.name,
                    success=False,
                    data=data,
                    metadata={},
                    error=str(e)
                )
    
    async def _align_image_columns(self, data: pd.DataFrame, config: PipelineConfig, step_config: Dict[str, Any]) -> List[str]:
        """对齐图像列"""
        image_separator = step_config.get("image_separator", "|")
        normalize_paths = step_config.get("normalize_paths", True)
        check_exists = step_config.get("check_image_exists", True)
        
        aligned_images = []
        
        for idx, row in data.iterrows():
            image_paths = []
            
            # 收集所有图像列的路径
            for col in config.image_columns:
                if col in data.columns:
                    value = row[col]
                    if pd.notna(value) and str(value).strip():
                        paths = self._parse_image_paths(str(value), image_separator)
                        image_paths.extend(paths)
            
            # 处理路径
            processed_paths = []
            for path in image_paths:
                if normalize_paths:
                    path = self._normalize_path(path)
                
                if check_exists and not self._check_file_exists(path):
                    self.logger.warning(f"图像文件不存在: {path}")
                    continue
                
                processed_paths.append(path)
            
            # 合并为字符串
            aligned_images.append(image_separator.join(processed_paths))
        
        return aligned_images
    
    async def _align_text_columns(self, data: pd.DataFrame, config: PipelineConfig, step_config: Dict[str, Any]) -> List[str]:
        """对齐文本列"""
        text_separator = step_config.get("text_separator", "\\n").replace("\\n", "\n")
        
        aligned_texts = []
        
        for idx, row in data.iterrows():
            text_parts = []
            
            # 收集所有文本列的内容
            for col in config.text_columns:
                if col in data.columns:
                    value = row[col]
                    if pd.notna(value) and str(value).strip():
                        text_parts.append(str(value).strip())
            
            # 合并为字符串
            aligned_texts.append(text_separator.join(text_parts))
        
        return aligned_texts
    
    async def _align_harmful_image_columns(self, data: pd.DataFrame, config: PipelineConfig, step_config: Dict[str, Any]) -> List[str]:
        """对齐有害图像列"""
        image_separator = step_config.get("image_separator", "|")
        
        aligned_harmful_images = []
        
        for idx, row in data.iterrows():
            harmful_flags = []
            
            # 收集所有有害图像列的标记
            for col in config.harmful_image_columns:
                if col in data.columns:
                    value = row[col]
                    if pd.notna(value):
                        harmful_flags.append(str(value))
            
            # 合并为字符串
            aligned_harmful_images.append(image_separator.join(harmful_flags))
        
        return aligned_harmful_images
    
    async def _align_harmful_text_columns(self, data: pd.DataFrame, config: PipelineConfig, step_config: Dict[str, Any]) -> List[str]:
        """对齐有害文本列"""
        text_separator = step_config.get("text_separator", "\\n").replace("\\n", "\n")
        
        aligned_harmful_texts = []
        
        for idx, row in data.iterrows():
            harmful_flags = []
            
            # 收集所有有害文本列的标记
            for col in config.harmful_text_columns:
                if col in data.columns:
                    value = row[col]
                    if pd.notna(value):
                        harmful_flags.append(str(value))
            
            # 合并为字符串
            aligned_harmful_texts.append(text_separator.join(harmful_flags))
        
        return aligned_harmful_texts
    
    def _parse_image_paths(self, value: str, separator: str) -> List[str]:
        """解析图像路径字符串"""
        if not value or not value.strip():
            return []
        
        # 如果已经包含分隔符，按分隔符分割
        if separator in value:
            paths = value.split(separator)
        else:
            paths = [value]
        
        return [path.strip() for path in paths if path.strip()]
    
    def _normalize_path(self, path: str) -> str:
        """标准化路径格式"""
        # 转换路径分隔符
        normalized = str(Path(path))
        return normalized
    
    def _check_file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        try:
            return Path(path).exists()
        except Exception:
            return False