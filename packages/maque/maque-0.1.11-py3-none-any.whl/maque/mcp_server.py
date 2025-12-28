"""
maque MCP Server - API 文档查询 + LLM 调用服务

提供两大功能：
1. API 文档查询：让 AI Agent 查询 maque 的可用功能
2. LLM 调用：直接调用配置好的 LLM 进行推理

启动方式:
    python -m maque.mcp_server

配置 Claude Code (~/.claude.json):
    {
        "mcpServers": {
            "maque": {
                "command": "python",
                "args": ["-m", "maque.mcp_server"]
            }
        }
    }
"""

import ast
import asyncio
import inspect
import pkgutil
import importlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# 核心模块列表（按重要性排序）- 只保留模块名，其他信息自动提取
CORE_MODULES = [
    "mllm",       # LLM/MLLM 客户端
    "embedding",  # 文本/多模态 Embedding
    "async_api",  # 异步并发执行
    "retriever",  # RAG 检索
    "clustering", # 聚类分析
    "io",         # 文件 IO
    "performance",# 性能监控
    "llm",        # LLM 推理服务
]


def get_module_exports(module_name: str) -> list[str]:
    """从模块的 __init__.py 自动获取 __all__ 导出列表"""
    root = get_maque_root()
    init_file = root / module_name / "__init__.py"

    if not init_file.exists():
        return []

    try:
        source = init_file.read_text(encoding='utf-8')
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, ast.List):
                            return [
                                elt.value for elt in node.value.elts
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                            ]
        return []
    except Exception:
        return []


def get_module_docstring(module_name: str) -> tuple[str, str]:
    """
    从模块的 __init__.py 自动获取 docstring

    Returns:
        (description, example): 描述和示例代码
    """
    root = get_maque_root()
    init_file = root / module_name / "__init__.py"

    if not init_file.exists():
        return ("", "")

    try:
        source = init_file.read_text(encoding='utf-8')
        tree = ast.parse(source)
        docstring = ast.get_docstring(tree) or ""

        # 分离描述和示例
        if "Example:" in docstring:
            parts = docstring.split("Example:", 1)
            description = parts[0].strip()
            example = parts[1].strip() if len(parts) > 1 else ""
        else:
            description = docstring.split("\n\n")[0].strip()  # 取第一段作为描述
            example = ""

        return (description, example)
    except Exception:
        return ("", "")


@dataclass
class APIInfo:
    """API 信息"""
    name: str
    module: str
    type: str  # 'class' | 'function' | 'module'
    signature: str
    docstring: str
    example: str = ""
    methods: list = None  # 类的主要方法列表


def get_maque_root() -> Path:
    """获取 maque 包的根目录"""
    import maque
    return Path(maque.__file__).parent


def extract_docstring_from_source(file_path: Path, target_name: str) -> Optional[str]:
    """从源码中提取指定类或函数的 docstring（不导入模块）"""
    try:
        source = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == target_name:
                    return ast.get_docstring(node)
        return None
    except Exception:
        return None


def extract_class_info_from_source(file_path: Path, class_name: str) -> Optional[APIInfo]:
    """从源码提取类信息（包括方法列表）"""
    try:
        source = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                docstring = ast.get_docstring(node) or "无文档"

                # 提取 __init__ 签名
                init_sig = ""
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        args = []
                        for arg in item.args.args[1:]:  # 跳过 self
                            arg_str = arg.arg
                            if arg.annotation:
                                arg_str += f": {ast.unparse(arg.annotation)}"
                            args.append(arg_str)

                        # 处理默认值
                        defaults = item.args.defaults
                        num_defaults = len(defaults)
                        num_args = len(args)
                        for i, default in enumerate(defaults):
                            arg_idx = num_args - num_defaults + i
                            try:
                                default_val = ast.unparse(default)
                                args[arg_idx] += f" = {default_val}"
                            except Exception:
                                pass

                        init_sig = f"({', '.join(args)})"

                    # 提取公开方法（不以 _ 开头，排除 __init__ 等）
                    elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not item.name.startswith('_'):
                            method_doc = ast.get_docstring(item) or ""
                            method_desc = method_doc.split('\n')[0] if method_doc else ""
                            # 构建方法签名
                            method_args = []
                            for arg in item.args.args:
                                if arg.arg in ('self', 'cls'):
                                    continue
                                method_args.append(arg.arg)
                            prefix = "async " if isinstance(item, ast.AsyncFunctionDef) else ""
                            methods.append({
                                "name": item.name,
                                "signature": f"{prefix}{item.name}({', '.join(method_args)})",
                                "description": method_desc[:100] if len(method_desc) > 100 else method_desc,
                            })

                return APIInfo(
                    name=class_name,
                    module=str(file_path.relative_to(get_maque_root().parent)).replace('/', '.').replace('.py', ''),
                    type='class',
                    signature=f"class {class_name}{init_sig}",
                    docstring=docstring[:1000] if len(docstring) > 1000 else docstring,
                    methods=methods[:10] if methods else None,  # 最多 10 个方法
                )
        return None
    except Exception as e:
        return None


