#!/usr/bin/env python3
"""
文件不可见字符清理工具

功能：
- 清理文件中的不间断空格(U+00A0)和其他常见不可见字符
- 支持单个文件或批量处理
- 自动备份原文件
- 提供详细的处理报告

使用方法：
    python clean_invisible_chars.py file.py
    python clean_invisible_chars.py *.py
    python clean_invisible_chars.py --dir /path/to/directory --pattern "*.py"
"""

import argparse
import glob
import os
import shutil
from pathlib import Path
from typing import List, Tuple


class InvisibleCharCleaner:
    """不可见字符清理器"""

    # 常见的需要清理的不可见字符映射
    CHAR_REPLACEMENTS = {
        "\u00a0": " ",  # 不间断空格 -> 普通空格
        "\u2000": " ",  # en quad -> 普通空格
        "\u2001": " ",  # em quad -> 普通空格
        "\u2002": " ",  # en space -> 普通空格
        "\u2003": " ",  # em space -> 普通空格
        "\u2004": " ",  # three-per-em space -> 普通空格
        "\u2005": " ",  # four-per-em space -> 普通空格
        "\u2006": " ",  # six-per-em space -> 普通空格
        "\u2007": " ",  # figure space -> 普通空格
        "\u2008": " ",  # punctuation space -> 普通空格
        "\u2009": " ",  # thin space -> 普通空格
        "\u200a": " ",  # hair space -> 普通空格
        "\u200b": "",  # 零宽空格 -> 删除
        "\u200c": "",  # 零宽非连接符 -> 删除
        "\u200d": "",  # 零宽连接符 -> 删除
        "\u2060": "",  # 字间连接符 -> 删除
        "\ufeff": "",  # 字节顺序标记(BOM) -> 删除
    }

    def __init__(self, backup=True, verbose=True):
        """
        初始化清理器

        Args:
            backup: 是否备份原文件
            verbose: 是否显示详细信息
        """
        self.backup = backup
        self.verbose = verbose
        self.stats = {
            "files_processed": 0,
            "files_modified": 0,
            "chars_replaced": 0,
            "backup_created": 0,
        }

    def detect_invisible_chars(self, content: str) -> List[Tuple[str, int, str]]:
        """
        检测文件中的不可见字符

        Args:
            content: 文件内容

        Returns:
            检测到的不可见字符列表: [(字符, 数量, 描述)]
        """
        detected = []

        char_descriptions = {
            "\u00a0": "不间断空格",
            "\u2000": "en quad",
            "\u2001": "em quad",
            "\u2002": "en space",
            "\u2003": "em space",
            "\u2004": "three-per-em space",
            "\u2005": "four-per-em space",
            "\u2006": "six-per-em space",
            "\u2007": "figure space",
            "\u2008": "punctuation space",
            "\u2009": "thin space",
            "\u200a": "hair space",
            "\u200b": "零宽空格",
            "\u200c": "零宽非连接符",
            "\u200d": "零宽连接符",
            "\u2060": "字间连接符",
            "\ufeff": "字节顺序标记(BOM)",
        }

        for char, description in char_descriptions.items():
            count = content.count(char)
            if count > 0:
                detected.append((char, count, description))

        return detected

    def clean_content(self, content: str) -> Tuple[str, int]:
        """
        清理文本内容中的不可见字符

        Args:
            content: 原始内容

        Returns:
            (清理后的内容, 替换的字符数量)
        """
        cleaned_content = content
        total_replacements = 0

        for old_char, new_char in self.CHAR_REPLACEMENTS.items():
            count = cleaned_content.count(old_char)
            if count > 0:
                cleaned_content = cleaned_content.replace(old_char, new_char)
                total_replacements += count

        return cleaned_content, total_replacements

    def backup_file(self, file_path: Path) -> Path:
        """
        备份文件

        Args:
            file_path: 原文件路径

        Returns:
            备份文件路径
        """
        backup_path = file_path.with_suffix(file_path.suffix + ".backup")
        shutil.copy2(file_path, backup_path)
        self.stats["backup_created"] += 1
        return backup_path

    def clean_file(self, file_path: Path) -> bool:
        """
        清理单个文件

        Args:
            file_path: 文件路径

        Returns:
            是否有修改
        """
        try:
            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()

            # 检测不可见字符
            detected_chars = self.detect_invisible_chars(original_content)

            if not detected_chars:
                if self.verbose:
                    print(f"✓ {file_path}: 未发现不可见字符")
                return False

            # 显示检测结果
            if self.verbose:
                print(f"\n📁 处理文件: {file_path}")
                print("🔍 检测到的不可见字符:")
                for char, count, desc in detected_chars:
                    hex_code = f"U+{ord(char):04X}"
                    print(f"  - {desc} ({hex_code}): {count} 个")

            # 备份原文件
            if self.backup:
                backup_path = self.backup_file(file_path)
                if self.verbose:
                    print(f"💾 已备份到: {backup_path}")

            # 清理内容
            cleaned_content, replacements = self.clean_content(original_content)

            # 写入清理后的内容
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(cleaned_content)

            # 更新统计
            self.stats["files_modified"] += 1
            self.stats["chars_replaced"] += replacements

            if self.verbose:
                print(f"✅ 已清理 {replacements} 个不可见字符")

            return True

        except Exception as e:
            print(f"❌ 处理文件 {file_path} 时出错: {e}")
            return False
        finally:
            self.stats["files_processed"] += 1

    def clean_files(self, file_paths: List[Path]) -> None:
        """
        批量清理文件

        Args:
            file_paths: 文件路径列表
        """
        print(f"🚀 开始处理 {len(file_paths)} 个文件...")
        print("=" * 60)

        for file_path in file_paths:
            if file_path.is_file():
                self.clean_file(file_path)
            else:
                print(f"⚠️  跳过非文件: {file_path}")

        # 显示统计信息
        self.print_summary()

    def print_summary(self) -> None:
        """打印处理摘要"""
        print("\n" + "=" * 60)
        print("📊 处理摘要")
        print("=" * 60)
        print(f"处理文件数: {self.stats['files_processed']}")
        print(f"修改文件数: {self.stats['files_modified']}")
        print(f"清理字符数: {self.stats['chars_replaced']}")
        if self.backup:
            print(f"创建备份数: {self.stats['backup_created']}")
        print("✨ 处理完成!")


