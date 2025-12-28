"""MLLM (多模态大语言模型) 命令组"""

import os
import sys

# 强制启用颜色支持
os.environ["FORCE_COLOR"] = "1"
if not os.environ.get("TERM"):
    os.environ["TERM"] = "xterm-256color"

from rich.console import Console
from rich import print
from rich.markdown import Markdown

console = Console(
    force_terminal=True,
    width=100,
    color_system="windows",
    legacy_windows=True,
    safe_box=True
)


def safe_print(*args, **kwargs):
    """安全的打印函数，确保在所有终端中正确显示颜色"""
    try:
        console.print(*args, **kwargs)
    except Exception:
        # 降级到普通print，处理编码问题
        import re
        import sys
        import builtins

        clean_args = []
        for arg in args:
            if isinstance(arg, str):
                # 去除rich markup
                clean_arg = re.sub(r"\[/?[^\]]*\]", "", str(arg))
                # 处理emoji和特殊字符
                try:
                    # 尝试编码为gbk (Windows默认编码)
                    clean_arg.encode('gbk')
                    clean_args.append(clean_arg)
                except UnicodeEncodeError:
                    # 如果包含无法编码的字符，替换emoji为文本描述
                    clean_arg = re.sub(r'❌', '[错误]', clean_arg)
                    clean_arg = re.sub(r'✅', '[成功]', clean_arg)
                    clean_arg = re.sub(r'💡', '[提示]', clean_arg)
                    clean_arg = re.sub(r'🚀', '[启动]', clean_arg)
                    clean_arg = re.sub(r'📦', '[模型]', clean_arg)
                    clean_arg = re.sub(r'🌐', '[服务器]', clean_arg)
                    clean_arg = re.sub(r'👋', '[再见]', clean_arg)
                    clean_arg = re.sub(r'📝', '[记录]', clean_arg)
                    clean_arg = re.sub(r'⚠️', '[警告]', clean_arg)
                    clean_arg = re.sub(r'🔍', '[搜索]', clean_arg)
                    clean_arg = re.sub(r'🤖', '[机器人]', clean_arg)
                    clean_arg = re.sub(r'📡', '[网络]', clean_arg)
                    clean_arg = re.sub(r'🔌', '[连接]', clean_arg)
                    clean_arg = re.sub(r'📋', '[配置]', clean_arg)
                    clean_arg = re.sub(r'📁', '[文件]', clean_arg)
                    clean_arg = re.sub(r'🔧', '[设置]', clean_arg)
                    clean_arg = re.sub(r'🎯', '[目标]', clean_arg)
                    clean_arg = re.sub(r'📊', '[统计]', clean_arg)
                    clean_arg = re.sub(r'🧠', '[思考]', clean_arg)
                    clean_arg = re.sub(r'💭', '[推理]', clean_arg)
                    clean_arg = re.sub(r'🔗', '[逻辑]', clean_arg)
                    # 移除其他无法显示的emoji
                    clean_arg = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF\U0001F900-\U0001F9FF]', '', clean_arg)
                    clean_args.append(clean_arg)
            else:
                clean_args.append(str(arg))

        # 使用内置print
        try:
            builtins.print(*clean_args, **kwargs)
        except UnicodeEncodeError:
            # 最后的降级：使用错误替换
            safe_args = [arg.encode('gbk', errors='replace').decode('gbk') if isinstance(arg, str) else arg for arg in clean_args]
            builtins.print(*safe_args, **kwargs)


def safe_print_stream(text, **kwargs):
    """安全的流式打印函数，用于流式输出

    默认使用原生 print 实现真正的流式输出，避免 Rich console 的格式化干扰。
    """
    import builtins

    flush = kwargs.pop('flush', True)  # 流式输出默认 flush
    end = kwargs.pop('end', '')  # 流式输出默认不换行

    try:
        builtins.print(text, end=end, flush=flush, **kwargs)
    except UnicodeEncodeError:
        # 编码失败时，尝试使用 stdout buffer
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout.buffer.write(text.encode('utf-8', errors='replace'))
            if flush:
                sys.stdout.buffer.flush()
        else:
            # 最后的降级方案：替换无法编码的字符
            safe_text = text.encode('gbk', errors='replace').decode('gbk')
            builtins.print(safe_text, end=end, flush=flush, **kwargs)


def safe_print_markdown(content, **kwargs):
    """安全的Markdown渲染函数"""
    try:
        # 使用Rich的Markdown渲染
        markdown = Markdown(content)
        console.print(markdown, **kwargs)
    except Exception:
        # 降级到普通打印
        safe_print(content, **kwargs)


class StreamingMarkdownRenderer:
    """流式Markdown渲染器 - 实时解析并渲染Markdown"""

    def __init__(self):
        self.buffer = ""
        self.last_rendered_length = 0
        self.in_code_block = False
        self.code_block_lang = ""

    def add_token(self, token):
        """添加新token并尝试渲染"""
        self.buffer += token
        self._try_render_incremental()

    def _try_render_incremental(self):
        """尝试增量渲染Markdown"""
        # 检测代码块
        if "```" in self.buffer[self.last_rendered_length:]:
            code_block_matches = self.buffer.count("```")
            self.in_code_block = (code_block_matches % 2) == 1

        # 如果在代码块中，直接输出原始文本
        if self.in_code_block:
            new_content = self.buffer[self.last_rendered_length:]
            if new_content:
                safe_print_stream(new_content, end="", flush=True)
                self.last_rendered_length = len(self.buffer)
            return

        # 尝试找到可以安全渲染的边界（句子、段落等）
        render_boundary = self._find_render_boundary()
        if render_boundary > self.last_rendered_length:
            content_to_render = self.buffer[self.last_rendered_length:render_boundary]
            self._render_content(content_to_render)
            self.last_rendered_length = render_boundary

    def _find_render_boundary(self):
        """找到适合渲染的边界位置"""
        content = self.buffer

        # 寻找句子结束标记
        for i in range(len(content) - 1, self.last_rendered_length - 1, -1):
            char = content[i]
            # 句子结束
            if char in '.!?。！？':
                # 确保后面有空格或换行，避免误判小数点等
                if i + 1 < len(content) and content[i + 1] in ' \n\t':
                    return i + 1
            # 段落结束
            elif char == '\n' and (i + 1 >= len(content) or content[i + 1] == '\n'):
                return i + 1

        # 如果没有找到合适的边界，返回当前长度（不渲染）
        return self.last_rendered_length

    def _render_content(self, content):
        """渲染内容片段"""
        if not content.strip():
            safe_print_stream(content, end="", flush=True)
            return

        # 简单的行内Markdown渲染
        try:
            # 检查是否包含Markdown元素
            if any(marker in content for marker in ['**', '*', '`', '#', '-', '1.']):
                # 简单的实时渲染，只处理基本元素
                rendered = self._simple_markdown_render(content)
                safe_print_stream(rendered, end="", flush=True)
            else:
                # 纯文本直接输出
                safe_print_stream(content, end="", flush=True)
        except Exception:
            # 出错时降级到原始文本
            safe_print_stream(content, end="", flush=True)

    def _simple_markdown_render(self, content):
        """简单的Markdown渲染 - 只处理基本格式"""
        import re

        # 粗体 **text**
        content = re.sub(r'\*\*([^\*]+)\*\*', r'[bold]\1[/bold]', content)
        # 斜体 *text*
        content = re.sub(r'\*([^\*]+)\*', r'[italic]\1[/italic]', content)
        # 行内代码 `code`
        content = re.sub(r'`([^`]+)`', r'[code]\1[/code]', content)

        return content

    def finalize(self):
        """完成渲染，处理剩余内容"""
        if self.last_rendered_length < len(self.buffer):
            remaining = self.buffer[self.last_rendered_length:]
            self._render_content(remaining)

        safe_print_stream("", end="\n")  # 换行