def search_in_module(module_path: Path, keyword: str) -> list[APIInfo]:
    """在模块中搜索关键词"""
    results = []
    keyword_lower = keyword.lower()

    try:
        source = module_path.read_text(encoding='utf-8')
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node) or ""
                if keyword_lower in node.name.lower() or keyword_lower in docstring.lower():
                    info = extract_class_info_from_source(module_path, node.name)
                    if info:
                        results.append(info)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 跳过私有函数
                if node.name.startswith('_'):
                    continue
                docstring = ast.get_docstring(node) or ""
                if keyword_lower in node.name.lower() or keyword_lower in docstring.lower():
                    # 构建签名
                    args = []
                    for arg in node.args.args:
                        arg_str = arg.arg
                        if arg.annotation:
                            try:
                                arg_str += f": {ast.unparse(arg.annotation)}"
                            except Exception:
                                pass
                        args.append(arg_str)

                    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
                    sig = f"{prefix} {node.name}({', '.join(args)})"

                    results.append(APIInfo(
                        name=node.name,
                        module=str(module_path.relative_to(get_maque_root().parent)).replace('/', '.').replace('.py', ''),
                        type='function',
                        signature=sig,
                        docstring=docstring[:300] if len(docstring) > 300 else docstring,
                    ))
    except Exception:
        pass

    return results


def search_maque(keyword: str) -> list[APIInfo]:
    """搜索 maque 中的 API"""
    results = []
    root = get_maque_root()

    for py_file in root.rglob("*.py"):
        # 跳过测试和私有模块
        if '__pycache__' in str(py_file) or py_file.name.startswith('_'):
            continue
        results.extend(search_in_module(py_file, keyword))

    return results[:20]  # 限制结果数量


def get_module_info(module_name: str) -> str:
    """获取模块的详细使用说明（自动从 docstring 提取）"""
    description, example = get_module_docstring(module_name)

    if example:
        return example

    if description:
        return description

    return f"模块 {module_name} 暂无详细使用示例。请使用 search_maque_api 搜索具体功能。"


def list_all_modules() -> str:
    """列出所有核心模块（自动从代码提取）"""
    lines = ["# maque 核心模块\n"]

    for module_name in CORE_MODULES:
        description, _ = get_module_docstring(module_name)
        exports = get_module_exports(module_name)

        # 取描述的第一行
        desc_line = description.split('\n')[0] if description else "无描述"

        lines.append(f"## {module_name}")
        lines.append(f"  {desc_line}")
        if exports:
            # 只显示前 5 个导出
            display_exports = exports[:5]
            suffix = f" ... (+{len(exports)-5})" if len(exports) > 5 else ""
            lines.append(f"  主要导出: {', '.join(display_exports)}{suffix}")
        lines.append("")

    lines.append("\n使用 `get_module_usage(module_name)` 获取详细用法")
    return "\n".join(lines)


# CLI 命令组映射
CLI_GROUPS = {
    "config": "配置管理",
    "mllm": "多模态 LLM 操作",
    "llm": "LLM 推理服务",
    "data": "数据处理工具",
    "embedding": "Embedding 服务",
    "system": "系统工具",
    "git": "Git 辅助命令",
    "service": "服务管理",
    "doctor": "诊断工具",
    "mcp": "MCP 服务",
}


@dataclass
class CLICommand:
    """CLI 命令信息"""
    name: str
    group: str  # 空字符串表示顶级命令
    description: str
    signature: str


