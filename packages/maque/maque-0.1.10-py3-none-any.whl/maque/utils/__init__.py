"""
工具模块 - 通用工具和辅助功能

整合了各种实用工具：颜色处理、字符串操作、距离计算、文件操作等
"""

# 基础工具（仅依赖标准库或核心依赖）
try:
    from .compress import *
    from .cursor import *
    from .net import *
    from .time import *
    from .distance import *
    from .ops import *  # string ops
    from .tar import *
    from .untar import *
except ImportError:
    pass  # 静默处理，避免启动时警告

# 需要 pandas 的模块（可选）
try:
    from .excel_helper import *
    from .helper_metrics import *
    from .helper_parser import *
except ImportError:
    pass  # pandas 未安装时静默跳过

# 核心工具（可能有循环依赖）
try:
    from .core import async_retry  # 只导入关键函数
except ImportError:
    # 简单的备用实现
    def async_retry(retry_times=3, retry_delay=1.0):
        def decorator(func):
            return func
        return decorator

# 颜色工具（可能有复杂依赖）
try:
    from .color import *
    from .constant import *  # color constants
    from .color_string import *
except ImportError:
    pass

# 路径工具
try:
    from .path import rel_to_abs, rel_path_join, ls, add_env_path
    relp = rel_to_abs  # alias
except ImportError:
    pass

__all__ = [
    'async_retry',
    # 其他具体导出项将根据实际模块内容确定
]