#!/usr/bin/env python3
"""
MLLM Data Processor Pipeline 使用示例

这个示例展示了如何使用Pipeline进行多模态大模型训练数据处理。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from maque.mllm_data_processor_pipeline import (
    DataProcessorPipeline, 
    PipelineConfig,
    WebApp
)
from maque.mllm_data_processor_pipeline.steps import *


async def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 1. 创建配置
    config = PipelineConfig(
        input_file="example_data.csv",
        input_type="csv",
        image_columns=["image_url"],
        text_columns=["text", "content"],
        harmful_image_columns=["harmful_img"],
        harmful_text_columns=["harmful_text"],
        output_dir="./output",
        checkpoint_dir="./checkpoints",
        mllm_config={
            "model_name": "gpt-4o",
            "api_key": "your-api-key-here",
            "temperature": 0.7,
            "max_tokens": 2048
        },
        steps_config={
            "data_validation": {
                "skip_validation": False,
                "min_text_length": 10,
                "require_images": False
            },
            "mllm_annotation": {
                "concurrent_config": {
                    "max_workers": 5,
                    "rate_limit": 1.0
                },
                "annotation_prompts": {
                    "system_prompt": "你是一个专业的数据标注员，请根据给定的图像和文本内容进行标注。",
                    "user_prompt_template": """请对以下内容进行标注：
文本：{text}

