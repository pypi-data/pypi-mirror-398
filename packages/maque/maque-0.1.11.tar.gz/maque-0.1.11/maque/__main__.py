"""
新版本的Sparrow CLI - 支持命令分组和改进的用户体验

这是重构后的CLI主文件，将原有的单层命令结构改为分组结构，
同时保持向后兼容性。
"""
from __future__ import annotations

import os
import pretty_errors
import rich
from rich import print
from typing import Literal, Tuple, Union
from pathlib import Path
import datetime

# 导入新的命令组
try:
    from .cli.groups import (
        ConfigGroup, MllmGroup, DataGroup,
        ServiceGroup, DoctorGroup, HelpGroup, EmbeddingGroup,
        GitGroup, SystemGroup, MCPGroup
    )
    from .cli.groups.llm import LlmGroup
    GROUPS_AVAILABLE = True
except ImportError as e:
    print(f"[yellow]警告: 无法导入新命令组: {e}[/yellow]")
    print("[yellow]将使用传统命令模式[/yellow]")
    GROUPS_AVAILABLE = False


class NewCli:
    """新版Sparrow CLI - 支持命令分组"""
    
    def __init__(self):
        self._config = {
            "server": "http://127.0.0.1:8000",
            "croc_relay": "142.171.214.153:27011",
        }

        # 加载 Sparrow 配置文件
        self.maque_config = self._load_maque_config()

        # 初始化命令组
        if GROUPS_AVAILABLE:
            self.config = ConfigGroup(self)
            self.mllm = MllmGroup(self)
            self.data = DataGroup(self)
            self.service = ServiceGroup(self)
            self.doctor = DoctorGroup(self)
            self.help = HelpGroup(self)
            self.embedding = EmbeddingGroup(self)
            self.git = GitGroup(self)
            self.system = SystemGroup(self)
            self.llm = LlmGroup(self)
            self.mcp = MCPGroup(self)
    
    # =============================================================================
    # 配置管理方法 (从原CLI类复制)
    # =============================================================================
    
    def _get_config_search_paths(self):
        """获取配置文件的搜索路径列表，按优先级排序"""
        search_paths = []

        # 1. 当前工作目录（最高优先级）
        search_paths.append(Path.cwd() / "maque_config.yaml")

        # 2. 项目根目录（如果当前不在项目根目录）
        current_path = Path.cwd()
        while current_path != current_path.parent:
            if (current_path / ".git").exists() or (current_path / "pyproject.toml").exists():
                project_config = current_path / "maque_config.yaml"
                if project_config not in search_paths:
                    search_paths.append(project_config)
                break
            current_path = current_path.parent

        # 3. 用户配置目录 ~/.maque/config.yaml（主要配置位置）
        search_paths.append(Path.home() / ".maque" / "config.yaml")

        return search_paths

    def _get_default_config_path(self):
        """获取默认配置文件路径"""
        return Path.home() / ".maque" / "config.yaml"

    def _load_maque_config(self):
        """从多个路径加载配置文件，如果不存在则自动创建默认配置"""
        from maque import yaml_load

        # 默认配置
        default_config = {
            "mllm": {
                "model": "gemma3:4b",
                "base_url": "http://localhost:11434/v1",
                "api_key": "EMPTY"
            }
        }

        config_paths = self._get_config_search_paths()

        # 按优先级依次尝试加载配置文件
        for config_path in config_paths:
            try:
                if config_path.exists():
                    file_config = yaml_load(str(config_path))
                    if file_config:
                        return self._deep_merge_config(default_config.copy(), file_config)
            except Exception as e:
                print(f"[yellow]警告: 无法加载配置文件 {config_path}: {e}[/yellow]")
                continue

        # 未找到配置文件，自动创建默认配置
        self._create_default_config()
        return default_config

    def _create_default_config(self):
        """在 ~/.maque/config.yaml 创建默认配置文件"""
        from maque import yaml_dump

        config_path = self._get_default_config_path()
        config_dir = config_path.parent

        try:
            # 创建目录
            config_dir.mkdir(parents=True, exist_ok=True)

            # 默认配置内容
            default_config = {
                "mllm": {
                    "model": "gemma3:4b",
                    "base_url": "http://localhost:11434/v1",
                    "api_key": "EMPTY"
                }
            }

            yaml_dump(str(config_path), default_config)
            print(f"[green]已创建默认配置文件: {config_path}[/green]")
            print(f"[dim]使用 'maque config edit' 编辑配置[/dim]")
        except Exception as e:
            print(f"[yellow]警告: 无法创建配置文件: {e}[/yellow]")

    def _deep_merge_config(self, base_config, new_config):
        """深度合并配置字典"""
        result = base_config.copy()
        
        for key, value in new_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_config(result[key], value)
            else:
                result[key] = value
        
        return result

    def get_config(self, key: str = None):
        """获取配置值
        
        Args:
            key (str): 配置键，支持点号分隔的嵌套键，如 'mllm.model'
                      如果为 None，返回整个配置
        """
        if key is None:
            return self.maque_config
        
        keys = key.split('.')
        value = self.maque_config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return None
    
    # =============================================================================
    # 向后兼容的传统命令
    # =============================================================================
    
    def init_config(self, path: str = None):
        """初始化配置文件

        Args:
            path (str): 配置文件路径，默认为 ~/.maque/config.yaml
        """
        if path is None:
            config_path = self._get_default_config_path()
        else:
            config_path = Path(path)

        if config_path.exists():
            print(f"配置文件已存在: {config_path.resolve()}")
            return

        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # 默认配置内容
        default_config_content = """# Maque 配置文件
# 配置搜索路径（按优先级）:
#   1. 当前目录: ./maque_config.yaml
#   2. 项目根目录: <project>/maque_config.yaml
#   3. 用户目录: ~/.maque/config.yaml

mllm:
  model: "gemma3:4b"
  base_url: "http://localhost:11434/v1"
  api_key: "EMPTY"
"""

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(default_config_content)
            print(f"[green]已创建配置文件: {config_path.resolve()}[/green]")
            print("[dim]使用 'maque config edit' 编辑配置[/dim]")
        except Exception as e:
            print(f"[red]创建配置文件失败: {e}[/red]")

    # 保留原有的核心命令以确保向后兼容性
    def mllm_call_table(self, *args, **kwargs):
        """向后兼容的MLLM表格调用"""
        if GROUPS_AVAILABLE:
            return self.mllm.call_table(*args, **kwargs)
        else:
            # 回退到传统实现
            print("[yellow]新版MLLM功能不可用，请检查依赖[/yellow]")
            return None
    
    def mllm_call_images(self, *args, **kwargs):
        """向后兼容的MLLM图像调用"""
        if GROUPS_AVAILABLE:
            return self.mllm.call_images(*args, **kwargs)
        else:
            print("[yellow]新版MLLM功能不可用，请检查依赖[/yellow]")
            return None

    def serve(
        self,
        model: str,
        host: str = "0.0.0.0",
        port: int = 8000,
        device: str = None,
        workers: int = 1,
        local_dir: str = None,
        type: str = None,
        dtype: str = None,
        attn: str = None,
    ):
        """启动模型推理服务 (自动检测模型类型)

        自动检测模型类型并启动相应的 API 服务：
        - Embedding 模型 -> /v1/embeddings
        - LLM/MLLM 模型 -> /v1/chat/completions

        Args:
            model: 模型名称或路径 (必填)
            host: 监听地址，默认 0.0.0.0
            port: 监听端口，默认 8000
            device: 设备类型 (cuda/cpu)，默认自动检测
            workers: worker 数量，默认 1 (仅 embedding 有效)
            local_dir: 本地模型目录
            type: 强制指定类型 (embedding/llm)，默认自动检测
            dtype: 数据类型 (float16/bfloat16/float32)，默认自动选择
            attn: 注意力实现 (eager/sdpa/flash_attention_2)，默认自动选择

        Examples:
            maque serve jinaai/jina-embeddings-v3 --local_dir=/path/to/models
            maque serve Qwen/Qwen2.5-7B-Instruct --local_dir=/path/to/models
            maque serve model --dtype=float32 --attn=eager
        """
        if not GROUPS_AVAILABLE:
            print("[yellow]服务不可用，请检查依赖[/yellow]")
            return None

        # 检测模型类型
        model_type = type or self._detect_model_type(model, local_dir)

        print(f"[blue]检测到模型类型: [bold]{model_type}[/bold][/blue]")

        if model_type == "embedding":
            return self.embedding.serve(
                model=model,
                host=host,
                port=port,
                device=device,
                workers=workers,
                local_dir=local_dir,
                dtype=dtype,
                attn=attn,
            )
        else:  # llm or mllm
            return self.llm.serve(
                model=model,
                host=host,
                port=port,
                device=device,
                local_dir=local_dir,
                dtype=dtype,
                attn=attn,
            )

    def _detect_model_type(self, model: str, local_dir: str = None) -> str:
        """检测模型类型

        检测逻辑：
        1. 检查是否有 modules.json (SentenceTransformer/Embedding)
        2. 检查 config.json 中的 architectures
        3. 根据模型名称关键字判断
        """
        from pathlib import Path
        import json

        # 解析模型路径
        model_path = None
        if local_dir:
            model_name = model.split("/")[-1]
            candidate = Path(local_dir) / model_name
            if candidate.exists():
                model_path = candidate

        # 1. 检查 modules.json (SentenceTransformer 特有)
        if model_path:
            if (model_path / "modules.json").exists():
                return "embedding"
            if (model_path / "config_sentence_transformers.json").exists():
                return "embedding"

        # 2. 检查 config.json 中的 architectures
        if model_path and (model_path / "config.json").exists():
            try:
                with open(model_path / "config.json", "r") as f:
                    config = json.load(f)
                architectures = config.get("architectures", [])

                # VL/Vision 模型
                for arch in architectures:
                    if "VL" in arch or "Vision" in arch or "vision" in arch.lower():
                        return "mllm"

                # Embedding 相关
                for arch in architectures:
                    arch_lower = arch.lower()
                    if "embedding" in arch_lower or "encoder" in arch_lower:
                        # 但排除 CausalLM
                        if "causallm" not in arch_lower:
                            return "embedding"

                # CausalLM -> LLM
                for arch in architectures:
                    if "CausalLM" in arch or "ForCausalLM" in arch:
                        return "llm"
            except Exception:
                pass

        # 3. 根据模型名称关键字判断
        model_lower = model.lower()

        embedding_keywords = ["embedding", "bge", "e5", "gte", "sentence", "sbert"]
        if any(kw in model_lower for kw in embedding_keywords):
            return "embedding"

        vl_keywords = ["-vl", "vl-", "vision", "qwen2-vl", "qwen2.5-vl"]
        if any(kw in model_lower for kw in vl_keywords):
            return "mllm"

        # 默认为 LLM
        return "llm"
    
    def table_viewer(self, *args, **kwargs):
        """向后兼容的表格查看器"""
        if GROUPS_AVAILABLE:
            return self.data.table_viewer(*args, **kwargs)
        else:
            print("[yellow]新版数据功能不可用，请检查依赖[/yellow]")
            return None

    @staticmethod
    def download(repo_id, download_dir=None, backend="huggingface", token=None, repo_type="model", use_mirror=True):
        """下载模型或数据集

        Args:
            repo_id: 模型或数据集仓库名称
            download_dir: 下载的本地目录，默认为当前目录下的 repo_id 文件夹
            backend: 下载源，"huggingface" 或 "modelscope"
            token: 访问私有仓库的身份验证令牌
            repo_type: 仓库类型，"model" 或 "dataset"
            use_mirror: 是否使用镜像下载模型（仅 huggingface）

        Examples:
            maque download meta-llama/Llama-2-7b-hf
            maque download SWHL/ChineseOCRBench --repo_type=dataset
            maque download qwen/Qwen-7B-Chat --backend=modelscope
        """
        from .utils.downloads import download_model
        return download_model(repo_id, download_dir=download_dir, backend=backend,
                             token=token, repo_type=repo_type, use_mirror=use_mirror)

    @staticmethod
    def crawl(
        keywords: str,
        num_images: int = 50,
        engines: str = "bing,google",
        save_dir: str = "downloaded_images",
        save_mapping: bool = True,
        flickr_api_key: str = None,
        flickr_api_secret: str = None,
        website_urls: str = None,
        url_list_file: str = None,
    ):
        """从网络爬取图片

        Args:
            keywords: 搜索关键词，多个关键词用逗号分隔
            num_images: 每个关键词下载的图片数量，默认50
            engines: 搜索引擎，多个用逗号分隔，支持: bing, google, baidu, flickr, unsplash, pixabay, pexels, website, urls
            save_dir: 图片保存目录，默认 "downloaded_images"
            save_mapping: 是否保存元数据到metadata.jsonl文件，默认True
            flickr_api_key: Flickr API密钥（使用flickr引擎时需要）
            flickr_api_secret: Flickr API密钥（使用flickr引擎时需要）
            website_urls: 网站URL列表，用逗号分隔（使用website引擎时需要）
            url_list_file: 包含图片URL列表的文件路径（使用urls引擎时需要）

        Examples:
            maque crawl "猫咪,狗狗" --num_images=20
            maque crawl "风景" --engines="unsplash,pixabay" --num_images=100
            maque crawl "产品图片" --engines="website" --website_urls="https://example.com"
        """
        try:
            from .web.image_downloader import download_images_cli
        except ImportError as e:
            print(f"[red]图片下载功能依赖缺失: {e}[/red]")
            print("请安装相关依赖: pip install icrawler Pillow requests beautifulsoup4")
            return
        
        # 处理参数
        keywords_list = [k.strip() for k in keywords.split(',')]
        engines_list = [e.strip() for e in engines.split(',')]
        
        return download_images_cli(
            keywords=keywords_list,
            num_images=num_images,
            engines=engines_list,
            save_dir=save_dir,
            save_mapping=save_mapping,
            flickr_api_key=flickr_api_key,
            flickr_api_secret=flickr_api_secret,
            website_urls=website_urls,
            url_list_file=url_list_file,
        )
    
    @staticmethod  
    def video_dedup(video_path: str, method: str = "phash", threshold: float = None, step: int = 1, resize: int = 256, workers: int = 1, fps: float = None, out_dir: str = "out"):
        """视频去重 - 保持向后兼容"""
        from maque.algorithms.video import VideoFrameDeduplicator
        from pathlib import Path
        from maque.performance._measure_time import MeasureTime
        
        # 延迟导入 cv2
        try:
            import cv2
        except ImportError:
            print("未检测到 opencv-python (cv2) 库。请先安装：pip install opencv-python")
            return

        mt = MeasureTime().start()

        try:
            dedup = VideoFrameDeduplicator(
                method=method,
                threshold=threshold,
                step=step,
                resize=resize,
                workers=workers,
                fps=fps
            )
        except ValueError as e:
            print(f"Error initializing deduplicator: {e}")
            return

        try:
            count = dedup.process_and_save_unique_frames(video_path, out_dir)
            mt.show_interval(f"Completed processing. Saved {count} frames.")
        except Exception as e:
            print(f"Operation failed: {e}")

    # =============================================================================
    # 新版帮助和引导系统  
    # =============================================================================
    
    def quick_start(self):
        """快速入门指南"""
        if GROUPS_AVAILABLE:
            self.help.getting_started()
        else:
            print("""[bold blue]Sparrow 快速入门[/bold blue]

[bold]1. 检查环境[/bold]
maque doctor check  # 或使用传统命令检查依赖

[bold]2. 初始化配置[/bold]
maque init-config   # 创建配置文件

[bold]3. 探索功能[/bold]
maque help examples  # 查看使用示例

[yellow]注意: 当前运行在兼容模式，某些新功能可能不可用[/yellow]
""")
    
    def version_info(self, full: bool = False):
        """版本信息"""
        if GROUPS_AVAILABLE:
            self.doctor.version(full=full)
        else:
            from maque import __version__
            print(f"maque {__version__}")
            if full:
                print("运行模式: 兼容模式")
    
    def show_welcome(self):
        """显示欢迎信息"""
        print("""[bold blue]
 ____                                  
/ ___| _ __   __ _ _ __ _ __ _____      __
\\___ \\| '_ \\ / _` | '__| '__/ _ \\ \\ /\\ / /
 ___) | |_) | (_| | |  | | | (_) \\ V  V / 
|____/| .__/ \\__,_|_|  |_|  \\___/ \\_/\\_/  
      |_|                               
[/bold blue]

欢迎使用 Sparrow - 多功能AI工具包!

[bold cyan]快速开始:[/bold cyan]
• 环境检查: [green]maque doctor check[/green]
• 查看帮助: [green]maque help getting-started[/green] 
• 初始化配置: [green]maque init-config[/green]

""" + ("[yellow]当前运行在兼容模式[/yellow]\n" if not GROUPS_AVAILABLE else ""))


