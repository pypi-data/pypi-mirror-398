#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM Backend 抽象基类

提供可扩展的 LLM 后端接口，用户可以继承并实现自己的后端。

使用示例:
    ```python
    from maque.llm import BaseLLMBackend, ModelConfig

    class MyCustomBackend(BaseLLMBackend):
        def _load_model_impl(self, config: ModelConfig) -> None:
            # 自定义模型加载逻辑
            pass

        def _generate_impl(self, messages, **kwargs) -> tuple[str, int, int]:
            # 自定义生成逻辑
            pass

        def _generate_stream_impl(self, messages, **kwargs):
            # 自定义流式生成
            yield "token"
    ```
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, List, Literal, Optional, Union

from pydantic import BaseModel, Field


# ============== 数据模型 ==============


@dataclass
class ModelConfig:
    """模型配置

    Attributes:
        model_id: 模型名称或路径
        device: 设备类型，None 表示自动检测
        torch_dtype: 数据类型，None 表示自动选择
        trust_remote_code: 是否信任远程代码
        local_dir: 本地模型目录
        attn_implementation: 注意力实现 (eager/sdpa/flash_attention_2)
        model_class: 模型类名 (如 "AutoModelForCausalLM", "Qwen3VLForConditionalGeneration")
        processor_class: 处理器类名 (如 "AutoTokenizer", "AutoProcessor")
        chat_template_kwargs: apply_chat_template 的额外参数 (如 {"enable_thinking": True})
        vision_processor: 视觉处理器类型 ("qwen_vl", "general", None)
        extra: 其他扩展配置
    """
    model_id: str
    device: Optional[str] = None  # None = auto
    torch_dtype: Optional[str] = None  # None = auto
    trust_remote_code: bool = True
    local_dir: Optional[str] = None
    attn_implementation: Optional[str] = None  # eager/sdpa/flash_attention_2
    # 新增：模型类配置
    model_class: Optional[str] = None  # None = 自动检测
    processor_class: Optional[str] = None  # None = 自动选择
    # 新增：chat template 额外参数
    chat_template_kwargs: dict = field(default_factory=dict)
    # 新增：视觉处理器类型
    vision_processor: Optional[str] = None  # "qwen_vl", "general", None
    # 扩展配置
    extra: dict = field(default_factory=dict)


class ImageURL(BaseModel):
    """图片 URL"""
    url: str = Field(..., description="图片 URL 或 base64")
    detail: Optional[str] = None


class ContentPart(BaseModel):
    """消息内容部分"""
    type: Literal["text", "image_url"]
    text: Optional[str] = None
    image_url: Optional[ImageURL] = None


class ChatMessage(BaseModel):
    """聊天消息"""
    role: Literal["system", "user", "assistant"]
    content: Union[str, List[ContentPart]] = Field(..., description="消息内容")


@dataclass
class GenerateConfig:
    """生成配置"""
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    stop: Optional[List[str]] = None
    # 扩展配置
    extra: dict = field(default_factory=dict)


# ============== 抽象基类 ==============


