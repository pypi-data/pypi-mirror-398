"""帮助和文档系统"""
import inspect
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print


class HelpGroup:
    """帮助和文档命令组"""
    
    def __init__(self, cli_instance):
        self.cli = cli_instance
        self.console = Console()
    
    def examples(self, command: str = None):
        """显示命令使用示例
        
        Args:
            command: 命令名称，不指定则显示所有示例
        """
        examples_data = {
            "config": {
                "description": "配置管理",
                "examples": [
                    {
                        "desc": "查看当前配置",
                        "cmd": "maque config show"
                    },
                    {
                        "desc": "设置MLLM模型",
                        "cmd": "maque config set mllm.model gpt-4o-mini"
                    },
                    {
                        "desc": "编辑配置文件",
                        "cmd": "maque config edit"
                    },
                    {
                        "desc": "验证配置文件",
                        "cmd": "maque config validate"
                    }
                ]
            },
            "mllm": {
                "description": "多模态大语言模型",
                "examples": [
                    {
                        "desc": "批量处理表格中的图像",
                        "cmd": "maque mllm call-table images.xlsx --output_file=results.csv"
                    },
                    {
                        "desc": "批量处理文件夹中的图像",
                        "cmd": "maque mllm call-images ./photos --max_num=100"
                    },
                    {
                        "desc": "交互式聊天",
                        "cmd": "maque mllm chat"
                    },
                    {
                        "desc": "单次图像分析",
                        "cmd": "maque mllm chat \"描述这张图片\" --image=photo.jpg"
                    },
                    {
                        "desc": "列出可用模型",
                        "cmd": "maque mllm models"
                    }
                ]
            },
            "doctor": {
                "description": "环境诊断",
                "examples": [
                    {
                        "desc": "检查环境和依赖",
                        "cmd": "maque doctor check"
                    },
                    {
                        "desc": "详细环境检查",
                        "cmd": "maque doctor check --verbose"
                    },
                    {
                        "desc": "自动修复问题",
                        "cmd": "maque doctor fix"
                    },
                    {
                        "desc": "显示详细版本信息",
                        "cmd": "maque doctor version --full"
                    }
                ]
            },
            "data": {
                "description": "数据处理",
                "examples": [
                    {
                        "desc": "启动表格查看器",
                        "cmd": "maque data table-viewer data.xlsx"
                    },
                    {
                        "desc": "数据格式转换",
                        "cmd": "maque data convert input.xlsx output.csv"
                    },
                    {
                        "desc": "数据统计分析",
                        "cmd": "maque data stats data.csv"
                    }
                ]
            },
            "video": {
                "description": "视频处理",
                "examples": [
                    {
                        "desc": "视频去重（提取唯一帧）",
                        "cmd": "maque video-dedup video.mp4 --method=phash"
                    },
                    {
                        "desc": "帧图像合成视频",
                        "cmd": "maque frames-to-video ./frames --fps=30"
                    },
                    {
                        "desc": "一步完成去重和合成",
                        "cmd": "maque dedup-and-create-video input.mp4 --video_fps=15"
                    }
                ]
            }
        }
        
        if command:
            if command in examples_data:
                self._show_command_examples(command, examples_data[command])
            else:
                print(f"[red]未找到命令 '{command}' 的示例[/red]")
                self._list_available_commands(examples_data)
        else:
            # 显示所有示例
            print("[bold blue]Sparrow 命令示例[/bold blue]\n")
            for cmd, data in examples_data.items():
                self._show_command_examples(cmd, data, compact=True)
    
    def _show_command_examples(self, command, data, compact=False):
        """显示单个命令的示例"""
        if compact:
            print(f"[bold cyan]{command}[/bold cyan] - {data['description']}")
            for example in data['examples'][:2]:  # 只显示前2个示例
                print(f"  [green]${example['cmd']}[/green]")
                if not compact:
                    print(f"    {example['desc']}")
            if len(data['examples']) > 2:
                print(f"  ... 更多示例请使用: maque help examples {command}")
            print()
        else:
            print(f"[bold blue]{command} 命令示例[/bold blue]")
            print(f"{data['description']}\n")
            
            for i, example in enumerate(data['examples'], 1):
                print(f"[bold]{i}. {example['desc']}[/bold]")
                print(f"   [green]$ {example['cmd']}[/green]\n")
    
    def _list_available_commands(self, examples_data):
        """列出可用的命令"""
        print("\n[bold]可用命令:[/bold]")
        for cmd in examples_data.keys():
            print(f"  [cyan]{cmd}[/cyan]")
    
    def cheatsheet(self):
        """显示快速参考表"""
        print(Panel.fit(
            """[bold blue]Sparrow 快速参考[/bold blue]

[bold cyan]配置管理[/bold cyan]
maque config show              # 查看配置
maque config set key value     # 设置配置
maque config edit              # 编辑配置

[bold cyan]环境诊断[/bold cyan]  
maque doctor check             # 环境检查
maque doctor fix               # 自动修复

[bold cyan]多模态AI[/bold cyan]
maque mllm chat                # 交互聊天
maque mllm call-images ./imgs  # 批量图像分析
maque mllm models              # 列出模型

[bold cyan]数据处理[/bold cyan]
maque data table-viewer file   # 表格查看器
maque data convert a.xlsx b.csv # 格式转换

[bold cyan]视频处理[/bold cyan]
maque video-dedup video.mp4    # 视频去重
maque frames-to-video ./frames # 合成视频

[bold cyan]开发工具[/bold cyan]
maque create myproject         # 创建项目
maque download model-name      # 下载模型

获得更多帮助: maque help examples <command>""",
            title="快速参考",
            border_style="blue"
        ))
    
    def topics(self, topic: str = None):
        """显示主题帮助
        
        Args:
            topic: 主题名称
        """
        topics_data = {
            "configuration": {
                "title": "配置文件详解",
                "content": """
[bold]配置文件位置（按优先级）:[/bold]
1. 当前目录: ./maque_config.yaml
2. 项目根目录: <project>/maque_config.yaml
3. 用户目录: ~/.maque/config.yaml

[bold]配置文件结构:[/bold]
```yaml
# 多模态大语言模型配置
mllm:
  model: "gpt-4o-mini"
  base_url: "https://api.openai.com/v1"
  api_key: "your-api-key"
  
# 其他设置...
```

[bold]常用配置命令:[/bold]
maque config show              # 查看当前配置
maque config set mllm.model gpt-4o  # 设置模型
maque config validate          # 验证配置文件
"""
            },
            "models": {
                "title": "模型支持说明",
                "content": """
[bold]支持的模型类型:[/bold]
• OpenAI兼容API (GPT-4, GPT-4o, Claude等)
• Ollama本地模型 (Llama, Gemma等)
• vLLM服务器部署的模型
• 其他OpenAI API兼容服务

[bold]模型配置示例:[/bold]
# OpenAI官方
maque config set mllm.model gpt-4o-mini
maque config set mllm.base_url https://api.openai.com/v1
maque config set mllm.api_key your-openai-key

# Ollama本地
maque config set mllm.model llama3:latest  
maque config set mllm.base_url http://localhost:11434/v1
maque config set mllm.api_key EMPTY

# 自定义服务
maque config set mllm.base_url http://your-server:8000/v1

[bold]查看可用模型:[/bold]
maque mllm models
"""
            },
            "troubleshooting": {
                "title": "故障排除",
                "content": """
[bold]常见问题解决:[/bold]

[bold cyan]1. 环境检查[/bold cyan]
maque doctor check --verbose   # 详细诊断
maque doctor fix               # 自动修复

[bold cyan]2. 依赖问题[/bold cyan]
pip install maque[dev]         # 安装开发依赖
pip install maque[torch]       # 安装深度学习依赖
pip install maque[video]       # 安装视频处理依赖

[bold cyan]3. 配置问题[/bold cyan]
maque config validate          # 验证配置
maque config reset             # 重置为默认配置

[bold cyan]4. 模型连接问题[/bold cyan]
maque mllm models              # 检查模型连接
curl http://localhost:11434      # 测试Ollama连接

[bold cyan]5. 权限问题[/bold cyan]
# Windows: 以管理员运行
# Linux/macOS: 检查文件权限
ls -la ~/.maque/config.yaml

获得更多帮助: https://github.com/your-repo/issues
"""
            }
        }
        
        if topic:
            if topic in topics_data:
                topic_info = topics_data[topic]
                print(Panel(
                    topic_info["content"].strip(),
                    title=topic_info["title"],
                    border_style="cyan"
                ))
            else:
                print(f"[red]未找到主题 '{topic}'[/red]")
                self._list_available_topics(topics_data)
        else:
            print("[bold blue]可用帮助主题:[/bold blue]\n")
            for topic_key, topic_info in topics_data.items():
                print(f"[cyan]{topic_key:<15}[/cyan] {topic_info['title']}")
            print(f"\n使用方法: maque help topics <topic>")
    
    def _list_available_topics(self, topics_data):
        """列出可用主题"""
        print("\n[bold]可用主题:[/bold]")
        for topic in topics_data.keys():
            print(f"  [cyan]{topic}[/cyan]")
    
    def commands(self, group: str = None):
        """列出所有命令或指定组的命令
        
        Args:
            group: 命令组名称
        """
        # 获取所有可用命令
        command_groups = {
            "config": ["show", "edit", "validate", "set", "get", "reset"],
            "mllm": ["call-table", "call-images", "chat", "models", "benchmark"],
            "doctor": ["check", "fix", "version"],
            "data": ["table-viewer", "convert", "stats", "validate"],
            "service": ["list", "status", "start", "stop", "logs"],
            "video": ["dedup", "frames-to-video", "dedup-and-create-video"],
            "legacy": ["传统单层命令", "如 download, create, split 等"]
        }
        
        if group:
            if group in command_groups:
                print(f"[bold blue]{group} 命令组[/bold blue]\n")
                if group == "legacy":
                    # 显示传统命令说明
                    print("[yellow]注意: 以下为传统单层命令，建议使用新的分组命令[/yellow]\n")
                    legacy_commands = [
                        "download", "create", "split", "merge", "pack", "unpack",
                        "clone", "gen-key", "send", "recv", "kill", "auto-commit"
                    ]
                    for cmd in legacy_commands:
                        print(f"  [dim cyan]{cmd}[/dim cyan]")
                else:
                    for cmd in command_groups[group]:
                        print(f"  [cyan]maque {group} {cmd}[/cyan]")
                
                print(f"\n获取详细帮助: maque help examples {group}")
            else:
                print(f"[red]未找到命令组 '{group}'[/red]")
                self._list_command_groups(command_groups)
        else:
            print("[bold blue]Sparrow 命令列表[/bold blue]\n")
            
            for group_name, commands in command_groups.items():
                if group_name == "legacy":
                    continue
                    
                print(f"[bold cyan]{group_name}[/bold cyan]")
                for cmd in commands[:3]:  # 只显示前3个命令
                    print(f"  maque {group_name} {cmd}")
                if len(commands) > 3:
                    print(f"  ... 共 {len(commands)} 个命令")
                print()
            
            print("[dim]使用 'maque help commands <group>' 查看特定组的所有命令[/dim]")
    
    def _list_command_groups(self, command_groups):
        """列出可用的命令组"""
        print("\n[bold]可用命令组:[/bold]")
        for group in command_groups.keys():
            if group != "legacy":
                print(f"  [cyan]{group}[/cyan]")
    
    def getting_started(self):
        """显示入门指南"""
        guide = """[bold blue]Sparrow 快速入门[/bold blue]

[bold]1. 环境检查[/bold]
首先检查你的环境是否配置正确:
[green]$ maque doctor check[/green]

[bold]2. 初始化配置[/bold]  
创建配置文件并设置你的偏好:
[green]$ maque config show[/green]
[green]$ maque config set mllm.model your-preferred-model[/green]

[bold]3. 尝试核心功能[/bold]
• 多模态AI分析:
  [green]$ maque mllm chat "Hello!"[/green]
  
• 数据处理:
  [green]$ maque data table-viewer your-data.xlsx[/green]
  
• 视频处理:
  [green]$ maque video-dedup your-video.mp4[/green]

[bold]4. 探索更多功能[/bold]
查看所有可用命令:
[green]$ maque help commands[/green]

查看具体示例:
[green]$ maque help examples mllm[/green]

[bold]5. 获得帮助[/bold]
• 快速参考: [green]maque help cheatsheet[/green]
• 主题帮助: [green]maque help topics configuration[/green]
• 故障排除: [green]maque help topics troubleshooting[/green]

准备好开始了吗？试试: [green]maque doctor check[/green]
"""
        print(Panel(guide.strip(), title="快速入门指南", border_style="green"))