def extract_cli_commands() -> list[CLICommand]:
    """提取所有 CLI 命令"""
    commands = []
    root = get_maque_root()

    # 1. 提取顶级命令（从 __main__.py 的 NewCli 类）
    main_file = root / "__main__.py"
    if main_file.exists():
        commands.extend(_extract_commands_from_class(main_file, "NewCli", ""))

    # 2. 提取分组命令（从 cli/groups/*.py）
    groups_dir = root / "cli" / "groups"
    if groups_dir.exists():
        for py_file in groups_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            # 从文件名推断 group 名称
            group_name = py_file.stem
            if group_name == "mllm_simple":
                continue  # 跳过简化版
            commands.extend(_extract_commands_from_file(py_file, group_name))

    return commands


def _extract_commands_from_class(file_path: Path, class_name: str, group: str) -> list[CLICommand]:
    """从指定类中提取命令"""
    commands = []
    try:
        source = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # 跳过私有方法和特殊方法
                        if item.name.startswith('_'):
                            continue
                        # 跳过属性方法（没有实际功能）
                        if any(isinstance(d, ast.Name) and d.id == 'property' for d in item.decorator_list):
                            continue

                        docstring = ast.get_docstring(item) or "无描述"
                        # 只取 docstring 第一行
                        desc = docstring.split('\n')[0].strip()

                        # 构建签名
                        args = []
                        for arg in item.args.args:
                            if arg.arg in ('self', 'cls'):
                                continue
                            args.append(arg.arg)
                        sig = f"({', '.join(args)})" if args else "()"

                        commands.append(CLICommand(
                            name=item.name,
                            group=group,
                            description=desc,
                            signature=sig,
                        ))
    except Exception:
        pass
    return commands


def _extract_commands_from_file(file_path: Path, group_name: str) -> list[CLICommand]:
    """从文件中提取 Group 类的命令"""
    commands = []
    try:
        source = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.endswith('Group'):
                commands.extend(_extract_commands_from_class(file_path, node.name, group_name))
                break  # 每个文件只处理一个 Group 类
    except Exception:
        pass
    return commands


def list_cli_commands() -> str:
    """列出所有 CLI 命令"""
    commands = extract_cli_commands()

    # 分组显示
    top_level = [c for c in commands if not c.group]
    grouped = {}
    for c in commands:
        if c.group:
            if c.group not in grouped:
                grouped[c.group] = []
            grouped[c.group].append(c)

    lines = ["# maque CLI 命令\n"]

    # 顶级命令
    if top_level:
        lines.append("## 顶级命令")
        lines.append("用法: `maque <command> [args]`\n")
        for cmd in sorted(top_level, key=lambda x: x.name):
            lines.append(f"- **{cmd.name}**{cmd.signature}: {cmd.description}")
        lines.append("")

    # 分组命令
    lines.append("## 分组命令")
    lines.append("用法: `maque <group> <command> [args]`\n")

    for group_name in sorted(grouped.keys()):
        group_desc = CLI_GROUPS.get(group_name, "")
        lines.append(f"### {group_name}" + (f" - {group_desc}" if group_desc else ""))
        for cmd in sorted(grouped[group_name], key=lambda x: x.name):
            lines.append(f"- **{cmd.name}**{cmd.signature}: {cmd.description}")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# LLM 客户端功能
# =============================================================================

def _load_llm_config() -> Dict[str, Any]:
    """加载 LLM 配置（从 maque 配置文件）"""
    from maque import yaml_load

    # 配置搜索路径
    search_paths = [
        Path.cwd() / "maque_config.yaml",
        Path.home() / ".maque" / "config.yaml",
    ]

    # 检查项目根目录
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            project_config = current / "maque_config.yaml"
            if project_config not in search_paths:
                search_paths.insert(1, project_config)
            break
        current = current.parent

    # 默认配置
    default_config = {
        "base_url": "http://localhost:11434/v1",
        "api_key": "EMPTY",
        "model": "gemma3:4b",
    }

    for path in search_paths:
        if path.exists():
            try:
                config = yaml_load(str(path))
                if config and "mllm" in config:
                    mllm_config = config["mllm"]
                    return {
                        "base_url": mllm_config.get("base_url", default_config["base_url"]),
                        "api_key": mllm_config.get("api_key", default_config["api_key"]),
                        "model": mllm_config.get("model", default_config["model"]),
                    }
            except Exception:
                continue

    return default_config


