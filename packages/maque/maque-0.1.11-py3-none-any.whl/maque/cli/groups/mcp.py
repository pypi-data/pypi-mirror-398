"""MCP Server 命令组"""
import subprocess

from rich import print
from rich.table import Table
from rich.console import Console


class MCPGroup:
    """MCP Server 管理命令组

    提供 maque 的 MCP (Model Context Protocol) 服务管理功能，
    让 AI Agent 能够查询 maque 的 API 文档。
    """

    def __init__(self, cli_instance):
        self.cli = cli_instance
        self.console = Console()

    def serve(self, port: int = 8765, host: str = "0.0.0.0"):
        """启动 MCP Server（SSE 模式，独立 HTTP 服务）

        Args:
            port: 服务端口，默认 8765
            host: 绑定地址，默认 0.0.0.0

        Examples:
            maque mcp serve
            maque mcp serve --port=9000
        """
        from maque.mcp_server import main_sse

        print(f"[bold blue]启动 MCP Server (SSE 模式)[/bold blue]")
        print(f"  地址: http://{host}:{port}")
        print(f"  配置: claude mcp add maque --transport sse --url http://localhost:{port}/sse")
        print()

        main_sse(host=host, port=port)

    def install(self, scope: str = "user", name: str = "maque"):
        """将 MCP Server 配置到 Claude Code

        Args:
            scope: 配置作用域，'user' 或 'project'，默认 'user'
            name: MCP Server 名称，默认 'maque'

        Examples:
            maque mcp install
            maque mcp install --scope=project
        """
        cmd = [
            "claude", "mcp", "add", name,
            f"--scope={scope}",
            "--",
            "python", "-m", "maque.mcp_server"
        ]

        print(f"[blue]配置 MCP Server 到 Claude Code...[/blue]")
        print(f"  作用域: {scope}")
        print()

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[green]✓ MCP Server '{name}' 已配置[/green]")
                print(f"  重启 Claude Code 后生效")
                print(f"  验证: 在 Claude Code 中输入 /mcp")
            else:
                print(f"[red]配置失败: {result.stderr}[/red]")
        except FileNotFoundError:
            print("[red]错误: 未找到 claude 命令[/red]")
            print("请确保已安装 Claude Code CLI")

    def uninstall(self, name: str = "maque", scope: str = "user"):
        """从 Claude Code 移除 MCP Server 配置

        Args:
            name: MCP Server 名称，默认 'maque'
            scope: 配置作用域，默认 'user'

        Examples:
            maque mcp uninstall
        """
        cmd = ["claude", "mcp", "remove", name, f"--scope={scope}"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[green]✓ MCP Server '{name}' 已移除[/green]")
            else:
                print(f"[red]移除失败: {result.stderr}[/red]")
        except FileNotFoundError:
            print("[red]错误: 未找到 claude 命令[/red]")

    def status(self):
        """查看 MCP Server 配置状态

        Examples:
            maque mcp status
        """
        try:
            result = subprocess.run(
                ["claude", "mcp", "list"],
                capture_output=True,
                text=True
            )
            print("[bold blue]Claude Code MCP 配置状态[/bold blue]\n")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
        except FileNotFoundError:
            print("[red]错误: 未找到 claude 命令[/red]")

    def test(self, with_llm: bool = False):
        """测试 MCP Server 功能

        Args:
            with_llm: 是否测试 LLM 调用功能（需要 LLM 服务运行中）

        Examples:
            maque mcp test
            maque mcp test --with_llm
        """
        print("[bold blue]测试 MCP Server 功能[/bold blue]\n")

        from maque.mcp_server import search_maque, get_module_info, list_all_modules

        # 测试 list_modules
        print("[cyan]1. 测试 list_maque_modules()[/cyan]")
        modules = list_all_modules()
        print(f"   返回 {len(modules.split('##')) - 1} 个模块")
        print("[green]   ✓ 通过[/green]\n")

        # 测试 search
        print("[cyan]2. 测试 search_maque_api('embedding')[/cyan]")
        results = search_maque("embedding")
        print(f"   找到 {len(results)} 个结果")
        if results:
            print(f"   首个结果: {results[0].name} ({results[0].module})")
        print("[green]   ✓ 通过[/green]\n")

        # 测试 get_module_usage
        print("[cyan]3. 测试 get_module_usage('mllm')[/cyan]")
        usage = get_module_info("mllm")
        print(f"   返回 {len(usage)} 字符的使用示例")
        print("[green]   ✓ 通过[/green]\n")

        # 测试 LLM 配置
        print("[cyan]4. 测试 llm_config()[/cyan]")
        from maque.mcp_server import llm_config
        config = llm_config()
        print(f"   base_url: {config.get('base_url')}")
        print(f"   model: {config.get('model')}")
        print("[green]   ✓ 通过[/green]\n")

        # 可选：测试 LLM 调用
        if with_llm:
            import asyncio
            print("[cyan]5. 测试 llm_chat()[/cyan]")
            from maque.mcp_server import llm_chat
            try:
                result = asyncio.run(llm_chat(
                    messages=[{"role": "user", "content": "说'测试成功'三个字"}],
                    max_tokens=20,
                ))
                print(f"   LLM 回复: {result[:50]}...")
                print("[green]   ✓ 通过[/green]\n")
            except Exception as e:
                print(f"[red]   ✗ LLM 调用失败: {e}[/red]\n")
        else:
            print("[dim]跳过 LLM 调用测试（使用 --with_llm 启用）[/dim]\n")

        print("[bold green]测试完成！[/bold green]")

    def tools(self):
        """列出 MCP Server 提供的工具

        Examples:
            maque mcp tools
        """
        # API 文档查询工具
        table1 = Table(title="API 文档查询工具", show_header=True)
        table1.add_column("工具名", style="cyan")
        table1.add_column("说明", style="green")
        table1.add_column("参数", style="yellow")

        table1.add_row(
            "search_maque_api",
            "搜索 maque 中的 API（类、函数、模块）",
            "keyword: str"
        )
        table1.add_row(
            "get_module_usage",
            "获取模块的详细使用示例",
            "module: str"
        )
        table1.add_row(
            "list_maque_modules",
            "列出所有核心模块",
            "无"
        )
        table1.add_row(
            "list_cli_commands",
            "列出所有 CLI 命令",
            "无"
        )

        self.console.print(table1)
        print()

        # LLM 调用工具
        table2 = Table(title="LLM 调用工具", show_header=True)
        table2.add_column("工具名", style="cyan")
        table2.add_column("说明", style="green")
        table2.add_column("参数", style="yellow")

        table2.add_row(
            "llm_chat",
            "调用 LLM 进行单条聊天",
            "messages, model?, max_tokens?, temperature?"
        )
        table2.add_row(
            "llm_chat_batch",
            "批量调用 LLM",
            "messages_list, model?, max_tokens?, temperature?"
        )
        table2.add_row(
            "llm_models",
            "获取可用模型列表",
            "无"
        )
        table2.add_row(
            "llm_config",
            "获取当前 LLM 配置",
            "无"
        )

        self.console.print(table2)

        print("\n[dim]在 Claude Code 中，AI 会自动调用这些工具[/dim]")
        print("[dim]LLM 配置来自 ~/.maque/config.yaml 或项目中的 maque_config.yaml[/dim]")
