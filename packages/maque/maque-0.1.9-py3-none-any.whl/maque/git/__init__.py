"""
Git 模块 - 纯 Python Git 操作

基于 Dulwich 实现，不依赖 git 客户端。
"""

try:
    from .pure_git import (
        PureGitRepo,
        GitStatus,
        GitCommitInfo,
        GitStashEntry,
        GitBlameEntry,
    )
except ImportError:
    pass

__all__ = [
    'PureGitRepo',
    'GitStatus',
    'GitCommitInfo',
    'GitStashEntry',
    'GitBlameEntry',
]