def find_files_by_pattern(directory: str, pattern: str) -> List[Path]:
    """
    根据模式查找文件

    Args:
        directory: 目录路径
        pattern: 文件模式 (如 "*.py")

    Returns:
        匹配的文件路径列表
    """
    search_pattern = os.path.join(directory, "**", pattern)
    file_paths = []

    for path_str in glob.glob(search_pattern, recursive=True):
        path = Path(path_str)
        if path.is_file():
            file_paths.append(path)

    return sorted(file_paths)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="清理文件中的不可见字符",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s file.py                     # 清理单个文件
  %(prog)s *.py                        # 清理当前目录下所有Python文件
  %(prog)s file1.py file2.py           # 清理多个文件
  %(prog)s --dir /path --pattern "*.py" # 递归清理目录下的Python文件
  %(prog)s --no-backup file.py         # 清理时不创建备份
  %(prog)s --quiet file.py             # 静默模式
        """,
    )

    parser.add_argument("files", nargs="*", help="要处理的文件路径")
    parser.add_argument("--dir", "-d", help="要处理的目录路径")
    parser.add_argument("--pattern", "-p", default="*", help='文件匹配模式 (如 "*.py")')
    parser.add_argument("--no-backup", action="store_true", help="不创建备份文件")
    parser.add_argument("--quiet", "-q", action="store_true", help="静默模式")

    args = parser.parse_args()

    # 收集要处理的文件
    file_paths = []

    if args.dir:
        # 目录模式
        if not os.path.isdir(args.dir):
            print(f"❌ 目录不存在: {args.dir}")
            return 1
        file_paths = find_files_by_pattern(args.dir, args.pattern)
        if not file_paths:
            print(f"❌ 在目录 {args.dir} 中未找到匹配 {args.pattern} 的文件")
            return 1
    elif args.files:
        # 文件列表模式
        for file_pattern in args.files:
            if "*" in file_pattern or "?" in file_pattern:
                # 通配符模式
                matched_files = glob.glob(file_pattern)
                if matched_files:
                    file_paths.extend([Path(f) for f in matched_files])
                else:
                    print(f"⚠️  未找到匹配 {file_pattern} 的文件")
            else:
                # 直接文件路径
                file_path = Path(file_pattern)
                if file_path.exists():
                    file_paths.append(file_path)
                else:
                    print(f"⚠️  文件不存在: {file_pattern}")
    else:
        # 没有指定文件或目录
        parser.print_help()
        return 1

    if not file_paths:
        print("❌ 没有找到要处理的文件")
        return 1

    # 创建清理器并处理文件
    cleaner = InvisibleCharCleaner(backup=not args.no_backup, verbose=not args.quiet)

    cleaner.clean_files(file_paths)
    return 0


if __name__ == "__main__":
    exit(main())