class BaseLLMBackend(ABC):
    """LLM 后端抽象基类

    子类需要实现以下方法:
    - _load_model_impl: 加载模型
    - _generate_impl: 同步生成
    - _generate_stream_impl: 流式生成 (可选，默认基于 _generate_impl)

    可选覆盖的方法:
    - _detect_multimodal: 检测是否多模态模型
    - _process_messages: 预处理消息
    - _process_image: 处理图片输入
    """

    def __init__(self):
        self._model = None
        self._config: Optional[ModelConfig] = None
        self._device: Optional[str] = None
        self._is_multimodal: bool = False
        self._vision_processor: Optional[str] = None  # "qwen_vl", "general", None
        self._lock = asyncio.Lock()

    # ============== 属性 ==============

    @property
    def device(self) -> str:
        """获取设备类型"""
        if self._device is None:
            self._device = self._detect_device()
        return self._device

    @property
    def is_multimodal(self) -> bool:
        """是否多模态模型"""
        return self._is_multimodal

    @property
    def model_id(self) -> Optional[str]:
        """当前模型 ID"""
        return self._config.model_id if self._config else None

    @property
    def is_loaded(self) -> bool:
        """模型是否已加载"""
        return self._model is not None

    # ============== 公共接口 ==============

    async def load_model(self, config: ModelConfig) -> None:
        """加载模型 (异步)"""
        async with self._lock:
            if self._model is not None:
                return

            from loguru import logger
            logger.info(f"Loading model: {config.model_id} on {self.device}")

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model_sync, config)

            self._config = config
            logger.info(f"Model loaded: {config.model_id} (multimodal={self._is_multimodal})")

    def load_model_sync(self, config: ModelConfig) -> None:
        """加载模型 (同步)"""
        if self._model is not None:
            return

        from loguru import logger
        logger.info(f"Loading model: {config.model_id} on {self.device}")

        self._load_model_sync(config)
        self._config = config
        logger.info(f"Model loaded: {config.model_id} (multimodal={self._is_multimodal})")

    async def generate(
        self,
        messages: List[ChatMessage],
        config: Optional[GenerateConfig] = None,
    ) -> tuple[str, int, int]:
        """生成响应 (异步)

        Returns:
            tuple: (生成文本, prompt_tokens, completion_tokens)
        """
        config = config or GenerateConfig()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._generate_sync, messages, config
        )

    def generate_sync(
        self,
        messages: List[ChatMessage],
        config: Optional[GenerateConfig] = None,
    ) -> tuple[str, int, int]:
        """生成响应 (同步)"""
        config = config or GenerateConfig()
        return self._generate_sync(messages, config)

    async def generate_stream(
        self,
        messages: List[ChatMessage],
        config: Optional[GenerateConfig] = None,
    ) -> AsyncGenerator[str, None]:
        """流式生成 (异步)"""
        config = config or GenerateConfig()

        # 默认实现：在线程中运行同步流式生成
        import queue
        import threading

        q = queue.Queue()
        stop_event = threading.Event()

        def producer():
            try:
                for token in self._generate_stream_sync(messages, config):
                    if stop_event.is_set():
                        break
                    q.put(token)
            except Exception as e:
                q.put(e)
            finally:
                q.put(None)  # 结束标记

        thread = threading.Thread(target=producer)
        thread.start()

        try:
            while True:
                # 非阻塞获取
                await asyncio.sleep(0.01)
                while not q.empty():
                    item = q.get_nowait()
                    if item is None:
                        return
                    if isinstance(item, Exception):
                        raise item
                    yield item
        finally:
            stop_event.set()
            thread.join(timeout=1)

    # ============== 内部同步方法 ==============

    def _load_model_sync(self, config: ModelConfig) -> None:
        """同步加载模型包装器"""
        # 解析模型路径
        model_path = self._resolve_model_path(config)

        # 检测是否多模态
        self._is_multimodal = self._detect_multimodal(model_path, config)

        # 设置视觉处理器类型
        if config.vision_processor:
            self._vision_processor = config.vision_processor
        elif self._is_multimodal:
            # 默认使用 qwen_vl（向后兼容）
            self._vision_processor = "qwen_vl"

        # 设置设备
        if config.device:
            self._device = config.device

        # 调用子类实现
        self._load_model_impl(model_path, config)

    def _generate_sync(
        self, messages: List[ChatMessage], config: GenerateConfig
    ) -> tuple[str, int, int]:
        """同步生成包装器"""
        # 预处理消息
        processed = self._process_messages(messages)

        # 调用子类实现
        return self._generate_impl(processed, config)

    def _generate_stream_sync(
        self, messages: List[ChatMessage], config: GenerateConfig
    ):
        """同步流式生成包装器"""
        processed = self._process_messages(messages)
        yield from self._generate_stream_impl(processed, config)

    # ============== 可覆盖的辅助方法 ==============

    def _detect_device(self) -> str:
        """检测设备类型，子类可覆盖

        检测顺序: CUDA > MPS (Apple Silicon) > CPU
        """
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        except ImportError:
            return "cpu"

    def _resolve_model_path(self, config: ModelConfig) -> str:
        """解析模型路径，子类可覆盖"""
        from pathlib import Path

        model_path = config.model_id
        if config.local_dir:
            local_path = Path(config.local_dir) / config.model_id.split("/")[-1]
            if local_path.exists():
                model_path = str(local_path)
                from loguru import logger
                logger.info(f"Using local model path: {model_path}")
        return model_path

    def _detect_multimodal(self, model_path: str, config: ModelConfig) -> bool:
        """检测是否多模态模型，子类可覆盖"""
        try:
            from transformers import AutoConfig
            model_config = AutoConfig.from_pretrained(
                model_path, trust_remote_code=config.trust_remote_code
            )
            architectures = getattr(model_config, "architectures", []) or []
            return any(
                "VL" in arch or "Vision" in arch or "vision" in arch.lower()
                for arch in architectures
            )
        except Exception:
            return False

    def _process_messages(self, messages: List[ChatMessage]) -> List[ChatMessage]:
        """预处理消息，子类可覆盖进行自定义处理"""
        return messages

    def _process_image(self, image_url: str) -> "Image":
        """处理图片输入，子类可覆盖

        Args:
            image_url: 图片 URL，支持 base64、http/https、本地路径

        Returns:
            PIL.Image 对象
        """
        import base64
        from io import BytesIO
        from PIL import Image

        if image_url.startswith("data:"):
            # base64 图片
            header, data = image_url.split(",", 1)
            image_data = base64.b64decode(data)
            return Image.open(BytesIO(image_data))
        elif image_url.startswith(("http://", "https://")):
            # URL 图片
            import requests
            response = requests.get(image_url, timeout=30)
            return Image.open(BytesIO(response.content))
        else:
            # 本地文件
            return Image.open(image_url)

    # ============== 抽象方法 (子类必须实现) ==============

    @abstractmethod
    def _load_model_impl(self, model_path: str, config: ModelConfig) -> None:
        """加载模型实现

        Args:
            model_path: 解析后的模型路径
            config: 模型配置

        子类需要:
        1. 加载模型到 self._model
        2. 加载 tokenizer/processor 到相应属性
        """
        pass

    @abstractmethod
    def _generate_impl(
        self, messages: List[ChatMessage], config: GenerateConfig
    ) -> tuple[str, int, int]:
        """生成实现

        Args:
            messages: 预处理后的消息列表
            config: 生成配置

        Returns:
            tuple: (生成文本, prompt_tokens, completion_tokens)
        """
        pass

    def _generate_stream_impl(
        self, messages: List[ChatMessage], config: GenerateConfig
    ):
        """流式生成实现

        默认实现调用 _generate_impl 并一次性返回。
        子类可覆盖以实现真正的流式输出。

        Yields:
            str: 生成的 token
        """
        text, _, _ = self._generate_impl(messages, config)
        yield text
