#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM 模块 - 提供 LLM/MLLM 推理服务

模块结构:
- base: 抽象基类 BaseLLMBackend，可继承实现自定义后端
- backend: Transformers 后端实现
- server: FastAPI HTTP 服务

使用示例:

1. 启动服务 (CLI):
    ```bash
    # 标准 LLM
    maque llm serve Qwen/Qwen2.5-7B-Instruct

    # 多模态 VL 模型
    maque llm serve Qwen/Qwen2.5-VL-3B-Instruct --port=8001

    # 自定义模型类 (如 HunyuanOCR)
    maque llm serve tencent/HunyuanOCR \\
        --model_class=HunYuanVLForConditionalGeneration \\
        --vision_processor=general

    # Qwen3 带 thinking 模式
    maque llm serve Qwen/Qwen3-0.6B --enable_thinking
    ```

2. 编程方式启动:
    ```python
    from maque.llm import create_server, ModelConfig

    # 简单启动
    server = create_server(model="Qwen/Qwen2.5-7B-Instruct")
    server.run(port=8000)

    # 带自定义配置
    server = create_server(
        model="tencent/HunyuanOCR",
        model_class="HunYuanVLForConditionalGeneration",
        vision_processor="general",
        chat_template_kwargs={"enable_thinking": True},
    )
    ```

3. 自定义后端:
    ```python
    from maque.llm import BaseLLMBackend, ModelConfig, GenerateConfig

    class MyBackend(BaseLLMBackend):
        def _load_model_impl(self, model_path, config):
            # 自定义加载逻辑
            pass

        def _generate_impl(self, messages, config):
            # 自定义生成逻辑
            return "response", 10, 20

    # 使用自定义后端
    from maque.llm import LLMServer
    server = LLMServer(backend=MyBackend(), model="my-model")
    server.run()
    ```

ModelConfig 配置说明:
- model_id: 模型名称或路径
- model_class: 模型类名 (如 "AutoModelForCausalLM", "HunYuanVLForConditionalGeneration")
- processor_class: 处理器类名 (如 "AutoTokenizer", "AutoProcessor")
- vision_processor: 视觉处理器类型 ("qwen_vl" 或 "general")
- chat_template_kwargs: chat template 额外参数 (如 {"enable_thinking": True})
"""

# 基类和数据模型
from .base import (
    BaseLLMBackend,
    ModelConfig,
    GenerateConfig,
    ChatMessage,
    ContentPart,
    ImageURL,
)

# 后端实现
from .backend import TransformersBackend, LLMBackend

# 服务端 (延迟导入，避免强依赖 fastapi)
def __getattr__(name):
    if name in ("LLMServer", "create_server"):
        from .server import LLMServer, create_server
        return {"LLMServer": LLMServer, "create_server": create_server}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # 基类
    "BaseLLMBackend",
    # 数据模型
    "ModelConfig",
    "GenerateConfig",
    "ChatMessage",
    "ContentPart",
    "ImageURL",
    # 后端
    "TransformersBackend",
    "LLMBackend",  # 别名
    # 服务端
    "LLMServer",
    "create_server",
]