def _get_llm_client():
    """获取 LLMClient 实例"""
    from maque.mllm import LLMClient
    from maque.mllm.response_cache import ResponseCacheConfig

    config = _load_llm_config()
    return LLMClient(
        base_url=config["base_url"],
        api_key=config["api_key"],
        model=config["model"],
        cache=ResponseCacheConfig.disabled(),  # MCP 服务不需要响应缓存
    )


async def llm_chat(
    messages: List[Dict[str, str]],
    model: str = None,
    max_tokens: int = None,
    temperature: float = None,
) -> str:
    """
    调用 LLM 进行单条聊天

    Args:
        messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
        model: 模型名称（可选，使用配置默认值）
        max_tokens: 最大生成 token 数
        temperature: 温度参数

    Returns:
        LLM 生成的回复
    """
    client = _get_llm_client()

    kwargs = {}
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    if temperature is not None:
        kwargs["temperature"] = temperature

    result = await client.chat_completions(
        messages=messages,
        model=model,
        **kwargs,
    )
    return result


async def llm_chat_batch(
    messages_list: List[List[Dict[str, str]]],
    model: str = None,
    max_tokens: int = None,
    temperature: float = None,
) -> List[str]:
    """
    批量调用 LLM

    Args:
        messages_list: 消息列表的列表
        model: 模型名称
        max_tokens: 最大生成 token 数
        temperature: 温度参数

    Returns:
        LLM 生成的回复列表
    """
    client = _get_llm_client()

    kwargs = {}
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    if temperature is not None:
        kwargs["temperature"] = temperature

    results = await client.chat_completions_batch(
        messages_list=messages_list,
        model=model,
        show_progress=False,
        **kwargs,
    )
    return results


def llm_models() -> List[str]:
    """获取可用模型列表"""
    client = _get_llm_client()
    return client.model_list()


def llm_config() -> Dict[str, Any]:
    """获取当前 LLM 配置"""
    config = _load_llm_config()
    # 隐藏 API key 的部分内容
    api_key = config.get("api_key", "")
    if api_key and len(api_key) > 8:
        config["api_key"] = api_key[:4] + "****" + api_key[-4:]
    return config


