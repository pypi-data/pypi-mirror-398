"""简化版的MLLM chat命令测试"""

from rich.console import Console

console = Console(force_terminal=True, width=120)


def safe_print(*args, **kwargs):
    """安全的打印函数，确保在所有终端中正确显示颜色"""
    try:
        console.print(*args, **kwargs)
    except Exception:
        # 降级到普通print，去除markup
        clean_args = []
        for arg in args:
            if isinstance(arg, str):
                # 简单去除rich markup
                import re

                clean_arg = re.sub(r"\[/?[^\]]*\]", "", str(arg))
                clean_args.append(clean_arg)
            else:
                clean_args.append(arg)
        print(*clean_args, **kwargs)


def simple_chat(cli_instance, message: str = None, model: str = None):
    """简化的chat命令测试"""
    import asyncio
    from maque.mllm.mllm_client import MllmClient

    async def _chat():
        # 从配置获取默认值
        mllm_config = cli_instance.maque_config.get("mllm", {})
        model_name = model or mllm_config.get("model", "gemma3:latest")
        base_url = mllm_config.get("base_url", "http://localhost:11434/v1")
        api_key = mllm_config.get("api_key", "EMPTY")

        # 初始化客户端
        client = MllmClient(model=model_name, base_url=base_url, api_key=api_key)

        if message:
            try:
                messages = [{"role": "user", "content": message}]
                results = await client.call_llm(messages_list=[messages])
                response = results[0] if results and results[0] else "无响应"
                safe_print(f"[bold blue]Assistant:[/bold blue] {response}")
                return response
            except Exception as e:
                safe_print(f"[red]错误: {e}[/red]")
                return None
        else:
            safe_print("[yellow]请提供消息内容[/yellow]")
            return None

    try:
        return asyncio.run(_chat())
    except Exception as e:
        safe_print(f"[red]运行错误: {e}[/red]")
        return None
