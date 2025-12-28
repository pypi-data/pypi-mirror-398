#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Embedding Server - 兼容 OpenAI/vLLM 的 Embedding API 服务

支持:
- jina-embeddings-v3 的 task 类型
- 多模型动态加载
- 批处理优化
- GPU/CPU 自动检测
"""

import asyncio
import base64
import struct
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Union

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger

if TYPE_CHECKING:
    from pathlib import Path
    from sentence_transformers import SentenceTransformer


# ============== Pydantic Models (OpenAI Compatible) ==============


class TaskType(str, Enum):
    """jina-embeddings-v3 支持的任务类型"""

    TEXT_MATCHING = "text-matching"
    RETRIEVAL_QUERY = "retrieval.query"
    RETRIEVAL_PASSAGE = "retrieval.passage"
    CLASSIFICATION = "classification"
    SEPARATION = "separation"


class EmbeddingRequest(BaseModel):
    """Embedding 请求 - 兼容 OpenAI 格式 + 扩展字段"""

    model: str = Field(..., description="模型名称")
    input: Union[str, List[str]] = Field(..., description="输入文本")
    encoding_format: Literal["float", "base64"] = Field(
        default="float", description="输出格式"
    )
    dimensions: Optional[int] = Field(
        default=None, description="输出维度 (Matryoshka)"
    )
    # 扩展字段
    task: Optional[TaskType] = Field(
        default=None, description="任务类型 (jina-v3)"
    )
    user: Optional[str] = Field(default=None, description="用户标识")


class EmbeddingObject(BaseModel):
    """单个 Embedding 结果"""

    object: Literal["embedding"] = "embedding"
    embedding: Union[List[float], str] = Field(..., description="向量或 base64")
    index: int = Field(..., description="索引")


class UsageInfo(BaseModel):
    """Token 使用统计"""

    prompt_tokens: int = 0
    total_tokens: int = 0


class EmbeddingResponse(BaseModel):
    """Embedding 响应 - 兼容 OpenAI 格式"""

    object: Literal["list"] = "list"
    data: List[EmbeddingObject] = Field(default_factory=list)
    model: str = ""
    usage: UsageInfo = Field(default_factory=UsageInfo)


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


# ============== Model Backend ==============


@dataclass
class ModelConfig:
    """模型配置"""

    model_id: str
    trust_remote_code: bool = True
    device: Optional[str] = None  # None = auto
    default_task: Optional[str] = None
    default_dimensions: Optional[int] = None
    local_dir: Optional[str] = None  # 本地模型目录
    torch_dtype: Optional[str] = None  # float16/bfloat16/float32
    attn_implementation: Optional[str] = None  # eager/sdpa/flash_attention_2


class EmbeddingBackend:
    """Embedding 模型后端 - 使用 SentenceTransformers"""

    def __init__(self):
        self._models: Dict[str, "SentenceTransformer"] = {}
        self._configs: Dict[str, ModelConfig] = {}
        self._device: Optional[str] = None
        self._lock = asyncio.Lock()

    @property
    def device(self) -> str:
        """检测设备类型: CUDA > MPS (Apple Silicon) > CPU"""
        if self._device is None:
            try:
                import torch

                if torch.cuda.is_available():
                    self._device = "cuda"
                elif torch.backends.mps.is_available():
                    self._device = "mps"
                else:
                    self._device = "cpu"
            except ImportError:
                self._device = "cpu"
        return self._device

    def _get_model_key(self, model_id: str) -> str:
        """标准化模型 key"""
        return model_id.lower().replace("/", "_")

    async def load_model(self, config: ModelConfig) -> None:
        """加载模型"""
        key = self._get_model_key(config.model_id)

        async with self._lock:
            if key in self._models:
                return

            logger.info(f"Loading model: {config.model_id} on {self.device}")

            # 在线程池中加载模型
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(
                None, self._load_model_sync, config
            )

            self._models[key] = model
            self._configs[key] = config
            logger.info(f"Model loaded: {config.model_id}")

    def _load_model_sync(self, config: ModelConfig) -> "SentenceTransformer":
        """同步加载模型"""
        from pathlib import Path
        from sentence_transformers import SentenceTransformer

        device = config.device or self.device
        model_path = config.model_id

        # 如果指定了本地目录，直接使用本地路径
        if config.local_dir:
            local_path = Path(config.local_dir) / config.model_id.split("/")[-1]
            if local_path.exists():
                model_path = str(local_path)
                logger.info(f"Using local model path: {model_path}")

        # 构建 model_kwargs
        model_kwargs = {}
        if config.torch_dtype:
            import torch
            torch_dtype = getattr(torch, config.torch_dtype, None)
            if torch_dtype:
                model_kwargs["torch_dtype"] = torch_dtype
                logger.info(f"Using dtype: {config.torch_dtype}")
        if config.attn_implementation:
            model_kwargs["attn_implementation"] = config.attn_implementation
            logger.info(f"Using attn: {config.attn_implementation}")

        return SentenceTransformer(
            model_path,
            trust_remote_code=config.trust_remote_code,
            device=device,
            model_kwargs=model_kwargs if model_kwargs else None,
        )

    def get_model(self, model_id: str) -> Optional["SentenceTransformer"]:
        """获取已加载的模型"""
        key = self._get_model_key(model_id)
        return self._models.get(key)

    def get_config(self, model_id: str) -> Optional[ModelConfig]:
        """获取模型配置"""
        key = self._get_model_key(model_id)
        return self._configs.get(key)

    def list_models(self) -> List[str]:
        """列出已加载的模型"""
        return [cfg.model_id for cfg in self._configs.values()]

    async def encode(
        self,
        model_id: str,
        texts: List[str],
        task: Optional[str] = None,
        dimensions: Optional[int] = None,
    ) -> np.ndarray:
        """编码文本"""
        model = self.get_model(model_id)
        if model is None:
            raise ValueError(f"Model not loaded: {model_id}")

        config = self.get_config(model_id)
        task = task or (config.default_task if config else None)
        dimensions = dimensions or (config.default_dimensions if config else None)

        # 构建 encode 参数
        encode_kwargs = {}
        if task:
            encode_kwargs["task"] = task
            encode_kwargs["prompt_name"] = task
        if dimensions:
            encode_kwargs["truncate_dim"] = dimensions

        # 在线程池中执行编码
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                **encode_kwargs,
            ),
        )

        return embeddings

    def unload_model(self, model_id: str) -> bool:
        """卸载模型"""
        key = self._get_model_key(model_id)
        if key in self._models:
            del self._models[key]
            del self._configs[key]
            return True
        return False


# ============== Server ==============


class EmbeddingServer:
    """Embedding 服务"""

    def __init__(
        self,
        models: Optional[List[str]] = None,
        default_model: Optional[str] = None,
        device: Optional[str] = None,
        local_dir: Optional[str] = None,
        dtype: Optional[str] = None,
        attn: Optional[str] = None,
    ):
        """
        初始化服务

        Args:
            models: 预加载的模型列表
            default_model: 默认模型
            device: 设备 (cuda/cpu/auto)
            local_dir: 本地模型目录
            dtype: 数据类型 (float16/bfloat16/float32)
            attn: 注意力实现 (eager/sdpa/flash_attention_2)
        """
        self.backend = EmbeddingBackend()
        if device:
            self.backend._device = device

        self._preload_models = models or []
        self._default_model = default_model
        self._local_dir = local_dir
        self._dtype = dtype
        self._attn = attn
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """创建 FastAPI 应用"""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # 启动时预加载模型
            for model_id in self._preload_models:
                try:
                    config = ModelConfig(
                        model_id=model_id,
                        local_dir=self._local_dir,
                        torch_dtype=self._dtype,
                        attn_implementation=self._attn,
                    )
                    await self.backend.load_model(config)
                except Exception as e:
                    logger.error(f"Failed to load {model_id}: {e}")

            if not self._default_model and self._preload_models:
                self._default_model = self._preload_models[0]

            yield
            # 关闭时清理

        app = FastAPI(
            title="Embedding Server",
            description="OpenAI Compatible Embedding API with Task Support",
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
            return {"status": "ok"}

        @app.get("/v1/models", response_model=ModelsResponse)
        async def list_models():
            models = self.backend.list_models()
            return ModelsResponse(
                data=[
                    ModelInfo(id=m, created=int(time.time()))
                    for m in models
                ]
            )

        @app.post("/v1/embeddings", response_model=EmbeddingResponse)
        async def create_embeddings(request: EmbeddingRequest):
            return await self._handle_embedding(request)

        # 兼容 vLLM 的路由
        @app.post("/embeddings", response_model=EmbeddingResponse)
        async def create_embeddings_alt(request: EmbeddingRequest):
            return await self._handle_embedding(request)

    async def _handle_embedding(
        self, request: EmbeddingRequest
    ) -> EmbeddingResponse:
        """处理 embedding 请求"""
        # 确定模型
        model_id = request.model
        if not self.backend.get_model(model_id):
            # 尝试自动加载
            try:
                await self.backend.load_model(ModelConfig(model_id=model_id))
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Failed to load model: {e}"
                )

        # 准备输入
        texts = request.input if isinstance(request.input, list) else [request.input]

        # 获取任务类型
        task = request.task.value if request.task else None

        try:
            # 编码
            embeddings = await self.backend.encode(
                model_id=model_id,
                texts=texts,
                task=task,
                dimensions=request.dimensions,
            )

            # 构建响应
            data = []
            for i, emb in enumerate(embeddings):
                if request.encoding_format == "base64":
                    # 转换为 base64
                    emb_bytes = struct.pack(f"{len(emb)}f", *emb.tolist())
                    emb_value = base64.b64encode(emb_bytes).decode("utf-8")
                else:
                    emb_value = emb.tolist()

                data.append(EmbeddingObject(embedding=emb_value, index=i))

            # 估算 token 数
            total_chars = sum(len(t) for t in texts)
            estimated_tokens = total_chars // 4

            return EmbeddingResponse(
                data=data,
                model=model_id,
                usage=UsageInfo(
                    prompt_tokens=estimated_tokens,
                    total_tokens=estimated_tokens,
                ),
            )

        except Exception as e:
            logger.exception(f"Embedding error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

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
    models: Optional[List[str]] = None,
    default_model: Optional[str] = None,
    device: Optional[str] = None,
    local_dir: Optional[str] = None,
    dtype: Optional[str] = None,
    attn: Optional[str] = None,
) -> EmbeddingServer:
    """创建 Embedding 服务实例

    Args:
        models: 预加载的模型列表
        default_model: 默认模型
        device: 设备 (cuda/cpu)
        local_dir: 本地模型目录
        dtype: 数据类型 (float16/bfloat16/float32)
        attn: 注意力实现 (eager/sdpa/flash_attention_2)
    """
    return EmbeddingServer(
        models=models,
        default_model=default_model,
        device=device,
        local_dir=local_dir,
        dtype=dtype,
        attn=attn,
    )


# CLI 入口
def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="Embedding Server")
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        nargs="+",
        default=["jinaai/jina-embeddings-v3"],
        help="Models to load",
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port")
    parser.add_argument(
        "--device", type=str, default=None, help="Device (cuda/cpu)"
    )
    parser.add_argument(
        "--dtype",
        type=str,
        default=None,
        help="Model precision (bf16/fp16/f16/fp32/f32, default: fp32)",
    )
    parser.add_argument(
        "--local-dir",
        type=str,
        default=None,
        help="Local models directory (auto setup HF cache symlinks)",
    )

    args = parser.parse_args()

    server = create_server(
        models=args.model,
        device=args.device,
        local_dir=args.local_dir,
        torch_dtype=args.dtype,
    )
    server.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