def safe_print_stream_markdown(content, is_complete=False, **kwargs):
    """流式Markdown渲染函数，累积内容后渲染"""
    if is_complete:
        # 完整内容，进行Markdown渲染
        try:
            markdown = Markdown(content)
            console.print(markdown, **kwargs)
        except Exception:
            safe_print_stream(content, **kwargs)
    else:
        # 流式输出，直接打印原始文本
        safe_print_stream(content, **kwargs)


def get_user_input(prompt_text="You"):
    """获取用户输入，支持Rich格式的提示"""
    try:
        # 使用console.input来支持Rich格式
        return console.input(f"[bold yellow]{prompt_text}:[/bold yellow] ")
    except Exception:
        # 降级到普通input
        return input(f"{prompt_text}: ")


class AdvancedInput:
    """高级输入处理器，支持多行输入（Alt+Enter 换行）"""

    def __init__(self):
        self._use_prompt_toolkit = False
        self._bindings = None
        self._init_prompt_toolkit()

    def _init_prompt_toolkit(self):
        """初始化 prompt_toolkit 的键绑定"""
        try:
            from prompt_toolkit.key_binding import KeyBindings
            from prompt_toolkit.keys import Keys

            # 创建快捷键绑定
            self._bindings = KeyBindings()

            @self._bindings.add(Keys.Enter)
            def _(event):
                """Enter 提交输入"""
                event.current_buffer.validate_and_handle()

            # Alt+Enter (Escape + Enter) 换行 - 最可靠的方式
            @self._bindings.add('escape', 'enter')
            def _(event):
                """Alt+Enter 换行"""
                event.current_buffer.insert_text('\n')

            self._use_prompt_toolkit = True
        except ImportError:
            self._use_prompt_toolkit = False

    def _sync_prompt(self, prompt_text: str) -> str:
        """同步调用 prompt_toolkit（在单独线程中运行）"""
        from prompt_toolkit import prompt as pt_prompt
        return pt_prompt(
            f"{prompt_text}: ",
            key_bindings=self._bindings,
            multiline=False,
        )

    def get_input(self, prompt_text="You") -> str:
        """获取用户输入，支持多行（同步版本）"""
        if self._use_prompt_toolkit:
            try:
                return self._sync_prompt(prompt_text)
            except (KeyboardInterrupt, EOFError):
                raise
            except Exception:
                # 出错时降级到基本输入
                self._use_prompt_toolkit = False

        # Fallback 到基本输入
        return get_user_input(prompt_text)

    async def get_input_async(self, prompt_text="You") -> str:
        """获取用户输入，支持多行（异步版本，在单独线程中运行）"""
        if self._use_prompt_toolkit:
            try:
                import asyncio
                # 在单独线程中运行 prompt_toolkit，避免与 asyncio 冲突
                return await asyncio.to_thread(self._sync_prompt, prompt_text)
            except (KeyboardInterrupt, EOFError):
                raise
            except Exception:
                # 出错时降级到基本输入
                self._use_prompt_toolkit = False

        # Fallback 到基本输入
        return get_user_input(prompt_text)


class ChatCommands:
    """聊天快捷命令处理器"""

    COMMANDS = {
        '/clear': '清空对话历史',
        '/retry': '重新生成上一条回复',
        '/save': '保存对话到文件 (用法: /save [文件名])',
        '/model': '切换模型 (用法: /model [模型名])',
        '/help': '显示帮助信息',
    }

    @classmethod
    def is_command(cls, text: str) -> bool:
        """检查是否是命令"""
        return text.strip().startswith('/')

    @classmethod
    def parse(cls, text: str) -> tuple:
        """解析命令，返回 (命令名, 参数列表)"""
        parts = text.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        return cmd, args

    @classmethod
    def show_help(cls):
        """显示帮助信息"""
        safe_print("\n[bold cyan]📋 可用命令:[/bold cyan]")
        for cmd, desc in cls.COMMANDS.items():
            safe_print(f"  [green]{cmd:12}[/green] - {desc}")
        safe_print("")

    @classmethod
    def handle_clear(cls, messages: list, system_prompt: str = None) -> list:
        """清空对话历史"""
        new_messages = []
        if system_prompt:
            new_messages.append({"role": "system", "content": system_prompt})
        safe_print("[dim]🗑️  对话历史已清空[/dim]\n")
        return new_messages

    @classmethod
    def handle_save(cls, messages: list, filename: str = None):
        """保存对话到文件"""
        import json
        from datetime import datetime

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_{timestamp}.json"

        if not filename.endswith('.json'):
            filename += '.json'

        # 过滤掉系统消息，只保存用户和助手的对话
        chat_history = [
            msg for msg in messages
            if msg.get('role') in ['user', 'assistant']
        ]

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'saved_at': datetime.now().isoformat(),
                    'messages': chat_history
                }, f, ensure_ascii=False, indent=2)
            safe_print(f"[green]💾 对话已保存到: {filename}[/green]\n")
        except Exception as e:
            safe_print(f"[red]❌ 保存失败: {e}[/red]\n")

    @classmethod
    def handle_retry(cls, messages: list) -> tuple:
        """准备重试：移除最后一条助手回复，返回是否需要重试"""
        if len(messages) < 2:
            safe_print("[yellow]⚠️  没有可以重试的回复[/yellow]\n")
            return messages, False

        # 找到最后一条助手消息并移除
        if messages[-1].get('role') == 'assistant':
            messages.pop()
            safe_print("[dim]🔄 正在重新生成...[/dim]")
            return messages, True
        else:
            safe_print("[yellow]⚠️  最后一条不是助手回复，无法重试[/yellow]\n")
            return messages, False