# 创建 MCP Server
server = Server("maque-docs")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        # ===== API 文档查询工具 =====
        Tool(
            name="search_maque_api",
            description="搜索 maque 库中的 API（类、函数、模块）。用于查找可复用的功能，避免重复造轮子。",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词，如 'embedding', 'llm', 'async', 'retry' 等"
                    }
                },
                "required": ["keyword"]
            }
        ),
        Tool(
            name="get_module_usage",
            description="获取 maque 指定模块的详细使用示例。",
            inputSchema={
                "type": "object",
                "properties": {
                    "module": {
                        "type": "string",
                        "description": "模块名称，如 'mllm', 'embedding', 'async_api', 'io', 'retriever', 'clustering'"
                    }
                },
                "required": ["module"]
            }
        ),
        Tool(
            name="list_maque_modules",
            description="列出 maque 所有核心模块及其功能概述。",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_cli_commands",
            description="列出 maque 所有可用的 CLI 命令，包括顶级命令和分组命令。",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        # ===== LLM 调用工具 =====
        Tool(
            name="llm_chat",
            description="调用 LLM 进行单条聊天。使用 maque 配置文件中的 LLM 设置。",
            inputSchema={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "description": "消息列表，格式为 [{\"role\": \"user\", \"content\": \"...\"}]",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                                "content": {"type": "string"}
                            },
                            "required": ["role", "content"]
                        }
                    },
                    "model": {
                        "type": "string",
                        "description": "模型名称（可选，使用配置默认值）"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "最大生成 token 数"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "温度参数 (0-2)"
                    }
                },
                "required": ["messages"]
            }
        ),
        Tool(
            name="llm_chat_batch",
            description="批量调用 LLM，适合处理多个独立请求。",
            inputSchema={
                "type": "object",
                "properties": {
                    "messages_list": {
                        "type": "array",
                        "description": "消息列表的列表，每个元素是一个完整的对话",
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string"},
                                    "content": {"type": "string"}
                                }
                            }
                        }
                    },
                    "model": {
                        "type": "string",
                        "description": "模型名称"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "最大生成 token 数"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "温度参数"
                    }
                },
                "required": ["messages_list"]
            }
        ),
        Tool(
            name="llm_models",
            description="获取可用的 LLM 模型列表。",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="llm_config",
            description="获取当前 LLM 配置信息（base_url, model 等）。",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""

    # ===== API 文档查询工具 =====
    if name == "search_maque_api":
        keyword = arguments.get("keyword", "")
        results = search_maque(keyword)

        if not results:
            return [TextContent(type="text", text=f"未找到与 '{keyword}' 相关的 API")]

        lines = [f"# 搜索结果: '{keyword}'\n"]
        for api in results:
            lines.append(f"## {api.name}")
            lines.append(f"  模块: `{api.module}`")
            lines.append(f"  类型: {api.type}")
            lines.append(f"  签名: `{api.signature}`")
            if api.docstring:
                lines.append(f"  说明: {api.docstring}")
            # 展示类的主要方法
            if api.methods:
                lines.append(f"  主要方法:")
                for method in api.methods:
                    desc = f" - {method['description']}" if method['description'] else ""
                    lines.append(f"    - `{method['signature']}`{desc}")
            lines.append("")

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "get_module_usage":
        module = arguments.get("module", "")
        usage = get_module_info(module)
        return [TextContent(type="text", text=f"# {module} 模块使用示例\n\n```python{usage}\n```")]

    elif name == "list_maque_modules":
        return [TextContent(type="text", text=list_all_modules())]

    elif name == "list_cli_commands":
        return [TextContent(type="text", text=list_cli_commands())]

    # ===== LLM 调用工具 =====
    elif name == "llm_chat":
        try:
            messages = arguments.get("messages", [])
            model = arguments.get("model")
            max_tokens = arguments.get("max_tokens")
            temperature = arguments.get("temperature")

            result = await llm_chat(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return [TextContent(type="text", text=result)]
        except Exception as e:
            return [TextContent(type="text", text=f"LLM 调用失败: {str(e)}")]

    elif name == "llm_chat_batch":
        try:
            messages_list = arguments.get("messages_list", [])
            model = arguments.get("model")
            max_tokens = arguments.get("max_tokens")
            temperature = arguments.get("temperature")

            results = await llm_chat_batch(
                messages_list=messages_list,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            # 格式化输出
            output_lines = ["# 批量调用结果\n"]
            for i, result in enumerate(results, 1):
                output_lines.append(f"## 结果 {i}")
                output_lines.append(result)
                output_lines.append("")
            return [TextContent(type="text", text="\n".join(output_lines))]
        except Exception as e:
            return [TextContent(type="text", text=f"批量 LLM 调用失败: {str(e)}")]

    elif name == "llm_models":
        try:
            models = llm_models()
            if models:
                lines = ["# 可用模型列表\n"]
                for model in models:
                    lines.append(f"- {model}")
                return [TextContent(type="text", text="\n".join(lines))]
            else:
                return [TextContent(type="text", text="未获取到模型列表，请检查 LLM 服务是否正常运行")]
        except Exception as e:
            return [TextContent(type="text", text=f"获取模型列表失败: {str(e)}")]

    elif name == "llm_config":
        try:
            config = llm_config()
            lines = ["# 当前 LLM 配置\n"]
            for key, value in config.items():
                lines.append(f"- **{key}**: {value}")
            return [TextContent(type="text", text="\n".join(lines))]
        except Exception as e:
            return [TextContent(type="text", text=f"获取配置失败: {str(e)}")]

    return [TextContent(type="text", text=f"未知工具: {name}")]


async def main_stdio():
    """以 stdio 模式启动 MCP Server（Claude Code 自动管理）"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main_sse(host: str = "0.0.0.0", port: int = 8765):
    """
    以 SSE 模式启动 MCP Server（独立 HTTP 服务）

    启动: python -m maque.mcp_server --sse --port 8765
    配置: claude mcp add maque-remote --transport sse --url http://localhost:8765/sse
    """
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    import uvicorn

    sse = SseServerTransport("/messages")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
        ]
    )

    print(f"🚀 MCP Server (SSE) running at http://{host}:{port}")
    print(f"   配置命令: claude mcp add maque --transport sse --url http://localhost:{port}/sse")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import sys
    import asyncio

    if "--sse" in sys.argv:
        # SSE 模式：独立 HTTP 服务
        port = 8765
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        main_sse(port=port)
    else:
        # stdio 模式：Claude Code 自动管理
        asyncio.run(main_stdio())
