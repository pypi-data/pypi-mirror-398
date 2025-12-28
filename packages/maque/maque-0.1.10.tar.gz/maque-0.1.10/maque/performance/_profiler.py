#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
现代化性能分析器

提供两种分析器：
1. Profile - 基于 pyinstrument，轻量级 CPU 分析
2. ScaleneProfile - 基于 Scalene，CPU + 内存 + GPU 全面分析

Example:
    # pyinstrument (轻量级)
    with Profile("数据处理") as p:
        process_data()

    # Scalene (全面分析)
    with ScaleneProfile("内存分析", memory=True):
        process_large_data()
"""

from typing import Optional, Literal
from pathlib import Path
import functools
import subprocess
import sys
import tempfile
import os

try:
    from pyinstrument import Profiler
    PYINSTRUMENT_AVAILABLE = True
except ImportError:
    PYINSTRUMENT_AVAILABLE = False
    Profiler = None

try:
    from scalene import scalene_profiler
    SCALENE_AVAILABLE = True
except ImportError:
    SCALENE_AVAILABLE = False
    scalene_profiler = None


OutputFormat = Literal["text", "html", "json", "speedscope"]


class Profile:
    """
    现代化性能分析器

    基于 pyinstrument 的采样式分析，低开销，支持异步代码。

    Example:
        >>> with Profile("任务名称") as p:
        ...     time.sleep(0.1)
        ...     do_something()

        # 查看 HTML 报告
        >>> p.open_in_browser()

        # 保存报告
        >>> p.save("report.html")
    """

    def __init__(
        self,
        name: str = "",
        *,
        interval: float = 0.001,  # 采样间隔（秒）
        async_mode: str = "enabled",  # enabled, disabled, strict
        show: bool = True,  # 退出时是否自动打印
        show_all: bool = False,  # 显示所有帧（包括库代码）
        timeline: bool = False,  # 时间线模式
        output: OutputFormat = "text",  # 输出格式
    ):
        if not PYINSTRUMENT_AVAILABLE:
            raise ImportError(
                "pyinstrument 未安装，请运行: pip install pyinstrument"
            )

        self.name = name
        self.show = show
        self.show_all = show_all
        self.output = output
        self._profiler = Profiler(interval=interval, async_mode=async_mode)
        self._timeline = timeline

    def __enter__(self):
        self._profiler.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._profiler.stop()
        if self.show:
            self.print()
        return False

    def start(self):
        """手动启动分析"""
        self._profiler.start()
        return self

    def stop(self):
        """手动停止分析"""
        self._profiler.stop()
        return self

    def print(self, **kwargs):
        """打印分析报告到终端"""
        if self.name:
            print(f"\n{'='*20} {self.name} {'='*20}")
        print(self._profiler.output_text(
            unicode=True,
            color=True,
            show_all=self.show_all,
            timeline=self._timeline,
            **kwargs
        ))

    def to_html(self) -> str:
        """生成 HTML 报告"""
        return self._profiler.output_html()

    def to_text(self, **kwargs) -> str:
        """生成文本报告"""
        return self._profiler.output_text(
            unicode=True,
            show_all=self.show_all,
            timeline=self._timeline,
            **kwargs
        )

    def to_json(self) -> str:
        """生成 JSON 报告（用于程序化分析）"""
        import json
        return json.dumps(self._profiler.last_session.frame_records, indent=2)

    def save(self, path: str):
        """
        保存报告到文件

        根据文件扩展名自动选择格式：
        - .html -> HTML 交互式报告
        - .txt -> 文本报告
        - .json -> JSON 数据
        """
        path = Path(path)
        suffix = path.suffix.lower()

        if suffix == ".html":
            content = self.to_html()
        elif suffix == ".json":
            content = self.to_json()
        else:
            content = self.to_text()

        path.write_text(content, encoding="utf-8")
        print(f"报告已保存: {path}")

    def open_in_browser(self):
        """在浏览器中打开交互式 HTML 报告"""
        self._profiler.open_in_browser(timeline=self._timeline)

    @property
    def session(self):
        """获取原始 session 对象用于高级操作"""
        return self._profiler.last_session


def profile(
    func=None,
    *,
    show: bool = True,
    show_all: bool = False,
    save_to: Optional[str] = None,
):
    """
    函数装饰器 - 分析函数性能

    Example:
        @profile
        def slow_function():
            ...

        @profile(show=False, save_to="report.html")
        def another_function():
            ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with Profile(fn.__name__, show=show, show_all=show_all) as p:
                result = fn(*args, **kwargs)
            if save_to:
                p.save(save_to)
            return result

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            with Profile(fn.__name__, show=show, show_all=show_all) as p:
                result = await fn(*args, **kwargs)
            if save_to:
                p.save(save_to)
            return result

        import asyncio
        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


