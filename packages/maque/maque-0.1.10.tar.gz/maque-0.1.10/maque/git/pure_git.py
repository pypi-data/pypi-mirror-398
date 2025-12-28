"""
Pure Git - 纯 Python Git 操作模块

基于 Dulwich 实现，不依赖 git 客户端。
提供面向对象的 API 进行 Git 仓库操作。

Usage:
    from maque.git import PureGitRepo

    # 初始化仓库
    repo = PureGitRepo.init('/path/to/repo')

    # 打开现有仓库
    repo = PureGitRepo.open('/path/to/repo')

    # 基本操作
    repo.add('.')
    repo.commit('Initial commit')
    print(repo.status())
    print(repo.log())

    # Rebase
    repo.rebase('main')  # rebase 当前分支到 main
    repo.rebase('main', interactive=True)  # 交互式 rebase

    # Stash
    repo.stash_push('WIP: my changes')
    repo.stash_pop()

    # Cherry-pick / Revert
    repo.cherry_pick('abc1234')
    repo.revert('abc1234')
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Callable
from dataclasses import dataclass

try:
    from dulwich import porcelain
    from dulwich.repo import Repo
    from dulwich.objects import Commit, Tree
    from dulwich.diff_tree import tree_changes
    DULWICH_AVAILABLE = True
except ImportError:
    DULWICH_AVAILABLE = False


@dataclass
class GitStatus:
    """Git 状态信息"""
    staged: List[str]      # 已暂存的文件
    unstaged: List[str]    # 已修改但未暂存的文件
    untracked: List[str]   # 未跟踪的文件

    def __str__(self):
        lines = []
        if self.staged:
            lines.append("Changes to be committed:")
            for f in self.staged:
                lines.append(f"  {f}")
        if self.unstaged:
            lines.append("Changes not staged for commit:")
            for f in self.unstaged:
                lines.append(f"  {f}")
        if self.untracked:
            lines.append("Untracked files:")
            for f in self.untracked:
                lines.append(f"  {f}")
        if not lines:
            lines.append("Nothing to commit, working tree clean")
        return "\n".join(lines)


@dataclass
class GitCommitInfo:
    """Git 提交信息"""
    sha: str
    message: str
    author: str
    date: str

    def __str__(self):
        return f"{self.sha[:7]} {self.message} ({self.author}, {self.date})"


@dataclass
class GitStashEntry:
    """Git stash 条目"""
    index: int
    message: str
    commit_sha: str

    def __str__(self):
        return f"stash@{{{self.index}}}: {self.message}"


@dataclass
class GitBlameEntry:
    """Git blame 条目"""
    commit_sha: str
    author: str
    line_number: int
    content: str

    def __str__(self):
        return f"{self.commit_sha[:7]} ({self.author}) {self.line_number}: {self.content}"


class PureGitRepo:
    """纯 Python Git 仓库操作类

    基于 Dulwich 实现，不依赖 git 客户端。
    """

    def __init__(self, path: str):
        """初始化仓库对象

        Args:
            path: 仓库路径
        """
        if not DULWICH_AVAILABLE:
            raise ImportError("dulwich 未安装，请运行: pip install dulwich")

        self.path = Path(path).resolve()
        self._repo: Optional[Repo] = None
        self._author_name: Optional[str] = None
        self._author_email: Optional[str] = None

    @property
    def repo(self) -> Repo:
        """获取 Dulwich Repo 对象"""
        if self._repo is None:
            git_dir = self.path / '.git'
            if git_dir.exists():
                self._repo = Repo(str(self.path))
            else:
                raise ValueError(f"不是有效的 Git 仓库: {self.path}")
        return self._repo

    def set_author(self, name: str, email: str) -> 'PureGitRepo':
        """设置提交作者信息

        Args:
            name: 作者名称
            email: 作者邮箱

        Returns:
            self，支持链式调用
        """
        self._author_name = name
        self._author_email = email
        return self

    @property
    def _author(self) -> Optional[bytes]:
        """获取作者字符串"""
        if self._author_name and self._author_email:
            return f"{self._author_name} <{self._author_email}>".encode('utf-8')
        return None

    # =========================================================================
    # 仓库操作
    # =========================================================================

    @classmethod
    def init(cls, path: str) -> 'PureGitRepo':
        """初始化新仓库

        Args:
            path: 仓库路径

        Returns:
            PureGitRepo 实例
        """
        if not DULWICH_AVAILABLE:
            raise ImportError("dulwich 未安装，请运行: pip install dulwich")

        path = Path(path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        porcelain.init(str(path))
        return cls(str(path))

    @classmethod
    def clone(cls, url: str, path: str,
              username: str = None, password: str = None) -> 'PureGitRepo':
        """克隆远程仓库

        Args:
            url: 远程仓库 URL
            path: 本地路径
            username: 用户名（可选）
            password: 密码/Token（可选）

        Returns:
            PureGitRepo 实例
        """
        if not DULWICH_AVAILABLE:
            raise ImportError("dulwich 未安装，请运行: pip install dulwich")

        porcelain.clone(url, path, username=username, password=password)
        return cls(path)

    @classmethod
    def open(cls, path: str = '.') -> 'PureGitRepo':
        """打开现有仓库

        Args:
            path: 仓库路径，默认为当前目录

        Returns:
            PureGitRepo 实例
        """
        repo = cls(path)
        # 验证是否是有效仓库
        _ = repo.repo
        return repo

    # =========================================================================
    # 基础操作
    # =========================================================================

    def add(self, paths: Union[str, List[str]] = '.') -> 'PureGitRepo':
        """添加文件到暂存区

        Args:
            paths: 文件路径或路径列表，'.' 表示所有文件

        Returns:
            self，支持链式调用
        """
        if isinstance(paths, str):
            if paths == '.':
                # 添加所有文件
                porcelain.add(str(self.path))
            else:
                porcelain.add(str(self.path), [paths])
        else:
            porcelain.add(str(self.path), paths)
        return self

    def commit(self, message: str, author: str = None) -> str:
        """提交更改

        Args:
            message: 提交信息
            author: 作者（格式: "Name <email>"），可选

        Returns:
            提交的 SHA
        """
        if author:
            author_bytes = author.encode('utf-8')
        else:
            author_bytes = self._author

        sha = porcelain.commit(
            str(self.path),
            message.encode('utf-8'),
            author=author_bytes,
            committer=author_bytes
        )
        return sha.decode('utf-8') if isinstance(sha, bytes) else str(sha)

    def status(self) -> GitStatus:
        """获取仓库状态

        Returns:
            GitStatus 对象
        """
        result = porcelain.status(str(self.path))

        staged = []
        unstaged = []
        untracked = []

        # result 是一个 GitStatus namedtuple
        if hasattr(result, 'staged'):
            # staged 是一个 dict: {'add': [...], 'modify': [...], 'delete': [...]}
            for action, files in result.staged.items():
                for f in files:
                    if isinstance(f, bytes):
                        f = f.decode('utf-8')
                    staged.append(f"{action}: {f}")

        if hasattr(result, 'unstaged'):
            for f in result.unstaged:
                if isinstance(f, bytes):
                    f = f.decode('utf-8')
                unstaged.append(f)

        if hasattr(result, 'untracked'):
            for f in result.untracked:
                if isinstance(f, bytes):
                    f = f.decode('utf-8')
                untracked.append(f)

        return GitStatus(staged=staged, unstaged=unstaged, untracked=untracked)

    def log(self, max_entries: int = 10) -> List[GitCommitInfo]:
        """获取提交日志

        Args:
            max_entries: 最大条目数

        Returns:
            GitCommitInfo 列表
        """
        from datetime import datetime
        from dulwich.walk import Walker

        commits = []
        try:
            # 使用底层 Walker API 获取提交历史
            walker = Walker(self.repo.object_store, [self.repo.head()])
            count = 0
            for entry in walker:
                if count >= max_entries:
                    break
                commit = entry.commit
                # commit.id 是 hex 字符串的 bytes，直接 decode
                sha = commit.id.decode('utf-8') if isinstance(commit.id, bytes) else str(commit.id)
                message = commit.message.decode('utf-8').strip().split('\n')[0]
                author = commit.author.decode('utf-8')
                date = datetime.fromtimestamp(commit.author_time).strftime('%Y-%m-%d %H:%M')
                commits.append(GitCommitInfo(sha=sha, message=message, author=author, date=date))
                count += 1
        except Exception:
            # 回退到 porcelain.log（会输出到 stdout）
            for entry in porcelain.log(str(self.path), max_entries=max_entries):
                if isinstance(entry, Commit):
                    sha = entry.id.decode('utf-8') if isinstance(entry.id, bytes) else str(entry.id)
                    message = entry.message.decode('utf-8').strip().split('\n')[0]
                    author = entry.author.decode('utf-8')
                    date = datetime.fromtimestamp(entry.author_time).strftime('%Y-%m-%d %H:%M')
                    commits.append(GitCommitInfo(sha=sha, message=message, author=author, date=date))
        return commits

    # =========================================================================
    # 分支操作
    # =========================================================================

    @property
    def branches(self) -> List[str]:
        """获取所有分支列表"""
        refs = porcelain.branch_list(str(self.path))
        return [ref.decode('utf-8') if isinstance(ref, bytes) else ref for ref in refs]

    @property
    def current_branch(self) -> str:
        """获取当前分支名"""
        try:
            head_ref = self.repo.refs.read_ref(b'HEAD')
            if head_ref and head_ref.startswith(b'ref: refs/heads/'):
                return head_ref[16:].decode('utf-8')
            # 如果是 detached HEAD
            with open(self.path / '.git' / 'HEAD', 'r') as f:
                content = f.read().strip()
                if content.startswith('ref: refs/heads/'):
                    return content[16:]
                return content[:7]  # detached HEAD, 返回短 SHA
        except Exception:
            return 'HEAD'

    def create_branch(self, name: str, ref: str = 'HEAD') -> 'PureGitRepo':
        """创建新分支

        Args:
            name: 分支名
            ref: 起始引用，默认为 HEAD

        Returns:
            self，支持链式调用
        """
        porcelain.branch_create(str(self.path), name)
        return self

    def checkout(self, branch: str) -> 'PureGitRepo':
        """切换分支

        Args:
            branch: 分支名

        Returns:
            self，支持链式调用
        """
        porcelain.checkout_branch(str(self.path), branch)
        return self

    def merge(self, branch: str) -> 'PureGitRepo':
        """合并分支

        Args:
            branch: 要合并的分支名

        Returns:
            self，支持链式调用
        """
        # Dulwich 的 merge 需要分支引用
        if not branch.startswith('refs/'):
            branch = f'refs/heads/{branch}'
        porcelain.merge(str(self.path), branch.encode('utf-8'))
        return self

    # =========================================================================
    # 远程操作
    # =========================================================================

    def fetch(self, remote: str = 'origin',
              username: str = None, password: str = None) -> 'PureGitRepo':
        """拉取远程更新（不合并）

        Args:
            remote: 远程仓库名
            username: 用户名
            password: 密码/Token

        Returns:
            self，支持链式调用
        """
        porcelain.fetch(str(self.path), remote, username=username, password=password)
        return self

    def pull(self, remote: str = 'origin',
             username: str = None, password: str = None) -> 'PureGitRepo':
        """拉取并合并远程更新

        Args:
            remote: 远程仓库名
            username: 用户名
            password: 密码/Token

        Returns:
            self，支持链式调用
        """
        porcelain.pull(str(self.path), remote, username=username, password=password)
        return self

    def push(self, remote: str = 'origin', branch: str = None,
             username: str = None, password: str = None) -> 'PureGitRepo':
        """推送到远程仓库

        Args:
            remote: 远程仓库名
            branch: 分支名，默认为当前分支
            username: 用户名
            password: 密码/Token

        Returns:
            self，支持链式调用
        """
        if branch is None:
            branch = self.current_branch
        ref = f'refs/heads/{branch}'
        porcelain.push(str(self.path), remote, ref, username=username, password=password)
        return self

    def remote_add(self, name: str, url: str) -> 'PureGitRepo':
        """添加远程仓库

        Args:
            name: 远程仓库名
            url: 远程仓库 URL

        Returns:
            self，支持链式调用
        """
        porcelain.remote_add(str(self.path), name, url)
        return self

    @property
    def remotes(self) -> Dict[str, str]:
        """获取远程仓库列表"""
        config = self.repo.get_config()
        remotes = {}
        for section in config.sections():
            if section[0] == b'remote':
                name = section[1].decode('utf-8')
                url = config.get(section, b'url')
                if url:
                    remotes[name] = url.decode('utf-8')
        return remotes

    # =========================================================================
    # 高级操作
    # =========================================================================

    def diff(self, ref1: str = None, ref2: str = None) -> str:
        """比较差异

        Args:
            ref1: 第一个引用（默认为 HEAD）
            ref2: 第二个引用（默认为工作区）

        Returns:
            diff 输出字符串
        """
        import io
        output = io.BytesIO()

        if ref1 is None and ref2 is None:
            # 比较 HEAD 和工作区
            porcelain.diff_tree(str(self.path), outstream=output)
        else:
            # 比较两个引用
            porcelain.diff_tree(str(self.path), ref1, ref2, outstream=output)

        return output.getvalue().decode('utf-8', errors='replace')

    def reset(self, ref: str = 'HEAD', mode: str = 'mixed') -> 'PureGitRepo':
        """重置到指定引用

        Args:
            ref: 目标引用
            mode: 重置模式 ('soft', 'mixed', 'hard')

        Returns:
            self，支持链式调用
        """
        if mode == 'hard':
            porcelain.reset(str(self.path), 'hard', ref)
        elif mode == 'soft':
            porcelain.reset(str(self.path), 'soft', ref)
        else:  # mixed
            porcelain.reset(str(self.path), 'mixed', ref)
        return self

    def tag(self, name: str, message: str = None) -> 'PureGitRepo':
        """创建标签

        Args:
            name: 标签名
            message: 标签消息（可选，创建 annotated tag）

        Returns:
            self，支持链式调用
        """
        if message:
            porcelain.tag_create(str(self.path), name, message=message.encode('utf-8'))
        else:
            porcelain.tag_create(str(self.path), name)
        return self

    @property
    def tags(self) -> List[str]:
        """获取所有标签列表"""
        tags = []
        for ref in self.repo.refs.keys():
            if isinstance(ref, bytes):
                ref = ref.decode('utf-8')
            if ref.startswith('refs/tags/'):
                tags.append(ref[10:])
        return tags

    def delete_tag(self, name: str) -> 'PureGitRepo':
        """删除标签

        Args:
            name: 标签名

        Returns:
            self，支持链式调用
        """
        porcelain.tag_delete(str(self.path), name)
        return self

    def delete_branch(self, name: str, force: bool = False) -> 'PureGitRepo':
        """删除分支

        Args:
            name: 分支名
            force: 强制删除（即使未合并）

        Returns:
            self，支持链式调用
        """
        porcelain.branch_delete(str(self.path), name, force=force)
        return self

    # =========================================================================
    # Rebase 操作
    # =========================================================================

    def rebase(
        self,
        upstream: str,
        onto: str = None,
        branch: str = None,
        interactive: bool = False,
        editor_callback: Callable[[bytes], bytes] = None,
    ) -> List[str]:
        """Rebase 当前分支到指定上游

        Args:
            upstream: 上游分支/提交
            onto: 目标提交（默认与 upstream 相同）
            branch: 要 rebase 的分支（默认当前分支）
            interactive: 是否交互式 rebase
            editor_callback: 交互式 rebase 时的编辑器回调

        Returns:
            新创建的提交 SHA 列表

        Raises:
            Exception: rebase 失败或发生冲突
        """
        upstream_bytes = upstream.encode('utf-8')
        onto_bytes = onto.encode('utf-8') if onto else None
        branch_bytes = branch.encode('utf-8') if branch else None

        result = porcelain.rebase(
            str(self.path),
            upstream_bytes,
            onto=onto_bytes,
            branch=branch_bytes,
            interactive=interactive,
        )
        return [sha.decode('utf-8') if isinstance(sha, bytes) else str(sha) for sha in result]

    def rebase_continue(self, interactive: bool = False) -> List[str]:
        """继续 rebase

        Args:
            interactive: 是否交互式 rebase

        Returns:
            新创建的提交 SHA 列表
        """
        result = porcelain.rebase(
            str(self.path),
            b'',  # upstream 不需要
            continue_rebase=True,
            interactive=interactive,
        )
        return [sha.decode('utf-8') if isinstance(sha, bytes) else str(sha) for sha in result]

    def rebase_abort(self) -> 'PureGitRepo':
        """中止 rebase

        Returns:
            self，支持链式调用
        """
        porcelain.rebase(str(self.path), b'', abort=True)
        return self

    def rebase_skip(self) -> List[str]:
        """跳过当前提交并继续 rebase

        Returns:
            新创建的提交 SHA 列表
        """
        result = porcelain.rebase(str(self.path), b'', skip=True)
        return [sha.decode('utf-8') if isinstance(sha, bytes) else str(sha) for sha in result]

    def is_rebasing(self) -> bool:
        """检查是否正在进行 rebase

        Returns:
            True 如果正在 rebase
        """
        rebase_merge = self.path / '.git' / 'rebase-merge'
        rebase_apply = self.path / '.git' / 'rebase-apply'
        return rebase_merge.exists() or rebase_apply.exists()

    # =========================================================================
    # Stash 操作
    # =========================================================================

    def stash_push(self, message: str = None, include_untracked: bool = False) -> str:
        """保存当前工作区到 stash

        Args:
            message: stash 消息
            include_untracked: 是否包含未跟踪的文件

        Returns:
            stash 提交的 SHA
        """
        result = porcelain.stash_push(
            str(self.path),
            message=message.encode('utf-8') if message else None,
            include_untracked=include_untracked,
        )
        return result.decode('utf-8') if isinstance(result, bytes) else str(result)

    def stash_pop(self, index: int = 0) -> 'PureGitRepo':
        """恢复 stash 并删除

        Args:
            index: stash 索引（默认 0，即最新）

        Returns:
            self，支持链式调用
        """
        porcelain.stash_pop(str(self.path), index)
        return self

    def stash_list(self) -> List[GitStashEntry]:
        """列出所有 stash

        Returns:
            GitStashEntry 列表
        """
        entries = []
        result = porcelain.stash_list(str(self.path))
        for idx, (sha, msg) in enumerate(result):
            sha_str = sha.decode('utf-8') if isinstance(sha, bytes) else str(sha)
            msg_str = msg.decode('utf-8') if isinstance(msg, bytes) else str(msg)
            entries.append(GitStashEntry(index=idx, message=msg_str, commit_sha=sha_str))
        return entries

    def stash_drop(self, index: int = 0) -> 'PureGitRepo':
        """删除 stash（不恢复）

        Args:
            index: stash 索引

        Returns:
            self，支持链式调用
        """
        porcelain.stash_drop(str(self.path), index)
        return self

    # =========================================================================
    # Cherry-pick / Revert
    # =========================================================================

    def cherry_pick(self, commit: str) -> str:
        """Cherry-pick 指定提交

        Args:
            commit: 提交 SHA 或引用

        Returns:
            新提交的 SHA
        """
        commit_bytes = commit.encode('utf-8')
        result = porcelain.cherry_pick(str(self.path), commit_bytes)
        return result.decode('utf-8') if isinstance(result, bytes) else str(result)

    def revert(self, commit: str) -> str:
        """撤销指定提交（创建新提交）

        Args:
            commit: 提交 SHA 或引用

        Returns:
            新提交的 SHA
        """
        commit_bytes = commit.encode('utf-8')
        result = porcelain.revert(str(self.path), commit_bytes)
        return result.decode('utf-8') if isinstance(result, bytes) else str(result)

    # =========================================================================
    # 文件操作
    # =========================================================================

    def clean(self, dry_run: bool = False) -> List[str]:
        """清理未跟踪的文件

        Args:
            dry_run: 仅显示将要删除的文件，不实际删除

        Returns:
            被删除（或将要删除）的文件列表
        """
        result = porcelain.clean(str(self.path), dry_run=dry_run)
        return [f.decode('utf-8') if isinstance(f, bytes) else str(f) for f in result]

    def rm(self, paths: Union[str, List[str]], cached: bool = False) -> 'PureGitRepo':
        """从仓库中移除文件

        Args:
            paths: 文件路径或路径列表
            cached: 仅从索引中移除，保留工作区文件

        Returns:
            self，支持链式调用
        """
        if isinstance(paths, str):
            paths = [paths]
        porcelain.rm(str(self.path), paths, cached=cached)
        return self

    def mv(self, src: str, dst: str) -> 'PureGitRepo':
        """移动/重命名文件

        Args:
            src: 源路径
            dst: 目标路径

        Returns:
            self，支持链式调用
        """
        porcelain.mv(str(self.path), [src], dst)
        return self

    # =========================================================================
    # 查询操作
    # =========================================================================

    def blame(self, path: str) -> List[GitBlameEntry]:
        """获取文件的 blame 信息

        Args:
            path: 文件路径

        Returns:
            GitBlameEntry 列表
        """
        entries = []
        result = porcelain.blame(str(self.path), path)
        for line_num, (commit, line_content) in enumerate(result, 1):
            if commit:
                sha = commit.id.decode('utf-8') if isinstance(commit.id, bytes) else str(commit.id)
                author = commit.author.decode('utf-8') if isinstance(commit.author, bytes) else str(commit.author)
                # 提取作者名（去掉 email）
                if '<' in author:
                    author = author.split('<')[0].strip()
            else:
                sha = '00000000'
                author = 'Not Committed'
            content = line_content.decode('utf-8') if isinstance(line_content, bytes) else str(line_content)
            entries.append(GitBlameEntry(
                commit_sha=sha,
                author=author,
                line_number=line_num,
                content=content.rstrip('\n'),
            ))
        return entries

    def show(self, ref: str = 'HEAD') -> str:
        """显示提交或对象的内容

        Args:
            ref: 引用（默认 HEAD）

        Returns:
            对象内容字符串
        """
        import io
        output = io.BytesIO()
        porcelain.show(str(self.path), ref, outstream=output)
        return output.getvalue().decode('utf-8', errors='replace')

    def ls_files(self, stage: bool = False) -> List[str]:
        """列出索引中的文件

        Args:
            stage: 是否显示暂存状态

        Returns:
            文件列表
        """
        result = porcelain.ls_files(str(self.path))
        return [f.decode('utf-8') if isinstance(f, bytes) else str(f) for f in result]

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """检查一个提交是否是另一个的祖先

        Args:
            ancestor: 祖先提交
            descendant: 后代提交

        Returns:
            True 如果 ancestor 是 descendant 的祖先
        """
        return porcelain.is_ancestor(
            str(self.path),
            ancestor.encode('utf-8'),
            descendant.encode('utf-8'),
        )

    def merge_base(self, commit1: str, commit2: str) -> str:
        """查找两个提交的公共祖先

        Args:
            commit1: 第一个提交
            commit2: 第二个提交

        Returns:
            公共祖先的 SHA
        """
        result = porcelain.merge_base(
            str(self.path),
            [commit1.encode('utf-8'), commit2.encode('utf-8')],
        )
        return result.decode('utf-8') if isinstance(result, bytes) else str(result)

    def describe(self, ref: str = 'HEAD') -> str:
        """描述提交（使用最近的标签）

        Args:
            ref: 引用

        Returns:
            描述字符串（如 v1.0.0-5-gabc1234）
        """
        result = porcelain.describe(str(self.path), ref)
        return result.decode('utf-8') if isinstance(result, bytes) else str(result)

    # =========================================================================
    # 辅助方法
    # =========================================================================

    def __repr__(self):
        return f"PureGitRepo('{self.path}')"

    def __str__(self):
        return f"Git repo at {self.path} (branch: {self.current_branch})"
