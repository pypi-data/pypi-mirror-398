"""
第6步：格式转换步骤
整理为训练格式，支持多种输出格式
"""

import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..core import PipelineStep, StepResult, PipelineConfig
from maque.performance import MeasureTime


class FormatConversionStep(PipelineStep):
    """格式转换步骤"""
    
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "output_formats": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["jsonl", "csv", "json", "parquet", "hf_dataset"]
                },
                "default": ["jsonl", "csv"],
                "description": "输出格式列表"
            },
            "format_configs": {
                "type": "object",
                "properties": {
                    "jsonl": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "default": "training_data.jsonl"},
                            "include_metadata": {"type": "boolean", "default": False}
                        }
                    },
                    "csv": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "default": "training_data.csv"},
                            "encoding": {"type": "string", "default": "utf-8"}
                        }
                    },
                    "json": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "default": "training_data.json"},
                            "indent": {"type": "integer", "default": 2}
                        }
                    },
                    "parquet": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "default": "training_data.parquet"}
                        }
                    },
                    "hf_dataset": {
                        "type": "object",
                        "properties": {
                            "dataset_name": {"type": "string", "default": "mllm_training_data"},
                            "split_ratios": {
                                "type": "object",
                                "properties": {
                                    "train": {"type": "number", "default": 0.8},
                                    "validation": {"type": "number", "default": 0.1},
                                    "test": {"type": "number", "default": 0.1}
                                }
                            }
                        }
                    }
                },
                "default": {}
            },
            "field_mapping": {
                "type": "object",
                "properties": {
                    "text_field": {"type": "string", "default": "text"},
                    "images_field": {"type": "string", "default": "images"},
                    "labels_field": {"type": "string", "default": "labels"},
                    "metadata_fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["summary", "tags", "sentiment", "quality"]
                    }
                },
                "default": {}
            },
            "filtering": {
                "type": "object",
                "properties": {
                    "only_successful": {"type": "boolean", "default": True},
                    "quality_threshold": {"type": "number", "default": 0.0},
                    "exclude_columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["__row_id", "__processing_status", "__loaded_at", "__aligned_at", "__validated_at", "__annotated_at", "__refined_at"]
                    }
                },
                "default": {}
            },
            "data_augmentation": {
                "type": "object",
                "properties": {
                    "duplicate_successful": {"type": "boolean", "default": False},
                    "add_negative_samples": {"type": "boolean", "default": False}
                },
                "default": {}
            }
        }
    }
    
    def __init__(self, name: str = "format_conversion", config: Dict[str, Any] = None):
        super().__init__(name, config)
    
    async def execute(self, data: pd.DataFrame, config: PipelineConfig) -> StepResult:
        """执行格式转换"""
        with MeasureTime(f"步骤 {self.name}"):
            try:
                step_config = self.get_step_config(config)
                
                # 过滤和预处理数据
                processed_data = await self._preprocess_data(data, step_config)
                
                # 转换为训练格式
                training_data = await self._convert_to_training_format(processed_data, step_config)
                
                # 输出多种格式
                output_files = await self._export_multiple_formats(training_data, config, step_config)
                
                # 生成统计信息
                stats = await self._generate_statistics(training_data, processed_data)
                
                metadata = {
                    "original_rows": len(data),
                    "processed_rows": len(processed_data),
                    "training_samples": len(training_data),
                    "output_files": output_files,
                    "statistics": stats
                }
                
                self.logger.info(f"格式转换完成，生成 {len(training_data)} 个训练样本")
                
                return StepResult(
                    step_name=self.name,
                    success=True,
                    data=processed_data,  # 返回处理后的数据
                    metadata=metadata
                )
                
            except Exception as e:
                self.logger.error(f"格式转换失败: {e}")
                return StepResult(
                    step_name=self.name,
                    success=False,
                    data=data,
                    metadata={},
                    error=str(e)
                )
    
    async def _preprocess_data(self, data: pd.DataFrame, step_config: Dict[str, Any]) -> pd.DataFrame:
        """预处理数据"""
        data_copy = data.copy()
        filtering = step_config.get("filtering", {})
        
        # 只保留成功处理的数据
        if filtering.get("only_successful", True):
            if '__mllm_annotation_success' in data_copy.columns:
                data_copy = data_copy[data_copy['__mllm_annotation_success'] == True]
                self.logger.info(f"筛选成功标注的数据，剩余 {len(data_copy)} 行")
        
        # 质量阈值过滤
        quality_threshold = filtering.get("quality_threshold", 0.0)
        if quality_threshold > 0:
            # 这里需要根据实际的质量评估逻辑来过滤
            pass
        
        # 移除不需要的列
        exclude_columns = filtering.get("exclude_columns", [])
        columns_to_drop = [col for col in exclude_columns if col in data_copy.columns]
        if columns_to_drop:
            data_copy = data_copy.drop(columns=columns_to_drop)
            self.logger.info(f"移除了 {len(columns_to_drop)} 个元数据列")
        
        return data_copy
    
    async def _convert_to_training_format(self, data: pd.DataFrame, step_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """转换为训练格式"""
        field_mapping = step_config.get("field_mapping", {})
        text_field = field_mapping.get("text_field", "text")
        images_field = field_mapping.get("images_field", "images")
        labels_field = field_mapping.get("labels_field", "labels")
        metadata_fields = field_mapping.get("metadata_fields", ["summary", "tags", "sentiment", "quality"])
        
        training_data = []
        
        for idx, row in data.iterrows():
            sample = {}
            
            # 文本字段
            text_content = str(row.get('text', '')) if pd.notna(row.get('text')) else ""
            sample[text_field] = text_content
            
            # 图像字段
            images_content = str(row.get('images', '')) if pd.notna(row.get('images')) else ""
            if images_content:
                # 分割图像路径
                image_paths = [p.strip() for p in images_content.split('|') if p.strip()]
                sample[images_field] = image_paths
            else:
                sample[images_field] = []
            
            # 标签字段（基于标注结果）
            labels = {}
            
            # 使用精标结果（如果存在），否则使用初标结果
            for field in metadata_fields:
                refined_field = f"refined_{field}"
                original_field = f"mllm_{field}"
                
                if refined_field in data.columns and pd.notna(row.get(refined_field)):
                    labels[field] = str(row[refined_field])
                elif original_field in data.columns and pd.notna(row.get(original_field)):
                    labels[field] = str(row[original_field])
                else:
                    labels[field] = ""
            
            sample[labels_field] = labels
            
            # 添加其他有用的字段
            sample["id"] = f"sample_{idx}"
            sample["source"] = "mllm_pipeline"
            
            # 添加有害内容标记（如果存在）
            if 'harmful_images' in data.columns:
                sample["harmful_images"] = str(row.get('harmful_images', ''))
            if 'harmful_text' in data.columns:
                sample["harmful_text"] = str(row.get('harmful_text', ''))
            
            training_data.append(sample)
        
        return training_data
    
    async def _export_multiple_formats(self, training_data: List[Dict[str, Any]], config: PipelineConfig, step_config: Dict[str, Any]) -> List[str]:
        """导出多种格式"""
        output_formats = step_config.get("output_formats", ["jsonl", "csv"])
        format_configs = step_config.get("format_configs", {})
        output_files = []
        
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for format_type in output_formats:
            try:
                if format_type == "jsonl":
                    file_path = await self._export_jsonl(training_data, output_dir, format_configs.get("jsonl", {}))
                elif format_type == "csv":
                    file_path = await self._export_csv(training_data, output_dir, format_configs.get("csv", {}))
                elif format_type == "json":
                    file_path = await self._export_json(training_data, output_dir, format_configs.get("json", {}))
                elif format_type == "parquet":
                    file_path = await self._export_parquet(training_data, output_dir, format_configs.get("parquet", {}))
                elif format_type == "hf_dataset":
                    file_path = await self._export_hf_dataset(training_data, output_dir, format_configs.get("hf_dataset", {}))
                else:
                    self.logger.warning(f"不支持的输出格式: {format_type}")
                    continue
                
                output_files.append(file_path)
                self.logger.info(f"导出 {format_type} 格式: {file_path}")
                
            except Exception as e:
                self.logger.error(f"导出 {format_type} 格式失败: {e}")
        
        return output_files
    
    async def _export_jsonl(self, training_data: List[Dict[str, Any]], output_dir: Path, config: Dict[str, Any]) -> str:
        """导出JSONL格式"""
        filename = config.get("filename", "training_data.jsonl")
        file_path = output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for sample in training_data:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
        
        return str(file_path)
    
    async def _export_csv(self, training_data: List[Dict[str, Any]], output_dir: Path, config: Dict[str, Any]) -> str:
        """导出CSV格式"""
        filename = config.get("filename", "training_data.csv")
        encoding = config.get("encoding", "utf-8")
        file_path = output_dir / filename
        
        # 将嵌套的字典和列表转换为字符串
        flattened_data = []
        for sample in training_data:
            flat_sample = {}
            for key, value in sample.items():
                if isinstance(value, (dict, list)):
                    flat_sample[key] = json.dumps(value, ensure_ascii=False)
                else:
                    flat_sample[key] = value
            flattened_data.append(flat_sample)
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(file_path, index=False, encoding=encoding)
        
        return str(file_path)
    
    async def _export_json(self, training_data: List[Dict[str, Any]], output_dir: Path, config: Dict[str, Any]) -> str:
        """导出JSON格式"""
        filename = config.get("filename", "training_data.json")
        indent = config.get("indent", 2)
        file_path = output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, ensure_ascii=False, indent=indent)
        
        return str(file_path)
    
    async def _export_parquet(self, training_data: List[Dict[str, Any]], output_dir: Path, config: Dict[str, Any]) -> str:
        """导出Parquet格式"""
        filename = config.get("filename", "training_data.parquet")
        file_path = output_dir / filename
        
        # 将嵌套的字典和列表转换为字符串
        flattened_data = []
        for sample in training_data:
            flat_sample = {}
            for key, value in sample.items():
                if isinstance(value, (dict, list)):
                    flat_sample[key] = json.dumps(value, ensure_ascii=False)
                else:
                    flat_sample[key] = value
            flattened_data.append(flat_sample)
        
        df = pd.DataFrame(flattened_data)
        df.to_parquet(file_path, index=False)
        
        return str(file_path)
    
    async def _export_hf_dataset(self, training_data: List[Dict[str, Any]], output_dir: Path, config: Dict[str, Any]) -> str:
        """导出HuggingFace Dataset格式"""
        try:
            from datasets import Dataset
        except ImportError:
            self.logger.error("需要安装 datasets 库才能导出 HuggingFace 格式")
            raise ImportError("pip install datasets")
        
        dataset_name = config.get("dataset_name", "mllm_training_data")
        split_ratios = config.get("split_ratios", {"train": 0.8, "validation": 0.1, "test": 0.1})
        
        # 创建数据集
        dataset = Dataset.from_list(training_data)
        
        # 分割数据集
        if len(split_ratios) > 1:
            train_ratio = split_ratios.get("train", 0.8)
            val_ratio = split_ratios.get("validation", 0.1)
            
            # 首先分割训练集和测试集
            train_test_split = dataset.train_test_split(test_size=1-train_ratio, seed=42)
            train_dataset = train_test_split["train"]
            temp_dataset = train_test_split["test"]
            
            # 再从剩余数据中分割验证集和测试集
            if val_ratio > 0:
                val_test_ratio = val_ratio / (val_ratio + split_ratios.get("test", 0.1))
                val_test_split = temp_dataset.train_test_split(test_size=1-val_test_ratio, seed=42)
                val_dataset = val_test_split["train"]
                test_dataset = val_test_split["test"]
            else:
                val_dataset = None
                test_dataset = temp_dataset
            
            # 保存分割后的数据集
            dataset_dir = output_dir / dataset_name
            train_dataset.save_to_disk(str(dataset_dir / "train"))
            if val_dataset:
                val_dataset.save_to_disk(str(dataset_dir / "validation"))
            test_dataset.save_to_disk(str(dataset_dir / "test"))
        else:
            # 不分割，直接保存
            dataset_dir = output_dir / dataset_name
            dataset.save_to_disk(str(dataset_dir))
        
        return str(dataset_dir)
    
    async def _generate_statistics(self, training_data: List[Dict[str, Any]], processed_data: pd.DataFrame) -> Dict[str, Any]:
        """生成统计信息"""
        stats = {
            "total_samples": len(training_data),
            "samples_with_images": len([s for s in training_data if s.get("images", [])]),
            "samples_with_text": len([s for s in training_data if s.get("text", "").strip()]),
            "average_text_length": 0,
            "image_count_distribution": {},
            "quality_distribution": {}
        }
        
        # 文本长度统计
        text_lengths = [len(s.get("text", "")) for s in training_data]
        if text_lengths:
            stats["average_text_length"] = sum(text_lengths) / len(text_lengths)
        
        # 图像数量分布
        image_counts = [len(s.get("images", [])) for s in training_data]
        for count in image_counts:
            stats["image_count_distribution"][str(count)] = stats["image_count_distribution"].get(str(count), 0) + 1
        
        return stats