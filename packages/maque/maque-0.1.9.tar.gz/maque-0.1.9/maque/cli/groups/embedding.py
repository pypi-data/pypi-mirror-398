"""Embedding 服务命令组"""
from typing import List, Optional
from rich import print
from rich.console import Console


class EmbeddingGroup:
    """Embedding 服务命令组

    提供 embedding 模型服务的启动、管理功能，
    支持 jina-embeddings-v3 等模型的 task 类型。
    """

    def __init__(self, cli_instance):
        self.cli = cli_instance
        self.console = Console()

    def serve(
        self,
        model: str = "jinaai/jina-embeddings-v3",
        host: str = "0.0.0.0",
        port: int = 8000,
        device: str = None,
        workers: int = 1,
        local_dir: str = None,
        dtype: str = None,
        attn: str = None,
    ):
        """启动 Embedding API 服务

        启动兼容 OpenAI/vLLM 的 Embedding API 服务，
        支持 jina-embeddings-v3 的 task 类型扩展。

        Args:
            model: 模型名称或路径，默认 jinaai/jina-embeddings-v3
            host: 监听地址，默认 0.0.0.0
            port: 监听端口，默认 8000
            device: 设备类型 (cuda/cpu)，默认自动检测
            workers: worker 数量，默认 1
            local_dir: 本地模型目录
            dtype: 数据类型 (float16/bfloat16/float32)，默认自动选择
            attn: 注意力实现 (eager/sdpa/flash_attention_2)，默认自动选择

        Examples:
            maque embedding serve
            maque embedding serve --model=BAAI/bge-m3 --port=8001
            maque embedding serve --dtype=float32 --attn=eager
        """
        try:
            from maque.embedding.server import create_server
        except ImportError as e:
            print(f"[red]无法导入 embedding 服务模块: {e}[/red]")
            print("请确保已安装依赖: pip install sentence-transformers fastapi uvicorn")
            return

        print(f"[bold blue]启动 Embedding 服务[/bold blue]")
        print(f"  模型: [cyan]{model}[/cyan]")
        print(f"  地址: [green]http://{host}:{port}[/green]")
        print(f"  设备: [yellow]{device or 'auto'}[/yellow]")
        print(f"  精度: [yellow]{dtype or 'auto'}[/yellow]")
        print(f"  注意力: [yellow]{attn or 'auto'}[/yellow]")
        if local_dir:
            print(f"  本地目录: [magenta]{local_dir}[/magenta]")
        print()

        # 处理多模型
        models = [m.strip() for m in model.split(",")] if "," in model else [model]

        server = create_server(
            models=models,
            device=device,
            local_dir=local_dir,
            dtype=dtype,
            attn=attn,
        )
        server.run(host=host, port=port, workers=workers)

    def test(
        self,
        url: str = "http://localhost:8000",
        model: str = "jinaai/jina-embeddings-v3",
        text: str = "Hello, world!",
        task: str = None,
    ):
        """测试 Embedding 服务

        Args:
            url: 服务 URL
            model: 模型名称
            text: 测试文本
            task: 任务类型 (text-matching/retrieval.query/retrieval.passage/classification/separation)

        Examples:
            maque embedding test
            maque embedding test --task=retrieval.query
            maque embedding test --url=http://localhost:8000
        """
        import requests
        import json

        endpoint = f"{url.rstrip('/')}/v1/embeddings"

        payload = {
            "model": model,
            "input": text,
        }
        if task:
            payload["task"] = task

        print(f"[blue]测试 Embedding 服务[/blue]")
        print(f"  URL: {endpoint}")
        print(f"  模型: {model}")
        print(f"  文本: {text[:50]}{'...' if len(text) > 50 else ''}")
        if task:
            print(f"  Task: {task}")
        print()

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            if "data" in data and len(data["data"]) > 0:
                embedding = data["data"][0]["embedding"]
                print(f"[green]成功![/green]")
                print(f"  向量维度: {len(embedding)}")
                print(f"  向量前5维: {embedding[:5]}")
                print(f"  Token 使用: {data.get('usage', {})}")
            else:
                print(f"[yellow]响应异常: {data}[/yellow]")

        except requests.exceptions.ConnectionError:
            print(f"[red]无法连接到服务: {endpoint}[/red]")
            print("请确保服务已启动")
        except Exception as e:
            print(f"[red]测试失败: {e}[/red]")

    def tasks(self):
        """显示支持的 task 类型

        显示 jina-embeddings-v3 支持的所有 task 类型及其用途。
        """
        from rich.table import Table

        print("[bold blue]jina-embeddings-v3 支持的 Task 类型[/bold blue]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Task", style="cyan")
        table.add_column("用途", style="green")
        table.add_column("适用场景", style="yellow")

        tasks = [
            ("text-matching", "语义相似度匹配", "对称检索、句子相似度计算"),
            ("retrieval.query", "检索查询编码", "非对称检索的查询端"),
            ("retrieval.passage", "检索文档编码", "非对称检索的文档/段落端"),
            ("classification", "文本分类", "分类任务的特征提取"),
            ("separation", "聚类/重排", "聚类分析、重排序任务"),
        ]

        for task, desc, usage in tasks:
            table.add_row(task, desc, usage)

        self.console.print(table)

        print("\n[dim]使用示例:[/dim]")
        print('  curl -X POST http://localhost:8000/v1/embeddings \\')
        print('    -H "Content-Type: application/json" \\')
        print('    -d \'{"model": "jinaai/jina-embeddings-v3", "input": "text", "task": "retrieval.query"}\'')

    def client(
        self,
        url: str = "http://localhost:8000",
        model: str = "jinaai/jina-embeddings-v3",
    ):
        """创建 Embedding 客户端 (交互模式)

        Args:
            url: 服务 URL
            model: 模型名称

        Examples:
            maque embedding client
            maque embedding client --url=http://localhost:8000
        """
        from maque.embedding import TextEmbedding

        print("[bold blue]Embedding 客户端 (交互模式)[/bold blue]")
        print(f"  URL: {url}")
        print(f"  模型: {model}")
        print("\n输入文本进行编码，输入 'quit' 退出")
        print("可选: 输入 'task:<type>' 切换任务类型\n")

        client = TextEmbedding(base_url=url, model=model)
        current_task = None

        while True:
            try:
                text = input(f"[{current_task or 'default'}] > ").strip()

                if not text:
                    continue
                if text.lower() == "quit":
                    break
                if text.startswith("task:"):
                    current_task = text[5:].strip() or None
                    print(f"  切换到 task: {current_task or 'default'}")
                    continue

                embeddings = client.embed(text, task=current_task)
                print(f"  维度: {len(embeddings[0])}, 前5维: {embeddings[0][:5]}")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"  [red]错误: {e}[/red]")

        print("\n[yellow]已退出[/yellow]")
