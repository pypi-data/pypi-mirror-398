"""Git 命令组 - 代理到 Dulwich CLI

直接调用 dulwich CLI，支持所有 git 命令。
注意：实际的 git 命令在 __main__.py 中直接处理，绕过 fire。

Usage:
    spr git <command> [args...]

Examples:
    spr git status
    spr git add .
    spr git commit -m "message"
    spr git log
    spr git rebase main
    spr git stash push
    spr git cherry-pick <commit>
    spr git config -l
"""


class GitGroup:
    """Git 命令组 - 代理到 Dulwich CLI

    注意：此类仅作为占位符，实际的 git 命令处理在 __main__.py 中，
    直接调用 dulwich CLI 以避免 fire 参数解析问题。
    """

    def __init__(self, cli_instance):
        self.cli = cli_instance