class ScaleneProfile:
    """
    全面性能分析器 - 基于 Scalene

    支持 CPU + 内存 + GPU 分析，自动检测内存泄漏。

    Example:
        # 基本使用
        with ScaleneProfile("数据处理"):
            process_data()

        # 含内存分析
        with ScaleneProfile("内存密集任务", memory=True, gpu=True):
            train_model()

        # 生成 HTML 报告
        with ScaleneProfile("分析", output="report.html"):
            heavy_work()

    Note:
        Scalene 使用采样分析，对于运行时间 < 1 秒的代码可能采样不足。
        建议用于分析耗时较长的代码块。
    """

    def __init__(
        self,
        name: str = "",
        *,
        cpu: bool = True,
        memory: bool = False,
        gpu: bool = False,
        output: Optional[str] = None,  # HTML 报告路径
        reduced_profile: bool = False,  # 仅显示有性能问题的行
    ):
        if not SCALENE_AVAILABLE:
            raise ImportError(
                "scalene 未安装，请运行: pip install scalene"
            )

        self.name = name
        self.cpu = cpu
        self.memory = memory
        self.gpu = gpu
        self.output = output
        self.reduced_profile = reduced_profile

    def __enter__(self):
        if self.name:
            print(f"\n🔬 Scalene 分析开始: {self.name}")
        scalene_profiler.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        scalene_profiler.stop()
        if self.name:
            print(f"✅ Scalene 分析完成: {self.name}")
        return False

    def start(self):
        """手动启动分析"""
        scalene_profiler.start()
        return self

    def stop(self):
        """手动停止分析"""
        scalene_profiler.stop()
        return self


def scalene_run(
    script: str,
    *args,
    cpu: bool = True,
    memory: bool = True,
    gpu: bool = False,
    output: Optional[str] = None,
    reduced: bool = False,
    **kwargs,
) -> subprocess.CompletedProcess:
    """
    使用 Scalene 运行 Python 脚本（推荐方式）

    Scalene 的完整功能需要从命令行启动，此函数封装了命令行调用。

    Example:
        # 分析脚本
        scalene_run("train.py", "--epochs", "10", output="report.html")

        # 分析模块
        scalene_run("-m", "pytest", "tests/", memory=True)

    Args:
        script: Python 脚本路径或 -m 模块名
        *args: 传递给脚本的参数
        cpu: 是否分析 CPU（默认 True）
        memory: 是否分析内存（默认 True）
        gpu: 是否分析 GPU
        output: HTML 报告输出路径
        reduced: 仅显示有问题的行

    Returns:
        subprocess.CompletedProcess 对象
    """
    cmd = [sys.executable, "-m", "scalene"]

    if not cpu:
        cmd.append("--cpu-only")
    if memory:
        cmd.append("--memory")
    if gpu:
        cmd.append("--gpu")
    if reduced:
        cmd.append("--reduced-profile")
    if output:
        cmd.extend(["--html", "--outfile", output])

    cmd.append("---")  # 分隔 Scalene 参数和脚本参数
    cmd.append(script)
    cmd.extend(args)

    print(f"🚀 运行: {' '.join(cmd)}")
    return subprocess.run(cmd, **kwargs)


def scalene_profile(
    func=None,
    *,
    memory: bool = False,
    gpu: bool = False,
):
    """
    Scalene 函数装饰器

    注意：需要用 `scalene` 命令启动脚本才能生效。

    Example:
        @scalene_profile(memory=True)
        def process_data():
            ...

        # 运行时使用: scalene script.py
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with ScaleneProfile(fn.__name__, memory=memory, gpu=gpu):
                return fn(*args, **kwargs)
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator
