#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM Server - 兼容 OpenAI 的 Chat Completions API 服务

基于 FastAPI 的 HTTP 服务封装，使用 LLMBackend 进行推理。
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import List, Literal, Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field

from .base import ChatMessage, GenerateConfig, ModelConfig, BaseLLMBackend
from .backend import TransformersBackend


# ============== API 响应模型 ==============


class ChatCompletionChoice(BaseModel):
    """响应选项"""
    index: int = 0
    message: ChatMessage
    finish_reason: Optional[str] = "stop"


class UsageInfo(BaseModel):
    """Token 使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    """Chat Completion 响应"""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:8]}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str = ""
    choices: List[ChatCompletionChoice] = Field(default_factory=list)
    usage: UsageInfo = Field(default_factory=UsageInfo)


class DeltaMessage(BaseModel):
    """流式响应的增量消息"""
    role: Optional[str] = None
    content: Optional[str] = None


class ChatCompletionChunkChoice(BaseModel):
    """流式响应选项"""
    index: int = 0
    delta: DeltaMessage
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    """流式响应块"""
    id: str = ""
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str = ""
    choices: List[ChatCompletionChunkChoice] = Field(default_factory=list)


class ChatCompletionRequest(BaseModel):
    """Chat Completion 请求"""
    model: str = Field(..., description="模型名称")
    messages: List[ChatMessage] = Field(..., description="消息列表")
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=0.9, ge=0, le=1)
    max_tokens: Optional[int] = Field(default=512)
    stream: bool = Field(default=False)
    stop: Optional[Union[str, List[str]]] = None


class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    object: Literal["model"] = "model"
    created: int = 0
    owned_by: str = "local"


class ModelsResponse(BaseModel):
    """模型列表响应"""
    object: Literal["list"] = "list"
    data: List[ModelInfo] = Field(default_factory=list)


# ============== Server ==============


class LLMServer:
    """LLM HTTP 服务

    Args:
        backend: LLM 后端实例，默认使用 TransformersBackend
        model: 预加载的模型 ID
        device: 设备类型
        local_dir: 本地模型目录
        dtype: 数据类型 (float16/bfloat16/float32)
        attn: 注意力实现 (eager/sdpa/flash_attention_2)
        model_class: 模型类名
        processor_class: 处理器类名
        vision_processor: 视觉处理器类型 (qwen_vl/general)
        chat_template_kwargs: chat template 额外参数
    """

    def __init__(
        self,
        backend: Optional[BaseLLMBackend] = None,
        model: Optional[str] = None,
        device: Optional[str] = None,
        local_dir: Optional[str] = None,
        dtype: Optional[str] = None,
        attn: Optional[str] = None,
        model_class: Optional[str] = None,
        processor_class: Optional[str] = None,
        vision_processor: Optional[str] = None,
        chat_template_kwargs: Optional[dict] = None,
    ):
        self.backend = backend or TransformersBackend()
        if device:
            self.backend._device = device

        self._preload_model = model
        self._local_dir = local_dir
        self._dtype = dtype
        self._attn = attn
        self._model_class = model_class
        self._processor_class = processor_class
        self._vision_processor = vision_processor
        self._chat_template_kwargs = chat_template_kwargs or {}
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """创建 FastAPI 应用"""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            if self._preload_model:
                try:
                    config = ModelConfig(
                        model_id=self._preload_model,
                        local_dir=self._local_dir,
                        torch_dtype=self._dtype,
                        attn_implementation=self._attn,
                        model_class=self._model_class,
                        processor_class=self._processor_class,
                        vision_processor=self._vision_processor,
                        chat_template_kwargs=self._chat_template_kwargs,
                    )
                    await self.backend.load_model(config)
                except Exception as e:
                    logger.error(f"Failed to load {self._preload_model}: {e}")
                    raise
            yield

        app = FastAPI(
            title="LLM Server",
            description="OpenAI Compatible Chat Completions API",
            version="1.0.0",
            lifespan=lifespan,
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._register_routes(app)
        return app

    def _register_routes(self, app: FastAPI) -> None:
        """注册路由"""

        @app.get("/health")
        async def health():
            return {"status": "ok", "model": self.backend.model_id}

        @app.get("/v1/models", response_model=ModelsResponse)
        async def list_models():
            models = []
            if self.backend.model_id:
                models.append(ModelInfo(id=self.backend.model_id, created=int(time.time())))
            return ModelsResponse(data=models)

        @app.post("/v1/chat/completions")
        async def chat_completions(request: ChatCompletionRequest):
            return await self._handle_chat(request)

    async def _handle_chat(self, request: ChatCompletionRequest):
        """处理 chat 请求"""
        if not self.backend.is_loaded:
            raise HTTPException(status_code=503, detail="Model not loaded")

        stop = request.stop if isinstance(request.stop, list) else (
            [request.stop] if request.stop else None
        )

        gen_config = GenerateConfig(
            max_tokens=request.max_tokens or 512,
            temperature=request.temperature,
            top_p=request.top_p,
            stop=stop,
        )

        try:
            if request.stream:
                return await self._stream_response(request, gen_config)
            else:
                return await self._normal_response(request, gen_config)
        except Exception as e:
            logger.exception(f"Chat error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _normal_response(
        self, request: ChatCompletionRequest, config: GenerateConfig
    ) -> ChatCompletionResponse:
        """普通响应"""
        text, prompt_tokens, completion_tokens = await self.backend.generate(
            messages=request.messages,
            config=config,
        )

        return ChatCompletionResponse(
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    message=ChatMessage(role="assistant", content=text),
                    finish_reason="stop",
                )
            ],
            usage=UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    async def _stream_response(
        self, request: ChatCompletionRequest, config: GenerateConfig
    ) -> StreamingResponse:
        """流式响应"""
        response_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"

        async def generate():
            # 发送角色
            chunk = ChatCompletionChunk(
                id=response_id,
                model=request.model,
                choices=[
                    ChatCompletionChunkChoice(
                        delta=DeltaMessage(role="assistant"),
                    )
                ],
            )
            yield f"data: {chunk.model_dump_json()}\n\n"

            # 流式内容
            async for text in self.backend.generate_stream(
                messages=request.messages,
                config=config,
            ):
                chunk = ChatCompletionChunk(
                    id=response_id,
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            delta=DeltaMessage(content=text),
                        )
                    ],
                )
                yield f"data: {chunk.model_dump_json()}\n\n"

            # 结束标记
            chunk = ChatCompletionChunk(
                id=response_id,
                model=request.model,
                choices=[
                    ChatCompletionChunkChoice(
                        delta=DeltaMessage(),
                        finish_reason="stop",
                    )
                ],
            )
            yield f"data: {chunk.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
        )

    def run(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        workers: int = 1,
        **kwargs,
    ) -> None:
        """运行服务"""
        import uvicorn

        uvicorn.run(
            self.app,
            host=host,
            port=port,
            workers=workers,
            **kwargs,
        )


def create_server(
    model: Optional[str] = None,
    device: Optional[str] = None,
    local_dir: Optional[str] = None,
    backend: Optional[BaseLLMBackend] = None,
    dtype: Optional[str] = None,
    attn: Optional[str] = None,
    model_class: Optional[str] = None,
    processor_class: Optional[str] = None,
    vision_processor: Optional[str] = None,
    chat_template_kwargs: Optional[dict] = None,
) -> LLMServer:
    """创建 LLM 服务实例

    Args:
        model: 模型 ID
        device: 设备类型
        local_dir: 本地模型目录
        backend: 自定义后端实例
        dtype: 数据类型 (float16/bfloat16/float32)
        attn: 注意力实现 (eager/sdpa/flash_attention_2)
        model_class: 模型类名 (如 "AutoModelForCausalLM")
        processor_class: 处理器类名 (如 "AutoTokenizer")
        vision_processor: 视觉处理器类型 (qwen_vl/general)
        chat_template_kwargs: chat template 额外参数

    Returns:
        LLMServer 实例
    """
    return LLMServer(
        backend=backend,
        model=model,
        device=device,
        local_dir=local_dir,
        dtype=dtype,
        attn=attn,
        model_class=model_class,
        processor_class=processor_class,
        vision_processor=vision_processor,
        chat_template_kwargs=chat_template_kwargs,
    )
