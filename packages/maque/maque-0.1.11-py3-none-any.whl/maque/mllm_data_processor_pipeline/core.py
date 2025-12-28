"""
Pipeline核心架构实现
"""

import json
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
import pandas as pd
from datetime import datetime

from loguru import logger
from maque.performance import MeasureTime


@dataclass
class PipelineConfig:
    """Pipeline配置类"""

    # 输入配置
    input_file: str = ""
    input_type: str = "csv"  # csv, excel
    sheet_name: Optional[str] = None

    # 列映射配置
    image_columns: List[str] = None  # 图像列名称
    harmful_image_columns: List[str] = None  # 有害图像列
    harmful_text_columns: List[str] = None  # 有害文本列
    text_columns: List[str] = None  # 文本列

    # 输出配置
    output_dir: str = "./output"
    checkpoint_dir: str = "./checkpoints"

    # 步骤配置
    steps_config: Dict[str, Dict[str, Any]] = None

    # MLLM配置
    mllm_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.image_columns is None:
            self.image_columns = []
        if self.harmful_image_columns is None:
            self.harmful_image_columns = []
        if self.harmful_text_columns is None:
            self.harmful_text_columns = []
        if self.text_columns is None:
            self.text_columns = []
        if self.steps_config is None:
            self.steps_config = {}
        if self.mllm_config is None:
            self.mllm_config = {}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        return cls(**data)

    def save(self, filepath: str):
        """保存配置到文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "PipelineConfig":
        """从文件加载配置"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class StepResult:
    """步骤执行结果"""

    step_name: str
    success: bool
    data: pd.DataFrame
    metadata: Dict[str, Any]
    error: Optional[str] = None
    execution_time: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "step_name": self.step_name,
            "success": self.success,
            "metadata": self.metadata,
            "error": self.error,
            "execution_time": self.execution_time,
            "data_shape": self.data.shape if self.data is not None else None,
            "timestamp": datetime.now().isoformat(),
        }
        return result

    def save_checkpoint(self, checkpoint_dir: str):
        """保存检查点"""
        checkpoint_path = Path(checkpoint_dir)
        checkpoint_path.mkdir(parents=True, exist_ok=True)

        # 保存数据
        data_file = checkpoint_path / f"{self.step_name}_data.csv"
        if self.data is not None:
            self.data.to_csv(data_file, index=False, encoding="utf-8")

        # 保存元数据
        meta_file = checkpoint_path / f"{self.step_name}_metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_checkpoint(
        cls, step_name: str, checkpoint_dir: str
    ) -> Optional["StepResult"]:
        """加载检查点"""
        checkpoint_path = Path(checkpoint_dir)
        data_file = checkpoint_path / f"{step_name}_data.csv"
        meta_file = checkpoint_path / f"{step_name}_metadata.json"

        if not (data_file.exists() and meta_file.exists()):
            return None

        # 加载数据
        data = pd.read_csv(data_file, encoding="utf-8")

        # 加载元数据
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata_info = json.load(f)

        return cls(
            step_name=metadata_info["step_name"],
            success=metadata_info["success"],
            data=data,
            metadata=metadata_info["metadata"],
            error=metadata_info.get("error"),
            execution_time=metadata_info.get("execution_time"),
        )


class PipelineStep(ABC):
    """Pipeline步骤基类"""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = logger

    @abstractmethod
    async def execute(self, data: pd.DataFrame, config: PipelineConfig) -> StepResult:
        """执行步骤"""
        pass

    def validate_input(self, data: pd.DataFrame, config: PipelineConfig) -> bool:
        """验证输入数据"""
        return data is not None and not data.empty

    def get_step_config(self, config: PipelineConfig) -> Dict[str, Any]:
        """获取步骤特定配置"""
        return config.steps_config.get(self.name, {})


