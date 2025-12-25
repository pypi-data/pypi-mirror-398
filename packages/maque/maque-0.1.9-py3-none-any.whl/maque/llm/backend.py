#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transformers 后端实现

基于 HuggingFace Transformers 的 LLM/MLLM 后端。
支持通过配置动态选择模型类和处理器类。
"""

from typing import List, Optional, Type

from .base import BaseLLMBackend, ChatMessage, GenerateConfig, ModelConfig


def _get_model_class(class_name: str) -> Type:
    """动态获取模型类

    Args:
        class_name: 类名，如 "AutoModelForCausalLM", "Qwen3VLForConditionalGeneration"

    Returns:
        模型类
    """
    import transformers

    # 首先尝试从 transformers 直接获取
    if hasattr(transformers, class_name):
        return getattr(transformers, class_name)

    # 尝试从 transformers.models 的子模块获取
    # 例如 HunYuanVLForConditionalGeneration
    for module_name in dir(transformers.models):
        try:
            module = getattr(transformers.models, module_name)
            if hasattr(module, class_name):
                return getattr(module, class_name)
        except Exception:
            continue

    raise ValueError(f"无法找到模型类: {class_name}")


def _get_processor_class(class_name: str) -> Type:
    """动态获取处理器类

    Args:
        class_name: 类名，如 "AutoTokenizer", "AutoProcessor"

    Returns:
        处理器类
    """
    import transformers

    if hasattr(transformers, class_name):
        return getattr(transformers, class_name)

    raise ValueError(f"无法找到处理器类: {class_name}")


class TransformersBackend(BaseLLMBackend):
    """基于 Transformers 的 LLM 后端

    支持:
    - 纯文本 LLM (AutoModelForCausalLM)
    - 多模态 VL 模型 (AutoModelForVision2Seq 或其他)
    - 流式输出 (TextIteratorStreamer)
    - 动态模型类和处理器类配置

    配置示例:
        # 使用 HunyuanOCR
        config = ModelConfig(
            model_id="tencent/HunyuanOCR",
            model_class="HunYuanVLForConditionalGeneration",
            processor_class="AutoProcessor",
            vision_processor="general",
        )

        # 使用 Qwen3 带 thinking
        config = ModelConfig(
            model_id="Qwen/Qwen3-0.6B",
            chat_template_kwargs={"enable_thinking": True},
        )
    """

    def __init__(self):
        super().__init__()
        self._tokenizer = None
        self._processor = None  # 多模态用

    # ============== 实现抽象方法 ==============

    def _load_model_impl(self, model_path: str, config: ModelConfig) -> None:
        """加载 Transformers 模型"""
        import torch

        # 确定 dtype
        if config.torch_dtype:
            torch_dtype = getattr(torch, config.torch_dtype, torch.float16)
        else:
            # 自动选择最佳 dtype
            # CUDA: 优先 bfloat16 > float16
            # MPS/CPU: 使用 float32 (更稳定)
            if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
                torch_dtype = torch.bfloat16
            elif torch.cuda.is_available():
                torch_dtype = torch.float16
            else:
                # MPS 和 CPU 使用 float32 更稳定
                torch_dtype = torch.float32

        if self._is_multimodal:
            self._load_multimodal_model(model_path, config, torch_dtype)
        else:
            self._load_text_model(model_path, config, torch_dtype)

    def _generate_impl(
        self, messages: List[ChatMessage], config: GenerateConfig
    ) -> tuple[str, int, int]:
        """Transformers 生成实现"""
        import torch

        # 构建输入
        if self._is_multimodal:
            inputs = self._build_multimodal_inputs(messages)
        else:
            inputs = self._build_text_inputs(messages)

        prompt_tokens = inputs["input_ids"].shape[1]

        # 生成参数
        gen_kwargs = {
            "max_new_tokens": config.max_tokens,
            "temperature": config.temperature if config.temperature > 0 else 1.0,
            "top_p": config.top_p,
            "do_sample": config.temperature > 0,
            "pad_token_id": self._get_pad_token_id(),
        }

        with torch.no_grad():
            outputs = self._model.generate(**inputs, **gen_kwargs)

        # 解码
        new_tokens = outputs[0][prompt_tokens:]
        completion_tokens = len(new_tokens)

        if self._is_multimodal:
            text = self._processor.decode(new_tokens, skip_special_tokens=True)
        else:
            text = self._tokenizer.decode(new_tokens, skip_special_tokens=True)

        return text, prompt_tokens, completion_tokens

    def _generate_stream_impl(
        self, messages: List[ChatMessage], config: GenerateConfig
    ):
        """Transformers 流式生成实现"""
        from threading import Thread
        from transformers import TextIteratorStreamer

        # 构建输入
        if self._is_multimodal:
            inputs = self._build_multimodal_inputs(messages)
            tokenizer = self._processor.tokenizer
        else:
            inputs = self._build_text_inputs(messages)
            tokenizer = self._tokenizer

        # 创建 streamer
        streamer = TextIteratorStreamer(
            tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )

        gen_kwargs = {
            **inputs,
            "max_new_tokens": config.max_tokens,
            "temperature": config.temperature if config.temperature > 0 else 1.0,
            "top_p": config.top_p,
            "do_sample": config.temperature > 0,
            "pad_token_id": self._get_pad_token_id(),
            "streamer": streamer,
        }

        # 在线程中运行生成
        thread = Thread(target=self._model.generate, kwargs=gen_kwargs)
        thread.start()

        # 流式输出
        for text in streamer:
            yield text

        thread.join()

    # ============== 内部方法 ==============

    def _load_text_model(self, model_path: str, config: ModelConfig, torch_dtype) -> None:
        """加载纯文本模型"""
        from transformers import AutoModelForCausalLM, AutoTokenizer

        # 确定处理器类
        processor_class_name = config.processor_class or "AutoTokenizer"
        ProcessorClass = _get_processor_class(processor_class_name)

        self._tokenizer = ProcessorClass.from_pretrained(
            model_path, trust_remote_code=config.trust_remote_code
        )

        # 确定模型类
        model_class_name = config.model_class or "AutoModelForCausalLM"
        ModelClass = _get_model_class(model_class_name)

        model_kwargs = {
            "torch_dtype": torch_dtype,
            "device_map": self._device,
            "trust_remote_code": config.trust_remote_code,
        }
        if config.attn_implementation:
            model_kwargs["attn_implementation"] = config.attn_implementation

        self._model = ModelClass.from_pretrained(model_path, **model_kwargs)
        self._model.eval()

    def _load_multimodal_model(self, model_path: str, config: ModelConfig, torch_dtype) -> None:
        """加载多模态模型"""
        from transformers import AutoProcessor, AutoModelForVision2Seq

        # 确定处理器类
        processor_class_name = config.processor_class or "AutoProcessor"
        ProcessorClass = _get_processor_class(processor_class_name)

        processor_kwargs = {"trust_remote_code": config.trust_remote_code}
        # HunyuanOCR 需要 use_fast=False
        if "hunyuan" in model_path.lower():
            processor_kwargs["use_fast"] = False

        self._processor = ProcessorClass.from_pretrained(model_path, **processor_kwargs)

        # 确定模型类
        model_class_name = config.model_class or "AutoModelForVision2Seq"
        ModelClass = _get_model_class(model_class_name)

        model_kwargs = {
            "torch_dtype": torch_dtype,
            "device_map": self._device,
            "trust_remote_code": config.trust_remote_code,
        }
        if config.attn_implementation:
            model_kwargs["attn_implementation"] = config.attn_implementation

        self._model = ModelClass.from_pretrained(model_path, **model_kwargs)
        self._model.eval()

    def _build_text_inputs(self, messages: List[ChatMessage]):
        """构建纯文本输入"""
        # 转换为标准格式
        formatted = []
        for msg in messages:
            content = msg.content if isinstance(msg.content, str) else " ".join(
                p.text for p in msg.content if p.type == "text" and p.text
            )
            formatted.append({"role": msg.role, "content": content})

        # 获取 chat_template_kwargs
        chat_kwargs = {"tokenize": False, "add_generation_prompt": True}
        if self._config and self._config.chat_template_kwargs:
            chat_kwargs.update(self._config.chat_template_kwargs)

        text = self._tokenizer.apply_chat_template(formatted, **chat_kwargs)
        inputs = self._tokenizer(text, return_tensors="pt")
        return inputs.to(self._device)

    def _build_multimodal_inputs(self, messages: List[ChatMessage]):
        """构建多模态输入

        根据 vision_processor 配置选择不同的处理方式：
        - qwen_vl: 使用 qwen_vl_utils.process_vision_info (Qwen-VL 系列)
        - general: 通用处理方式 (HunyuanOCR, dots.ocr 等)
        """
        if self._vision_processor == "qwen_vl":
            return self._build_qwen_vl_inputs(messages)
        else:
            return self._build_general_vl_inputs(messages)

    def _build_qwen_vl_inputs(self, messages: List[ChatMessage]):
        """构建 Qwen-VL 风格的输入"""
        from qwen_vl_utils import process_vision_info

        # 转换为 Qwen-VL 格式
        qwen_messages = []
        for msg in messages:
            if isinstance(msg.content, str):
                qwen_messages.append({"role": msg.role, "content": msg.content})
            else:
                content_parts = []
                for part in msg.content:
                    if part.type == "text":
                        content_parts.append({"type": "text", "text": part.text})
                    elif part.type == "image_url" and part.image_url:
                        image_url = part.image_url.url
                        if image_url.startswith("data:"):
                            image = self._process_image(image_url)
                            content_parts.append({"type": "image", "image": image})
                        else:
                            content_parts.append({"type": "image", "image": image_url})
                qwen_messages.append({"role": msg.role, "content": content_parts})

        # 获取 chat_template_kwargs
        chat_kwargs = {"tokenize": False, "add_generation_prompt": True}
        if self._config and self._config.chat_template_kwargs:
            chat_kwargs.update(self._config.chat_template_kwargs)

        # 使用 processor 处理
        text = self._processor.apply_chat_template(qwen_messages, **chat_kwargs)
        image_inputs, video_inputs = process_vision_info(qwen_messages)

        inputs = self._processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        return inputs.to(self._device)

    def _build_general_vl_inputs(self, messages: List[ChatMessage]):
        """构建通用多模态输入 (适用于大多数 VL 模型)"""
        # 提取图片和文本
        images = []
        formatted_messages = []

        for msg in messages:
            if isinstance(msg.content, str):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                content_parts = []
                for part in msg.content:
                    if part.type == "text" and part.text:
                        content_parts.append({"type": "text", "text": part.text})
                    elif part.type == "image_url" and part.image_url:
                        image = self._process_image(part.image_url.url)
                        images.append(image)
                        content_parts.append({"type": "image"})

                formatted_messages.append({"role": msg.role, "content": content_parts})

        # 获取 chat_template_kwargs
        chat_kwargs = {"tokenize": False, "add_generation_prompt": True}
        if self._config and self._config.chat_template_kwargs:
            chat_kwargs.update(self._config.chat_template_kwargs)

        # 应用 chat template
        text = self._processor.apply_chat_template(formatted_messages, **chat_kwargs)

        # 处理输入
        if images:
            inputs = self._processor(
                text=[text],
                images=images,
                padding=True,
                return_tensors="pt",
            )
        else:
            inputs = self._processor(
                text=[text],
                padding=True,
                return_tensors="pt",
            )

        return inputs.to(self._device)

    def _get_pad_token_id(self) -> int:
        """获取 pad token id"""
        if self._is_multimodal:
            tokenizer = self._processor.tokenizer
        else:
            tokenizer = self._tokenizer

        if tokenizer.pad_token_id is not None:
            return tokenizer.pad_token_id
        return tokenizer.eos_token_id


# 默认后端别名
LLMBackend = TransformersBackend
