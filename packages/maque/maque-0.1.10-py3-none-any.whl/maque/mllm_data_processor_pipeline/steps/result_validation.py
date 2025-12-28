"""
第7步：结果校验步骤
对最终结果进行质量检查和验证
"""

import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from ..core import PipelineStep, StepResult, PipelineConfig
from maque.performance import MeasureTime


class ResultValidationStep(PipelineStep):
    """结果校验步骤"""
    
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "validation_criteria": {
                "type": "object",
                "properties": {
                    "min_samples": {"type": "integer", "default": 10},
                    "min_success_rate": {"type": "number", "default": 0.8},
                    "required_fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["text", "images", "labels"]
                    },
                    "quality_thresholds": {
                        "type": "object",
                        "properties": {
                            "min_text_length": {"type": "integer", "default": 10},
                            "max_empty_fields": {"type": "integer", "default": 2}
                        }
                    }
                }
            },
            "validation_tests": {
                "type": "object",
                "properties": {
                    "check_duplicates": {"type": "boolean", "default": True},
                    "check_data_integrity": {"type": "boolean", "default": True},
                    "check_file_references": {"type": "boolean", "default": True},
                    "check_format_consistency": {"type": "boolean", "default": True},
                    "run_statistical_analysis": {"type": "boolean", "default": True}
                }
            },
            "output_reports": {
                "type": "object",
                "properties": {
                    "generate_summary_report": {"type": "boolean", "default": True},
                    "generate_detailed_report": {"type": "boolean", "default": True},
                    "generate_quality_metrics": {"type": "boolean", "default": True},
                    "save_failed_samples": {"type": "boolean", "default": True}
                }
            },
            "remediation": {
                "type": "object",
                "properties": {
                    "auto_fix_minor_issues": {"type": "boolean", "default": True},
                    "remove_invalid_samples": {"type": "boolean", "default": False},
                    "flag_problematic_samples": {"type": "boolean", "default": True}
                }
            }
        }
    }
    
    def __init__(self, name: str = "result_validation", config: Dict[str, Any] = None):
        super().__init__(name, config)
    
    async def execute(self, data: pd.DataFrame, config: PipelineConfig) -> StepResult:
        """执行结果校验"""
        with MeasureTime(f"步骤 {self.name}"):
            try:
                step_config = self.get_step_config(config)
                
                # 执行各种验证测试
                validation_results = await self._run_validation_tests(data, config, step_config)
                
                # 生成质量报告
                quality_report = await self._generate_quality_report(data, validation_results, step_config)
                
                # 执行修复措施
                corrected_data = await self._apply_remediation(data, validation_results, step_config)
                
                # 保存报告
                report_files = await self._save_reports(quality_report, config, step_config)
                
                # 更新处理状态
                corrected_data['__processing_status'] = 'validated_final'
                corrected_data['__final_validated_at'] = pd.Timestamp.now()
                
                # 判断整体验证是否通过
                overall_passed = self._assess_overall_quality(validation_results, step_config)
                
                metadata = {
                    "validation_passed": overall_passed,
                    "total_samples": len(corrected_data),
                    "validation_results": validation_results,
                    "quality_score": quality_report.get("overall_quality_score", 0.0),
                    "report_files": report_files,
                    "corrected_issues": quality_report.get("corrected_issues", 0)
                }
                
                self.logger.info(f"结果校验完成，整体质量评分: {quality_report.get('overall_quality_score', 0.0):.2f}")
                
                return StepResult(
                    step_name=self.name,
                    success=overall_passed,
                    data=corrected_data,
                    metadata=metadata
                )
                
            except Exception as e:
                self.logger.error(f"结果校验失败: {e}")
                return StepResult(
                    step_name=self.name,
                    success=False,
                    data=data,
                    metadata={},
                    error=str(e)
                )
    
    async def _run_validation_tests(self, data: pd.DataFrame, config: PipelineConfig, step_config: Dict[str, Any]) -> Dict[str, Any]:
        """运行验证测试"""
        validation_tests = step_config.get("validation_tests", {})
        results = {}
        
        # 基本数据完整性检查
        if validation_tests.get("check_data_integrity", True):
            results["data_integrity"] = await self._check_data_integrity(data, step_config)
        
        # 重复数据检查
        if validation_tests.get("check_duplicates", True):
            results["duplicates"] = await self._check_duplicates(data)
        
        # 文件引用检查
        if validation_tests.get("check_file_references", True):
            results["file_references"] = await self._check_file_references(data)
        
        # 格式一致性检查
        if validation_tests.get("check_format_consistency", True):
            results["format_consistency"] = await self._check_format_consistency(data)
        
        # 统计分析
        if validation_tests.get("run_statistical_analysis", True):
            results["statistical_analysis"] = await self._run_statistical_analysis(data)
        
        return results
    
    async def _check_data_integrity(self, data: pd.DataFrame, step_config: Dict[str, Any]) -> Dict[str, Any]:
        """检查数据完整性"""
        criteria = step_config.get("validation_criteria", {})
        required_fields = criteria.get("required_fields", ["text", "images", "labels"])
        min_samples = criteria.get("min_samples", 10)
        quality_thresholds = criteria.get("quality_thresholds", {})
        
        issues = []
        passed_samples = 0
        
        # 检查样本数量
        if len(data) < min_samples:
            issues.append(f"样本数量不足: {len(data)} < {min_samples}")
        
        # 检查必需字段
        missing_fields = [field for field in required_fields if field not in data.columns]
        if missing_fields:
            issues.append(f"缺少必需字段: {missing_fields}")
        
        # 检查每个样本的质量
        for idx, row in data.iterrows():
            sample_issues = []
            
            # 检查文本长度
            text_content = str(row.get('text', ''))
            min_text_length = quality_thresholds.get("min_text_length", 10)
            if len(text_content.strip()) < min_text_length:
                sample_issues.append("文本长度不足")
            
            # 检查空字段数量
            empty_fields = sum(1 for field in required_fields 
                             if field in data.columns and (pd.isna(row[field]) or str(row[field]).strip() == ""))
            max_empty_fields = quality_thresholds.get("max_empty_fields", 2)
            if empty_fields > max_empty_fields:
                sample_issues.append(f"空字段过多: {empty_fields}")
            
            if not sample_issues:
                passed_samples += 1
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "passed_samples": passed_samples,
            "total_samples": len(data),
            "pass_rate": passed_samples / len(data) if len(data) > 0 else 0
        }
    
    async def _check_duplicates(self, data: pd.DataFrame) -> Dict[str, Any]:
        """检查重复数据"""
        # 基于文本和图像内容检查重复
        content_columns = ['text', 'images']
        available_columns = [col for col in content_columns if col in data.columns]
        
        if not available_columns:
            return {"passed": True, "duplicates": 0, "duplicate_pairs": []}
        
        # 查找重复项
        duplicates = data.duplicated(subset=available_columns, keep=False)
        duplicate_count = duplicates.sum()
        
        # 获取重复项的详细信息
        duplicate_pairs = []
        if duplicate_count > 0:
            duplicate_data = data[duplicates]
            groups = duplicate_data.groupby(available_columns)
            for name, group in groups:
                if len(group) > 1:
                    duplicate_pairs.append({
                        "content": dict(zip(available_columns, name)),
                        "indices": list(group.index)
                    })
        
        return {
            "passed": duplicate_count == 0,
            "duplicates": duplicate_count,
            "duplicate_pairs": duplicate_pairs
        }
    
    async def _check_file_references(self, data: pd.DataFrame) -> Dict[str, Any]:
        """检查文件引用"""
        if 'images' not in data.columns:
            return {"passed": True, "missing_files": [], "invalid_paths": []}
        
        missing_files = []
        invalid_paths = []
        
        for idx, row in data.iterrows():
            images_str = str(row.get('images', ''))
            if not images_str or images_str == 'nan':
                continue
            
            # 解析图像路径
            image_paths = [p.strip() for p in images_str.split('|') if p.strip()]
            
            for image_path in image_paths:
                try:
                    path_obj = Path(image_path)
                    if not path_obj.exists():
                        missing_files.append({
                            "row_index": idx,
                            "file_path": image_path
                        })
                except Exception:
                    invalid_paths.append({
                        "row_index": idx,
                        "file_path": image_path
                    })
        
        return {
            "passed": len(missing_files) == 0 and len(invalid_paths) == 0,
            "missing_files": missing_files,
            "invalid_paths": invalid_paths
        }
    
    async def _check_format_consistency(self, data: pd.DataFrame) -> Dict[str, Any]:
        """检查格式一致性"""
        issues = []
        
        # 检查图像路径格式
        if 'images' in data.columns:
            inconsistent_formats = []
            for idx, row in data.iterrows():
                images_str = str(row.get('images', ''))
                if images_str and images_str != 'nan':
                    # 检查是否使用了正确的分隔符
                    if '|' not in images_str and ',' in images_str:
                        inconsistent_formats.append(idx)
            
            if inconsistent_formats:
                issues.append(f"图像路径分隔符不一致: {len(inconsistent_formats)} 个样本")
        
        # 检查标签格式
        label_columns = [col for col in data.columns if 'mllm_' in col or 'refined_' in col]
        for col in label_columns:
            empty_count = data[col].isna().sum() + (data[col] == '').sum()
            if empty_count > len(data) * 0.5:  # 超过50%为空
                issues.append(f"标签列 {col} 空值过多: {empty_count}/{len(data)}")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues
        }
    
    async def _run_statistical_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """运行统计分析"""
        stats = {}
        
        # 文本长度统计
        if 'text' in data.columns:
            text_lengths = data['text'].astype(str).str.len()
            stats["text_length"] = {
                "mean": float(text_lengths.mean()),
                "std": float(text_lengths.std()),
                "min": int(text_lengths.min()),
                "max": int(text_lengths.max()),
                "median": float(text_lengths.median())
            }
        
        # 图像数量统计
        if 'images' in data.columns:
            image_counts = []
            for images_str in data['images']:
                if pd.notna(images_str) and str(images_str).strip():
                    count = len([p for p in str(images_str).split('|') if p.strip()])
                    image_counts.append(count)
                else:
                    image_counts.append(0)
            
            if image_counts:
                stats["image_count"] = {
                    "mean": sum(image_counts) / len(image_counts),
                    "min": min(image_counts),
                    "max": max(image_counts),
                    "samples_with_images": sum(1 for c in image_counts if c > 0)
                }
        
        # 标注成功率统计
        if '__mllm_annotation_success' in data.columns:
            success_rate = data['__mllm_annotation_success'].mean()
            stats["annotation_success_rate"] = float(success_rate)
        
        if '__mllm_refinement_success' in data.columns:
            refinement_rate = data['__mllm_refinement_success'].mean()
            stats["refinement_success_rate"] = float(refinement_rate)
        
        return {
            "passed": True,
            "statistics": stats
        }
    
    async def _generate_quality_report(self, data: pd.DataFrame, validation_results: Dict[str, Any], step_config: Dict[str, Any]) -> Dict[str, Any]:
        """生成质量报告"""
        report = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "total_samples": len(data),
            "validation_results": validation_results,
            "overall_quality_score": 0.0,
            "issues_summary": [],
            "recommendations": [],
            "corrected_issues": 0
        }
        
        # 计算总体质量分数
        quality_factors = []
        
        # 数据完整性权重: 40%
        if "data_integrity" in validation_results:
            integrity_score = validation_results["data_integrity"].get("pass_rate", 0.0)
            quality_factors.append(("data_integrity", integrity_score, 0.4))
        
        # 无重复性权重: 20%
        if "duplicates" in validation_results:
            dup_result = validation_results["duplicates"]
            no_dup_score = 1.0 if dup_result["passed"] else max(0.0, 1.0 - dup_result["duplicates"] / len(data))
            quality_factors.append(("no_duplicates", no_dup_score, 0.2))
        
        # 文件引用有效性权重: 20%
        if "file_references" in validation_results:
            file_result = validation_results["file_references"]
            file_score = 1.0 if file_result["passed"] else 0.5
            quality_factors.append(("file_references", file_score, 0.2))
        
        # 格式一致性权重: 20%
        if "format_consistency" in validation_results:
            format_result = validation_results["format_consistency"]
            format_score = 1.0 if format_result["passed"] else 0.7
            quality_factors.append(("format_consistency", format_score, 0.2))
        
        # 计算加权平均分
        if quality_factors:
            weighted_sum = sum(score * weight for _, score, weight in quality_factors)
            total_weight = sum(weight for _, _, weight in quality_factors)
            report["overall_quality_score"] = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # 收集问题摘要
        for test_name, result in validation_results.items():
            if not result.get("passed", True):
                if "issues" in result:
                    report["issues_summary"].extend(result["issues"])
                elif "duplicates" in result:
                    report["issues_summary"].append(f"发现 {result['duplicates']} 个重复样本")
                elif "missing_files" in result:
                    report["issues_summary"].append(f"发现 {len(result['missing_files'])} 个缺失文件")
        
        # 生成建议
        if report["overall_quality_score"] < 0.8:
            report["recommendations"].append("整体质量分数较低，建议检查数据源和处理流程")
        
        if "data_integrity" in validation_results:
            integrity_result = validation_results["data_integrity"]
            if integrity_result.get("pass_rate", 1.0) < 0.9:
                report["recommendations"].append("数据完整性不足，建议增强数据验证和清洗步骤")
        
        return report
    
    async def _apply_remediation(self, data: pd.DataFrame, validation_results: Dict[str, Any], step_config: Dict[str, Any]) -> pd.DataFrame:
        """应用修复措施"""
        remediation = step_config.get("remediation", {})
        data_copy = data.copy()
        corrected_count = 0
        
        # 自动修复小问题
        if remediation.get("auto_fix_minor_issues", True):
            # 清理空白字符
            text_columns = ['text', 'mllm_summary', 'refined_summary']
            for col in text_columns:
                if col in data_copy.columns:
                    data_copy[col] = data_copy[col].astype(str).str.strip()
                    corrected_count += 1
        
        # 标记有问题的样本
        if remediation.get("flag_problematic_samples", True):
            data_copy['__has_validation_issues'] = False
            
            # 标记重复样本
            if "duplicates" in validation_results and validation_results["duplicates"]["duplicate_pairs"]:
                for pair in validation_results["duplicates"]["duplicate_pairs"]:
                    for idx in pair["indices"]:
                        if idx in data_copy.index:
                            data_copy.at[idx, '__has_validation_issues'] = True
            
            # 标记文件缺失的样本
            if "file_references" in validation_results:
                for missing_file in validation_results["file_references"].get("missing_files", []):
                    idx = missing_file["row_index"]
                    if idx in data_copy.index:
                        data_copy.at[idx, '__has_validation_issues'] = True
        
        # 移除无效样本
        if remediation.get("remove_invalid_samples", False):
            initial_count = len(data_copy)
            # 这里可以根据具体的无效性标准来移除样本
            # 暂时保留所有样本
            removed_count = initial_count - len(data_copy)
            if removed_count > 0:
                self.logger.info(f"移除了 {removed_count} 个无效样本")
                corrected_count += removed_count
        
        return data_copy
    
    async def _save_reports(self, quality_report: Dict[str, Any], config: PipelineConfig, step_config: Dict[str, Any]) -> List[str]:
        """保存报告"""
        output_reports = step_config.get("output_reports", {})
        report_files = []
        
        output_dir = Path(config.output_dir) / "validation_reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存摘要报告
        if output_reports.get("generate_summary_report", True):
            summary_file = output_dir / "validation_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(quality_report, f, ensure_ascii=False, indent=2)
            report_files.append(str(summary_file))
        
        # 保存详细报告
        if output_reports.get("generate_detailed_report", True):
            detailed_file = output_dir / "validation_detailed.json"
            detailed_report = {
                "summary": quality_report,
                "detailed_validation_results": quality_report["validation_results"]
            }
            with open(detailed_file, 'w', encoding='utf-8') as f:
                json.dump(detailed_report, f, ensure_ascii=False, indent=2)
            report_files.append(str(detailed_file))
        
        return report_files
    
    def _assess_overall_quality(self, validation_results: Dict[str, Any], step_config: Dict[str, Any]) -> bool:
        """评估整体质量是否合格"""
        criteria = step_config.get("validation_criteria", {})
        min_success_rate = criteria.get("min_success_rate", 0.8)
        
        # 检查数据完整性
        if "data_integrity" in validation_results:
            integrity_result = validation_results["data_integrity"]
            if not integrity_result["passed"] or integrity_result.get("pass_rate", 0.0) < min_success_rate:
                return False
        
        # 检查其他关键指标
        critical_tests = ["duplicates", "file_references"]
        for test in critical_tests:
            if test in validation_results and not validation_results[test]["passed"]:
                # 对于某些问题，如果影响不大，可以容忍
                if test == "file_references":
                    missing_count = len(validation_results[test].get("missing_files", []))
                    if missing_count > len(validation_results.get("data_integrity", {}).get("total_samples", 1)) * 0.1:
                        return False
        
        return True