# 主CLI类 - 继承原有类以保持完全兼容
class Cli(NewCli):
    """主CLI类 - 集成新旧功能"""
    
    def __init__(self):
        super().__init__()
        
        # 如果新功能不可用，显示提示
        if not GROUPS_AVAILABLE:
            self._show_compatibility_notice()
    
    def _show_compatibility_notice(self):
        """显示兼容性提示"""
        pass  # 静默处理，避免每次初始化都显示

    # 保留原有CLI类的所有方法，通过继承自动包含
    # 这里只需要特殊处理的方法...

    @staticmethod
    def clean_invisible_chars(
        *files,
        dir: str = None,
        pattern: str = "*",
        no_backup: bool = False,
        quiet: bool = False
    ):
        """清理文件中的不可见字符

        清理文件中的不间断空格(U+00A0)和其他常见不可见字符，
        支持单个文件或批量处理，自动备份原文件。

        Args:
            *files: 要处理的文件路径（可以包含通配符）
            dir: 要处理的目录路径
            pattern: 文件匹配模式 (如 "*.py")，仅在指定dir时有效
            no_backup: 不创建备份文件
            quiet: 静默模式

        Examples:
            # 清理单个文件
            maque clean-invisible-chars file.py

            # 清理多个文件
            maque clean-invisible-chars file1.py file2.py

            # 清理当前目录下所有Python文件
            maque clean-invisible-chars "*.py"

            # 递归清理目录下的Python文件
            maque clean-invisible-chars --dir /path/to/dir --pattern "*.py"

            # 清理时不创建备份
            maque clean-invisible-chars file.py --no-backup

            # 静默模式
            maque clean-invisible-chars file.py --quiet
        """
        from pathlib import Path
        import glob as glob_module

        try:
            from .cli.clean_invisible_chars import InvisibleCharCleaner, find_files_by_pattern
        except ImportError as e:
            print(f"[red]无法导入不可见字符清理工具: {e}[/red]")
            return

        # 收集要处理的文件
        file_paths = []

        if dir:
            # 目录模式
            if not os.path.isdir(dir):
                print(f"❌ 目录不存在: {dir}")
                return
            file_paths = find_files_by_pattern(dir, pattern)
            if not file_paths:
                print(f"❌ 在目录 {dir} 中未找到匹配 {pattern} 的文件")
                return
        elif files:
            # 文件列表模式
            for file_pattern in files:
                if "*" in file_pattern or "?" in file_pattern:
                    # 通配符模式
                    matched_files = glob_module.glob(file_pattern)
                    if matched_files:
                        file_paths.extend([Path(f) for f in matched_files])
                    else:
                        print(f"⚠️  未找到匹配 {file_pattern} 的文件")
                else:
                    # 直接文件路径
                    file_path = Path(file_pattern)
                    if file_path.exists():
                        file_paths.append(file_path)
                    else:
                        print(f"⚠️  文件不存在: {file_pattern}")
        else:
            # 没有指定文件或目录
            print("❌ 请指定要处理的文件或目录")
            print("使用示例: maque clean-invisible-chars file.py")
            print("更多帮助: maque clean-invisible-chars --help")
            return

        if not file_paths:
            print("❌ 没有找到要处理的文件")
            return

        # 创建清理器并处理文件
        cleaner = InvisibleCharCleaner(backup=not no_backup, verbose=not quiet)
        cleaner.clean_files(file_paths)

    # =============================================================================
    # 系统工具命令 - 委托给 SystemGroup (保持向后兼容)
    # =============================================================================

    def kill(self, ports, view: bool = False):
        """杀死指定端口的进程 (委托给 system.kill)"""
        if GROUPS_AVAILABLE:
            return self.system.kill(ports, view)
        print("[yellow]系统工具不可用[/yellow]")

    def get_ip(self, env: str = "inner"):
        """获取本机IP地址 (委托给 system.get_ip)"""
        if GROUPS_AVAILABLE:
            return self.system.get_ip(env)
        print("[yellow]系统工具不可用[/yellow]")

    def pack(self, source_path: str, target_path: str = None, format: str = 'gztar'):
        """压缩文件或文件夹 (委托给 system.pack)"""
        if GROUPS_AVAILABLE:
            return self.system.pack(source_path, target_path, format)
        print("[yellow]系统工具不可用[/yellow]")

    def unpack(self, filename: str, extract_dir: str = None, format: str = None):
        """解压文件 (委托给 system.unpack)"""
        if GROUPS_AVAILABLE:
            return self.system.unpack(filename, extract_dir, format)
        print("[yellow]系统工具不可用[/yellow]")

    def split(self, file_path: str, chunk_size: str = "1G"):
        """将大文件分割成多个块 (委托给 system.split)"""
        if GROUPS_AVAILABLE:
            return self.system.split(file_path, chunk_size)
        print("[yellow]系统工具不可用[/yellow]")

    def merge(self, input_prefix: str, input_dir: str = '.', output_path: str = None):
        """合并分割后的文件块 (委托给 system.merge)"""
        if GROUPS_AVAILABLE:
            return self.system.merge(input_prefix, input_dir, output_path)
        print("[yellow]系统工具不可用[/yellow]")

    def gen_key(self, name: str, email: str = None, key_type: str = 'rsa'):
        """生成SSH密钥对 (委托给 system.gen_key)"""
        if GROUPS_AVAILABLE:
            return self.system.gen_key(name, email, key_type)
        print("[yellow]系统工具不可用[/yellow]")

    def timer(self, interval: float = 0.05):
        """交互式计时器工具 (委托给 system.timer)"""
        if GROUPS_AVAILABLE:
            return self.system.timer(interval)
        print("[yellow]系统工具不可用[/yellow]")