class MllmGroup:
    """MLLM命令组 - 统一管理多模态大语言模型相关功能"""

    def __init__(self, cli_instance):
        self.cli = cli_instance

    def call_table(
        self,
        table_path: str,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        image_col: str = "image",
        system_prompt: str = "你是一个专业的图像识别专家。",
        text_prompt: str = "请描述这张图像。",
        system_prompt_file: str = None,
        text_prompt_file: str = None,
        sheet_name: str = 0,
        max_num=None,
        output_file: str = "table_results.csv",
        temperature: float = 0.1,
        max_tokens: int = 2000,
        concurrency_limit: int = 10,
        max_qps: int = 50,
        retry_times: int = 3,
        skip_existing: bool = False,
        **kwargs,
    ):
        """对表格中的图像列进行批量大模型识别和分析

        Args:
            table_path: 表格文件路径 (xlsx/csv)
            model: 模型名称
            base_url: API服务地址
            api_key: API密钥
            image_col: 图片列名
            system_prompt: 系统提示词
            text_prompt: 文本提示词
            system_prompt_file: 系统提示词文件路径（优先于 system_prompt）
            text_prompt_file: 文本提示词文件路径（优先于 text_prompt）
            sheet_name: sheet名称
            max_num: 最大处理数量
            output_file: 输出文件路径
            temperature: 温度参数
            max_tokens: 最大token数
            concurrency_limit: 并发限制
            max_qps: 最大QPS
            retry_times: 重试次数
            skip_existing: 是否跳过已有结果的行（断点续传）
        """
        import asyncio
        import pandas as pd
        import os
        from maque.mllm.mllm_client import MllmClient

        # 从配置文件获取默认值
        mllm_config = self.cli.maque_config.get("mllm", {})
        model = model or mllm_config.get("model", "gemma3:latest")
        base_url = base_url or mllm_config.get("base_url", "http://localhost:11434/v1")
        api_key = api_key or mllm_config.get("api_key", "EMPTY")

        # 从文件读取 prompt（如果指定）
        if system_prompt_file and os.path.exists(system_prompt_file):
            with open(system_prompt_file, 'r', encoding='utf-8') as f:
                system_prompt = f.read().strip()
            safe_print(f"[dim]📄 从文件加载 system_prompt: {system_prompt_file}[/dim]")

        if text_prompt_file and os.path.exists(text_prompt_file):
            with open(text_prompt_file, 'r', encoding='utf-8') as f:
                text_prompt = f.read().strip()
            safe_print(f"[dim]📄 从文件加载 text_prompt: {text_prompt_file}[/dim]")

        async def run_call_table():
            try:
                safe_print(f"\n[bold green]📊 开始批量处理表格[/bold green]")
                safe_print(f"[cyan]📁 文件: {table_path}[/cyan]")
                safe_print(f"[dim]🔧 模型: {model} | 并发: {concurrency_limit} | QPS: {max_qps}[/dim]")

                # 初始化客户端
                client = MllmClient(
                    model=model,
                    base_url=base_url,
                    api_key=api_key,
                    concurrency_limit=concurrency_limit,
                    max_qps=max_qps,
                    retry_times=retry_times,
                    **kwargs,
                )

                # 加载数据
                if table_path.endswith(".xlsx"):
                    df = pd.read_excel(table_path, sheet_name=sheet_name)
                else:
                    df = pd.read_csv(table_path)

                total_rows = len(df)
                if max_num:
                    df = df.head(max_num)

                safe_print(f"[dim]📝 总行数: {total_rows}, 处理行数: {len(df)}[/dim]")

                # 检查并创建结果列
                result_col = "mllm_result"
                if result_col not in df.columns:
                    df[result_col] = None

                # 断点续传：过滤已有结果的行
                if skip_existing and os.path.exists(output_file):
                    existing_df = pd.read_csv(output_file) if output_file.endswith('.csv') else pd.read_excel(output_file)
                    if result_col in existing_df.columns:
                        # 合并已有结果
                        df[result_col] = existing_df[result_col] if len(existing_df) == len(df) else df[result_col]
                        safe_print(f"[yellow]⏭️  断点续传: 检测到已有结果文件[/yellow]")

                # 找出需要处理的行
                if skip_existing:
                    pending_mask = df[result_col].isna() | (df[result_col] == '') | (df[result_col] == 'None')
                    pending_indices = df[pending_mask].index.tolist()
                else:
                    pending_indices = df.index.tolist()

                if not pending_indices:
                    safe_print(f"[green]✅ 所有行已处理完成，无需重新处理[/green]")
                    return

                safe_print(f"[cyan]🔄 待处理: {len(pending_indices)} 行[/cyan]")

                # 构建待处理的 messages
                messages_list = []
                for idx in pending_indices:
                    row = df.loc[idx]
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": text_prompt},
                            {"type": "image_url", "image_url": {"url": str(row[image_col])}},
                        ],
                    })
                    messages_list.append(messages)

                # 调用 MLLM
                results = await client.call_llm(
                    messages_list,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # 填充结果
                for i, idx in enumerate(pending_indices):
                    df.at[idx, result_col] = results[i] if i < len(results) else None

                # 保存结果
                if output_file.endswith('.csv'):
                    df.to_csv(output_file, index=False, encoding='utf-8-sig')
                else:
                    df.to_excel(output_file, index=False)

                safe_print(f"\n[bold green]✅ 处理完成！结果已保存到: {output_file}[/bold green]")

                # 统计
                success_count = df[result_col].notna().sum()
                safe_print(f"[dim]📊 成功: {success_count}/{len(df)}[/dim]")

            except Exception as e:
                safe_print(f"[red]❌ 处理失败: {e}[/red]")
                import traceback
                traceback.print_exc()

        return asyncio.run(run_call_table())

    def call_images(
        self,
        folder_path: str,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        system_prompt: str = "你是一个专业的图像识别专家。",
        text_prompt: str = "请描述这张图像。",
        system_prompt_file: str = None,
        text_prompt_file: str = None,
        recursive: bool = True,
        max_num: int = None,
        extensions: str = None,
        output_file: str = "results.csv",
        temperature: float = 0.1,
        max_tokens: int = 2000,
        concurrency_limit: int = 10,
        max_qps: int = 50,
        retry_times: int = 3,
        skip_existing: bool = False,
        **kwargs,
    ):
        """对文件夹中的图像进行批量大模型识别和分析

        Args:
            folder_path: 文件夹路径
            model: 模型名称
            base_url: API服务地址
            api_key: API密钥
            system_prompt: 系统提示词
            text_prompt: 文本提示词
            system_prompt_file: 系统提示词文件路径（优先于 system_prompt）
            text_prompt_file: 文本提示词文件路径（优先于 text_prompt）
            recursive: 是否递归扫描子文件夹
            max_num: 最大处理数量
            extensions: 支持的文件扩展名（逗号分隔，如 "jpg,png,webp"）
            output_file: 输出文件路径
            temperature: 温度参数
            max_tokens: 最大token数
            concurrency_limit: 并发限制
            max_qps: 最大QPS
            retry_times: 重试次数
            skip_existing: 是否跳过已处理的图片（断点续传）
        """
        import asyncio
        import pandas as pd
        import os
        from pathlib import Path
        from maque.mllm.mllm_client import MllmClient

        # 从配置文件获取默认值
        mllm_config = self.cli.maque_config.get("mllm", {})
        model = model or mllm_config.get("model", "gemma3:latest")
        base_url = base_url or mllm_config.get("base_url", "http://localhost:11434/v1")
        api_key = api_key or mllm_config.get("api_key", "EMPTY")

        # 从文件读取 prompt（如果指定）
        if system_prompt_file and os.path.exists(system_prompt_file):
            with open(system_prompt_file, 'r', encoding='utf-8') as f:
                system_prompt = f.read().strip()
            safe_print(f"[dim]📄 从文件加载 system_prompt: {system_prompt_file}[/dim]")

        if text_prompt_file and os.path.exists(text_prompt_file):
            with open(text_prompt_file, 'r', encoding='utf-8') as f:
                text_prompt = f.read().strip()
            safe_print(f"[dim]📄 从文件加载 text_prompt: {text_prompt_file}[/dim]")

        # 解析扩展名
        ext_set = None
        if extensions:
            ext_set = {f".{ext.strip().lower().lstrip('.')}" for ext in extensions.split(',')}

        async def run_call_images():
            try:
                safe_print(f"\n[bold green]📁 开始批量处理文件夹图片[/bold green]")
                safe_print(f"[cyan]📂 路径: {folder_path}[/cyan]")
                safe_print(f"[dim]🔧 模型: {model} | 并发: {concurrency_limit} | QPS: {max_qps}[/dim]")

                # 初始化客户端
                client = MllmClient(
                    model=model,
                    base_url=base_url,
                    api_key=api_key,
                    concurrency_limit=concurrency_limit,
                    max_qps=max_qps,
                    retry_times=retry_times,
                    **kwargs,
                )

                # 扫描图片文件
                image_files = client.folder.scan_folder_images(
                    folder_path=folder_path,
                    recursive=recursive,
                    max_num=max_num,
                    extensions=ext_set,
                )

                if not image_files:
                    safe_print(f"[yellow]⚠️  未找到图片文件[/yellow]")
                    return

                # 创建结果 DataFrame
                df = pd.DataFrame({'image_path': image_files})
                result_col = "mllm_result"
                df[result_col] = None

                # 断点续传：加载已有结果
                processed_paths = set()
                if skip_existing and os.path.exists(output_file):
                    try:
                        existing_df = pd.read_csv(output_file) if output_file.endswith('.csv') else pd.read_excel(output_file)
                        if 'image_path' in existing_df.columns and result_col in existing_df.columns:
                            # 创建路径到结果的映射
                            for _, row in existing_df.iterrows():
                                path = row['image_path']
                                result = row[result_col]
                                if pd.notna(result) and result != '' and result != 'None':
                                    processed_paths.add(path)
                                    # 更新 df 中对应行的结果
                                    mask = df['image_path'] == path
                                    if mask.any():
                                        df.loc[mask, result_col] = result
                            safe_print(f"[yellow]⏭️  断点续传: 已处理 {len(processed_paths)} 个文件[/yellow]")
                    except Exception as e:
                        safe_print(f"[yellow]⚠️  读取已有结果失败: {e}[/yellow]")

                # 找出需要处理的文件
                pending_indices = []
                for idx, row in df.iterrows():
                    if row['image_path'] not in processed_paths:
                        pending_indices.append(idx)

                if not pending_indices:
                    safe_print(f"[green]✅ 所有图片已处理完成，无需重新处理[/green]")
                    return

                safe_print(f"[cyan]🔄 待处理: {len(pending_indices)} 个图片[/cyan]")

                # 构建 messages
                messages_list = []
                pending_files = []
                for idx in pending_indices:
                    image_path = df.loc[idx, 'image_path']
                    pending_files.append(image_path)
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "text", "text": text_prompt},
                            {"type": "image_url", "image_url": {"url": f"file://{image_path}"}},
                        ],
                    })
                    messages_list.append(messages)

                # 调用 MLLM
                results = await client.call_llm(
                    messages_list,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # 填充结果
                for i, idx in enumerate(pending_indices):
                    df.at[idx, result_col] = results[i] if i < len(results) else None

                # 保存结果
                if output_file.endswith('.csv'):
                    df.to_csv(output_file, index=False, encoding='utf-8-sig')
                else:
                    df.to_excel(output_file, index=False)

                safe_print(f"\n[bold green]✅ 处理完成！结果已保存到: {output_file}[/bold green]")

                # 统计
                success_count = df[result_col].notna().sum()
                safe_print(f"[dim]📊 成功: {success_count}/{len(df)}[/dim]")

            except Exception as e:
                safe_print(f"[red]❌ 处理失败: {e}[/red]")
                import traceback
                traceback.print_exc()

        return asyncio.run(run_call_images())

    def chat(
        self,
        message: str = None,
        image: str = None,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        system_prompt: str = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        stream: bool = True,
        **kwargs,
    ):
        """交互式多模态对话"""
        # 同步版本，简化处理
        import asyncio
        from maque.mllm.mllm_client import MllmClient

        # 从配置文件获取默认值
        mllm_config = self.cli.maque_config.get("mllm", {})

        if model is None:
            model_name = mllm_config.get("model", "gemma3:latest")
        else:
            model_name = model

        if base_url is None:
            base_url_val = mllm_config.get("base_url", "http://localhost:11434/v1")
        else:
            base_url_val = base_url

        if api_key is None:
            api_key_val = mllm_config.get("api_key", "EMPTY")
        else:
            api_key_val = api_key

        if message:
            # 单次对话模式
            def run_single_chat():
                async def _single_chat():
                    try:
                        # 初始化客户端
                        client = MllmClient(
                            model=model_name,
                            base_url=base_url_val,
                            api_key=api_key_val,
                            **kwargs,
                        )

                        messages = [
                            {
                                "role": "user",
                                "content": message
                                if not image
                                else [
                                    {"type": "text", "text": message},
                                    {"type": "image_url", "image_url": {"url": image}},
                                ],
                            }
                        ]

                        if system_prompt:
                            messages.insert(
                                0, {"role": "system", "content": system_prompt}
                            )

                        if stream:
                            # 流式输出 - 使用优雅的Markdown渲染器
                            safe_print(f"[bold blue]Assistant:[/bold blue] ")

                            renderer = StreamingMarkdownRenderer()
                            try:
                                async for token in client.call_llm_stream(
                                    messages=messages,
                                    temperature=temperature,
                                    max_tokens=max_tokens,
                                    **kwargs,
                                ):
                                    renderer.add_token(token)
                                # 完成流式输出
                                renderer.finalize()
                            except KeyboardInterrupt:
                                safe_print_stream("\n")
                                safe_print("[dim]⏸️  输出已中断[/dim]")
                            return renderer.buffer
                        else:
                            # 非流式输出，使用Markdown渲染
                            results = await client.call_llm(
                                messages_list=[messages], show_progress=False
                            )
                            response = (
                                results[0] if results and results[0] else "无响应"
                            )
                            safe_print(f"[bold blue]Assistant:[/bold blue]")
                            safe_print_markdown(response)
                            return response
                    except KeyboardInterrupt:
                        safe_print("\n[dim]👋 再见！[/dim]")
                        return None
                    except Exception as e:
                        safe_print(f"[red]❌ 执行错误: {e}[/red]")
                        safe_print("[yellow]💡 请检查模型配置和网络连接[/yellow]")
                        return None

                try:
                    return asyncio.run(_single_chat())
                except KeyboardInterrupt:
                    safe_print("\n[dim]👋 再见！[/dim]")
                    return None

            return run_single_chat()
        else:
            # 多轮交互模式
            def run_interactive_chat():
                async def _interactive_chat():
                    try:
                        # 初始化客户端
                        client = MllmClient(
                            model=model_name,
                            base_url=base_url_val,
                            api_key=api_key_val,
                            **kwargs,
                        )

                        # 初始化对话历史
                        messages = []
                        if system_prompt:
                            messages.append(
                                {"role": "system", "content": system_prompt}
                            )

                        # 初始化高级输入处理器
                        advanced_input = AdvancedInput()
                        current_model = model_name  # 用于支持 /model 切换

                        safe_print("\n[bold green]🚀 多轮对话模式启动[/bold green]")
                        safe_print(f"[cyan]📦 模型: [/cyan][bold]{current_model}[/bold]")
                        safe_print(f"[cyan]🌐 服务器: [/cyan][bold]{base_url_val}[/bold]")
                        safe_print(f"[dim]💡 输入 [bold]/help[/bold] 查看命令 | [bold]Ctrl+C[/bold] 退出 | [bold]Alt+Enter[/bold] 换行[/dim]")
                        safe_print(f"[dim]{'─' * 60}[/dim]\n")

                        while True:
                            try:
                                # 获取用户输入（支持多行，异步版本避免与 asyncio 冲突）
                                user_input = (await advanced_input.get_input_async("You")).strip()

                                # 检查退出命令
                                if user_input.lower() in ["quit", "exit", "q", "退出"]:
                                    safe_print("[dim]👋 再见！[/dim]")
                                    break

                                if not user_input:
                                    continue

                                # 处理快捷命令
                                if ChatCommands.is_command(user_input):
                                    cmd, args = ChatCommands.parse(user_input)

                                    if cmd == '/help':
                                        ChatCommands.show_help()
                                        continue

                                    elif cmd == '/clear':
                                        messages = ChatCommands.handle_clear(messages, system_prompt)
                                        continue

                                    elif cmd == '/save':
                                        ChatCommands.handle_save(messages, args if args else None)
                                        continue

                                    elif cmd == '/model':
                                        if args:
                                            current_model = args.strip()
                                            # 重新创建客户端
                                            client = MllmClient(
                                                model=current_model,
                                                base_url=base_url_val,
                                                api_key=api_key_val,
                                                **kwargs,
                                            )
                                            safe_print(f"[green]✅ 模型已切换为: {current_model}[/green]\n")
                                        else:
                                            safe_print(f"[cyan]当前模型: {current_model}[/cyan]")
                                            safe_print(f"[dim]用法: /model <模型名>[/dim]\n")
                                        continue

                                    elif cmd == '/retry':
                                        messages, should_retry = ChatCommands.handle_retry(messages)
                                        if not should_retry:
                                            continue
                                        # 继续执行下面的生成逻辑
                                    else:
                                        safe_print(f"[yellow]⚠️  未知命令: {cmd}[/yellow]")
                                        safe_print(f"[dim]输入 /help 查看可用命令[/dim]\n")
                                        continue

                                # 检测是否包含图片路径或URL
                                import os
                                import re

                                # /retry 时不需要添加新消息，直接重新生成
                                is_retry = ChatCommands.is_command(user_input) and ChatCommands.parse(user_input)[0] == '/retry'
                                image_path = None
                                text_content = user_input

                                if not is_retry:
                                    # 检查是否是URL
                                    url_pattern = r'(https?://[^\s]+\.(?:jpg|jpeg|png|gif|bmp|webp)(?:\?[^\s]*)?)'
                                    url_match = re.search(url_pattern, user_input, re.IGNORECASE)

                                    if url_match:
                                        image_path = url_match.group(1)
                                        text_content = user_input.replace(image_path, "").strip()
                                        if not text_content:
                                            text_content = "请描述这张图片"
                                    else:
                                        # 检查是否包含本地文件路径
                                        # 支持多种格式：绝对路径、相对路径、带引号的路径
                                        path_patterns = [
                                            r'"([^"]+\.(?:jpg|jpeg|png|gif|bmp|webp))"',  # 双引号路径
                                            r"'([^']+\.(?:jpg|jpeg|png|gif|bmp|webp))'",  # 单引号路径
                                            r'([^\s]+\.(?:jpg|jpeg|png|gif|bmp|webp))(?:\s|$)',  # 无引号路径
                                        ]

                                        for pattern in path_patterns:
                                            match = re.search(pattern, user_input, re.IGNORECASE)
                                            if match:
                                                potential_path = match.group(1)
                                                # 检查文件是否存在
                                                if os.path.exists(potential_path):
                                                    image_path = os.path.abspath(potential_path)
                                                    text_content = user_input.replace(match.group(0), "").strip()
                                                    if not text_content:
                                                        text_content = "请描述这张图片"
                                                    break
                                                # 尝试相对路径
                                                elif os.path.exists(os.path.join(os.getcwd(), potential_path)):
                                                    image_path = os.path.abspath(os.path.join(os.getcwd(), potential_path))
                                                    text_content = user_input.replace(match.group(0), "").strip()
                                                    if not text_content:
                                                        text_content = "请描述这张图片"
                                                    break

                                    # 构建消息内容
                                    if image_path:
                                        # 如果是本地文件，转换为file://格式
                                        if not image_path.startswith('http'):
                                            image_url = f"file://{image_path.replace(os.sep, '/')}"
                                        else:
                                            image_url = image_path

                                        safe_print(f"[dim]📷 发送图片: {image_path}[/dim]")
                                        message_content = [
                                            {"type": "text", "text": text_content},
                                            {"type": "image_url", "image_url": {"url": image_url}}
                                        ]
                                    else:
                                        message_content = user_input

                                    # 添加用户消息到历史
                                    messages.append({"role": "user", "content": message_content})

                                if stream:
                                    # 流式输出 - 使用优雅的Markdown渲染器
                                    safe_print(f"[bold blue]Assistant:[/bold blue] ")

                                    renderer = StreamingMarkdownRenderer()
                                    stream_interrupted = False
                                    try:
                                        async for token in client.call_llm_stream(
                                            messages=messages,
                                            temperature=temperature,
                                            max_tokens=max_tokens,
                                            **kwargs,
                                        ):
                                            renderer.add_token(token)
                                    except KeyboardInterrupt:
                                        stream_interrupted = True
                                        safe_print_stream("\n")
                                        safe_print("[dim]⏸️  输出已中断[/dim]")

                                    # 完成流式输出
                                    if not stream_interrupted:
                                        renderer.finalize()
                                    full_response = renderer.buffer

                                    # 添加助手响应到历史（即使中断也保存已获取的内容）
                                    if full_response:
                                        messages.append(
                                            {
                                                "role": "assistant",
                                                "content": full_response,
                                            }
                                        )
                                else:
                                    # 非流式输出，使用Markdown渲染
                                    results = await client.call_llm(
                                        messages_list=[messages],
                                        show_progress=False,
                                        temperature=temperature,
                                        max_tokens=max_tokens,
                                        **kwargs,
                                    )
                                    response = (
                                        results[0]
                                        if results and results[0]
                                        else "无响应"
                                    )
                                    safe_print(f"[bold blue]Assistant:[/bold blue]")
                                    safe_print_markdown(response)

                                    # 添加助手响应到历史
                                    if response and response != "无响应":
                                        messages.append(
                                            {"role": "assistant", "content": response}
                                        )

                            except KeyboardInterrupt:
                                safe_print("\n[dim]👋 再见！[/dim]")
                                break
                            except EOFError:
                                safe_print("\n[dim]👋 再见！[/dim]")
                                break
                            except Exception as e:
                                safe_print(f"[red]❌ 处理错误: {e}[/red]")
                                safe_print("[yellow]💡 请重试或输入 'quit' 退出[/yellow]")
                                continue

                    except Exception as e:
                        safe_print(f"[red]❌ 初始化错误: {e}[/red]")
                        safe_print("[yellow]💡 请检查MLLM客户端配置或服务器连接[/yellow]")
                        return None

                try:
                    return asyncio.run(_interactive_chat())
                except KeyboardInterrupt:
                    safe_print("\n[dim]👋 再见！[/dim]")
                    return None

            # 检查是否在交互环境中
            import sys

            if not sys.stdin.isatty():
                safe_print("[red]❌ 错误: 交互模式需要在终端中运行[/red]")
                safe_print(
                    "[yellow]💡 请在交互式终端中运行此命令，或提供具体的消息参数[/yellow]"
                )
                safe_print('[dim]📝 示例: [bold]maque mllm chat "你好"[/bold][/dim]')
                return

            try:
                return run_interactive_chat()
            except KeyboardInterrupt:
                safe_print("\n[dim]👋 再见！[/dim]")
                return None

    def models(self, base_url: str = None, api_key: str = None):
        """列出可用模型"""
        import requests

        # 从配置获取默认值
        mllm_config = self.cli.maque_config.get("mllm", {})
        base_url = base_url or mllm_config.get("base_url", "http://localhost:11434/v1")
        api_key = api_key or mllm_config.get("api_key", "EMPTY")

        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                f"{base_url.rstrip('/')}/models", headers=headers, timeout=10
            )

            if response.status_code == 200:
                models_data = response.json()

                safe_print(f"\n[bold blue]🤖 可用模型列表[/bold blue]")
                safe_print(f"[dim]📡 服务器: {base_url}[/dim]")
                safe_print(f"[dim]{'─' * 50}[/dim]")

                if isinstance(models_data, dict) and "data" in models_data:
                    models = models_data["data"]
                elif isinstance(models_data, list):
                    models = models_data
                else:
                    models = []

                if models:
                    for i, model in enumerate(models, 1):
                        if isinstance(model, dict):
                            model_id = model.get("id", model.get("name", "unknown"))
                            safe_print(f"[green]{i:2d}. [/green][cyan]{model_id}[/cyan]")
                        else:
                            safe_print(f"[green]{i:2d}. [/green][cyan]{model}[/cyan]")
                    safe_print(f"\n[dim]✅ 共找到 {len(models)} 个可用模型[/dim]")
                else:
                    safe_print("[yellow]⚠️  未找到可用模型[/yellow]")
                    safe_print("[dim]💡 请检查服务器配置或网络连接[/dim]")

            else:
                safe_print(f"[red]❌ 获取模型列表失败: HTTP {response.status_code}[/red]")
                safe_print(f"[yellow]💡 请检查服务器状态或API权限[/yellow]")

        except requests.exceptions.RequestException as e:
            safe_print(f"[red]🔌 连接失败: {e}[/red]")
            safe_print(f"[yellow]💡 请检查服务地址: [bold]{base_url}[/bold][/yellow]")
            safe_print(f"[dim]提示: 确保服务器正在运行并且地址正确[/dim]")
        except Exception as e:
            safe_print(f"[red]❌ 未知错误: {e}[/red]")

    def test(
        self,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        message: str = "Hello, please respond with 'OK' if you can see this message.",
        timeout: int = 30,
    ):
        """测试MLLM服务连接和配置

        Args:
            model: 模型名称（可选，不指定则只测试连接）
            base_url: API服务地址
            api_key: API密钥
            message: 测试消息
            timeout: 超时时间（秒）
        """
        import requests
        import time

        # 从配置获取默认值
        mllm_config = self.cli.maque_config.get("mllm", {})
        base_url = base_url or mllm_config.get("base_url", "http://localhost:11434/v1")
        api_key = api_key or mllm_config.get("api_key", "EMPTY")
        model = model or mllm_config.get("model")

        safe_print(f"\n[bold blue]🔍 MLLM 服务连接测试[/bold blue]")
        safe_print(f"[dim]{'─' * 50}[/dim]")

        results = {
            "connection": False,
            "models_api": False,
            "chat_api": False,
        }

        # 1. 测试基本连接
        safe_print(f"\n[cyan]1. 测试服务器连接...[/cyan]")
        safe_print(f"   [dim]地址: {base_url}[/dim]")
        try:
            start_time = time.time()
            response = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=timeout
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                safe_print(f"   [green]✅ 连接成功[/green] [dim]({elapsed:.2f}s)[/dim]")
                results["connection"] = True
                results["models_api"] = True

                # 解析模型列表
                models_data = response.json()
                if isinstance(models_data, dict) and "data" in models_data:
                    models = models_data["data"]
                elif isinstance(models_data, list):
                    models = models_data
                else:
                    models = []

                model_count = len(models)
                safe_print(f"   [dim]可用模型数: {model_count}[/dim]")

            elif response.status_code == 401:
                safe_print(f"   [yellow]⚠️  认证失败 (401)[/yellow]")
                safe_print(f"   [dim]请检查 API Key 是否正确[/dim]")
                results["connection"] = True
            elif response.status_code == 404:
                safe_print(f"   [yellow]⚠️  /models 端点不存在 (404)[/yellow]")
                safe_print(f"   [dim]服务器可能不支持 OpenAI 兼容 API[/dim]")
                results["connection"] = True
            else:
                safe_print(f"   [yellow]⚠️  HTTP {response.status_code}[/yellow]")
                results["connection"] = True

        except requests.exceptions.ConnectionError:
            safe_print(f"   [red]❌ 连接失败: 无法连接到服务器[/red]")
            safe_print(f"   [dim]请检查服务器是否运行在 {base_url}[/dim]")
        except requests.exceptions.Timeout:
            safe_print(f"   [red]❌ 连接超时 ({timeout}s)[/red]")
        except Exception as e:
            safe_print(f"   [red]❌ 连接错误: {e}[/red]")

        # 2. 测试 Chat API（如果指定了模型）
        if model and results["connection"]:
            safe_print(f"\n[cyan]2. 测试 Chat API...[/cyan]")
            safe_print(f"   [dim]模型: {model}[/dim]")

            try:
                start_time = time.time()
                response = requests.post(
                    f"{base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": message}],
                        "max_tokens": 50,
                        "temperature": 0.1
                    },
                    timeout=timeout
                )
                elapsed = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    content = ""
                    if "choices" in data and data["choices"]:
                        content = data["choices"][0].get("message", {}).get("content", "")

                    safe_print(f"   [green]✅ Chat API 正常[/green] [dim]({elapsed:.2f}s)[/dim]")
                    if content:
                        # 截断过长的响应
                        display_content = content[:100] + "..." if len(content) > 100 else content
                        safe_print(f"   [dim]响应: {display_content}[/dim]")
                    results["chat_api"] = True

                    # 显示 token 使用情况
                    usage = data.get("usage", {})
                    if usage:
                        safe_print(f"   [dim]Token 使用: prompt={usage.get('prompt_tokens', 'N/A')}, "
                                  f"completion={usage.get('completion_tokens', 'N/A')}[/dim]")

                elif response.status_code == 404:
                    safe_print(f"   [yellow]⚠️  模型不存在或 API 端点不可用[/yellow]")
                    safe_print(f"   [dim]请检查模型名称: {model}[/dim]")
                elif response.status_code == 401:
                    safe_print(f"   [yellow]⚠️  认证失败[/yellow]")
                else:
                    safe_print(f"   [yellow]⚠️  HTTP {response.status_code}[/yellow]")
                    try:
                        error_detail = response.json()
                        safe_print(f"   [dim]{error_detail}[/dim]")
                    except:
                        pass

            except requests.exceptions.Timeout:
                safe_print(f"   [yellow]⚠️  请求超时 ({timeout}s)[/yellow]")
                safe_print(f"   [dim]模型可能正在加载或服务器繁忙[/dim]")
            except Exception as e:
                safe_print(f"   [red]❌ 请求失败: {e}[/red]")

        # 3. 总结
        safe_print(f"\n[dim]{'─' * 50}[/dim]")
        safe_print(f"[bold]测试结果汇总:[/bold]")

        status_icons = {True: "[green]✅[/green]", False: "[red]❌[/red]"}

        safe_print(f"  {status_icons[results['connection']]} 服务器连接")
        safe_print(f"  {status_icons[results['models_api']]} Models API")
        if model:
            safe_print(f"  {status_icons[results['chat_api']]} Chat API ({model})")

        # 给出建议
        if all(results.values()) or (results["connection"] and results["models_api"] and not model):
            safe_print(f"\n[green]🎉 所有测试通过！MLLM 服务配置正确。[/green]")
        else:
            safe_print(f"\n[yellow]💡 建议:[/yellow]")
            if not results["connection"]:
                safe_print(f"   - 检查服务器是否启动")
                safe_print(f"   - 检查 base_url 配置是否正确")
            if results["connection"] and not results["models_api"]:
                safe_print(f"   - 检查 API Key 是否正确")
                safe_print(f"   - 确认服务器支持 OpenAI 兼容 API")
            if model and not results["chat_api"]:
                safe_print(f"   - 检查模型名称是否正确")
                safe_print(f"   - 使用 'mq mllm models' 查看可用模型")

        return results

    def chain_analysis(
        self,
        query: str,
        steps: int = 3,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        show_details: bool = False,
        **kwargs,
    ):
        """使用Chain of Thought进行分析推理
        
        Args:
            query: 要分析的问题或内容
            steps: 分析步骤数，默认3步
            model: 使用的模型
            base_url: API服务地址
            api_key: API密钥
            temperature: 温度参数
            max_tokens: 最大token数
            show_details: 是否显示每个步骤的详细信息
        """
        import asyncio
        from maque.mllm.chain_of_thought_client import ChainOfThoughtClient, LinearStep, ExecutionConfig
        from maque.mllm.openaiclient import OpenAIClient

        # 从配置获取默认值
        mllm_config = self.cli.maque_config.get("mllm", {})
        model = model or mllm_config.get("model", "gemma3:latest")
        base_url = base_url or mllm_config.get("base_url", "http://localhost:11434/v1")
        api_key = api_key or mllm_config.get("api_key", "EMPTY")

        async def run_chain_analysis():
            try:
                safe_print(f"[bold green]🔍 开始Chain of Thought分析推理[/bold green]")
                safe_print(f"[cyan]📝 问题: {query}[/cyan]")
                safe_print(f"[dim]🔧 模型: {model}, 步骤数: {steps}[/dim]\n")

                # 初始化客户端
                openai_client = OpenAIClient(model=model, base_url=base_url, api_key=api_key)
                
                # 配置执行参数
                config = ExecutionConfig(
                    enable_monitoring=True,
                    enable_progress=show_details,
                    log_level="INFO" if show_details else "WARNING"
                )
                
                chain_client = ChainOfThoughtClient(openai_client, config)

                # 定义分析步骤
                def create_analysis_step(step_num: int, step_name: str, prompt_template: str):
                    def prepare_messages(context):
                        previous_analysis = ""
                        if context.history:
                            previous_analysis = "\n\n".join([
                                f"步骤{i+1}: {step.response}" 
                                for i, step in enumerate(context.history)
                            ])
                        
                        system_prompt = f"""你是一个专业的分析师，正在进行第{step_num}步分析。
请根据问题和之前的分析结果，{step_name}。
保持逻辑清晰，分析深入。"""

                        user_prompt = prompt_template.format(
                            query=context.query,
                            previous_analysis=previous_analysis
                        )

                        return [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    
                    return LinearStep(
                        name=f"analysis_step_{step_num}",
                        prepare_messages_fn=prepare_messages,
                        model_params={
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            **kwargs
                        }
                    )

                # 创建分析链条
                analysis_steps = []
                
                if steps >= 1:
                    analysis_steps.append(create_analysis_step(
                        1, "理解和分解问题",
                        "请仔细分析这个问题：\n{query}\n\n请分解这个问题的关键要素，明确分析的方向和重点。"
                    ))
                
                if steps >= 2:
                    analysis_steps.append(create_analysis_step(
                        2, "深入分析各个方面",
                        "基于第一步的分析：\n{previous_analysis}\n\n请从多个角度深入分析问题，探讨可能的解决方案或答案。"
                    ))
                
                if steps >= 3:
                    analysis_steps.append(create_analysis_step(
                        3, "综合结论和建议",
                        "基于前面的分析：\n{previous_analysis}\n\n请总结分析结果，给出明确的结论和实用的建议。"
                    ))
                
                # 如果步骤超过3步，添加更多细化分析
                for i in range(4, steps + 1):
                    analysis_steps.append(create_analysis_step(
                        i, f"进一步细化分析第{i-3}个方面",
                        "继续深化分析：\n{previous_analysis}\n\n请进一步细化和补充分析，提供更详细的见解。"
                    ))

                # 创建线性链条
                first_step = chain_client.create_linear_chain(analysis_steps, "analysis_chain")
                
                # 执行链条
                context = chain_client.create_context({"query": query})
                result_context = await chain_client.execute_chain(
                    first_step, context, show_step_details=show_details
                )

                # 显示结果
                if result_context.history:
                    safe_print(f"\n[bold blue]🎯 Chain of Thought 分析结果[/bold blue]")
                    safe_print(f"[dim]{'=' * 60}[/dim]")
                    
                    for i, step_result in enumerate(result_context.history):
                        step_title = f"步骤 {i+1}"
                        if i == 0:
                            step_title += " - 问题理解"
                        elif i == 1:
                            step_title += " - 深入分析"
                        elif i == 2:
                            step_title += " - 综合结论"
                        else:
                            step_title += f" - 细化分析 {i-2}"
                            
                        safe_print(f"\n[bold cyan]{step_title}[/bold cyan]")
                        safe_print(f"[green]{step_result.response}[/green]")
                    
                    # 执行摘要
                    summary = result_context.get_execution_summary()
                    safe_print(f"\n[dim]📊 执行统计: {summary['total_steps']} 个步骤, "
                              f"耗时 {summary['total_execution_time']:.2f}秒, "
                              f"成功率 {summary['success_rate']*100:.1f}%[/dim]")
                else:
                    safe_print("[red]❌ 分析执行失败，没有生成结果[/red]")

            except Exception as e:
                safe_print(f"[red]❌ Chain of Thought分析执行失败: {e}[/red]")
                safe_print("[yellow]💡 请检查模型配置和网络连接[/yellow]")

        return asyncio.run(run_chain_analysis())

    def chain_reasoning(
        self,
        query: str,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        show_details: bool = False,
        **kwargs,
    ):
        """使用Chain of Thought进行逻辑推理
        
        Args:
            query: 需要推理的问题或情境
            model: 使用的模型
            base_url: API服务地址
            api_key: API密钥
            temperature: 温度参数
            max_tokens: 最大token数
            show_details: 是否显示每个步骤的详细信息
        """
        import asyncio
        from maque.mllm.chain_of_thought_client import ChainOfThoughtClient, LinearStep, ExecutionConfig
        from maque.mllm.openaiclient import OpenAIClient

        # 从配置获取默认值
        mllm_config = self.cli.maque_config.get("mllm", {})
        model = model or mllm_config.get("model", "gemma3:latest")
        base_url = base_url or mllm_config.get("base_url", "http://localhost:11434/v1")
        api_key = api_key or mllm_config.get("api_key", "EMPTY")

        async def run_chain_reasoning():
            try:
                safe_print(f"[bold green]🧠 开始Chain of Thought逻辑推理[/bold green]")
                safe_print(f"[cyan]💭 推理问题: {query}[/cyan]")
                safe_print(f"[dim]🔧 模型: {model}[/dim]\n")

                # 初始化客户端
                openai_client = OpenAIClient(model=model, base_url=base_url, api_key=api_key)
                
                config = ExecutionConfig(
                    enable_monitoring=True,
                    enable_progress=show_details,
                    log_level="INFO" if show_details else "WARNING"
                )
                
                chain_client = ChainOfThoughtClient(openai_client, config)

                # 定义推理步骤
                def create_reasoning_step(step_name: str, prompt_template: str):
                    def prepare_messages(context):
                        previous_reasoning = ""
                        if context.history:
                            previous_reasoning = "\n\n".join([
                                f"[{step.step_name}]: {step.response}" 
                                for step in context.history
                            ])
                        
                        return [
                            {"role": "system", "content": "你是一个逻辑推理专家。请使用严谨的逻辑思维，一步一步地分析和推理。每一步都要有明确的逻辑依据。"},
                            {"role": "user", "content": prompt_template.format(
                                query=context.query,
                                previous_reasoning=previous_reasoning
                            )}
                        ]
                    
                    return LinearStep(
                        name=step_name,
                        prepare_messages_fn=prepare_messages,
                        model_params={
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            **kwargs
                        }
                    )

                # 创建推理链条
                reasoning_steps = [
                    create_reasoning_step(
                        "observation",
                        "首先，让我观察和理解这个问题：\n{query}\n\n请仔细观察问题中的关键信息、已知条件和要求解答的内容。列出所有重要的事实和假设。"
                    ),
                    create_reasoning_step(
                        "hypothesis",
                        "基于观察到的信息：\n{previous_reasoning}\n\n现在请提出可能的假设或解决方案。考虑多种可能性，并说明每种假设的依据。"
                    ),
                    create_reasoning_step(
                        "deduction",
                        "基于前面的观察和假设：\n{previous_reasoning}\n\n现在进行逻辑推导。使用演绎推理，从已知条件推导出结论。确保每一步推理都有明确的逻辑关系。"
                    ),
                    create_reasoning_step(
                        "verification",
                        "基于推理过程：\n{previous_reasoning}\n\n现在验证推理结果。检查逻辑是否一致，结论是否合理，是否遗漏了重要因素。如果发现问题，请指出并修正。"
                    ),
                    create_reasoning_step(
                        "conclusion",
                        "综合整个推理过程：\n{previous_reasoning}\n\n请给出最终结论。总结推理的关键步骤，明确回答原始问题，并说明结论的可信度。"
                    )
                ]

                # 创建和执行链条
                first_step = chain_client.create_linear_chain(reasoning_steps, "reasoning_chain")
                context = chain_client.create_context({"query": query})
                result_context = await chain_client.execute_chain(
                    first_step, context, show_step_details=show_details
                )

                # 显示推理结果
                if result_context.history:
                    safe_print(f"\n[bold blue]🎯 Chain of Thought 推理结果[/bold blue]")
                    safe_print(f"[dim]{'=' * 60}[/dim]")
                    
                    step_names = {
                        "observation": "🔍 观察分析",
                        "hypothesis": "💡 假设提出", 
                        "deduction": "🔗 逻辑推导",
                        "verification": "✅ 验证检查",
                        "conclusion": "🎯 最终结论"
                    }
                    
                    for step_result in result_context.history:
                        step_display = step_names.get(step_result.step_name, step_result.step_name)
                        safe_print(f"\n[bold cyan]{step_display}[/bold cyan]")
                        safe_print(f"[green]{step_result.response}[/green]")
                    
                    # 执行摘要
                    summary = result_context.get_execution_summary()
                    safe_print(f"\n[dim]📊 推理统计: {summary['total_steps']} 个步骤, "
                              f"耗时 {summary['total_execution_time']:.2f}秒, "
                              f"成功率 {summary['success_rate']*100:.1f}%[/dim]")
                else:
                    safe_print("[red]❌ 推理执行失败，没有生成结果[/red]")

            except Exception as e:
                safe_print(f"[red]❌ Chain of Thought推理执行失败: {e}[/red]")
                safe_print("[yellow]💡 请检查模型配置和网络连接[/yellow]")

        return asyncio.run(run_chain_reasoning())

    def chain_run(
        self,
        config_file: str,
        input_data: str = None,
        model: str = None,
        base_url: str = None,
        api_key: str = None,
        show_details: bool = False,
        **kwargs,
    ):
        """运行自定义的Chain of Thought配置文件
        
        Args:
            config_file: YAML格式的链条配置文件路径
            input_data: 输入数据，会作为query传入
            model: 使用的模型（覆盖配置文件中的设置）
            base_url: API服务地址
            api_key: API密钥
            show_details: 是否显示详细执行信息
        """
        import asyncio
        import yaml
        import os
        from pathlib import Path
        from maque.mllm.chain_of_thought_client import ChainOfThoughtClient, LinearStep, ExecutionConfig
        from maque.mllm.openaiclient import OpenAIClient

        async def run_chain_config():
            try:
                # 读取配置文件
                config_path = Path(config_file)
                if not config_path.exists():
                    safe_print(f"[red]❌ 配置文件不存在: {config_file}[/red]")
                    return

                safe_print(f"[bold green]📋 运行Chain of Thought配置[/bold green]")
                safe_print(f"[cyan]📁 配置文件: {config_file}[/cyan]")

                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # 从配置文件和命令行参数合并设置
                mllm_config = self.cli.maque_config.get("mllm", {})
                
                # 模型配置优先级: 命令行 > 配置文件 > 全局配置
                final_model = model or config.get('model') or mllm_config.get("model", "gemma3:latest")
                final_base_url = base_url or config.get('base_url') or mllm_config.get("base_url", "http://localhost:11434/v1")
                final_api_key = api_key or config.get('api_key') or mllm_config.get("api_key", "EMPTY")

                # 获取输入数据
                query = input_data or config.get('query', '')
                if not query:
                    safe_print("[red]❌ 缺少输入数据，请通过 --input-data 参数或在配置文件中的 'query' 字段指定[/red]")
                    return

                safe_print(f"[cyan]📝 输入: {query}[/cyan]")
                safe_print(f"[dim]🔧 模型: {final_model}[/dim]\n")

                # 初始化客户端
                openai_client = OpenAIClient(model=final_model, base_url=final_base_url, api_key=final_api_key)
                
                # 执行配置
                exec_config = ExecutionConfig(
                    enable_monitoring=config.get('enable_monitoring', True),
                    enable_progress=show_details,
                    log_level="INFO" if show_details else "WARNING",
                    step_timeout=config.get('step_timeout'),
                    chain_timeout=config.get('chain_timeout'),
                    max_retries=config.get('max_retries', 0),
                    retry_delay=config.get('retry_delay', 1.0)
                )
                
                chain_client = ChainOfThoughtClient(openai_client, exec_config)

                # 构建步骤
                steps = config.get('steps', [])
                if not steps:
                    safe_print("[red]❌ 配置文件中没有定义步骤[/red]")
                    return

                def create_config_step(step_config):
                    step_name = step_config['name']
                    system_prompt = step_config.get('system_prompt', '')
                    user_prompt = step_config.get('user_prompt', '')
                    
                    def prepare_messages(context):
                        # 处理模板变量
                        template_vars = {
                            'query': context.query,
                            'previous_responses': '\n\n'.join([f"[{s.step_name}]: {s.response}" for s in context.history])
                        }
                        
                        # 添加自定义变量
                        custom_vars = context.get_custom_data('template_vars', {})
                        template_vars.update(custom_vars)
                        
                        messages = []
                        if system_prompt:
                            messages.append({
                                "role": "system", 
                                "content": system_prompt.format(**template_vars)
                            })
                        
                        messages.append({
                            "role": "user",
                            "content": user_prompt.format(**template_vars)
                        })
                        
                        return messages
                    
                    # 获取模型参数
                    model_params = step_config.get('model_params', {})
                    model_params.update(kwargs)  # 命令行参数覆盖
                    
                    return LinearStep(
                        name=step_name,
                        prepare_messages_fn=prepare_messages,
                        model_params=model_params
                    )

                # 创建所有步骤
                chain_steps = [create_config_step(step_config) for step_config in steps]
                
                # 创建和执行链条
                chain_name = config.get('name', 'custom_chain')
                first_step = chain_client.create_linear_chain(chain_steps, chain_name)
                
                # 添加自定义模板变量到上下文
                context = chain_client.create_context({"query": query})
                if config.get('template_vars'):
                    context.add_custom_data('template_vars', config['template_vars'])
                
                result_context = await chain_client.execute_chain(
                    first_step, context, show_step_details=show_details
                )

                # 显示结果
                if result_context.history:
                    safe_print(f"\n[bold blue]🎯 {config.get('name', 'Chain')} 执行结果[/bold blue]")
                    safe_print(f"[dim]{'=' * 60}[/dim]")
                    
                    for step_result in result_context.history:
                        step_display = step_result.step_name.replace('_', ' ').title()
                        safe_print(f"\n[bold cyan]📝 {step_display}[/bold cyan]")
                        safe_print(f"[green]{step_result.response}[/green]")
                    
                    # 执行摘要
                    summary = result_context.get_execution_summary()
                    safe_print(f"\n[dim]📊 执行统计: {summary['total_steps']} 个步骤, "
                              f"耗时 {summary['total_execution_time']:.2f}秒, "
                              f"成功率 {summary['success_rate']*100:.1f}%[/dim]")
                else:
                    safe_print("[red]❌ 链条执行失败，没有生成结果[/red]")

            except yaml.YAMLError as e:
                safe_print(f"[red]❌ YAML配置文件解析错误: {e}[/red]")
            except FileNotFoundError as e:
                safe_print(f"[red]❌ 配置文件未找到: {e}[/red]")
            except Exception as e:
                safe_print(f"[red]❌ Chain执行失败: {e}[/red]")
                safe_print("[yellow]💡 请检查配置文件格式和模型连接[/yellow]")

        return asyncio.run(run_chain_config())
