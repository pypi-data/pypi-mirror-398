"""配置管理命令组"""
import os
import yaml
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import print


class ConfigGroup:
    """配置管理命令组"""
    
    def __init__(self, cli_instance):
        self.cli = cli_instance
        self.console = Console()
    
    def show(self):
        """显示当前配置"""
        config = self.cli.maque_config
        
        print("[bold blue]Sparrow 配置信息[/bold blue]\n")
        
        # 显示配置来源
        config_paths = self.cli._get_config_search_paths()
        for path in config_paths:
            if path.exists():
                print(f"[green]✓[/green] 配置文件: {path}")
                break
        else:
            print("[yellow]⚠[/yellow] 未找到配置文件，使用默认配置")
        
        print("\n[bold]当前配置:[/bold]")
        self._print_config_dict(config, indent=0)
    
    def _print_config_dict(self, config, indent=0):
        """递归打印配置字典"""
        prefix = "  " * indent
        for key, value in config.items():
            if isinstance(value, dict):
                print(f"{prefix}[cyan]{key}[/cyan]:")
                self._print_config_dict(value, indent + 1)
            else:
                print(f"{prefix}[cyan]{key}[/cyan]: [green]{value}[/green]")
    
    def edit(self, editor: str = None):
        """交互式编辑配置文件
        
        Args:
            editor: 使用的编辑器，默认使用系统默认编辑器
        """
        config_paths = self.cli._get_config_search_paths()
        
        # 寻找现有配置文件
        config_file = None
        for path in config_paths:
            if path.exists():
                config_file = path
                break
        
        # 如果没有配置文件，创建一个
        if not config_file:
            config_file = self.cli._get_default_config_path()
            if not config_file.exists():
                self.cli.init_config()
        
        # 使用编辑器打开
        editor_cmd = editor or os.environ.get('EDITOR', 'notepad' if os.name == 'nt' else 'nano')
        os.system(f'{editor_cmd} "{config_file}"')
        
        print(f"[green]配置文件已编辑: {config_file}[/green]")
        print("重新启动maque以应用新配置")
    
    def validate(self):
        """验证配置文件"""
        print("[bold blue]验证配置文件...[/bold blue]\n")
        
        config_paths = self.cli._get_config_search_paths()
        errors = []
        
        for path in config_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                    print(f"[green]✓[/green] {path} - 语法正确")
                    
                    # 验证配置内容
                    config = self.cli._load_maque_config()
                    self._validate_config_content(config, errors)
                    break
                    
                except yaml.YAMLError as e:
                    errors.append(f"{path}: YAML语法错误 - {e}")
                except Exception as e:
                    errors.append(f"{path}: 读取错误 - {e}")
        
        if errors:
            print("\n[bold red]发现配置错误:[/bold red]")
            for error in errors:
                print(f"[red]✗[/red] {error}")
            return False
        else:
            print("\n[green]✓ 配置验证通过[/green]")
            return True
    
    def _validate_config_content(self, config, errors):
        """验证配置内容的合理性"""
        # 验证MLLM配置
        if 'mllm' in config:
            mllm_config = config['mllm']
            if 'base_url' in mllm_config:
                url = mllm_config['base_url']
                if not (url.startswith('http://') or url.startswith('https://')):
                    errors.append("mllm.base_url 应该以 http:// 或 https:// 开头")
    
    def set(self, key: str, value: str, config_file: str = None):
        """设置配置值

        Args:
            key: 配置键，支持点号分隔如 'mllm.model'
            value: 配置值
            config_file: 指定配置文件路径，默认使用 ~/.maque/config.yaml
        """
        if config_file is None:
            config_path = self.cli._get_default_config_path()
        else:
            config_path = Path(config_file)
        
        # 加载现有配置
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        # 设置嵌套键值
        keys = key.split('.')
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 尝试转换值的类型
        try:
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)
        except:
            pass  # 保持字符串类型
        
        current[keys[-1]] = value
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"[green]✓[/green] 已设置 {key} = {value}")
        print(f"配置保存到: {config_path.resolve()}")
    
    def get(self, key: str = None):
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔如 'mllm.model'，为空则显示所有配置
        """
        if key is None:
            return self.show()
        
        value = self.cli.get_config(key)
        if value is not None:
            print(f"[cyan]{key}[/cyan]: [green]{value}[/green]")
        else:
            print(f"[yellow]配置项 '{key}' 不存在[/yellow]")
        
        return value
    
    def reset(self, confirm: bool = False):
        """重置配置到默认值
        
        Args:
            confirm: 确认重置，为False时会提示确认
        """
        if not confirm:
            response = input("确定要重置配置到默认值吗？这会覆盖现有配置 (y/N): ")
            if response.lower() != 'y':
                print("操作已取消")
                return
        
        config_paths = self.cli._get_config_search_paths()
        for path in config_paths:
            if path.exists():
                # 备份现有配置
                backup_path = path.with_suffix(path.suffix + '.backup')
                path.rename(backup_path)
                print(f"原配置已备份到: {backup_path}")
                break
        
        # 创建新的默认配置
        self.cli.init_config()
        print("[green]配置已重置为默认值[/green]")