def fire_commands():
    import os
    import sys
    import fire
    # less 分页器配置（仅 Unix-like 系统）
    # -R 保留颜色，-X 退出后内容保留在屏幕，-F 内容少时直接输出
    if sys.platform != 'win32':
        os.environ['PAGER'] = 'less -RXF'
    fire.Fire(Cli)


def typer_commands():
    import typer
    app = typer.Typer()
    # [app.command()(i) for i in func_list]
    # app()


def main():
    # 检查是否请求帮助信息
    import sys

    if len(sys.argv) > 1:
        first_arg = sys.argv[1].lower()

        # 特殊处理一些命令
        if first_arg == "welcome":
            cli = Cli()
            cli.show_welcome()
            return
        elif first_arg == "quick-start":
            cli = Cli()
            cli.quick_start()
            return
        elif first_arg == "git":
            # git 命令直接代理到 dulwich，绕过 fire 的参数解析
            try:
                from dulwich.cli import main as dulwich_main
                sys.argv = ['dulwich'] + sys.argv[2:]  # 移除 'spr' 和 'git'
                sys.exit(dulwich_main())
            except ImportError:
                print("错误: dulwich 未安装，请运行: pip install dulwich")
                sys.exit(1)
    
    # 添加自动补全支持
    try:
        import argcomplete
        
        # 为 fire 命令设置自动补全
        if len(sys.argv) > 1 and sys.argv[1] in ['--completion-script', '--completion']:
            # 生成补全脚本
            print(f"""
# 将以下内容添加到你的 shell 配置文件中 (如 ~/.bashrc, ~/.zshrc):

# For bash:
eval "$(_MQ_COMPLETE=bash_source mq)"
eval "$(_MAQUE_COMPLETE=bash_source maque)"

# For zsh:
eval "$(_MQ_COMPLETE=zsh_source mq)"
eval "$(_MAQUE_COMPLETE=zsh_source maque)"

# 或者运行以下命令来安装补全:
activate-global-python-argcomplete
""")
            return
            
        # 尝试启用 argcomplete (如果可用)
        argcomplete.autocomplete(None)
    except ImportError:
        pass  # argcomplete 不可用时忽略
    
    fire_commands()


if __name__ == "__main__":
    main()