class DataProcessorPipeline:
    """数据处理Pipeline主类"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.steps: List[PipelineStep] = []
        self.results: List[StepResult] = []
        self.logger = logger
        self.status_callback: Optional[Callable] = None

        # 创建输出目录
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        Path(config.checkpoint_dir).mkdir(parents=True, exist_ok=True)

    def add_step(self, step: PipelineStep) -> "DataProcessorPipeline":
        """添加处理步骤"""
        self.steps.append(step)
        return self

    def set_status_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """设置状态回调函数"""
        self.status_callback = callback

    def _notify_status(self, status: str, data: Dict[str, Any] = None):
        """通知状态更新"""
        if self.status_callback:
            self.status_callback(status, data or {})

    async def load_data(self) -> pd.DataFrame:
        """加载输入数据"""
        self._notify_status("loading_data", {"file": self.config.input_file})

        if self.config.input_type == "csv":
            data = pd.read_csv(self.config.input_file, encoding="utf-8")
        elif self.config.input_type == "excel":
            # 如果有图像列，使用maque的excel_helper
            if self.config.image_columns:
                from maque.utils.excel_helper import extract_excel_with_images

                data = extract_excel_with_images(
                    excel_path=self.config.input_file,
                    image_column_names=self.config.image_columns,
                    sheet_name=self.config.sheet_name,
                    image_output_dir=Path(self.config.output_dir) / "images",
                )
            else:
                data = pd.read_excel(
                    self.config.input_file, sheet_name=self.config.sheet_name
                )
        else:
            raise ValueError(f"不支持的输入类型: {self.config.input_type}")

        self.logger.info(f"加载数据完成，共{len(data)}行")
        return data

    async def run(self, resume_from: Optional[str] = None) -> List[StepResult]:
        """运行Pipeline"""
        with MeasureTime("Pipeline执行"):
            self._notify_status("starting", {"total_steps": len(self.steps)})

            # 加载数据
            current_data = await self.load_data()

            # 确定开始步骤
            start_idx = 0
            if resume_from:
                # 尝试从检查点恢复
                checkpoint_result = StepResult.load_checkpoint(
                    resume_from, self.config.checkpoint_dir
                )
                if checkpoint_result:
                    current_data = checkpoint_result.data
                    start_idx = (
                        next(
                            (
                                i
                                for i, step in enumerate(self.steps)
                                if step.name == resume_from
                            ),
                            0,
                        )
                        + 1
                    )
                    self.results.append(checkpoint_result)
                    self.logger.info(f"从检查点恢复: {resume_from}")

            # 执行步骤
            for i, step in enumerate(self.steps[start_idx:], start_idx):
                self._notify_status(
                    "executing_step",
                    {
                        "step_name": step.name,
                        "step_index": i,
                        "total_steps": len(self.steps),
                    },
                )

                try:
                    self.logger.info(f"执行步骤 {i + 1}/{len(self.steps)}: {step.name}")

                    # 验证输入
                    if not step.validate_input(current_data, self.config):
                        raise ValueError(f"步骤 {step.name} 输入验证失败")

                    # 执行步骤
                    result = await step.execute(current_data, self.config)

                    # 保存检查点
                    result.save_checkpoint(self.config.checkpoint_dir)

                    # 更新当前数据
                    current_data = result.data
                    self.results.append(result)

                    self.logger.info(f"步骤 {step.name} 执行完成")

                except Exception as e:
                    error_msg = f"步骤 {step.name} 执行失败: {str(e)}"
                    self.logger.error(error_msg)

                    # 创建失败结果
                    failed_result = StepResult(
                        step_name=step.name,
                        success=False,
                        data=current_data,
                        metadata={},
                        error=error_msg,
                    )
                    failed_result.save_checkpoint(self.config.checkpoint_dir)
                    self.results.append(failed_result)

                    self._notify_status(
                        "step_failed", {"step_name": step.name, "error": error_msg}
                    )

                    raise

            self._notify_status("completed", {"total_results": len(self.results)})
            self.logger.info("Pipeline执行完成")

            return self.results

    def get_status(self) -> Dict[str, Any]:
        """获取Pipeline状态"""
        return {
            "total_steps": len(self.steps),
            "completed_steps": len([r for r in self.results if r.success]),
            "failed_steps": len([r for r in self.results if not r.success]),
            "current_step": len(self.results),
            "steps": [
                {"name": step.name, "config": step.config} for step in self.steps
            ],
            "results": [result.to_dict() for result in self.results],
        }

    def save_final_results(self):
        """保存最终结果"""
        if not self.results:
            return

        final_result = self.results[-1]
        if final_result.success and final_result.data is not None:
            output_file = Path(self.config.output_dir) / "final_output.csv"
            final_result.data.to_csv(output_file, index=False, encoding="utf-8")
            self.logger.info(f"最终结果已保存至: {output_file}")

        # 保存执行摘要
        summary = {
            "config": self.config.to_dict(),
            "execution_summary": self.get_status(),
            "timestamp": datetime.now().isoformat(),
        }

        summary_file = Path(self.config.output_dir) / "execution_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
