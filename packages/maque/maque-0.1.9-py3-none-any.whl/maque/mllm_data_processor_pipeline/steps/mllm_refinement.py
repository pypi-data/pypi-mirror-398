"""
第5步：第二轮大模型精标润色
对第一轮标注结果进行精细化和润色
"""

import pandas as pd
import asyncio
from typing import List, Dict, Any, Optional
from ..core import PipelineStep, StepResult, PipelineConfig
from maque.performance import MeasureTime
from maque.mllm.mllm_client import MllmClient
from maque.async_api.concurrent_executor import ConcurrentExecutor


class MllmRefinementStep(PipelineStep):
    """MLLM精标润色步骤"""
    
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "mllm_config": {
                "type": "object",
                "properties": {
                    "model_name": {"type": "string", "default": "gpt-4o"},
                    "base_url": {"type": "string"},
                    "api_key": {"type": "string"},
                    "temperature": {"type": "number", "default": 0.3},
                    "max_tokens": {"type": "integer", "default": 3072}
                },
                "required": ["model_name"]
            },
            "refinement_prompts": {
                "type": "object",
                "properties": {
                    "system_prompt": {
                        "type": "string",
                        "default": "你是一个专业的数据质量专家，负责对已有的标注结果进行精细化和质量提升。"
                    },
                    "user_prompt_template": {
                        "type": "string",
                        "default": "请对以下标注结果进行精细化处理：\n\n原始内容：\n文本：{text}\n\n第一轮标注结果：\n摘要：{summary}\n标签：{tags}\n情感：{sentiment}\n质量：{quality}\n\n请提供：\n1. 优化后的摘要\n2. 更准确的标签\n3. 精确的情感分析\n4. 详细的质量评估\n5. 改进建议"
                    }
                }
            },
            "refinement_criteria": {
                "type": "object",
                "properties": {
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["accuracy", "completeness", "consistency", "clarity"],
                        "description": "重点改进的方面"
                    },
                    "quality_threshold": {
                        "type": "number",
                        "default": 0.7,
                        "description": "质量阈值，低于此值的数据会被优先精标"
                    },
                    "skip_high_quality": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否跳过高质量数据的精标"
                    }
                }
            },
            "concurrent_config": {
                "type": "object",
                "properties": {
                    "max_workers": {"type": "integer", "default": 3},
                    "batch_size": {"type": "integer", "default": 5},
                    "rate_limit": {"type": "number", "default": 0.5}
                }
            },
            "output_columns": {
                "type": "object",
                "properties": {
                    "refined_summary": {"type": "string", "default": "refined_summary"},
                    "refined_tags": {"type": "string", "default": "refined_tags"},
                    "refined_sentiment": {"type": "string", "default": "refined_sentiment"},
                    "refined_quality": {"type": "string", "default": "refined_quality"},
                    "improvement_suggestions": {"type": "string", "default": "improvement_suggestions"},
                    "refinement_raw_response": {"type": "string", "default": "refinement_raw_response"}
                }
            },
            "retry_config": {
                "type": "object",
                "properties": {
                    "max_retries": {"type": "integer", "default": 2},
                    "retry_delay": {"type": "number", "default": 2.0}
                }
            }
        }
    }
    
    def __init__(self, name: str = "mllm_refinement", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.mllm_client: Optional[MllmClient] = None
    
    async def execute(self, data: pd.DataFrame, config: PipelineConfig) -> StepResult:
        """执行MLLM精标润色"""
        with MeasureTime(f"步骤 {self.name}"):
            try:
                step_config = self.get_step_config(config)
                data_copy = data.copy()
                
                # 初始化MLLM客户端
                await self._initialize_mllm_client(step_config)
                
                # 筛选需要精标的数据
                refinement_candidates = await self._select_refinement_candidates(data_copy, step_config)
                
                if not refinement_candidates:
                    self.logger.info("没有需要精标的数据")
                    return StepResult(
                        step_name=self.name,
                        success=True,
                        data=data_copy,
                        metadata={"skipped": True, "reason": "no_candidates"}
                    )
                
                # 准备精标任务
                refinement_tasks = await self._prepare_refinement_tasks(data_copy, refinement_candidates, step_config)
                
                # 执行并发精标
                refinement_results = await self._execute_concurrent_refinement(
                    refinement_tasks, step_config
                )
                
                # 处理精标结果
                await self._process_refinement_results(
                    data_copy, refinement_results, step_config
                )
                
                # 更新处理状态
                data_copy['__processing_status'] = 'refined'
                data_copy['__refined_at'] = pd.Timestamp.now()
                
                # 统计结果
                successful_refinements = len([r for r in refinement_results if r.get('success', False)])
                failed_refinements = len(refinement_results) - successful_refinements
                
                metadata = {
                    "total_rows": len(data_copy),
                    "refinement_candidates": len(refinement_candidates),
                    "successful_refinements": successful_refinements,
                    "failed_refinements": failed_refinements,
                    "success_rate": successful_refinements / len(refinement_results) if refinement_results else 0,
                    "mllm_model": step_config.get("mllm_config", {}).get("model_name", "unknown")
                }
                
                self.logger.info(f"MLLM精标完成，成功率: {metadata['success_rate']:.2%}")
                
                return StepResult(
                    step_name=self.name,
                    success=True,
                    data=data_copy,
                    metadata=metadata
                )
                
            except Exception as e:
                self.logger.error(f"MLLM精标失败: {e}")
                return StepResult(
                    step_name=self.name,
                    success=False,
                    data=data,
                    metadata={},
                    error=str(e)
                )
    
    async def _initialize_mllm_client(self, step_config: Dict[str, Any]):
        """初始化MLLM客户端"""
        mllm_config = step_config.get("mllm_config", {})
        
        self.mllm_client = MllmClient(
            model_name=mllm_config.get("model_name", "gpt-4o"),  
            base_url=mllm_config.get("base_url"),
            api_key=mllm_config.get("api_key"),
            temperature=mllm_config.get("temperature", 0.3),
            max_tokens=mllm_config.get("max_tokens", 3072)
        )
        
        self.logger.info(f"初始化精标MLLM客户端: {mllm_config.get('model_name', 'gpt-4o')}")
    
    async def _select_refinement_candidates(self, data: pd.DataFrame, step_config: Dict[str, Any]) -> List[int]:
        """选择需要精标的数据"""
        criteria = step_config.get("refinement_criteria", {})
        quality_threshold = criteria.get("quality_threshold", 0.7)
        skip_high_quality = criteria.get("skip_high_quality", True)
        
        candidates = []
        
        # 检查是否有第一轮标注结果
        if '__mllm_annotation_success' not in data.columns:
            self.logger.warning("未找到第一轮标注结果，将对所有数据进行精标")
            return list(data.index)
        
        for idx, row in data.iterrows():
            # 只对第一轮标注成功的数据进行精标
            if not row.get('__mllm_annotation_success', False):
                continue
            
            should_refine = True
            
            if skip_high_quality:
                # 评估质量，决定是否需要精标
                quality_score = self._assess_annotation_quality(row)
                if quality_score >= quality_threshold:
                    should_refine = False
            
            if should_refine:
                candidates.append(idx)
        
        self.logger.info(f"选择了 {len(candidates)} 条数据进行精标")
        return candidates
    
    def _assess_annotation_quality(self, row: pd.Series) -> float:
        """评估标注质量"""
        quality_score = 0.0
        factors = 0
        
        # 检查摘要质量
        summary = str(row.get('mllm_summary', ''))
        if summary and len(summary.strip()) >= 20:
            quality_score += 0.25
        factors += 1
        
        # 检查标签质量
        tags = str(row.get('mllm_tags', ''))
        if tags and len(tags.strip()) >= 5:
            quality_score += 0.25
        factors += 1
        
        # 检查情感分析
        sentiment = str(row.get('mllm_sentiment', ''))
        if sentiment and sentiment.strip():
            quality_score += 0.25
        factors += 1
        
        # 检查质量评估
        quality = str(row.get('mllm_quality', ''))
        if quality and quality.strip():
            quality_score += 0.25
        factors += 1
        
        return quality_score
    
    async def _prepare_refinement_tasks(self, data: pd.DataFrame, candidates: List[int], step_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """准备精标任务"""
        tasks = []
        
        prompts = step_config.get("refinement_prompts", {})
        system_prompt = prompts.get("system_prompt", "你是一个专业的数据质量专家。")
        user_prompt_template = prompts.get("user_prompt_template", "请对以下标注结果进行精细化处理：\n\n原始内容：\n文本：{text}\n\n第一轮标注结果：\n摘要：{summary}\n标签：{tags}\n情感：{sentiment}\n质量：{quality}")
        
        for idx in candidates:
            row = data.loc[idx]
            
            text_content = str(row.get('text', ''))
            current_summary = str(row.get('mllm_summary', ''))
            current_tags = str(row.get('mllm_tags', ''))
            current_sentiment = str(row.get('mllm_sentiment', ''))
            current_quality = str(row.get('mllm_quality', ''))
            
            # 构建用户提示
            user_prompt = user_prompt_template.format(
                text=text_content,
                summary=current_summary,
                tags=current_tags,
                sentiment=current_sentiment,
                quality=current_quality
            )
            
            # 准备图像路径（如果有）
            image_list = []
            images = str(row.get('images', ''))
            if images:
                separator = "|"  # 使用固定分隔符
                image_list = [p.strip() for p in images.split(separator) if p.strip()]
            
            task = {
                "row_index": idx,
                "text": text_content,
                "images": image_list,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "current_annotations": {
                    "summary": current_summary,
                    "tags": current_tags,
                    "sentiment": current_sentiment,
                    "quality": current_quality
                }
            }
            
            tasks.append(task)
        
        self.logger.info(f"准备了 {len(tasks)} 个精标任务")
        return tasks
    
    async def _execute_concurrent_refinement(self, tasks: List[Dict[str, Any]], step_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行并发精标"""
        concurrent_config = step_config.get("concurrent_config", {})
        max_workers = concurrent_config.get("max_workers", 3)
        rate_limit = concurrent_config.get("rate_limit", 0.5)
        
        # 创建并发执行器
        executor = ConcurrentExecutor(
            max_concurrent=max_workers,
            rate_limit=rate_limit
        )
        
        # 准备异步任务
        async_tasks = []
        for task in tasks:
            async_task = self._refine_single_item(task, step_config)
            async_tasks.append(async_task)
        
        # 执行并发精标
        results = await executor.execute_all(async_tasks)
        
        return results
    
    async def _refine_single_item(self, task: Dict[str, Any], step_config: Dict[str, Any]) -> Dict[str, Any]:
        """精标单个数据项"""
        retry_config = step_config.get("retry_config", {})
        max_retries = retry_config.get("max_retries", 2)
        retry_delay = retry_config.get("retry_delay", 2.0)
        
        for attempt in range(max_retries + 1):
            try:
                # 调用MLLM
                response = await self.mllm_client.chat_async(
                    messages=[
                        {"role": "system", "content": task["system_prompt"]},
                        {"role": "user", "content": task["user_prompt"]}
                    ],
                    images=task["images"]
                )
                
                # 解析响应
                parsed_result = self._parse_refinement_response(response)
                
                return {
                    "row_index": task["row_index"],
                    "success": True,
                    "raw_response": response,
                    **parsed_result
                }
                
            except Exception as e:
                self.logger.warning(f"第 {attempt + 1} 次精标失败 (行 {task['row_index']}): {e}")
                
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    return {
                        "row_index": task["row_index"],
                        "success": False,
                        "error": str(e),
                        "raw_response": "",
                        "refined_summary": "",
                        "refined_tags": "",
                        "refined_sentiment": "",
                        "refined_quality": "",
                        "improvement_suggestions": ""
                    }
    
    def _parse_refinement_response(self, response: str) -> Dict[str, str]:
        """解析精标响应"""
        result = {
            "refined_summary": "",
            "refined_tags": "",
            "refined_sentiment": "",
            "refined_quality": "",
            "improvement_suggestions": ""
        }
        
        try:
            lines = response.strip().split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 检查是否是新的部分标题
                if "优化后的摘要" in line or "refined summary" in line.lower():
                    current_section = "refined_summary"
                elif "更准确的标签" in line or "refined tag" in line.lower():
                    current_section = "refined_tags"
                elif "精确的情感" in line or "refined sentiment" in line.lower():
                    current_section = "refined_sentiment"
                elif "详细的质量" in line or "refined quality" in line.lower():
                    current_section = "refined_quality"
                elif "改进建议" in line or "improvement" in line.lower():
                    current_section = "improvement_suggestions"
                elif current_section and line:
                    # 移除常见的前缀
                    content = line.replace("：", "").replace(":", "").strip()
                    if content and not content.startswith(("1.", "2.", "3.", "4.", "5.")):
                        if result[current_section]:
                            result[current_section] += " " + content
                        else:
                            result[current_section] = content
            
            # 如果解析失败，将整个响应作为改进建议
            if not any(result.values()):
                result["improvement_suggestions"] = response[:800]
                
        except Exception as e:
            self.logger.warning(f"解析精标响应失败: {e}")
            result["improvement_suggestions"] = response[:800] if response else ""
        
        return result
    
    async def _process_refinement_results(self, data: pd.DataFrame, results: List[Dict[str, Any]], step_config: Dict[str, Any]):
        """处理精标结果"""
        output_columns = step_config.get("output_columns", {})
        
        refined_summary_col = output_columns.get("refined_summary", "refined_summary")
        refined_tags_col = output_columns.get("refined_tags", "refined_tags")
        refined_sentiment_col = output_columns.get("refined_sentiment", "refined_sentiment")
        refined_quality_col = output_columns.get("refined_quality", "refined_quality")
        improvement_suggestions_col = output_columns.get("improvement_suggestions", "improvement_suggestions")
        refinement_raw_response_col = output_columns.get("refinement_raw_response", "refinement_raw_response")
        
        # 初始化新列
        data[refined_summary_col] = ""
        data[refined_tags_col] = ""
        data[refined_sentiment_col] = ""
        data[refined_quality_col] = ""
        data[improvement_suggestions_col] = ""
        data[refinement_raw_response_col] = ""
        data['__mllm_refinement_success'] = False
        
        # 填充结果
        for result in results:
            row_idx = result["row_index"]
            
            data.at[row_idx, refined_summary_col] = result.get("refined_summary", "")
            data.at[row_idx, refined_tags_col] = result.get("refined_tags", "")
            data.at[row_idx, refined_sentiment_col] = result.get("refined_sentiment", "")
            data.at[row_idx, refined_quality_col] = result.get("refined_quality", "")
            data.at[row_idx, improvement_suggestions_col] = result.get("improvement_suggestions", "")
            data.at[row_idx, refinement_raw_response_col] = result.get("raw_response", "")
            data.at[row_idx, '__mllm_refinement_success'] = result.get("success", False)