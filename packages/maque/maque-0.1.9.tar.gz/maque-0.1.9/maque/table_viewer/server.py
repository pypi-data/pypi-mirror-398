"""
表格查看器后端服务 - 基于FastAPI
支持表格展示、图片URL预览、筛选、编辑等功能
"""

from fastapi import FastAPI, Request, HTTPException, Query, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import json
import uvicorn
import webbrowser
import asyncio
from dataclasses import dataclass
import re
import requests
import aiohttp
import aiofiles
from urllib.parse import urlparse
import hashlib
import tempfile
import os
import random
import time
from maque.utils.helper_parser import split_image_paths


@dataclass
class FilterConfig:
    """筛选配置"""

    column: str
    operator: str  # eq, ne, contains, startswith, endswith, gt, lt, ge, le
    value: Any


class TableViewerServer:
    """表格查看器服务器"""

    def __init__(
        self,
        file_path: Optional[str] = None,
        port: int = 8080,
        host: str = "127.0.0.1",
        sheet_name: Union[str, int] = 0,
        image_columns: Optional[List[str]] = None,
        auto_detect_images: bool = True,
    ):
        self.file_path = Path(file_path) if file_path else None
        self.port = port
        self.host = host
        self.sheet_name = sheet_name
        self.image_columns = image_columns or []
        self.auto_detect_images = auto_detect_images

        # 初始化FastAPI应用
        self.app = FastAPI(
            title="Sparrow Table Viewer",
            description="高性能表格查看器，支持图片预览、筛选、编辑",
            version="1.0.0",
        )

        # 设置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 挂载静态文件
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=static_dir), name="static")

        # 设置模板目录
        template_dir = Path(__file__).parent / "templates"
        self.templates = Jinja2Templates(directory=template_dir)

        # 加载数据
        if self.file_path:
            self.df = self._load_data()
            self.original_df = self.df.copy()

            # 自动检测图片列
            if self.auto_detect_images:
                self._detect_image_columns()
        else:
            # 创建空数据框
            self.df = pd.DataFrame()
            self.original_df = pd.DataFrame()

        # 图片缓存
        self._image_cache = {}
        self._temp_dir = tempfile.mkdtemp(prefix="maque_table_viewer_")

        # 上传文件缓存
        self._uploads_dir = Path(self._temp_dir) / "uploads"
        self._uploads_dir.mkdir(exist_ok=True)

        # 异步HTTP会话
        self._http_session = None

        # 反爬虫User-Agent池
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        ]

        # 注册路由
        self._setup_routes()

    async def _get_http_session(self):
        """获取或创建HTTP会话"""
        if self._http_session is None or self._http_session.closed:
            # 创建连接器，优化性能
            connector = aiohttp.TCPConnector(
                limit=100,  # 总连接池大小
                limit_per_host=20,  # 每个主机的连接数
                ttl_dns_cache=300,  # DNS缓存时间
                use_dns_cache=True,
            )

            # 创建超时配置
            timeout = aiohttp.ClientTimeout(
                total=30,  # 总超时时间
                connect=10,  # 连接超时
                sock_read=20,  # 读取超时
            )

            self._http_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "no-cache",
                    "Sec-Fetch-Dest": "image",
                    "Sec-Fetch-Mode": "no-cors",
                    "Sec-Fetch-Site": "cross-site",
                },
            )
        return self._http_session

    def _get_anti_bot_headers(self):
        """获取反爬虫请求头"""
        return {
            "User-Agent": random.choice(self._user_agents),
            "Referer": "https://www.google.com/",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

    async def _download_image_async(
        self, url: str, cache_path: Path, max_retries: int = 3
    ) -> bool:
        """异步下载图片到缓存路径，包含重试机制"""
        session = await self._get_http_session()

        for attempt in range(max_retries):
            try:
                # 随机延迟，避免被反爬虫检测
                if attempt > 0:
                    delay = (2**attempt) + random.uniform(
                        0.1, 0.5
                    )  # 指数退避 + 随机抖动
                    await asyncio.sleep(delay)

                # 获取反爬虫请求头
                headers = self._get_anti_bot_headers()

                async with session.get(url, headers=headers) as response:
                    # 检查响应状态
                    if response.status == 200:
                        # 异步写入文件
                        async with aiofiles.open(cache_path, "wb") as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        return True
                    elif response.status == 403:
                        # 403错误，可能是反爬虫，增加延迟
                        print(
                            f"图片下载被拒绝 (403): {url}, 尝试 {attempt + 1}/{max_retries}"
                        )
                        if attempt < max_retries - 1:
                            await asyncio.sleep(random.uniform(1.0, 3.0))
                            continue
                    elif response.status == 429:
                        # 429限流，增加更长延迟
                        print(
                            f"请求过于频繁 (429): {url}, 尝试 {attempt + 1}/{max_retries}"
                        )
                        if attempt < max_retries - 1:
                            await asyncio.sleep(random.uniform(3.0, 8.0))
                            continue
                    else:
                        print(f"图片下载失败，状态码 {response.status}: {url}")
                        if attempt < max_retries - 1:
                            continue

            except asyncio.TimeoutError:
                print(f"图片下载超时: {url}, 尝试 {attempt + 1}/{max_retries}")
            except aiohttp.ClientError as e:
                print(f"网络错误: {url}, {e}, 尝试 {attempt + 1}/{max_retries}")
            except Exception as e:
                print(f"图片下载异常: {url}, {e}, 尝试 {attempt + 1}/{max_retries}")

            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                await asyncio.sleep(random.uniform(0.5, 2.0))

        return False

    def _reload_data(self, new_file_path: Path):
        """重新加载新的数据文件"""
        self.file_path = new_file_path
        self.df = self._load_data_from_path(new_file_path)
        self.original_df = self.df.copy()

        # 重新检测图片列
        self.image_columns = []
        if self.auto_detect_images:
            self._detect_image_columns()

    def _load_data(self) -> pd.DataFrame:
        """加载当前文件路径的数据"""
        if not self.file_path:
            return pd.DataFrame()
        return self._load_data_from_path(self.file_path)

    def _load_data_from_path(self, file_path: Path) -> pd.DataFrame:
        """加载指定路径的表格数据"""
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_extension = file_path.suffix.lower()

        if file_extension == ".csv":
            try:
                # 尝试不同编码
                for encoding in ["utf-8", "gbk", "gb2312", "latin1"]:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        print(f"成功使用 {encoding} 编码加载CSV文件")
                        return df
                    except UnicodeDecodeError:
                        continue
                raise ValueError("无法确定CSV文件编码")
            except Exception as e:
                raise ValueError(f"加载CSV文件失败: {e}")

        elif file_extension in [".xlsx", ".xls"]:
            try:
                df = pd.read_excel(file_path, sheet_name=self.sheet_name)
                return df
            except Exception as e:
                raise ValueError(f"加载Excel文件失败: {e}")
        else:
            raise ValueError(f"不支持的文件格式: {file_extension}")

    def _detect_image_columns(self):
        """自动检测包含图片URL的列"""
        for column in self.df.columns:
            # 检查前10行的数据
            sample_data = self.df[column].dropna().head(10)
            image_count = 0

            for value in sample_data:
                if isinstance(value, str):
                    # 使用split_image_paths检测图片路径
                    image_paths = split_image_paths(value)
                    if image_paths:
                        image_count += 1

            # 如果超过50%的样本包含图片URL，则认为是图片列
            if image_count / len(sample_data) > 0.5 if len(sample_data) > 0 else False:
                if column not in self.image_columns:
                    self.image_columns.append(column)
                    print(f"自动检测到图片列: {column}")

    def _setup_routes(self):
        """设置API路由"""

        @self.app.get("/", response_class=HTMLResponse)
        async def get_index(request: Request):
            """主页面"""
            return self.templates.TemplateResponse("index.html", {"request": request})

        @self.app.get("/api/table/info")
        async def get_table_info():
            """获取表格基本信息"""
            return {
                "total_rows": len(self.original_df),
                "total_columns": len(self.original_df.columns),
                "columns": list(self.original_df.columns),
                "image_columns": self.image_columns,
                "file_path": str(self.file_path),
                "dtypes": {
                    col: str(dtype) for col, dtype in self.original_df.dtypes.items()
                },
            }

        @self.app.get("/api/table/data")
        async def get_table_data(
            page: int = Query(1, ge=1),
            page_size: int = Query(100, ge=10, le=1000),
            sort_by: Optional[str] = None,
            sort_order: str = Query("asc", pattern="^(asc|desc)$"),
            filters: Optional[str] = None,
            visible_columns: Optional[str] = None,
            separator: Optional[str] = Query(None, description="自定义分隔符"),
        ):
            """获取表格数据（分页）"""
            df = self.df.copy()

            # 应用行筛选
            if filters:
                try:
                    filter_configs = json.loads(filters)
                    df = self._apply_filters(df, filter_configs)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"筛选参数错误: {e}")

            # 应用列筛选
            display_columns = list(df.columns)
            if visible_columns:
                try:
                    visible_cols = json.loads(visible_columns)
                    if visible_cols and isinstance(visible_cols, list):
                        # 确保列存在
                        display_columns = [
                            col for col in visible_cols if col in df.columns
                        ]
                        if display_columns:
                            df = df[display_columns]
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"列筛选参数错误: {e}")

            # 排序
            if sort_by and sort_by in df.columns:
                ascending = sort_order == "asc"
                df = df.sort_values(by=sort_by, ascending=ascending)

            # 分页
            total_rows = len(df)
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_rows)
            page_data = df.iloc[start_idx:end_idx]

            # 转换为前端格式
            data = []
            for idx, row in page_data.iterrows():
                row_data = {"_index": idx}
                for col in df.columns:
                    value = row[col]
                    # 处理NaN值
                    if pd.isna(value):
                        row_data[col] = None
                    else:
                        # 如果是图像列，预处理切分图像路径
                        if col in self.image_columns and isinstance(value, str):
                            # 处理自定义分隔符
                            separators = None
                            if separator:
                                # 处理特殊字符串
                                if separator == '\\n':
                                    separator = '\n'
                                elif separator == '\\r':
                                    separator = '\r'
                                elif separator == '\\t':
                                    separator = '\t'
                                separators = [separator]
                            image_paths = split_image_paths(value, separators=separators)
                            row_data[col] = {
                                "original": value,  # 保留原始字符串
                                "paths": image_paths,  # 切分后的路径数组
                            }
                        else:
                            row_data[col] = value
                data.append(row_data)

            return {
                "data": data,
                "total": total_rows,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_rows + page_size - 1) // page_size,
                "visible_columns": display_columns,
            }

        @self.app.put("/api/table/cell/{row_index}/{column}")
        async def update_cell(row_index: int, column: str, request: Request):
            """更新单元格数据"""
            # 检查是否有数据
            if self.df.empty:
                raise HTTPException(
                    status_code=400, detail="没有加载任何表格数据，请先上传文件"
                )

            if column not in self.df.columns:
                raise HTTPException(status_code=404, detail="列不存在")

            if row_index < 0 or row_index >= len(self.df):
                raise HTTPException(status_code=404, detail="行索引超出范围")

            body = await request.json()
            new_value = body.get("value")

            # 更新数据
            try:
                self.df.at[row_index, column] = new_value
                return {"success": True, "message": "更新成功"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

        @self.app.post("/api/table/save")
        async def save_table():
            """保存表格到原文件"""
            if not self.file_path:
                raise HTTPException(
                    status_code=400,
                    detail="没有原始文件，无法保存。请使用文件上传功能。",
                )

            if self.df.empty:
                raise HTTPException(status_code=400, detail="没有数据可保存")

            try:
                if self.file_path.suffix.lower() == ".csv":
                    self.df.to_csv(self.file_path, index=False, encoding="utf-8")
                else:
                    self.df.to_excel(
                        self.file_path, index=False, sheet_name=self.sheet_name
                    )
                return {"success": True, "message": "保存成功"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")

        @self.app.post("/api/table/reset")
        async def reset_table():
            """重置表格到原始状态"""
            if not self.file_path:
                raise HTTPException(
                    status_code=400, detail="没有原始文件，无法重置。请重新上传文件。"
                )

            self.df = self.original_df.copy()
            return {"success": True, "message": "重置成功"}

        @self.app.get("/api/image/proxy")
        async def image_proxy(url: str):
            """图片代理服务（解决跨域问题）"""
            if not url:
                raise HTTPException(status_code=400, detail="URL参数缺失")

            # 检查缓存
            url_hash = hashlib.md5(url.encode()).hexdigest()
            cache_path = Path(self._temp_dir) / f"{url_hash}"

            if cache_path.exists():
                return FileResponse(cache_path)

            try:
                # 判断是本地文件还是网络URL
                if url.startswith(("http://", "https://")):
                    # 异步下载网络图片
                    success = await self._download_image_async(url, cache_path)
                    if success:
                        return FileResponse(cache_path)
                    else:
                        raise HTTPException(status_code=500, detail="图片下载失败")
                else:
                    # 本地文件
                    try:
                        # 规范化路径，处理各种路径格式
                        local_path = Path(url).resolve()

                        # 检查文件是否存在
                        if local_path.exists() and local_path.is_file():
                            # 检查是否为图像文件
                            if local_path.suffix.lower() in [
                                ".jpg",
                                ".jpeg",
                                ".png",
                                ".gif",
                                ".bmp",
                                ".webp",
                            ]:
                                return FileResponse(local_path)
                            else:
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"不支持的图像格式: {local_path.suffix}",
                                )
                        else:
                            # 提供更详细的错误信息
                            if not local_path.exists():
                                raise HTTPException(
                                    status_code=404, detail=f"文件不存在: {local_path}"
                                )
                            else:
                                raise HTTPException(
                                    status_code=400, detail=f"不是文件: {local_path}"
                                )
                    except Exception as e:
                        if isinstance(e, HTTPException):
                            raise
                        raise HTTPException(
                            status_code=500, detail=f"处理本地文件时出错: {str(e)}"
                        )

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"加载图片失败: {e}")

        @self.app.post("/api/table/upload")
        async def upload_file(file: UploadFile = File(...)):
            """上传新的表格文件"""
            try:
                # 验证文件格式
                if not file.filename:
                    raise HTTPException(status_code=400, detail="未提供文件名")

                file_extension = Path(file.filename).suffix.lower()
                if file_extension not in [".csv", ".xlsx", ".xls"]:
                    raise HTTPException(
                        status_code=400, detail=f"不支持的文件格式: {file_extension}"
                    )

                # 保存上传的文件
                upload_path = self._uploads_dir / file.filename
                with open(upload_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)

                # 重新加载数据
                self._reload_data(upload_path)

                return {
                    "success": True,
                    "message": "文件上传成功",
                    "filename": file.filename,
                    "total_rows": len(self.df),
                    "total_columns": len(self.df.columns),
                    "columns": list(self.df.columns),
                    "image_columns": self.image_columns,
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

    def _apply_filters(
        self, df: pd.DataFrame, filter_configs: List[Dict]
    ) -> pd.DataFrame:
        """应用筛选条件"""
        for filter_config in filter_configs:
            column = filter_config.get("column")
            operator = filter_config.get("operator", "contains")
            value = filter_config.get("value", "")

            if not column or column not in df.columns:
                continue

            if operator == "contains":
                mask = (
                    df[column]
                    .astype(str)
                    .str.contains(str(value), case=False, na=False)
                )
            elif operator == "eq":
                mask = df[column] == value
            elif operator == "ne":
                mask = df[column] != value
            elif operator == "startswith":
                mask = df[column].astype(str).str.startswith(str(value), na=False)
            elif operator == "endswith":
                mask = df[column].astype(str).str.endswith(str(value), na=False)
            elif operator == "gt":
                mask = pd.to_numeric(df[column], errors="coerce") > float(value)
            elif operator == "lt":
                mask = pd.to_numeric(df[column], errors="coerce") < float(value)
            elif operator == "ge":
                mask = pd.to_numeric(df[column], errors="coerce") >= float(value)
            elif operator == "le":
                mask = pd.to_numeric(df[column], errors="coerce") <= float(value)
            else:
                continue

            df = df[mask]

        return df

    def run(self, auto_open: bool = True):
        """启动服务器"""
        print(f"启动表格查看器服务...")
        print(f"文件: {self.file_path}")
        print(f"地址: http://{self.host}:{self.port}")
        print(f"数据: {len(self.df)} 行 x {len(self.df.columns)} 列")
        if self.image_columns:
            print(f"图片列: {', '.join(self.image_columns)}")
            # 显示每个图像列的示例路径（用于调试）
            for col in self.image_columns:
                sample_value = (
                    self.df[col].dropna().iloc[0]
                    if not self.df[col].dropna().empty
                    else None
                )
                if sample_value:
                    sample_paths = split_image_paths(str(sample_value))
                    print(
                        f"  {col}: 示例路径 -> {sample_paths[:2]}{'...' if len(sample_paths) > 2 else ''}"
                    )
        else:
            print("未检测到图片列")
        print(f"提示: 双击单元格可编辑，Ctrl+C 停止服务")

        if auto_open:
            # 延迟打开浏览器
            def open_browser():
                import time

                time.sleep(1.5)
                webbrowser.open(f"http://{self.host}:{self.port}")

            import threading

            threading.Thread(target=open_browser, daemon=True).start()

        try:
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
                log_level="warning",  # 减少日志输出
            )
        except KeyboardInterrupt:
            print("\n服务器已停止")
        finally:
            # 清理HTTP会话
            if self._http_session and not self._http_session.closed:
                asyncio.run(self._http_session.close())

            # 清理临时文件
            import shutil

            if Path(self._temp_dir).exists():
                shutil.rmtree(self._temp_dir, ignore_errors=True)


def start_table_viewer(
    file_path: str,
    port: int = 8080,
    host: str = "0.0.0.0",
    sheet_name: Union[str, int] = 0,
    image_columns: Optional[List[str]] = None,
    auto_detect_images: bool = True,
    auto_open: bool = True,
):
    """启动表格查看器的便捷函数"""
    server = TableViewerServer(
        file_path=file_path,
        port=port,
        host=host,
        sheet_name=sheet_name,
        image_columns=image_columns,
        auto_detect_images=auto_detect_images,
    )
    server.run(auto_open=auto_open)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python server.py <文件路径>")
        sys.exit(1)

    start_table_viewer(sys.argv[1])
