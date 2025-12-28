"""
第4步：第一轮大模型标注
使用多模态大模型对数据进行初步标注
"""

import pandas as pd
import asyncio
from typing import List, Dict, Any, Optional
from ..core import PipelineStep, StepResult, PipelineConfig
from maque.performance import MeasureTime
from maque.mllm.mllm_client import MllmClient
from maque.async_api.concurrent_executor import ConcurrentExecutor


class MllmAnnotationStep(PipelineStep):
    """MLLM标注步骤"""
    
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "mllm_config": {
                "type": "object",
                "properties": {
                    "model_name": {"type": "string", "default": "gpt-4o"},
                    "base_url": {"type": "string"},
                    "api_key": {"type": "string"},
                    "temperature": {"type": "number", "default": 0.7},
                    "max_tokens": {"type": "integer", "default": 2048}
                },
                "required": ["model_name"]
            },
            "annotation_prompts": {
                "type": "object",
                "properties": {
                    "system_prompt": {
                        "type": "string",
                        "default": "你是一个专业的数据标注员，请根据给定的图像和文本内容进行标注。"
                    },
                    "user_prompt_template": {
                        "type": "string", 
                        "default": "请对以下内容进行标注：\n文本：{text}\n\n请提供：\n1. 内容摘要\n2. 主要标签\n3. 情感倾向\n4. 质量评估"
                    }
                }
            },
            "concurrent_config": {
                "type": "object",
                "properties": {
                    "max_workers": {"type": "integer", "default": 5},
                    "batch_size": {"type": "integer", "default": 10},
                    "rate_limit": {"type": "number", "default": 1.0}
                }
            },
            "output_columns": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "default": "mllm_summary"},
                    "tags": {"type": "string", "default": "mllm_tags"},
                    "sentiment": {"type": "string", "default": "mllm_sentiment"},
                    "quality": {"type": "string", "default": "mllm_quality"},
                    "raw_response": {"type": "string", "default": "mllm_raw_response"}
                }
            },
            "retry_config": {
                "type": "object",
                "properties": {
                    "max_retries": {"type": "integer", "default": 3},
                    "retry_delay": {"type": "number", "default": 1.0}
                }
            }
        }
    }
    
    def __init__(self, name: str = "mllm_annotation", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.mllm_client: Optional[MllmClient] = None
    
    async def execute(self, data: pd.DataFrame, config: PipelineConfig) -> StepResult:
        """执行MLLM标注"""
        with MeasureTime(f"步骤 {self.name}"):
            try:
                step_config = self.get_step_config(config)
                data_copy = data.copy()
                
                # 初始化MLLM客户端
                await self._initialize_mllm_client(step_config)
                
                # 准备标注任务
                annotation_tasks = await self._prepare_annotation_tasks(data_copy, step_config)
                
                # 执行并发标注
                annotation_results = await self._execute_concurrent_annotation(
                    annotation_tasks, step_config
                )
                
                # 处理标注结果
                await self._process_annotation_results(
                    data_copy, annotation_results, step_config
                )
                
                # 更新处理状态
                data_copy['__processing_status'] = 'annotated'
                data_copy['__annotated_at'] = pd.Timestamp.now()
                
                # 统计结果
                successful_annotations = len([r for r in annotation_results if r.get('success', False)])
                failed_annotations = len(annotation_results) - successful_annotations
                
                metadata = {
                    "total_rows": len(data_copy),
                    "successful_annotations": successful_annotations,
                    "failed_annotations": failed_annotations,
                    "success_rate": successful_annotations / len(annotation_results) if annotation_results else 0,
                    "mllm_model": step_config.get("mllm_config", {}).get("model_name", "unknown")
                }
                
                self.logger.info(f"MLLM标注完成，成功率: {metadata['success_rate']:.2%}")
                
                return StepResult(
                    step_name=self.name,
                    success=True,
                    data=data_copy,
                    metadata=metadata
                )
                
            except Exception as e:
                self.logger.error(f"MLLM标注失败: {e}")
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
            temperature=mllm_config.get("temperature", 0.7),
            max_tokens=mllm_config.get("max_tokens", 2048)
        )
        
        self.logger.info(f"初始化MLLM客户端: {mllm_config.get('model_name', 'gpt-4o')}")
    
    async def _prepare_annotation_tasks(self, data: pd.DataFrame, step_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """准备标注任务"""
        tasks = []
        
        prompts = step_config.get("annotation_prompts", {})
        system_prompt = prompts.get("system_prompt", "你是一个专业的数据标注员。")
        user_prompt_template = prompts.get("user_prompt_template", "请对以下内容进行标注：\n文本：{text}")
        
        text_col = "text"  # 从data_alignment步骤输出的列名
        image_col = "images"  # 从data_alignment步骤输出的列名
        
        for idx, row in data.iterrows():
            text_content = str(row[text_col]) if pd.notna(row[text_col]) else ""
            image_paths = str(row[image_col]) if pd.notna(row[image_col]) else ""
            
            # 构建用户提示
            user_prompt = user_prompt_template.format(
                text=text_content,
                images=image_paths
            )
            
            # 准备图像路径列表
            image_list = []
            if image_paths:
                separator = step_config.get("image_separator", "|")  
                image_list = [p.strip() for p in image_paths.split(separator) if p.strip()]
            
            task = {
                "row_index": idx,
                "text": text_content,
                "images": image_list,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt
            }
            
            tasks.append(task)
        
        self.logger.info(f"准备了 {len(tasks)} 个标注任务")
        return tasks
    
    async def _execute_concurrent_annotation(self, tasks: List[Dict[str, Any]], step_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行并发标注"""
        concurrent_config = step_config.get("concurrent_config", {})
        max_workers = concurrent_config.get("max_workers", 5)
        batch_size = concurrent_config.get("batch_size", 10)
        rate_limit = concurrent_config.get("rate_limit", 1.0)
        
        # 创建并发执行器
        executor = ConcurrentExecutor(
            max_concurrent=max_workers,
            rate_limit=rate_limit
        )
        
        # 准备异步任务
        async_tasks = []
        for task in tasks:
            async_task = self._annotate_single_item(task, step_config)
            async_tasks.append(async_task)
        
        # 执行并发标注
        results = await executor.execute_all(async_tasks)
        
        return results
    
    async def _annotate_single_item(self, task: Dict[str, Any], step_config: Dict[str, Any]) -> Dict[str, Any]:
        """标注单个数据项"""
        retry_config = step_config.get("retry_config", {})
        max_retries = retry_config.get("max_retries", 3)
        retry_delay = retry_config.get("retry_delay", 1.0)
        
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
                parsed_result = self._parse_mllm_response(response)
                
                return {
                    "row_index": task["row_index"],
                    "success": True,
                    "raw_response": response,
                    **parsed_result
                }
                
            except Exception as e:
                self.logger.warning(f"第 {attempt + 1} 次标注失败 (行 {task['row_index']}): {e}")
                
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    return {
                        "row_index": task["row_index"],
                        "success": False,
                        "error": str(e),
                        "raw_response": "",
                        "summary": "",
                        "tags": "",
                        "sentiment": "",
                        "quality": ""
                    }
    
    def _parse_mllm_response(self, response: str) -> Dict[str, str]:
        """解析MLLM响应"""
        # 简单的响应解析，实际使用时可能需要更复杂的解析逻辑
        result = {
            "summary": "",
            "tags": "",
            "sentiment": "",
            "quality": ""
        }
        
        try:
            lines = response.strip().split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 检查是否是新的部分标题
                if "摘要" in line or "summary" in line.lower():
                    current_section = "summary"
                elif "标签" in line or "tag" in line.lower():
                    current_section = "tags"
                elif "情感" in line or "sentiment" in line.lower():
                    current_section = "sentiment"
                elif "质量" in line or "quality" in line.lower():
                    current_section = "quality"
                elif current_section and line:
                    # 移除常见的前缀
                    content = line.replace("：", "").replace(":", "").strip()
                    if content and not content.startswith(("1.", "2.", "3.", "4.")):
                        if result[current_section]:
                            result[current_section] += " " + content
                        else:
                            result[current_section] = content
            
            # 如果解析失败，将整个响应作为摘要
            if not any(result.values()):
                result["summary"] = response[:500]  # 截取前500字符
                
        except Exception as e:
            self.logger.warning(f"解析MLLM响应失败: {e}")
            result["summary"] = response[:500] if response else ""
        
        return result
    
    async def _process_annotation_results(self, data: pd.DataFrame, results: List[Dict[str, Any]], step_config: Dict[str, Any]):
        """处理标注结果"""
        output_columns = step_config.get("output_columns", {})
        
        summary_col = output_columns.get("summary", "mllm_summary")
        tags_col = output_columns.get("tags", "mllm_tags")
        sentiment_col = output_columns.get("sentiment", "mllm_sentiment")
        quality_col = output_columns.get("quality", "mllm_quality")
        raw_response_col = output_columns.get("raw_response", "mllm_raw_response")
        
        # 初始化新列
        data[summary_col] = ""
        data[tags_col] = ""
        data[sentiment_col] = ""
        data[quality_col] = ""
        data[raw_response_col] = ""
        data['__mllm_annotation_success'] = False
        
        # 填充结果
        for result in results:
            row_idx = result["row_index"]
            
            data.at[row_idx, summary_col] = result.get("summary", "")
            data.at[row_idx, tags_col] = result.get("tags", "")
            data.at[row_idx, sentiment_col] = result.get("sentiment", "")
            data.at[row_idx, quality_col] = result.get("quality", "")
            data.at[row_idx, raw_response_col] = result.get("raw_response", "")
            data.at[row_idx, '__mllm_annotation_success'] = result.get("success", False)