"""LLM 服务命令组"""
from rich import print
from rich.console import Console


class LlmGroup:
    """LLM 服务命令组

    提供 LLM/MLLM 模型服务的启动、管理功能，
    支持纯文本 LLM 和多模态 VL 模型。
    """

    def __init__(self, cli_instance):
        self.cli = cli_instance
        self.console = Console()

    def serve(
        self,
        model: str,
        host: str = "0.0.0.0",
        port: int = 8000,
        device: str = None,
        local_dir: str = None,
        dtype: str = None,
        attn: str = None,
        model_class: str = None,
        processor_class: str = None,
        vision_processor: str = None,
        enable_thinking: bool = False,
    ):
        """启动 LLM/MLLM API 服务

        启动兼容 OpenAI 的 Chat Completions API 服务，
        自动检测多模态 VL 模型并启用图片处理。

        Args:
            model: 模型名称或路径 (如 Qwen/Qwen2.5-7B-Instruct)
            host: 监听地址，默认 0.0.0.0
            port: 监听端口，默认 8000
            device: 设备类型 (cuda/cpu)，默认自动检测
            local_dir: 本地模型目录
            dtype: 数据类型 (float16/bfloat16/float32)，默认自动选择
            attn: 注意力实现 (eager/sdpa/flash_attention_2)，默认自动选择
            model_class: 模型类名 (如 HunYuanVLForConditionalGeneration)
            processor_class: 处理器类名 (如 AutoProcessor)
            vision_processor: 视觉处理器类型 (qwen_vl/general)
            enable_thinking: 启用 Qwen3 的 thinking 模式

        Examples:
            # 标准 LLM
            maque llm serve Qwen/Qwen2.5-7B-Instruct

            # 多模态 VL 模型
            maque llm serve Qwen/Qwen2.5-VL-3B-Instruct --port=8001

            # 自定义精度和注意力
            maque llm serve model --dtype=float32 --attn=eager

            # HunyuanOCR (自定义模型类)
            maque llm serve tencent/HunyuanOCR --model_class=HunYuanVLForConditionalGeneration --vision_processor=general

            # Qwen3 带 thinking 模式
            maque llm serve Qwen/Qwen3-0.6B --enable_thinking
        """
        try:
            from maque.llm.server import create_server
        except ImportError as e:
            print(f"[red]无法导入 LLM 服务模块: {e}[/red]")
            print("请确保已安装依赖: pip install transformers torch fastapi uvicorn")
            return

        print(f"[bold blue]启动 LLM 服务[/bold blue]")
        print(f"  模型: [cyan]{model}[/cyan]")
        print(f"  地址: [green]http://{host}:{port}[/green]")
        print(f"  设备: [yellow]{device or 'auto'}[/yellow]")
        print(f"  精度: [yellow]{dtype or 'auto'}[/yellow]")
        print(f"  注意力: [yellow]{attn or 'auto'}[/yellow]")
        if local_dir:
            print(f"  本地目录: [magenta]{local_dir}[/magenta]")
        if model_class:
            print(f"  模型类: [cyan]{model_class}[/cyan]")
        if processor_class:
            print(f"  处理器类: [cyan]{processor_class}[/cyan]")
        if vision_processor:
            print(f"  视觉处理器: [cyan]{vision_processor}[/cyan]")
        if enable_thinking:
            print(f"  Thinking 模式: [green]启用[/green]")
        print()

        # 构建 chat_template_kwargs
        chat_template_kwargs = {}
        if enable_thinking:
            chat_template_kwargs["enable_thinking"] = True

        server = create_server(
            model=model,
            device=device,
            local_dir=local_dir,
            dtype=dtype,
            attn=attn,
            model_class=model_class,
            processor_class=processor_class,
            vision_processor=vision_processor,
            chat_template_kwargs=chat_template_kwargs if chat_template_kwargs else None,
        )
        server.run(host=host, port=port)

    def test(
        self,
        url: str = "http://localhost:8000",
        model: str = None,
        prompt: str = "你好，请介绍一下你自己。",
        stream: bool = False,
    ):
        """测试 LLM 服务

        Args:
            url: 服务 URL
            model: 模型名称 (可选，不指定则自动获取)
            prompt: 测试提示词
            stream: 是否使用流式输出

        Examples:
            maque llm test
            maque llm test --stream
            maque llm test --url=http://localhost:8000
        """
        import requests

        # 获取模型名称
        if not model:
            try:
                resp = requests.get(f"{url.rstrip('/')}/v1/models", timeout=5)
                data = resp.json()
                if data.get("data"):
                    model = data["data"][0]["id"]
            except Exception:
                pass

        if not model:
            print("[red]无法获取模型名称，请使用 --model 指定[/red]")
            return

        endpoint = f"{url.rstrip('/')}/v1/chat/completions"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream,
            "max_tokens": 256,
        }

        print(f"[blue]测试 LLM 服务[/blue]")
        print(f"  URL: {endpoint}")
        print(f"  模型: {model}")
        print(f"  提示: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
        print(f"  流式: {stream}")
        print()

        try:
            if stream:
                self._test_stream(endpoint, payload)
            else:
                self._test_normal(endpoint, payload)

        except requests.exceptions.ConnectionError:
            print(f"[red]无法连接到服务: {endpoint}[/red]")
            print("请确保服务已启动")
        except Exception as e:
            print(f"[red]测试失败: {e}[/red]")

    def _test_normal(self, endpoint: str, payload: dict):
        """普通请求测试"""
        import requests

        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()

        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            print(f"[green]响应:[/green]")
            print(content)
            print()
            print(f"[dim]Token 使用: {data.get('usage', {})}[/dim]")
        else:
            print(f"[yellow]响应异常: {data}[/yellow]")

    def _test_stream(self, endpoint: str, payload: dict):
        """流式请求测试"""
        import requests

        print("[green]响应:[/green]", end=" ")

        with requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=120,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json
                            chunk = json.loads(data)
                            if chunk["choices"][0]["delta"].get("content"):
                                print(chunk["choices"][0]["delta"]["content"], end="", flush=True)
                        except Exception:
                            pass

        print("\n")
