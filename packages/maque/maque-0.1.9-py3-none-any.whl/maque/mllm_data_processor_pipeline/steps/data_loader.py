"""
第1步：数据加载步骤
读取表格数据，支持csv、excel，处理图像链接、有害图像列、有害文本列
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from ..core import PipelineStep, StepResult, PipelineConfig


class DataLoaderStep(PipelineStep):
    """数据加载步骤"""

    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "image_columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "图像列名称列表",
            },
            "harmful_image_columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "有害图像列名称列表",
            },
            "harmful_text_columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "有害文本列名称列表",
            },
            "text_columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "文本列名称列表",
            },
            "extract_images_from_excel": {
                "type": "boolean",
                "default": True,
                "description": "是否从Excel中提取图像",
            },
            "image_output_dir": {
                "type": "string",
                "default": "extracted_images",
                "description": "提取图像的输出目录",
            },
        },
    }

    def __init__(self, name: str = "data_loader", config: Dict[str, Any] = None):
        super().__init__(name, config)

    async def execute(self, data: pd.DataFrame, config: PipelineConfig) -> StepResult:
        """执行数据加载"""
        try:
            step_config = self.get_step_config(config)

            # 如果是第一步，data可能为空，需要从文件加载
            if data is None or data.empty:
                data = await self._load_from_file(config, step_config)

            # 验证必要的列是否存在
            self._validate_columns(data, step_config)

            # 处理图像列
            if (
                step_config.get("extract_images_from_excel", True)
                and config.input_type == "excel"
            ):
                data = await self._extract_images_from_excel(data, config, step_config)

            # 添加元数据列
            data = self._add_metadata_columns(data, step_config)

            metadata = {
                "total_rows": len(data),
                "columns": list(data.columns),
                "image_columns": step_config.get("image_columns", []),
                "harmful_image_columns": step_config.get("harmful_image_columns", []),
                "harmful_text_columns": step_config.get("harmful_text_columns", []),
                "text_columns": step_config.get("text_columns", []),
            }

            self.logger.info(f"数据加载完成，共{len(data)}行，{len(data.columns)}列")

            return StepResult(
                step_name=self.name, success=True, data=data, metadata=metadata
            )

        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            return StepResult(
                step_name=self.name, success=False, data=data, metadata={}, error=str(e)
            )

    async def _load_from_file(
        self, config: PipelineConfig, step_config: Dict[str, Any]
    ) -> pd.DataFrame:
        """从文件加载数据"""
        if config.input_type == "csv":
            data = pd.read_csv(config.input_file, encoding="utf-8")
        elif config.input_type == "excel":
            if (
                step_config.get("extract_images_from_excel", True)
                and config.image_columns
            ):
                # 使用maque的excel_helper提取图像
                from maque.utils.excel_helper import extract_excel_with_images

                image_output_dir = Path(config.output_dir) / step_config.get(
                    "image_output_dir", "extracted_images"
                )

                data = extract_excel_with_images(
                    excel_path=config.input_file,
                    image_column_names=config.image_columns,
                    sheet_name=config.sheet_name,
                    image_output_dir=str(image_output_dir),
                    use_hash_filename=True,
                    use_absolute_path=False,
                )
            else:
                data = pd.read_excel(config.input_file, sheet_name=config.sheet_name)
        else:
            raise ValueError(f"不支持的输入类型: {config.input_type}")

        return data

    def _validate_columns(self, data: pd.DataFrame, step_config: Dict[str, Any]):
        """验证列是否存在"""
        all_columns = set(data.columns)

        # 检查必需的列
        required_columns = []
        required_columns.extend(step_config.get("image_columns", []))
        required_columns.extend(step_config.get("text_columns", []))

        missing_columns = [col for col in required_columns if col not in all_columns]
        if missing_columns:
            raise ValueError(f"缺少必需的列: {missing_columns}")

        # 检查可选的列（有害内容列可能不存在）
        optional_columns = []
        optional_columns.extend(step_config.get("harmful_image_columns", []))
        optional_columns.extend(step_config.get("harmful_text_columns", []))

        missing_optional = [col for col in optional_columns if col not in all_columns]
        if missing_optional:
            self.logger.warning(f"可选列不存在: {missing_optional}")

    async def _extract_images_from_excel(
        self, data: pd.DataFrame, config: PipelineConfig, step_config: Dict[str, Any]
    ) -> pd.DataFrame:
        """从Excel中提取图像（如果还没有提取的话）"""
        # 如果已经在_load_from_file中处理过了，这里可能不需要再处理
        return data

    def _add_metadata_columns(
        self, data: pd.DataFrame, step_config: Dict[str, Any]
    ) -> pd.DataFrame:
        """添加元数据列"""
        # 添加行ID
        data["__row_id"] = range(len(data))

        # 添加处理状态列
        data["__processing_status"] = "loaded"

        # 添加时间戳
        data["__loaded_at"] = pd.Timestamp.now()

        return data
