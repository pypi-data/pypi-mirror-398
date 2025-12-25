"""
Web界面应用框架
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from .core import DataProcessorPipeline, PipelineConfig, StepResult
from .steps import get_all_steps, create_step_from_config
from loguru import logger


class PipelineRunRequest(BaseModel):
    """Pipeline运行请求"""

    config: Dict[str, Any]
    resume_from: Optional[str] = None


class PipelineStatusResponse(BaseModel):
    """Pipeline状态响应"""

    pipeline_id: str
    status: str  # idle, running, completed, failed
    current_step: Optional[str] = None
    progress: float = 0.0
    results: List[Dict[str, Any]] = []
    error: Optional[str] = None


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.connections[client_id] = websocket
        logger.info(f"WebSocket连接建立: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.connections:
            del self.connections[client_id]
            logger.info(f"WebSocket连接断开: {client_id}")

    async def send_message(self, client_id: str, message: Dict[str, Any]):
        if client_id in self.connections:
            try:
                await self.connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"发送WebSocket消息失败: {e}")
                self.disconnect(client_id)


class PipelineManager:
    """Pipeline管理器"""

    def __init__(self):
        self.pipelines: Dict[str, DataProcessorPipeline] = {}
        self.pipeline_status: Dict[str, Dict[str, Any]] = {}
        self.websocket_manager = WebSocketManager()

    def create_pipeline(self, config: PipelineConfig) -> str:
        """创建Pipeline"""
        pipeline_id = str(uuid.uuid4())
        pipeline = DataProcessorPipeline(config)

        self.pipelines[pipeline_id] = pipeline
        self.pipeline_status[pipeline_id] = {
            "status": "idle",
            "current_step": None,
            "progress": 0.0,
            "results": [],
            "error": None,
            "created_at": datetime.now().isoformat(),
        }

        # 设置状态回调
        pipeline.set_status_callback(
            lambda status, data: asyncio.create_task(
                self._update_pipeline_status(pipeline_id, status, data)
            )
        )

        return pipeline_id

    async def _update_pipeline_status(
        self, pipeline_id: str, status: str, data: Dict[str, Any]
    ):
        """更新Pipeline状态"""
        if pipeline_id not in self.pipeline_status:
            return

        pipeline_status = self.pipeline_status[pipeline_id]

        if status == "starting":
            pipeline_status["status"] = "running"
            pipeline_status["progress"] = 0.0
        elif status == "executing_step":
            pipeline_status["current_step"] = data.get("step_name")
            pipeline_status["progress"] = (data.get("step_index", 0) + 1) / data.get(
                "total_steps", 1
            )
        elif status == "step_failed":
            pipeline_status["status"] = "failed"
            pipeline_status["error"] = data.get("error")
        elif status == "completed":
            pipeline_status["status"] = "completed"
            pipeline_status["progress"] = 1.0
            pipeline_status["current_step"] = None

        # 通过WebSocket发送状态更新
        await self.websocket_manager.send_message(
            pipeline_id,
            {
                "type": "status_update",
                "pipeline_id": pipeline_id,
                "status": pipeline_status,
            },
        )

    async def run_pipeline(self, pipeline_id: str, resume_from: Optional[str] = None):
        """运行Pipeline"""
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline {pipeline_id} 不存在")

        pipeline = self.pipelines[pipeline_id]

        try:
            results = await pipeline.run(resume_from=resume_from)
            self.pipeline_status[pipeline_id]["results"] = [
                r.to_dict() for r in results
            ]
            pipeline.save_final_results()
        except Exception as e:
            logger.error(f"Pipeline {pipeline_id} 执行失败: {e}")
            self.pipeline_status[pipeline_id]["status"] = "failed"
            self.pipeline_status[pipeline_id]["error"] = str(e)

    def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """获取Pipeline状态"""
        if pipeline_id not in self.pipeline_status:
            raise ValueError(f"Pipeline {pipeline_id} 不存在")

        return self.pipeline_status[pipeline_id]

    def list_pipelines(self) -> List[Dict[str, Any]]:
        """列出所有Pipeline"""
        return [
            {"pipeline_id": pid, **status}
            for pid, status in self.pipeline_status.items()
        ]


class WebApp:
    """Web应用主类"""

    def __init__(self, static_dir: Optional[str] = None):
        self.app = FastAPI(title="MLLM Data Processor Pipeline", version="0.1.0")
        self.pipeline_manager = PipelineManager()
        self.static_dir = static_dir or str(Path(__file__).parent / "static")

        self._setup_routes()
        self._setup_static_files()

    def _setup_static_files(self):
        """设置静态文件服务"""
        static_path = Path(self.static_dir)
        if static_path.exists():
            self.app.mount(
                "/static", StaticFiles(directory=str(static_path)), name="static"
            )

    def _setup_routes(self):
        """设置路由"""

        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            """主页"""
            html_file = Path(self.static_dir) / "index.html"
            if html_file.exists():
                return FileResponse(html_file)
            return self._get_default_html()

        @self.app.post("/api/pipeline/create")
        async def create_pipeline(request: PipelineRunRequest):
            """创建Pipeline"""
            try:
                config = PipelineConfig.from_dict(request.config)
                pipeline_id = self.pipeline_manager.create_pipeline(config)
                return {"pipeline_id": pipeline_id, "status": "created"}
            except Exception as e:
                logger.error(f"创建Pipeline失败: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/api/pipeline/{pipeline_id}/run")
        async def run_pipeline(
            pipeline_id: str,
            background_tasks: BackgroundTasks,
            resume_from: Optional[str] = None,
        ):
            """运行Pipeline"""
            try:
                background_tasks.add_task(
                    self.pipeline_manager.run_pipeline, pipeline_id, resume_from
                )
                return {"message": "Pipeline开始执行", "pipeline_id": pipeline_id}
            except Exception as e:
                logger.error(f"运行Pipeline失败: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/api/pipeline/{pipeline_id}/status")
        async def get_pipeline_status(pipeline_id: str):
            """获取Pipeline状态"""
            try:
                return self.pipeline_manager.get_pipeline_status(pipeline_id)
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))

        @self.app.get("/api/pipelines")
        async def list_pipelines():
            """列出所有Pipeline"""
            return self.pipeline_manager.list_pipelines()

        @self.app.get("/api/steps")
        async def get_available_steps():
            """获取可用的处理步骤"""
            return {
                "steps": [
                    {
                        "name": step_class.__name__,
                        "description": getattr(step_class, "__doc__", ""),
                        "config_schema": getattr(step_class, "CONFIG_SCHEMA", {}),
                    }
                    for step_class in get_all_steps()
                ]
            }

        @self.app.post("/api/upload")
        async def upload_file(file: UploadFile = File(...)):
            """上传文件"""
            try:
                upload_dir = Path("uploads")
                upload_dir.mkdir(exist_ok=True)

                file_path = upload_dir / file.filename
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)

                return {
                    "filename": file.filename,
                    "file_path": str(file_path),
                    "size": len(content),
                }
            except Exception as e:
                logger.error(f"文件上传失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            """WebSocket端点"""
            await self.pipeline_manager.websocket_manager.connect(websocket, client_id)
            try:
                while True:
                    data = await websocket.receive_text()
                    # 处理客户端消息
                    message = json.loads(data)
                    logger.info(f"收到WebSocket消息: {message}")
            except Exception as e:
                logger.error(f"WebSocket错误: {e}")
            finally:
                self.pipeline_manager.websocket_manager.disconnect(client_id)

    def _get_default_html(self) -> str:
        """获取默认HTML页面"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MLLM Data Processor Pipeline</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 1200px; margin: 0 auto; }
                h1 { color: #333; }
                .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>MLLM Data Processor Pipeline</h1>
                <div class="section">
                    <h2>欢迎使用多模态大模型训练数据处理Pipeline</h2>
                    <p>这是一个灵活的、模块化的数据处理流水线，支持Web界面交互和断点续传。</p>
                    <p>请访问 <a href="/docs">/docs</a> 查看API文档</p>
                </div>
            </div>
        </body>
        </html>
        """

    def run(self, host: str = "127.0.0.1", port: int = 8000, **kwargs):
        """运行Web应用"""
        logger.info(f"启动Web应用: http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port, **kwargs)
