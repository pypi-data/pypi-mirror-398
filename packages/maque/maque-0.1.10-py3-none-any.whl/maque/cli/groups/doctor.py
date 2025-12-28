"""环境检查和诊断命令组"""
import os
import sys
import subprocess
import importlib
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print


class DoctorGroup:
    """环境检查和诊断命令组"""
    
    def __init__(self, cli_instance):
        self.cli = cli_instance
        self.console = Console()
    
    def check(self, verbose: bool = False):
        """检查环境和依赖"""
        print("[bold blue]Sparrow 环境诊断[/bold blue]\n")
        
        issues = []
        
        # 检查Python版本
        issues.extend(self._check_python_version(verbose))
        
        # 检查核心依赖
        issues.extend(self._check_core_dependencies(verbose))
        
        # 检查可选依赖
        issues.extend(self._check_optional_dependencies(verbose))
        
        # 检查配置文件
        issues.extend(self._check_config_files(verbose))
        
        # 检查服务连接
        issues.extend(self._check_services(verbose))
        
        # 汇总结果
        print("\n" + "="*50)
        if issues:
            print(f"[yellow]发现 {len(issues)} 个问题:[/yellow]")
            for i, issue in enumerate(issues, 1):
                print(f"{i}. [yellow]{issue}[/yellow]")
            
            print(f"\n[bold cyan]建议运行 'maque doctor fix' 来自动修复部分问题[/bold cyan]")
        else:
            print("[green]✓ 环境检查完成，未发现问题[/green]")
        
        return len(issues) == 0
    
    def _check_python_version(self, verbose):
        """检查Python版本"""
        issues = []
        python_version = sys.version_info
        
        if verbose or python_version < (3, 8):
            print(f"Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        if python_version < (3, 8):
            issues.append("Python版本过低，建议使用Python 3.8+")
        elif verbose:
            print("[green]✓[/green] Python版本符合要求")
        
        return issues
    
    def _check_core_dependencies(self, verbose):
        """检查核心依赖"""
        core_deps = [
            'fire',
            'rich', 
            'pyyaml',
            'requests',
            'pathlib'  # 标准库，但检查兼容性
        ]
        
        issues = []
        
        if verbose:
            print("\n[bold]核心依赖检查:[/bold]")
        
        for dep in core_deps:
            try:
                importlib.import_module(dep.replace('-', '_'))
                if verbose:
                    print(f"[green]✓[/green] {dep}")
            except ImportError:
                issues.append(f"缺少核心依赖: {dep}")
                if verbose:
                    print(f"[red]✗[/red] {dep} - 未安装")
        
        return issues
    
    def _check_optional_dependencies(self, verbose):
        """检查可选依赖"""
        optional_deps = {
            'cv2': 'opencv-python (视频处理)',
            'torch': 'torch (深度学习)',
            'pandas': 'pandas (数据处理)',
            'numpy': 'numpy (数值计算)',
            'PIL': 'pillow (图像处理)',
            'httpx': 'httpx (异步HTTP客户端)',
            'uvicorn': 'uvicorn (Web服务器)'
        }
        
        issues = []
        missing_optional = []
        
        if verbose:
            print("\n[bold]可选依赖检查:[/bold]")
        
        for dep, description in optional_deps.items():
            try:
                importlib.import_module(dep)
                if verbose:
                    print(f"[green]✓[/green] {dep} - {description}")
            except ImportError:
                missing_optional.append(f"{dep} ({description})")
                if verbose:
                    print(f"[yellow]○[/yellow] {dep} - {description} (未安装)")
        
        if missing_optional and not verbose:
            # 非详细模式下只提示有多少个可选依赖未安装
            print(f"[yellow]提示: {len(missing_optional)} 个可选依赖未安装，某些功能可能不可用[/yellow]")
        
        return issues
    
    def _check_config_files(self, verbose):
        """检查配置文件"""
        issues = []
        
        if verbose:
            print("\n[bold]配置文件检查:[/bold]")
        
        config_paths = self.cli._get_config_search_paths()
        found_config = False
        
        for path in config_paths:
            if path.exists():
                found_config = True
                try:
                    # 验证配置文件
                    config = self.cli._load_maque_config()
                    if verbose:
                        print(f"[green]✓[/green] 配置文件: {path}")
                    break
                except Exception as e:
                    issues.append(f"配置文件错误: {path} - {e}")
                    if verbose:
                        print(f"[red]✗[/red] 配置文件: {path} - 错误: {e}")
        
        if not found_config:
            if verbose:
                print("[yellow]○[/yellow] 未找到配置文件，将使用默认配置")
        
        return issues
    
    def _check_services(self, verbose):
        """检查服务连接"""
        issues = []
        
        if verbose:
            print("\n[bold]服务连接检查:[/bold]")
        
        # 检查MLLM服务
        mllm_config = self.cli.maque_config.get('mllm', {})
        base_url = mllm_config.get('base_url')
        
        if base_url:
            try:
                import requests
                # 简单的连接测试
                response = requests.get(f"{base_url.rstrip('/')}/models", timeout=5)
                if response.status_code == 200:
                    if verbose:
                        print(f"[green]✓[/green] MLLM服务: {base_url}")
                else:
                    issues.append(f"MLLM服务响应异常: {base_url} (状态码: {response.status_code})")
            except requests.RequestException as e:
                issues.append(f"无法连接MLLM服务: {base_url}")
                if verbose:
                    print(f"[red]✗[/red] MLLM服务: {base_url} - {e}")
            except ImportError:
                pass  # requests未安装，已在依赖检查中处理

        return issues
    
    def fix(self, auto: bool = False):
        """自动修复常见问题
        
        Args:
            auto: 自动修复而不询问
        """
        print("[bold blue]自动修复工具[/bold blue]\n")
        
        fixes_applied = 0
        
        # 检查并创建配置文件
        config_paths = self.cli._get_config_search_paths()
        has_config = any(p.exists() for p in config_paths)
        
        if not has_config:
            if auto or self._confirm("创建默认配置文件？"):
                self.cli.init_config()
                print("[green]✓[/green] 已创建默认配置文件")
                fixes_applied += 1
        
        # 可以添加更多自动修复逻辑...
        
        if fixes_applied > 0:
            print(f"\n[green]已应用 {fixes_applied} 个修复[/green]")
        else:
            print("[yellow]未发现可自动修复的问题[/yellow]")
    
    def _confirm(self, message):
        """确认对话"""
        response = input(f"{message} (y/N): ")
        return response.lower() == 'y'
    
    def version(self, full: bool = False):
        """显示版本信息
        
        Args:
            full: 显示详细版本信息
        """
        from maque import __version__
        
        if not full:
            print(f"maque {__version__}")
            return
        
        # 详细版本信息
        print(f"[bold blue]Sparrow v{__version__}[/bold blue]\n")
        
        # Python信息
        print(f"Python: {sys.version}")
        print(f"平台: {sys.platform}")
        
        # 安装位置
        maque_path = Path(__file__).parent.parent.parent
        print(f"安装路径: {maque_path}")
        
        # 依赖版本
        deps_info = []
        key_deps = ['fire', 'rich', 'requests', 'pyyaml']
        
        for dep in key_deps:
            try:
                mod = importlib.import_module(dep)
                version = getattr(mod, '__version__', 'unknown')
                deps_info.append(f"{dep}: {version}")
            except ImportError:
                deps_info.append(f"{dep}: 未安装")
        
        if deps_info:
            print(f"\n依赖版本:")
            for info in deps_info:
                print(f"  {info}")