请提供：
1. 内容摘要（50字以内）
2. 主要标签（用逗号分隔）
3. 情感倾向（正面/负面/中性）
4. 质量评估（高/中/低）"""
                }
            },
            "mllm_refinement": {
                "concurrent_config": {
                    "max_workers": 3,
                    "rate_limit": 0.5
                },
                "refinement_criteria": {
                    "quality_threshold": 0.7,
                    "skip_high_quality": True
                }
            },
            "format_conversion": {
                "output_formats": ["jsonl", "csv", "json"],
                "field_mapping": {
                    "text_field": "text",
                    "images_field": "images",
                    "labels_field": "labels"
                }
            }
        }
    )
    
    # 2. 创建Pipeline
    pipeline = DataProcessorPipeline(config)
    
    # 3. 添加处理步骤
    pipeline.add_step(DataLoaderStep()) \
           .add_step(DataAlignmentStep()) \
           .add_step(DataValidationStep()) \
           .add_step(MllmAnnotationStep()) \
           .add_step(MllmRefinementStep()) \
           .add_step(FormatConversionStep()) \
           .add_step(ResultValidationStep())
    
    # 4. 设置状态回调（可选）
    def status_callback(status, data):
        print(f"状态更新: {status} - {data}")
    
    pipeline.set_status_callback(status_callback)
    
    # 5. 运行Pipeline
    try:
        results = await pipeline.run()
        
        print("\n=== 执行结果 ===")
        for i, result in enumerate(results):
            step_name = result.step_name
            success = "✓" if result.success else "✗"
            print(f"{i+1}. {step_name}: {success}")
            if result.error:
                print(f"   错误: {result.error}")
        
        # 6. 保存最终结果
        pipeline.save_final_results()
        print("\n处理完成！结果已保存到output目录。")
        
    except Exception as e:
        print(f"Pipeline执行失败: {e}")


async def example_resume_from_checkpoint():
    """从检查点恢复示例"""
    print("=== 从检查点恢复示例 ===")
    
    config = PipelineConfig(
        input_file="example_data.csv",
        input_type="csv",
        checkpoint_dir="./checkpoints"
    )
    
    pipeline = DataProcessorPipeline(config)
    # 添加步骤...
    
    # 从特定步骤恢复
    try:
        results = await pipeline.run(resume_from="mllm_annotation")
        print("从检查点恢复执行成功！")
    except Exception as e:
        print(f"从检查点恢复失败: {e}")


def example_web_interface():
    """Web界面示例"""
    print("=== Web界面示例 ===")
    
    # 创建Web应用
    app = WebApp(static_dir="./static")
    
    # 启动Web服务器
    print("启动Web界面...")
    print("访问: http://localhost:8000")
    app.run(host="0.0.0.0", port=8000)


def example_custom_step():
    """自定义步骤示例"""
    print("=== 自定义步骤示例 ===")
    
    class CustomProcessingStep(PipelineStep):
        """自定义处理步骤"""
        
        def __init__(self, name: str = "custom_processing"):
            super().__init__(name)
        
        async def execute(self, data, config):
            """执行自定义处理"""
            try:
                # 自定义处理逻辑
                processed_data = data.copy()
                
                # 添加自定义列
                processed_data['custom_score'] = 0.85
                processed_data['custom_tag'] = 'processed'
                
                return StepResult(
                    step_name=self.name,
                    success=True,
                    data=processed_data,
                    metadata={"custom_metric": 42}
                )
                
            except Exception as e:
                return StepResult(
                    step_name=self.name,
                    success=False,
                    data=data,
                    metadata={},
                    error=str(e)
                )
    
    # 使用自定义步骤
    config = PipelineConfig(input_file="example_data.csv")
    pipeline = DataProcessorPipeline(config)
    
    pipeline.add_step(DataLoaderStep()) \
           .add_step(CustomProcessingStep()) \
           .add_step(FormatConversionStep())
    
    print("自定义步骤已添加到Pipeline")


async def example_with_excel():
    """Excel文件处理示例"""
    print("=== Excel文件处理示例 ===")
    
    config = PipelineConfig(
        input_file="example_data.xlsx",
        input_type="excel",
        sheet_name=None,  # 使用默认工作表
        image_columns=["image1", "image2"],  # Excel中包含图像的列
        text_columns=["title", "description"],
        output_dir="./excel_output",
        steps_config={
            "data_loader": {
                "extract_images_from_excel": True,
                "image_output_dir": "extracted_images"
            }
        }
    )
    
    pipeline = DataProcessorPipeline(config)
    pipeline.add_step(DataLoaderStep()) \
           .add_step(DataAlignmentStep()) \
           .add_step(FormatConversionStep())
    
    try:
        results = await pipeline.run()
        print("Excel文件处理完成！")
    except Exception as e:
        print(f"Excel文件处理失败: {e}")


def create_sample_data():
    """创建示例数据文件"""
    import pandas as pd
    
    # 创建示例CSV数据
    sample_data = {
        'text': [
            '这是一个关于猫的有趣故事。',
            '人工智能技术正在快速发展。', 
            '今天的天气非常好，适合出游。',
            '这款产品的质量令人担忧。',
            '学习编程需要持续的练习和思考。'
        ],
        'image_url': [
            'images/cat1.jpg',
            'images/ai_tech.png',
            'images/sunny_day.jpg',
            'images/product.jpg',
            'images/coding.png'
        ],
        'harmful_img': [0, 0, 0, 1, 0],
        'harmful_text': [0, 0, 0, 1, 0]
    }
    
    df = pd.DataFrame(sample_data)
    df.to_csv('example_data.csv', index=False, encoding='utf-8')
    print("示例数据文件 example_data.csv 已创建")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MLLM Data Processor Pipeline 示例')
    parser.add_argument('--mode', choices=['basic', 'resume', 'web', 'custom', 'excel', 'create-sample'], 
                       default='basic', help='运行模式')
    
    args = parser.parse_args()
    
    if args.mode == 'create-sample':
        create_sample_data()
    elif args.mode == 'basic':
        asyncio.run(example_basic_usage())
    elif args.mode == 'resume':
        asyncio.run(example_resume_from_checkpoint())
    elif args.mode == 'web':
        example_web_interface()
    elif args.mode == 'custom':
        example_custom_step()
    elif args.mode == 'excel':
        asyncio.run(example_with_excel())


if __name__ == "__main__":
    main()